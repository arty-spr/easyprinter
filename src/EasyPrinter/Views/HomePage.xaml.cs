using System.Windows;
using System.Windows.Controls;

namespace EasyPrinter.Views
{
    public partial class HomePage : Page
    {
        private readonly MainWindow _mainWindow;

        public HomePage(MainWindow mainWindow)
        {
            InitializeComponent();
            _mainWindow = mainWindow;
        }

        private void PrintButton_Click(object sender, RoutedEventArgs e)
        {
            _mainWindow.NavigateTo(typeof(PrintView));
        }

        private void ScanButton_Click(object sender, RoutedEventArgs e)
        {
            _mainWindow.NavigateTo(typeof(ScanView));
        }

        private void CopyButton_Click(object sender, RoutedEventArgs e)
        {
            _mainWindow.NavigateTo(typeof(CopyView));
        }

        private void StatusButton_Click(object sender, RoutedEventArgs e)
        {
            _mainWindow.NavigateTo(typeof(StatusView));
        }
    }
}
