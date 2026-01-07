using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using EasyPrinter.Models;
using EasyPrinter.Services;
using Microsoft.Win32;

namespace EasyPrinter.Views
{
    public partial class PrintView : Page
    {
        private readonly MainWindow _mainWindow;
        private readonly PreviewService _previewService;
        private readonly ImageProcessingService _imageProcessing;
        private readonly StatusService _statusService;
        private readonly PrinterService _printerService;

        private string? _currentFilePath;
        private int _currentPage = 0;
        private int _totalPages = 1;
        private bool _isUpdatingPreview = false;

        public PrintView(MainWindow mainWindow)
        {
            InitializeComponent();

            _mainWindow = mainWindow;
            _previewService = new PreviewService();
            _imageProcessing = new ImageProcessingService();
            _statusService = new StatusService();
            _printerService = new PrinterService(_statusService, _imageProcessing);
        }

        private void BackButton_Click(object sender, RoutedEventArgs e)
        {
            _previewService.CloseDocument();
            _mainWindow.GoHome();
        }

        private async void BrowseButton_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new OpenFileDialog
            {
                Title = "Выберите файл для печати",
                Filter = "Все поддерживаемые|*.pdf;*.jpg;*.jpeg;*.png;*.bmp;*.tiff;*.tif|" +
                         "PDF документы|*.pdf|" +
                         "Изображения|*.jpg;*.jpeg;*.png;*.bmp;*.tiff;*.tif",
                FilterIndex = 1
            };

            if (dialog.ShowDialog() == true)
            {
                await LoadDocument(dialog.FileName);
            }
        }

        private async Task LoadDocument(string filePath)
        {
            try
            {
                _currentFilePath = filePath;
                FilePathTextBox.Text = filePath;

                var docType = PreviewService.GetDocumentType(filePath);

                if (docType == DocumentType.PDF)
                {
                    _previewService.LoadDocument(filePath);
                    _totalPages = _previewService.PageCount;
                    _currentPage = 0;

                    // Показываем навигацию по страницам
                    PageNavigationPanel.Visibility = _totalPages > 1 ? Visibility.Visible : Visibility.Collapsed;
                    UpdatePageInfo();

                    await UpdatePreview();
                }
                else if (docType == DocumentType.Image)
                {
                    _totalPages = 1;
                    _currentPage = 0;
                    PageNavigationPanel.Visibility = Visibility.Collapsed;

                    await UpdatePreview();
                }

                PlaceholderText.Visibility = Visibility.Collapsed;
                PreviewScrollViewer.Visibility = Visibility.Visible;
                PrintButton.IsEnabled = true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка загрузки файла: {ex.Message}", "Ошибка",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async Task UpdatePreview()
        {
            if (_currentFilePath == null || _isUpdatingPreview) return;

            _isUpdatingPreview = true;

            try
            {
                BitmapSource? preview = null;

                var docType = PreviewService.GetDocumentType(_currentFilePath);

                if (docType == DocumentType.PDF)
                {
                    preview = _previewService.RenderPdfPage(_currentPage, 150);
                }
                else if (docType == DocumentType.Image)
                {
                    var adjustments = GetCurrentImageAdjustments();
                    if (adjustments.HasChanges)
                    {
                        preview = _previewService.LoadImageWithAdjustments(
                            _currentFilePath, adjustments, _imageProcessing);
                    }
                    else
                    {
                        preview = _previewService.LoadImage(_currentFilePath);
                    }
                }

                if (preview != null)
                {
                    PreviewImage.Source = preview;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка предпросмотра: {ex.Message}", "Ошибка",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
            }
            finally
            {
                _isUpdatingPreview = false;
            }
        }

        private void UpdatePageInfo()
        {
            PageInfoText.Text = $"Страница {_currentPage + 1} из {_totalPages}";
        }

        private async void PrevPageButton_Click(object sender, RoutedEventArgs e)
        {
            if (_currentPage > 0)
            {
                _currentPage--;
                UpdatePageInfo();
                await UpdatePreview();
            }
        }

        private async void NextPageButton_Click(object sender, RoutedEventArgs e)
        {
            if (_currentPage < _totalPages - 1)
            {
                _currentPage++;
                UpdatePageInfo();
                await UpdatePreview();
            }
        }

        private void IncreaseCopies_Click(object sender, RoutedEventArgs e)
        {
            if (int.TryParse(CopiesTextBox.Text, out int copies) && copies < 99)
            {
                CopiesTextBox.Text = (copies + 1).ToString();
            }
        }

        private void DecreaseCopies_Click(object sender, RoutedEventArgs e)
        {
            if (int.TryParse(CopiesTextBox.Text, out int copies) && copies > 1)
            {
                CopiesTextBox.Text = (copies - 1).ToString();
            }
        }

        private void PageRangeComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (PageRangeTextBox != null)
            {
                PageRangeTextBox.Visibility = PageRangeComboBox.SelectedIndex == 2
                    ? Visibility.Visible
                    : Visibility.Collapsed;
            }
        }

        private void ScaleSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (ScaleValueText != null)
            {
                ScaleValueText.Text = $"{(int)ScaleSlider.Value}%";
            }
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
            if (GammaValueText != null)
                GammaValueText.Text = (GammaSlider.Value / 100.0).ToString("F1");

            // Обновляем предпросмотр для изображений
            if (_currentFilePath != null &&
                PreviewService.GetDocumentType(_currentFilePath) == DocumentType.Image)
            {
                // Добавляем небольшую задержку для избежания слишком частых обновлений
                await Task.Delay(100);
                await UpdatePreview();
            }
        }

        private async void ResetImageSettings_Click(object sender, RoutedEventArgs e)
        {
            BrightnessSlider.Value = 0;
            ContrastSlider.Value = 0;
            SharpnessSlider.Value = 0;
            GammaSlider.Value = 100;

            if (_currentFilePath != null &&
                PreviewService.GetDocumentType(_currentFilePath) == DocumentType.Image)
            {
                await UpdatePreview();
            }
        }

        private ImageAdjustments GetCurrentImageAdjustments()
        {
            return new ImageAdjustments
            {
                Brightness = (int)BrightnessSlider.Value,
                Contrast = (int)ContrastSlider.Value,
                Sharpness = (int)SharpnessSlider.Value,
                Gamma = GammaSlider.Value / 100.0
            };
        }

        private PrintSettings GetCurrentPrintSettings()
        {
            var settings = new PrintSettings
            {
                Copies = int.TryParse(CopiesTextBox.Text, out int copies) ? copies : 1,
                PaperSize = (Models.PaperSize)PaperSizeComboBox.SelectedIndex,
                PaperSource = (Models.PaperSource)PaperSourceComboBox.SelectedIndex,
                Quality = (PrintQuality)QualityComboBox.SelectedIndex,
                Orientation = OrientationComboBox.SelectedIndex == 0
                    ? PageOrientation.Portrait
                    : PageOrientation.Landscape,
                PagesPerSheet = GetPagesPerSheet(),
                Scale = (int)ScaleSlider.Value,
                Duplex = DuplexCheckBox.IsChecked == true
                    ? DuplexMode.ManualDuplex
                    : DuplexMode.None,
                ImageAdjustments = GetCurrentImageAdjustments()
            };

            // Диапазон страниц
            if (PageRangeComboBox.SelectedIndex == 2) // Диапазон
            {
                settings.PageRange = PageRangeTextBox.Text;
            }
            else if (PageRangeComboBox.SelectedIndex == 1) // Текущая
            {
                settings.PageRange = (_currentPage + 1).ToString();
            }

            return settings;
        }

        private int GetPagesPerSheet()
        {
            return PagesPerSheetComboBox.SelectedIndex switch
            {
                0 => 1,
                1 => 2,
                2 => 4,
                3 => 6,
                4 => 9,
                5 => 16,
                _ => 1
            };
        }

        private async void PrintButton_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_currentFilePath)) return;

            try
            {
                PrintButton.IsEnabled = false;
                PrintButton.Content = "Печать...";

                var settings = GetCurrentPrintSettings();

                await Task.Run(() =>
                {
                    _printerService.Print(_currentFilePath, settings);
                });

                MessageBox.Show("Документ отправлен на печать!", "Успех",
                    MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка печати: {ex.Message}", "Ошибка",
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                PrintButton.IsEnabled = true;
                PrintButton.Content = "ПЕЧАТЬ";
            }
        }
    }
}
