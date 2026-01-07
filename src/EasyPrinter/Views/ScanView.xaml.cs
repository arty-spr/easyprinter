using System;
using System.Drawing;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using EasyPrinter.Models;
using EasyPrinter.Services;
using Microsoft.Win32;
using Ookii.Dialogs.Wpf;

namespace EasyPrinter.Views
{
    public partial class ScanView : Page
    {
        private readonly MainWindow _mainWindow;
        private readonly ImageProcessingService _imageProcessing;
        private readonly ScannerService _scannerService;

        private System.Drawing.Image? _scannedImage;
        private System.Drawing.Image? _processedImage;

        public ScanView(MainWindow mainWindow)
        {
            InitializeComponent();

            _mainWindow = mainWindow;
            _imageProcessing = new ImageProcessingService();
            _scannerService = new ScannerService(_imageProcessing);

            // Устанавливаем папку по умолчанию
            FolderTextBox.Text = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);

            // Подписываемся на события сканера
            _scannerService.ScanProgress += OnScanProgress;
            _scannerService.ScanCompleted += OnScanCompleted;

            // Генерируем имя файла по умолчанию
            FileNameTextBox.Text = $"Скан_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}";
        }

        private void BackButton_Click(object sender, RoutedEventArgs e)
        {
            CleanupImages();
            _mainWindow.GoHome();
        }

        private void CleanupImages()
        {
            _scannedImage?.Dispose();
            _scannedImage = null;

            _processedImage?.Dispose();
            _processedImage = null;
        }

        private void BrowseFolderButton_Click(object sender, RoutedEventArgs e)
        {
            // Используем стандартный диалог выбора папки Windows
            var dialog = new VistaFolderBrowserDialog
            {
                Description = "Выберите папку для сохранения сканов",
                UseDescriptionForTitle = true,
                SelectedPath = FolderTextBox.Text
            };

            if (dialog.ShowDialog() == true)
            {
                FolderTextBox.Text = dialog.SelectedPath;
            }
        }

        private async void ScanButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // Показываем прогресс
                PlaceholderPanel.Visibility = Visibility.Collapsed;
                PreviewScrollViewer.Visibility = Visibility.Collapsed;
                ProgressPanel.Visibility = Visibility.Visible;

                ScanButton.IsEnabled = false;
                SaveButton.IsEnabled = false;

                var settings = GetScanSettings();

                // Выполняем сканирование
                CleanupImages();
                _scannedImage = await _scannerService.ScanAsync(settings);

                if (_scannedImage != null)
                {
                    // Показываем результат
                    await UpdatePreview();

                    ProgressPanel.Visibility = Visibility.Collapsed;
                    PreviewScrollViewer.Visibility = Visibility.Visible;
                    SaveButton.IsEnabled = true;

                    // Обновляем имя файла
                    FileNameTextBox.Text = $"Скан_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}";
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка сканирования: {ex.Message}", "Ошибка",
                    MessageBoxButton.OK, MessageBoxImage.Error);

                ProgressPanel.Visibility = Visibility.Collapsed;
                PlaceholderPanel.Visibility = Visibility.Visible;
            }
            finally
            {
                ScanButton.IsEnabled = true;
            }
        }

        private async void SaveButton_Click(object sender, RoutedEventArgs e)
        {
            if (_scannedImage == null) return;

            try
            {
                SaveButton.IsEnabled = false;
                SaveButton.Content = "Сохранение...";

                var settings = GetScanSettings();

                // Применяем настройки изображения перед сохранением
                var imageToSave = GetCurrentImageAdjustments().HasChanges
                    ? _imageProcessing.ApplyAdjustments(_scannedImage, GetCurrentImageAdjustments())
                    : _scannedImage;

                await Task.Run(() =>
                {
                    _scannerService.SaveScan(imageToSave, settings);
                });

                MessageBox.Show($"Скан сохранён:\n{settings.GetFullPath()}", "Успех",
                    MessageBoxButton.OK, MessageBoxImage.Information);

                // Очищаем результат
                CleanupImages();
                PlaceholderPanel.Visibility = Visibility.Visible;
                PreviewScrollViewer.Visibility = Visibility.Collapsed;
                SaveButton.IsEnabled = false;

                // Генерируем новое имя файла
                FileNameTextBox.Text = $"Скан_{DateTime.Now:yyyy-MM-dd_HH-mm-ss}";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка сохранения: {ex.Message}", "Ошибка",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                SaveButton.Content = "СОХРАНИТЬ";
                if (_scannedImage != null)
                    SaveButton.IsEnabled = true;
            }
        }

        private void OnScanProgress(object? sender, ScanProgressEventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                ScanProgressBar.Value = e.Progress;
                ProgressText.Text = e.Message;
            });
        }

        private void OnScanCompleted(object? sender, ScanCompletedEventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                if (!e.Success)
                {
                    MessageBox.Show($"Сканирование не удалось: {e.Error}", "Ошибка",
                        MessageBoxButton.OK, MessageBoxImage.Error);
                }
            });
        }

        private async void ImageAdjustment_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            // Обновляем текстовые значения
            if (BrightnessValueText != null)
                BrightnessValueText.Text = ((int)BrightnessSlider.Value).ToString();
            if (ContrastValueText != null)
                ContrastValueText.Text = ((int)ContrastSlider.Value).ToString();
            if (SharpnessValueText != null)
                SharpnessValueText.Text = ((int)SharpnessSlider.Value).ToString();

            // Обновляем предпросмотр
            if (_scannedImage != null)
            {
                await Task.Delay(100); // Небольшая задержка
                await UpdatePreview();
            }
        }

        private async void ResetImageSettings_Click(object sender, RoutedEventArgs e)
        {
            BrightnessSlider.Value = 0;
            ContrastSlider.Value = 0;
            SharpnessSlider.Value = 0;

            if (_scannedImage != null)
            {
                await UpdatePreview();
            }
        }

        private async Task UpdatePreview()
        {
            if (_scannedImage == null) return;

            try
            {
                var adjustments = GetCurrentImageAdjustments();

                // Освобождаем предыдущее обработанное изображение
                _processedImage?.Dispose();
                _processedImage = null;

                System.Drawing.Image imageToShow;
                if (adjustments.HasChanges)
                {
                    _processedImage = _imageProcessing.ApplyAdjustments(_scannedImage, adjustments);
                    imageToShow = _processedImage;
                }
                else
                {
                    imageToShow = _scannedImage;
                }

                // Конвертируем в BitmapSource для WPF
                var bitmapSource = _imageProcessing.ConvertToBitmapSource(imageToShow);
                PreviewImage.Source = bitmapSource;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка обновления предпросмотра: {ex.Message}", "Ошибка",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private ImageAdjustments GetCurrentImageAdjustments()
        {
            return new ImageAdjustments
            {
                Brightness = (int)BrightnessSlider.Value,
                Contrast = (int)ContrastSlider.Value,
                Sharpness = (int)SharpnessSlider.Value,
                Gamma = 1.0
            };
        }

        private ScanSettings GetScanSettings()
        {
            var resolution = ResolutionComboBox.SelectedIndex switch
            {
                0 => ScanResolution.Dpi150,
                1 => ScanResolution.Dpi300,
                2 => ScanResolution.Dpi600,
                3 => ScanResolution.Dpi1200,
                _ => ScanResolution.Dpi300
            };

            var format = FormatComboBox.SelectedIndex switch
            {
                0 => ScanFormat.PDF,
                1 => ScanFormat.JPEG,
                2 => ScanFormat.PNG,
                3 => ScanFormat.TIFF,
                _ => ScanFormat.PDF
            };

            return new ScanSettings
            {
                Source = SourceComboBox.SelectedIndex == 0 ? ScanSource.Flatbed : ScanSource.ADF,
                Resolution = resolution,
                Format = format,
                OutputFolder = FolderTextBox.Text,
                FileName = FileNameTextBox.Text,
                ImageAdjustments = GetCurrentImageAdjustments()
            };
        }
    }
}
