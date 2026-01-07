namespace EasyPrinter.Models
{
    /// <summary>
    /// Настройки печати
    /// </summary>
    public class PrintSettings
    {
        /// <summary>
        /// Количество копий (1-99)
        /// </summary>
        public int Copies { get; set; } = 1;

        /// <summary>
        /// Размер бумаги
        /// </summary>
        public PaperSize PaperSize { get; set; } = PaperSize.A4;

        /// <summary>
        /// Источник бумаги
        /// </summary>
        public PaperSource PaperSource { get; set; } = PaperSource.Auto;

        /// <summary>
        /// Качество печати
        /// </summary>
        public PrintQuality Quality { get; set; } = PrintQuality.Normal;

        /// <summary>
        /// Двусторонняя печать
        /// </summary>
        public DuplexMode Duplex { get; set; } = DuplexMode.None;

        /// <summary>
        /// Диапазон страниц (null = все страницы)
        /// </summary>
        public string? PageRange { get; set; }

        /// <summary>
        /// Страниц на листе
        /// </summary>
        public int PagesPerSheet { get; set; } = 1;

        /// <summary>
        /// Масштаб (25-400%)
        /// </summary>
        public int Scale { get; set; } = 100;

        /// <summary>
        /// Ориентация
        /// </summary>
        public PageOrientation Orientation { get; set; } = PageOrientation.Portrait;

        /// <summary>
        /// Настройки изображения
        /// </summary>
        public ImageAdjustments ImageAdjustments { get; set; } = new();
    }

    public enum PaperSize
    {
        A4,
        Letter,
        Legal,
        A5,
        Envelope10,
        EnvelopeC5,
        EnvelopeDL
    }

    public enum PaperSource
    {
        Auto,
        Tray1,
        ManualFeed
    }

    public enum PrintQuality
    {
        Draft,      // Черновик (600dpi)
        Normal,     // Нормальное
        High        // Высокое (FastRes 1200)
    }

    public enum DuplexMode
    {
        None,           // Односторонняя
        ManualDuplex    // Ручной дуплекс
    }

    public enum PageOrientation
    {
        Portrait,   // Книжная
        Landscape   // Альбомная
    }
}
