using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Windows.Media.Imaging;
using PdfiumViewer;

namespace EasyPrinter.Services
{
    /// <summary>
    /// Сервис предпросмотра документов (PDF и изображения)
    /// </summary>
    public class PreviewService : IDisposable
    {
        private PdfDocument? _currentPdf;
        private string? _currentFilePath;
        private bool _isDisposed;

        /// <summary>
        /// Загрузить документ для предпросмотра
        /// </summary>
        public void LoadDocument(string filePath)
        {
            // Закрываем предыдущий документ
            CloseDocument();

            _currentFilePath = filePath;

            var extension = Path.GetExtension(filePath).ToLowerInvariant();
            if (extension == ".pdf")
            {
                _currentPdf = PdfDocument.Load(filePath);
            }
        }

        /// <summary>
        /// Закрыть текущий документ
        /// </summary>
        public void CloseDocument()
        {
            _currentPdf?.Dispose();
            _currentPdf = null;
            _currentFilePath = null;
        }

        /// <summary>
        /// Проверяет, является ли файл PDF
        /// </summary>
        public bool IsPdf => _currentPdf != null;

        /// <summary>
        /// Получить количество страниц в PDF
        /// </summary>
        public int PageCount => _currentPdf?.PageCount ?? 1;

        /// <summary>
        /// Получить размер страницы PDF
        /// </summary>
        public SizeF GetPageSize(int pageIndex)
        {
            if (_currentPdf != null && pageIndex >= 0 && pageIndex < _currentPdf.PageCount)
            {
                return _currentPdf.PageSizes[pageIndex];
            }
            return new SizeF(210, 297); // A4 по умолчанию
        }

        /// <summary>
        /// Рендерить страницу PDF в изображение
        /// </summary>
        public BitmapSource RenderPdfPage(int pageIndex, int dpi = 150)
        {
            if (_currentPdf == null)
                throw new InvalidOperationException("PDF документ не загружен");

            if (pageIndex < 0 || pageIndex >= _currentPdf.PageCount)
                throw new ArgumentOutOfRangeException(nameof(pageIndex));

            // Рендерим страницу
            using var image = _currentPdf.Render(pageIndex, dpi, dpi, true);

            return ConvertToBitmapSource(image);
        }

        /// <summary>
        /// Рендерить миниатюры всех страниц PDF
        /// </summary>
        public List<BitmapSource> RenderAllThumbnails(int thumbnailHeight = 150)
        {
            var thumbnails = new List<BitmapSource>();

            if (_currentPdf == null)
                return thumbnails;

            for (int i = 0; i < _currentPdf.PageCount; i++)
            {
                var pageSize = _currentPdf.PageSizes[i];
                var aspectRatio = pageSize.Width / pageSize.Height;
                var thumbnailWidth = (int)(thumbnailHeight * aspectRatio);

                // Вычисляем DPI для нужного размера миниатюры
                var dpi = (int)(thumbnailHeight / pageSize.Height * 72);

                using var image = _currentPdf.Render(i, dpi, dpi, true);
                thumbnails.Add(ConvertToBitmapSource(image));
            }

            return thumbnails;
        }

        /// <summary>
        /// Загрузить изображение для предпросмотра
        /// </summary>
        public BitmapSource LoadImage(string filePath)
        {
            _currentFilePath = filePath;

            var bitmap = new BitmapImage();
            bitmap.BeginInit();
            bitmap.UriSource = new Uri(filePath, UriKind.Absolute);
            bitmap.CacheOption = BitmapCacheOption.OnLoad;
            bitmap.EndInit();
            bitmap.Freeze();

            return bitmap;
        }

        /// <summary>
        /// Загрузить изображение с применением настроек
        /// </summary>
        public BitmapSource LoadImageWithAdjustments(string filePath, Models.ImageAdjustments adjustments,
            ImageProcessingService imageProcessing)
        {
            using var image = Image.FromFile(filePath);

            if (adjustments.HasChanges)
            {
                using var processed = imageProcessing.ApplyAdjustments(image, adjustments);
                return ConvertToBitmapSource(processed);
            }

            return ConvertToBitmapSource(image);
        }

        /// <summary>
        /// Определить тип файла
        /// </summary>
        public static DocumentType GetDocumentType(string filePath)
        {
            var extension = Path.GetExtension(filePath).ToLowerInvariant();

            return extension switch
            {
                ".pdf" => DocumentType.PDF,
                ".jpg" or ".jpeg" or ".png" or ".bmp" or ".tiff" or ".tif" or ".gif" => DocumentType.Image,
                _ => DocumentType.Unknown
            };
        }

        /// <summary>
        /// Проверить, поддерживается ли формат файла
        /// </summary>
        public static bool IsSupportedFormat(string filePath)
        {
            return GetDocumentType(filePath) != DocumentType.Unknown;
        }

        private BitmapSource ConvertToBitmapSource(Image image)
        {
            using var bitmap = new Bitmap(image);
            var hBitmap = bitmap.GetHbitmap();

            try
            {
                var source = System.Windows.Interop.Imaging.CreateBitmapSourceFromHBitmap(
                    hBitmap,
                    IntPtr.Zero,
                    System.Windows.Int32Rect.Empty,
                    BitmapSizeOptions.FromEmptyOptions());

                source.Freeze();
                return source;
            }
            finally
            {
                DeleteObject(hBitmap);
            }
        }

        [System.Runtime.InteropServices.DllImport("gdi32.dll")]
        private static extern bool DeleteObject(IntPtr hObject);

        public void Dispose()
        {
            if (!_isDisposed)
            {
                CloseDocument();
                _isDisposed = true;
            }
        }
    }

    public enum DocumentType
    {
        Unknown,
        PDF,
        Image
    }
}
