using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Threading.Tasks;
using EasyPrinter.Models;
using NAPS2.Scan;
using PdfSharp.Drawing;
using PdfSharp.Pdf;

namespace EasyPrinter.Services
{
    /// <summary>
    /// Сервис сканирования документов через WIA
    /// </summary>
    public class ScannerService : IDisposable
    {
        private readonly ImageProcessingService _imageProcessing;
        private bool _isDisposed;

        public event EventHandler<ScanProgressEventArgs>? ScanProgress;
        public event EventHandler<ScanCompletedEventArgs>? ScanCompleted;

        public ScannerService(ImageProcessingService imageProcessing)
        {
            _imageProcessing = imageProcessing;
        }

        /// <summary>
        /// Выполнить сканирование
        /// </summary>
        public async Task<Image?> ScanAsync(ScanSettings settings)
        {
            try
            {
                ScanProgress?.Invoke(this, new ScanProgressEventArgs { Message = "Поиск сканера...", Progress = 10 });

                using var scanningContext = new ScanningContext();

                // Получаем список доступных сканеров
                var controller = new ScanController(scanningContext);
                var devices = await controller.GetDeviceList();

                // Ищем HP сканер
                ScanDevice? hpScanner = null;
                foreach (var device in devices)
                {
                    if (device.Name.Contains("HP", StringComparison.OrdinalIgnoreCase) ||
                        device.Name.Contains("1536", StringComparison.OrdinalIgnoreCase))
                    {
                        hpScanner = device;
                        break;
                    }
                }

                if (hpScanner == null && devices.Count > 0)
                {
                    // Берём первый доступный сканер
                    hpScanner = devices[0];
                }

                if (hpScanner == null)
                {
                    throw new InvalidOperationException("Сканер не найден");
                }

                ScanProgress?.Invoke(this, new ScanProgressEventArgs
                {
                    Message = $"Сканирование на {hpScanner.Name}...",
                    Progress = 30
                });

                // Настройки сканирования
                var scanOptions = new ScanOptions
                {
                    Device = hpScanner,
                    Dpi = (int)settings.Resolution,
                    PaperSource = settings.Source == ScanSource.ADF
                        ? NAPS2.Scan.PaperSource.Feeder
                        : NAPS2.Scan.PaperSource.Flatbed,
                    BitDepth = BitDepth.Color,
                    PageSize = PageSize.A4
                };

                // Выполняем сканирование
                Image? resultImage = null;

                await foreach (var image in controller.Scan(scanOptions))
                {
                    ScanProgress?.Invoke(this, new ScanProgressEventArgs
                    {
                        Message = "Обработка изображения...",
                        Progress = 70
                    });

                    // Конвертируем NAPS2 изображение в System.Drawing.Image
                    using var stream = new MemoryStream();
                    image.Save(stream, ImageFileFormat.Png);
                    stream.Position = 0;
                    resultImage = Image.FromStream(stream);

                    // Применяем настройки изображения если есть
                    if (settings.ImageAdjustments.HasChanges)
                    {
                        var processed = _imageProcessing.ApplyAdjustments(resultImage, settings.ImageAdjustments);
                        resultImage.Dispose();
                        resultImage = processed;
                    }

                    // Для простоты берём только первую страницу
                    // Для многостраничного сканирования нужна дополнительная логика
                    break;
                }

                ScanProgress?.Invoke(this, new ScanProgressEventArgs
                {
                    Message = "Сканирование завершено",
                    Progress = 100
                });

                return resultImage;
            }
            catch (Exception ex)
            {
                ScanCompleted?.Invoke(this, new ScanCompletedEventArgs
                {
                    Success = false,
                    Error = ex.Message
                });
                throw;
            }
        }

        /// <summary>
        /// Сохранить отсканированное изображение
        /// </summary>
        public void SaveScan(Image image, ScanSettings settings)
        {
            var outputPath = settings.GetFullPath();

            // Создаём директорию если не существует
            var directory = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            switch (settings.Format)
            {
                case ScanFormat.PDF:
                    SaveAsPdf(image, outputPath);
                    break;
                case ScanFormat.JPEG:
                    image.Save(outputPath, ImageFormat.Jpeg);
                    break;
                case ScanFormat.PNG:
                    image.Save(outputPath, ImageFormat.Png);
                    break;
                case ScanFormat.TIFF:
                    image.Save(outputPath, ImageFormat.Tiff);
                    break;
            }

            ScanCompleted?.Invoke(this, new ScanCompletedEventArgs
            {
                Success = true,
                FilePath = outputPath
            });
        }

        /// <summary>
        /// Сохранить изображение как PDF
        /// </summary>
        private void SaveAsPdf(Image image, string outputPath)
        {
            using var document = new PdfDocument();
            var page = document.AddPage();

            // Устанавливаем размер страницы по размеру изображения
            page.Width = XUnit.FromPoint(image.Width * 72 / image.HorizontalResolution);
            page.Height = XUnit.FromPoint(image.Height * 72 / image.VerticalResolution);

            using var graphics = XGraphics.FromPdfPage(page);

            // Сохраняем изображение во временный файл для XImage
            var tempPath = Path.GetTempFileName() + ".png";
            try
            {
                image.Save(tempPath, ImageFormat.Png);
                using var xImage = XImage.FromFile(tempPath);
                graphics.DrawImage(xImage, 0, 0, page.Width, page.Height);
            }
            finally
            {
                if (File.Exists(tempPath))
                    File.Delete(tempPath);
            }

            document.Save(outputPath);
        }

        /// <summary>
        /// Получить список доступных сканеров
        /// </summary>
        public async Task<string[]> GetAvailableScannersAsync()
        {
            try
            {
                using var scanningContext = new ScanningContext();
                var controller = new ScanController(scanningContext);
                var devices = await controller.GetDeviceList();

                var names = new string[devices.Count];
                for (int i = 0; i < devices.Count; i++)
                {
                    names[i] = devices[i].Name;
                }
                return names;
            }
            catch
            {
                return Array.Empty<string>();
            }
        }

        public void Dispose()
        {
            if (!_isDisposed)
            {
                _isDisposed = true;
            }
        }
    }

    public class ScanProgressEventArgs : EventArgs
    {
        public string Message { get; set; } = string.Empty;
        public int Progress { get; set; }
    }

    public class ScanCompletedEventArgs : EventArgs
    {
        public bool Success { get; set; }
        public string? FilePath { get; set; }
        public string? Error { get; set; }
    }
}
