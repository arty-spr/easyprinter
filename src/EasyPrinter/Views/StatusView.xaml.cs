using System;
using System.Collections.ObjectModel;
using System.Printing;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using EasyPrinter.Models;
using EasyPrinter.Services;

namespace EasyPrinter.Views
{
    public partial class StatusView : Page
    {
        private readonly MainWindow _mainWindow;
        private readonly StatusService _statusService;
        private ObservableCollection<PrintJobInfo> _printJobs;

        public StatusView(MainWindow mainWindow)
        {
            InitializeComponent();

            _mainWindow = mainWindow;
            _statusService = new StatusService();
            _printJobs = new ObservableCollection<PrintJobInfo>();

            PrintQueueListView.ItemsSource = _printJobs;

            // Загружаем статус при открытии
            RefreshStatus();
        }

        private void BackButton_Click(object sender, RoutedEventArgs e)
        {
            _statusService.Dispose();
            _mainWindow.GoHome();
        }

        private void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            RefreshStatus();
        }

        private void RefreshStatus()
        {
            try
            {
                var status = _statusService.GetCurrentStatus();
                var printer = _statusService.FindHPPrinter();

                if (printer != null)
                {
                    // Обновляем имя и статус
                    PrinterNameText.Text = printer.Name;
                    UpdateStatusDisplay(printer);

                    // Обновляем уровень тонера
                    UpdateTonerDisplay(status.TonerLevel);

                    // Обновляем очередь печати
                    UpdatePrintQueue(printer);
                }
                else
                {
                    PrinterNameText.Text = "Принтер не найден";
                    StatusText.Text = "HP принтер не обнаружен в системе";
                    StatusIndicator.Fill = (SolidColorBrush)FindResource("ErrorBrush");

                    TonerProgressBar.Value = 0;
                    TonerPercentText.Text = "?";
                    TonerStatusText.Text = "Информация недоступна";
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка получения статуса: {ex.Message}", "Ошибка",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void UpdateStatusDisplay(PrintQueue printer)
        {
            var queueStatus = printer.QueueStatus;
            string statusMessage;
            SolidColorBrush statusColor;

            if (printer.IsOffline || queueStatus.HasFlag(PrintQueueStatus.Offline))
            {
                statusMessage = "Не в сети";
                statusColor = (SolidColorBrush)FindResource("ErrorBrush");
            }
            else if (queueStatus.HasFlag(PrintQueueStatus.PaperJam))
            {
                statusMessage = "Замятие бумаги!";
                statusColor = (SolidColorBrush)FindResource("ErrorBrush");
            }
            else if (queueStatus.HasFlag(PrintQueueStatus.PaperOut))
            {
                statusMessage = "Нет бумаги";
                statusColor = (SolidColorBrush)FindResource("AccentBrush");
            }
            else if (queueStatus.HasFlag(PrintQueueStatus.TonerLow))
            {
                statusMessage = "Мало тонера";
                statusColor = (SolidColorBrush)FindResource("AccentBrush");
            }
            else if (queueStatus.HasFlag(PrintQueueStatus.Error))
            {
                statusMessage = "Ошибка принтера";
                statusColor = (SolidColorBrush)FindResource("ErrorBrush");
            }
            else if (queueStatus.HasFlag(PrintQueueStatus.Printing))
            {
                statusMessage = "Идёт печать...";
                statusColor = (SolidColorBrush)FindResource("PrimaryBrush");
            }
            else if (queueStatus.HasFlag(PrintQueueStatus.WarmingUp))
            {
                statusMessage = "Прогревается...";
                statusColor = (SolidColorBrush)FindResource("AccentBrush");
            }
            else
            {
                statusMessage = "Готов к работе";
                statusColor = (SolidColorBrush)FindResource("SuccessBrush");
            }

            StatusText.Text = statusMessage;
            StatusIndicator.Fill = statusColor;
        }

        private void UpdateTonerDisplay(int tonerLevel)
        {
            if (tonerLevel >= 0)
            {
                TonerProgressBar.Value = tonerLevel;
                TonerPercentText.Text = $"{tonerLevel}%";

                if (tonerLevel > 20)
                {
                    TonerProgressBar.Foreground = (SolidColorBrush)FindResource("SuccessBrush");
                    TonerStatusText.Text = "Уровень тонера в норме";
                }
                else if (tonerLevel > 10)
                {
                    TonerProgressBar.Foreground = (SolidColorBrush)FindResource("AccentBrush");
                    TonerStatusText.Text = "Тонер заканчивается";
                }
                else
                {
                    TonerProgressBar.Foreground = (SolidColorBrush)FindResource("ErrorBrush");
                    TonerStatusText.Text = "Тонер почти закончился! Замените картридж HP 78A";
                }
            }
            else
            {
                // Уровень тонера неизвестен - показываем примерное значение
                TonerProgressBar.Value = 50;
                TonerPercentText.Text = "~";
                TonerStatusText.Text = "Точный уровень тонера недоступен";
                TonerProgressBar.Foreground = (SolidColorBrush)FindResource("TextSecondaryBrush");
            }
        }

        private void UpdatePrintQueue(PrintQueue printer)
        {
            _printJobs.Clear();

            try
            {
                var jobs = printer.GetPrintJobInfoCollection();

                foreach (var job in jobs)
                {
                    _printJobs.Add(new PrintJobInfo
                    {
                        DocumentName = job.Name ?? "Без имени",
                        Status = GetJobStatusText(job.JobStatus),
                        Pages = job.NumberOfPages > 0 ? $"{job.NumberOfPages} стр." : ""
                    });
                }

                // Показываем/скрываем сообщение о пустой очереди
                EmptyQueuePanel.Visibility = _printJobs.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
                PrintQueueListView.Visibility = _printJobs.Count > 0 ? Visibility.Visible : Visibility.Collapsed;
            }
            catch
            {
                // Если не удалось получить очередь
                EmptyQueuePanel.Visibility = Visibility.Visible;
                PrintQueueListView.Visibility = Visibility.Collapsed;
            }
        }

        private string GetJobStatusText(PrintJobStatus status)
        {
            if (status.HasFlag(PrintJobStatus.Printing))
                return "Печатается...";
            if (status.HasFlag(PrintJobStatus.Paused))
                return "Приостановлено";
            if (status.HasFlag(PrintJobStatus.Deleting))
                return "Удаляется...";
            if (status.HasFlag(PrintJobStatus.Error))
                return "Ошибка";
            if (status.HasFlag(PrintJobStatus.Offline))
                return "Не в сети";
            if (status.HasFlag(PrintJobStatus.Spooling))
                return "В очереди";

            return "Ожидает";
        }

        private void ClearQueueButton_Click(object sender, RoutedEventArgs e)
        {
            var result = MessageBox.Show(
                "Вы уверены, что хотите очистить очередь печати?",
                "Подтверждение",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result == MessageBoxResult.Yes)
            {
                try
                {
                    var printer = _statusService.FindHPPrinter();
                    if (printer != null)
                    {
                        printer.Purge();
                        RefreshStatus();

                        MessageBox.Show("Очередь печати очищена", "Успех",
                            MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Ошибка очистки очереди: {ex.Message}", "Ошибка",
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }
    }

    /// <summary>
    /// Информация о задании печати для отображения
    /// </summary>
    public class PrintJobInfo
    {
        public string DocumentName { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public string Pages { get; set; } = string.Empty;
    }
}
