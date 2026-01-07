namespace EasyPrinter.Models
{
    /// <summary>
    /// Настройки сканирования
    /// </summary>
    public class ScanSettings
    {
        /// <summary>
        /// Разрешение сканирования (DPI)
        /// </summary>
        public ScanResolution Resolution { get; set; } = ScanResolution.Dpi300;

        /// <summary>
        /// Формат сохранения
        /// </summary>
        public ScanFormat Format { get; set; } = ScanFormat.PDF;

        /// <summary>
        /// Папка для сохранения
        /// </summary>
        public string OutputFolder { get; set; } = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);

        /// <summary>
        /// Имя файла (без расширения)
        /// </summary>
        public string FileName { get; set; } = $"Скан_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}";

        /// <summary>
        /// Источник сканирования
        /// </summary>
        public ScanSource Source { get; set; } = ScanSource.Flatbed;

        /// <summary>
        /// Настройки изображения
        /// </summary>
        public ImageAdjustments ImageAdjustments { get; set; } = new();

        /// <summary>
        /// Получить полный путь к файлу
        /// </summary>
        public string GetFullPath()
        {
            var extension = Format switch
            {
                ScanFormat.PDF => ".pdf",
                ScanFormat.JPEG => ".jpg",
                ScanFormat.PNG => ".png",
                ScanFormat.TIFF => ".tiff",
                _ => ".pdf"
            };

            return Path.Combine(OutputFolder, FileName + extension);
        }
    }

    public enum ScanResolution
    {
        Dpi150 = 150,
        Dpi300 = 300,
        Dpi600 = 600,
        Dpi1200 = 1200
    }

    public enum ScanFormat
    {
        PDF,
        JPEG,
        PNG,
        TIFF
    }

    public enum ScanSource
    {
        Flatbed,    // Стекло сканера
        ADF         // Автоподатчик документов
    }
}
