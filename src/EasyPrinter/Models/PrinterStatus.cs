namespace EasyPrinter.Models
{
    /// <summary>
    /// Статус принтера
    /// </summary>
    public class PrinterStatus
    {
        /// <summary>
        /// Имя принтера
        /// </summary>
        public string PrinterName { get; set; } = string.Empty;

        /// <summary>
        /// Принтер онлайн
        /// </summary>
        public bool IsOnline { get; set; }

        /// <summary>
        /// Текущее состояние
        /// </summary>
        public PrinterState State { get; set; } = PrinterState.Unknown;

        /// <summary>
        /// Сообщение о статусе
        /// </summary>
        public string StatusMessage { get; set; } = string.Empty;

        /// <summary>
        /// Уровень тонера (0-100, -1 если неизвестно)
        /// </summary>
        public int TonerLevel { get; set; } = -1;

        /// <summary>
        /// Количество заданий в очереди печати
        /// </summary>
        public int JobsInQueue { get; set; }

        /// <summary>
        /// Поддерживает сканирование
        /// </summary>
        public bool SupportsScanning { get; set; } = true;

        /// <summary>
        /// Поддерживает копирование
        /// </summary>
        public bool SupportsCopying { get; set; } = true;

        /// <summary>
        /// Последнее обновление статуса
        /// </summary>
        public DateTime LastUpdated { get; set; } = DateTime.Now;
    }

    public enum PrinterState
    {
        Unknown,
        Ready,          // Готов
        Printing,       // Печатает
        Scanning,       // Сканирует
        Copying,        // Копирует
        Warming,        // Прогревается
        PaperJam,       // Замятие бумаги
        PaperOut,       // Нет бумаги
        TonerLow,       // Мало тонера
        Error,          // Ошибка
        Offline         // Не в сети
    }
}
