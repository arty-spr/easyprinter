using System;
using System.Linq;
using System.Management;
using System.Printing;
using System.Timers;
using EasyPrinter.Models;

namespace EasyPrinter.Services
{
    /// <summary>
    /// Сервис мониторинга статуса принтера
    /// </summary>
    public class StatusService : IDisposable
    {
        private readonly Timer _timer;
        private PrinterStatus _lastStatus;
        private bool _isDisposed;

        private const string TargetPrinterName = "HP LaserJet M1536dnf";

        public event EventHandler<PrinterStatusEventArgs>? StatusChanged;

        public StatusService()
        {
            _lastStatus = new PrinterStatus();
            _timer = new Timer(5000); // Обновление каждые 5 секунд
            _timer.Elapsed += OnTimerElapsed;
        }

        /// <summary>
        /// Запустить мониторинг статуса
        /// </summary>
        public void StartMonitoring()
        {
            UpdateStatus();
            _timer.Start();
        }

        /// <summary>
        /// Остановить мониторинг статуса
        /// </summary>
        public void StopMonitoring()
        {
            _timer.Stop();
        }

        /// <summary>
        /// Получить текущий статус принтера
        /// </summary>
        public PrinterStatus GetCurrentStatus()
        {
            return _lastStatus;
        }

        /// <summary>
        /// Найти HP принтер в системе
        /// </summary>
        public PrintQueue? FindHPPrinter()
        {
            try
            {
                using var printServer = new LocalPrintServer();
                var queues = printServer.GetPrintQueues();

                // Ищем HP LaserJet M1536dnf
                var hpPrinter = queues.FirstOrDefault(q =>
                    q.Name.Contains("HP", StringComparison.OrdinalIgnoreCase) &&
                    (q.Name.Contains("1536", StringComparison.OrdinalIgnoreCase) ||
                     q.Name.Contains("LaserJet", StringComparison.OrdinalIgnoreCase)));

                return hpPrinter;
            }
            catch
            {
                return null;
            }
        }

        private void OnTimerElapsed(object? sender, ElapsedEventArgs e)
        {
            UpdateStatus();
        }

        private void UpdateStatus()
        {
            try
            {
                var printer = FindHPPrinter();

                if (printer != null)
                {
                    var status = new PrinterStatus
                    {
                        PrinterName = printer.Name,
                        IsOnline = !printer.IsOffline,
                        JobsInQueue = printer.NumberOfJobs,
                        LastUpdated = DateTime.Now
                    };

                    // Определяем состояние принтера
                    var queueStatus = printer.QueueStatus;

                    if (queueStatus.HasFlag(PrintQueueStatus.Offline))
                    {
                        status.State = PrinterState.Offline;
                        status.StatusMessage = "Принтер не в сети";
                        status.IsOnline = false;
                    }
                    else if (queueStatus.HasFlag(PrintQueueStatus.PaperJam))
                    {
                        status.State = PrinterState.PaperJam;
                        status.StatusMessage = "Замятие бумаги";
                    }
                    else if (queueStatus.HasFlag(PrintQueueStatus.PaperOut))
                    {
                        status.State = PrinterState.PaperOut;
                        status.StatusMessage = "Нет бумаги";
                    }
                    else if (queueStatus.HasFlag(PrintQueueStatus.TonerLow))
                    {
                        status.State = PrinterState.TonerLow;
                        status.StatusMessage = "Мало тонера";
                    }
                    else if (queueStatus.HasFlag(PrintQueueStatus.Error))
                    {
                        status.State = PrinterState.Error;
                        status.StatusMessage = "Ошибка принтера";
                    }
                    else if (queueStatus.HasFlag(PrintQueueStatus.Printing))
                    {
                        status.State = PrinterState.Printing;
                        status.StatusMessage = "Идёт печать...";
                    }
                    else if (queueStatus.HasFlag(PrintQueueStatus.WarmingUp))
                    {
                        status.State = PrinterState.Warming;
                        status.StatusMessage = "Прогрев...";
                    }
                    else
                    {
                        status.State = PrinterState.Ready;
                        status.StatusMessage = "Готов к работе";
                    }

                    // Попробуем получить уровень тонера через WMI
                    status.TonerLevel = GetTonerLevelViaWMI(printer.Name);

                    _lastStatus = status;

                    StatusChanged?.Invoke(this, new PrinterStatusEventArgs
                    {
                        PrinterName = status.PrinterName,
                        IsOnline = status.IsOnline,
                        StatusMessage = status.StatusMessage,
                        TonerLevel = status.TonerLevel
                    });
                }
                else
                {
                    _lastStatus = new PrinterStatus
                    {
                        PrinterName = null,
                        IsOnline = false,
                        State = PrinterState.Offline,
                        StatusMessage = "HP принтер не найден",
                        TonerLevel = -1,
                        LastUpdated = DateTime.Now
                    };

                    StatusChanged?.Invoke(this, new PrinterStatusEventArgs
                    {
                        PrinterName = null,
                        IsOnline = false,
                        StatusMessage = "HP принтер не найден",
                        TonerLevel = -1
                    });
                }
            }
            catch (Exception ex)
            {
                _lastStatus = new PrinterStatus
                {
                    IsOnline = false,
                    State = PrinterState.Error,
                    StatusMessage = $"Ошибка: {ex.Message}",
                    LastUpdated = DateTime.Now
                };

                StatusChanged?.Invoke(this, new PrinterStatusEventArgs
                {
                    IsOnline = false,
                    StatusMessage = $"Ошибка: {ex.Message}",
                    TonerLevel = -1
                });
            }
        }

        /// <summary>
        /// Попытка получить уровень тонера через WMI
        /// </summary>
        private int GetTonerLevelViaWMI(string printerName)
        {
            try
            {
                // Поиск информации о расходных материалах через WMI
                var query = new ObjectQuery("SELECT * FROM Win32_Printer WHERE Name LIKE '%" +
                    printerName.Replace("\\", "\\\\").Replace("'", "\\'") + "%'");

                using var searcher = new ManagementObjectSearcher(query);
                foreach (var obj in searcher.Get())
                {
                    // К сожалению, WMI обычно не предоставляет точный уровень тонера
                    // Для HP принтеров можно использовать SNMP или HP SDK
                    // Возвращаем примерное значение
                }

                // По умолчанию возвращаем -1 (неизвестно)
                // В реальном приложении можно использовать SNMP запрос к принтеру
                return -1;
            }
            catch
            {
                return -1;
            }
        }

        public void Dispose()
        {
            if (!_isDisposed)
            {
                _timer.Stop();
                _timer.Dispose();
                _isDisposed = true;
            }
        }
    }

    /// <summary>
    /// Аргументы события изменения статуса принтера
    /// </summary>
    public class PrinterStatusEventArgs : EventArgs
    {
        public string? PrinterName { get; set; }
        public bool IsOnline { get; set; }
        public string StatusMessage { get; set; } = string.Empty;
        public int TonerLevel { get; set; } = -1;
    }
}
