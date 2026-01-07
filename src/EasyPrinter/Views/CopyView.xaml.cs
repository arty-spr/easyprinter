using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using EasyPrinter.Models;
using EasyPrinter.Services;

namespace EasyPrinter.Views
{
    public partial class CopyView : Page
    {
        private readonly MainWindow _mainWindow;
        private readonly ImageProcessingService _imageProcessing;
        private readonly ScannerService _scannerService;
        private readonly StatusService _statusService;
        private readonly PrinterService _printerService;

        private int _copies = 1;

        public CopyView(MainWindow mainWindow)
        {
            InitializeComponent();

            _mainWindow = mainWindow;
            _imageProcessing = new ImageProcessingService();
            _statusService = new StatusService();
            _scannerService = new ScannerService(_imageProcessing);
            _printerService = new PrinterService(_statusService, _imageProcessing);
        }

        private void BackButton_Click(object sender, RoutedEventArgs e)
        {
            _mainWindow.GoHome();
        }

        private void IncreaseCopies_Click(object sender, RoutedEventArgs e)
        {
            if (_copies < 99)
            {
                _copies++;
                CopiesText.Text = _copies.ToString();
            }
        }

        private void DecreaseCopies_Click(object sender, RoutedEventArgs e)
        {
            if (_copies > 1)
            {
                _copies--;
                CopiesText.Text = _copies.ToString();
            }
        }

        private async void CopyButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                CopyButton.IsEnabled = false;
                CopyButton.Content = "Копирование...";

                // Получаем настройки
                var scanSettings = new ScanSettings
                {
                    Source = SourceComboBox.SelectedIndex == 0 ? ScanSource.Flatbed : ScanSource.ADF,
                    Resolution = ScanResolution.Dpi300, // Для копирования 300 dpi достаточно
                    Format = ScanFormat.PNG
                };

                var printQuality = QualityComboBox.SelectedIndex switch
                {
                    0 => PrintQuality.Draft,
                    1 => PrintQuality.Normal,
                    2 => PrintQuality.High,
                    _ => PrintQuality.Normal
                };

                var scale = ScaleComboBox.SelectedIndex switch
                {
                    0 => 50,
                    1 => 75,
                    2 => 100,
                    3 => 125,
                    4 => 150,
                    5 => 200,
                    _ => 100
                };

                // Сканируем документ
                CopyButton.Content = "Сканирование...";
                var scannedImage = await _scannerService.ScanAsync(scanSettings);

                if (scannedImage == null)
                {
                    MessageBox.Show("Не удалось отсканировать документ", "Ошибка",
                        MessageBoxButton.OK, MessageBoxImage.Error);
                    return;
                }

                // Печатаем копии
                CopyButton.Content = "Печать...";

                var printSettings = new PrintSettings
                {
                    Copies = _copies,
                    Quality = printQuality,
                    Scale = scale,
                    PaperSize = Models.PaperSize.A4
                };

                // Сохраняем во временный файл и печатаем
                var tempFile = System.IO.Path.GetTempFileName() + ".png";
                try
                {
                    scannedImage.Save(tempFile, System.Drawing.Imaging.ImageFormat.Png);
                    await Task.Run(() =>
                    {
                        _printerService.PrintImage(tempFile, printSettings);
                    });

                    MessageBox.Show($"Копирование завершено!\nСделано копий: {_copies}", "Успех",
                        MessageBoxButton.OK, MessageBoxImage.Information);
                }
                finally
                {
                    if (System.IO.File.Exists(tempFile))
                        System.IO.File.Delete(tempFile);
                    scannedImage.Dispose();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка копирования: {ex.Message}", "Ошибка",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                CopyButton.IsEnabled = true;
                CopyButton.Content = "КОПИРОВАТЬ";
            }
        }
    }
}
