using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Navigation;
using EasyPrinter.Views;
using EasyPrinter.Services;

namespace EasyPrinter
{
    public partial class MainWindow : Window
    {
        private readonly StatusService _statusService;

        public MainWindow()
        {
            InitializeComponent();

            _statusService = new StatusService();

            // Показываем главную страницу
            MainFrame.Navigate(new HomePage(this));

            // Подписываемся на обновления статуса
            _statusService.StatusChanged += OnPrinterStatusChanged;

            // Запускаем мониторинг статуса
            _statusService.StartMonitoring();
        }

        public void NavigateTo(Type pageType)
        {
            object? page = null;

            if (pageType == typeof(HomePage))
                page = new HomePage(this);
            else if (pageType == typeof(PrintView))
                page = new PrintView(this);
            else if (pageType == typeof(ScanView))
                page = new ScanView(this);
            else if (pageType == typeof(CopyView))
                page = new CopyView(this);
            else if (pageType == typeof(StatusView))
                page = new StatusView(this);

            if (page != null)
            {
                MainFrame.Navigate(page);
            }
        }

        public void GoHome()
        {
            MainFrame.Navigate(new HomePage(this));
        }

        private void OnPrinterStatusChanged(object? sender, PrinterStatusEventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                // Обновляем индикатор статуса
                StatusIndicator.Fill = e.IsOnline
                    ? (SolidColorBrush)FindResource("SuccessBrush")
                    : (SolidColorBrush)FindResource("ErrorBrush");

                // Обновляем текст статуса
                StatusText.Text = e.StatusMessage;

                // Обновляем имя принтера
                PrinterNameText.Text = e.PrinterName ?? "Принтер не найден";

                // Обновляем уровень тонера
                if (e.TonerLevel >= 0)
                {
                    TonerLevel.Value = e.TonerLevel;
                    TonerPercentText.Text = $" {e.TonerLevel}%";

                    // Цвет индикатора тонера
                    if (e.TonerLevel > 20)
                        TonerLevel.Foreground = (SolidColorBrush)FindResource("SuccessBrush");
                    else if (e.TonerLevel > 10)
                        TonerLevel.Foreground = (SolidColorBrush)FindResource("AccentBrush");
                    else
                        TonerLevel.Foreground = (SolidColorBrush)FindResource("ErrorBrush");
                }
            });
        }

        protected override void OnClosed(EventArgs e)
        {
            _statusService.StopMonitoring();
            _statusService.StatusChanged -= OnPrinterStatusChanged;
            base.OnClosed(e);
        }
    }
}
