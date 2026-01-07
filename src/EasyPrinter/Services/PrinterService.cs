using System;
using System.Drawing;
using System.Drawing.Printing;
using System.IO;
using System.Linq;
using System.Printing;
using System.Windows.Media.Imaging;
using EasyPrinter.Models;
using PdfiumViewer;

namespace EasyPrinter.Services
{
    /// <summary>
    /// Сервис печати документов
    /// </summary>
    public class PrinterService
    {
        private readonly StatusService _statusService;
        private readonly ImageProcessingService _imageProcessing;

        public PrinterService(StatusService statusService, ImageProcessingService imageProcessing)
        {
            _statusService = statusService;
            _imageProcessing = imageProcessing;
        }

        /// <summary>
        /// Печать PDF файла
        /// </summary>
        public void PrintPdf(string filePath, PrintSettings settings)
        {
            var printer = _statusService.FindHPPrinter();
            if (printer == null)
                throw new InvalidOperationException("HP принтер не найден");

            using var document = PdfDocument.Load(filePath);

            using var printDocument = document.CreatePrintDocument();
            printDocument.PrinterSettings.PrinterName = printer.Name;
            printDocument.PrinterSettings.Copies = (short)settings.Copies;

            // Настройка диапазона страниц
            if (!string.IsNullOrEmpty(settings.PageRange))
            {
                var range = ParsePageRange(settings.PageRange, document.PageCount);
                printDocument.PrinterSettings.PrintRange = PrintRange.SomePages;
                printDocument.PrinterSettings.FromPage = range.from;
                printDocument.PrinterSettings.ToPage = range.to;
            }

            // Настройка размера бумаги
            SetPaperSize(printDocument.DefaultPageSettings, settings.PaperSize);

            // Настройка ориентации
            printDocument.DefaultPageSettings.Landscape = settings.Orientation == PageOrientation.Landscape;

            // Запуск печати
            printDocument.Print();
        }

        /// <summary>
        /// Печать изображения
        /// </summary>
        public void PrintImage(string filePath, PrintSettings settings)
        {
            var printer = _statusService.FindHPPrinter();
            if (printer == null)
                throw new InvalidOperationException("HP принтер не найден");

            using var image = Image.FromFile(filePath);

            // Применяем настройки изображения если есть изменения
            Image processedImage = image;
            if (settings.ImageAdjustments.HasChanges)
            {
                processedImage = _imageProcessing.ApplyAdjustments(image, settings.ImageAdjustments);
            }

            using var printDocument = new PrintDocument();
            printDocument.PrinterSettings.PrinterName = printer.Name;
            printDocument.PrinterSettings.Copies = (short)settings.Copies;

            // Настройка размера бумаги
            SetPaperSize(printDocument.DefaultPageSettings, settings.PaperSize);

            // Настройка ориентации
            printDocument.DefaultPageSettings.Landscape = settings.Orientation == PageOrientation.Landscape;

            printDocument.PrintPage += (sender, e) =>
            {
                if (e.Graphics == null) return;

                // Вычисляем размер для масштабирования
                var pageWidth = e.PageBounds.Width - e.PageSettings.Margins.Left - e.PageSettings.Margins.Right;
                var pageHeight = e.PageBounds.Height - e.PageSettings.Margins.Top - e.PageSettings.Margins.Bottom;

                // Применяем масштаб
                var scale = settings.Scale / 100.0f;
                pageWidth = (int)(pageWidth * scale);
                pageHeight = (int)(pageHeight * scale);

                // Сохраняем пропорции
                var imageRatio = (float)processedImage.Width / processedImage.Height;
                var pageRatio = pageWidth / pageHeight;

                int destWidth, destHeight;
                if (imageRatio > pageRatio)
                {
                    destWidth = (int)pageWidth;
                    destHeight = (int)(pageWidth / imageRatio);
                }
                else
                {
                    destHeight = (int)pageHeight;
                    destWidth = (int)(pageHeight * imageRatio);
                }

                // Центрируем изображение
                var x = e.PageSettings.Margins.Left + (int)((pageWidth / scale - destWidth) / 2);
                var y = e.PageSettings.Margins.Top + (int)((pageHeight / scale - destHeight) / 2);

                e.Graphics.DrawImage(processedImage, x, y, destWidth, destHeight);
            };

            printDocument.Print();

            // Освобождаем обработанное изображение если оно отличается от оригинала
            if (processedImage != image)
            {
                processedImage.Dispose();
            }
        }

        /// <summary>
        /// Печать документа (определяет тип по расширению)
        /// </summary>
        public void Print(string filePath, PrintSettings settings)
        {
            var extension = Path.GetExtension(filePath).ToLowerInvariant();

            switch (extension)
            {
                case ".pdf":
                    PrintPdf(filePath, settings);
                    break;
                case ".jpg":
                case ".jpeg":
                case ".png":
                case ".bmp":
                case ".tiff":
                case ".tif":
                case ".gif":
                    PrintImage(filePath, settings);
                    break;
                default:
                    throw new NotSupportedException($"Формат файла {extension} не поддерживается");
            }
        }

        /// <summary>
        /// Получить список доступных принтеров
        /// </summary>
        public string[] GetAvailablePrinters()
        {
            return PrinterSettings.InstalledPrinters.Cast<string>().ToArray();
        }

        private void SetPaperSize(PageSettings pageSettings, Models.PaperSize paperSize)
        {
            var rawKind = paperSize switch
            {
                Models.PaperSize.A4 => PaperKind.A4,
                Models.PaperSize.Letter => PaperKind.Letter,
                Models.PaperSize.Legal => PaperKind.Legal,
                Models.PaperSize.A5 => PaperKind.A5,
                Models.PaperSize.Envelope10 => PaperKind.Number10Envelope,
                Models.PaperSize.EnvelopeC5 => PaperKind.C5Envelope,
                Models.PaperSize.EnvelopeDL => PaperKind.DLEnvelope,
                _ => PaperKind.A4
            };

            foreach (System.Drawing.Printing.PaperSize ps in pageSettings.PrinterSettings.PaperSizes)
            {
                if (ps.Kind == rawKind)
                {
                    pageSettings.PaperSize = ps;
                    break;
                }
            }
        }

        private (int from, int to) ParsePageRange(string range, int totalPages)
        {
            // Простой парсинг вида "1-5" или "3"
            if (range.Contains('-'))
            {
                var parts = range.Split('-');
                if (parts.Length == 2 &&
                    int.TryParse(parts[0].Trim(), out int from) &&
                    int.TryParse(parts[1].Trim(), out int to))
                {
                    return (Math.Max(1, from), Math.Min(totalPages, to));
                }
            }
            else if (int.TryParse(range.Trim(), out int page))
            {
                return (page, page);
            }

            return (1, totalPages);
        }
    }
}
