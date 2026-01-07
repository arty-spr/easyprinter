using System;
using System.Drawing;
using System.Drawing.Imaging;
using EasyPrinter.Models;

namespace EasyPrinter.Services
{
    /// <summary>
    /// Сервис обработки изображений (яркость, контраст, резкость, гамма)
    /// </summary>
    public class ImageProcessingService
    {
        /// <summary>
        /// Применить все настройки к изображению
        /// </summary>
        public Image ApplyAdjustments(Image source, ImageAdjustments adjustments)
        {
            var result = new Bitmap(source);

            if (adjustments.Brightness != 0 || adjustments.Contrast != 0)
            {
                result = ApplyBrightnessContrast(result, adjustments.Brightness, adjustments.Contrast);
            }

            if (Math.Abs(adjustments.Gamma - 1.0) > 0.01)
            {
                result = ApplyGamma(result, adjustments.Gamma);
            }

            if (adjustments.Sharpness > 0)
            {
                result = ApplySharpness(result, adjustments.Sharpness);
            }

            return result;
        }

        /// <summary>
        /// Применить яркость и контрастность
        /// </summary>
        public Bitmap ApplyBrightnessContrast(Bitmap source, int brightness, int contrast)
        {
            // Нормализуем значения
            float brightnessFactor = brightness / 100.0f;
            float contrastFactor = (100.0f + contrast) / 100.0f;
            contrastFactor *= contrastFactor;

            var result = new Bitmap(source.Width, source.Height);

            // Используем ColorMatrix для быстрой обработки
            float b = brightnessFactor;
            float c = contrastFactor;
            float t = (1.0f - c) / 2.0f + b;

            var colorMatrix = new ColorMatrix(new float[][]
            {
                new float[] { c, 0, 0, 0, 0 },
                new float[] { 0, c, 0, 0, 0 },
                new float[] { 0, 0, c, 0, 0 },
                new float[] { 0, 0, 0, 1, 0 },
                new float[] { t, t, t, 0, 1 }
            });

            using var attributes = new ImageAttributes();
            attributes.SetColorMatrix(colorMatrix);

            using var graphics = Graphics.FromImage(result);
            graphics.DrawImage(source,
                new Rectangle(0, 0, source.Width, source.Height),
                0, 0, source.Width, source.Height,
                GraphicsUnit.Pixel,
                attributes);

            return result;
        }

        /// <summary>
        /// Применить гамма-коррекцию
        /// </summary>
        public Bitmap ApplyGamma(Bitmap source, double gamma)
        {
            var result = new Bitmap(source.Width, source.Height);

            // Создаём таблицу гамма-коррекции
            byte[] gammaTable = new byte[256];
            for (int i = 0; i < 256; i++)
            {
                gammaTable[i] = (byte)Math.Min(255, Math.Max(0,
                    Math.Pow(i / 255.0, 1.0 / gamma) * 255));
            }

            using var attributes = new ImageAttributes();
            attributes.SetGamma((float)gamma);

            using var graphics = Graphics.FromImage(result);
            graphics.DrawImage(source,
                new Rectangle(0, 0, source.Width, source.Height),
                0, 0, source.Width, source.Height,
                GraphicsUnit.Pixel,
                attributes);

            return result;
        }

        /// <summary>
        /// Применить резкость (Unsharp Mask)
        /// </summary>
        public Bitmap ApplySharpness(Bitmap source, int amount)
        {
            if (amount <= 0) return new Bitmap(source);

            // Нормализуем amount (0-100) к множителю ядра
            float strength = amount / 100.0f * 2.0f;

            // Ядро резкости (Unsharp Mask)
            float[,] kernel = new float[,]
            {
                { 0, -strength, 0 },
                { -strength, 1 + 4 * strength, -strength },
                { 0, -strength, 0 }
            };

            return ApplyConvolution(source, kernel);
        }

        /// <summary>
        /// Применить свёрточный фильтр
        /// </summary>
        private Bitmap ApplyConvolution(Bitmap source, float[,] kernel)
        {
            int width = source.Width;
            int height = source.Height;
            var result = new Bitmap(width, height);

            int kernelWidth = kernel.GetLength(1);
            int kernelHeight = kernel.GetLength(0);
            int kernelOffsetX = kernelWidth / 2;
            int kernelOffsetY = kernelHeight / 2;

            // Для производительности используем LockBits
            var sourceData = source.LockBits(
                new Rectangle(0, 0, width, height),
                ImageLockMode.ReadOnly,
                PixelFormat.Format32bppArgb);

            var resultData = result.LockBits(
                new Rectangle(0, 0, width, height),
                ImageLockMode.WriteOnly,
                PixelFormat.Format32bppArgb);

            unsafe
            {
                byte* sourcePtr = (byte*)sourceData.Scan0;
                byte* resultPtr = (byte*)resultData.Scan0;
                int stride = sourceData.Stride;

                for (int y = 0; y < height; y++)
                {
                    for (int x = 0; x < width; x++)
                    {
                        float r = 0, g = 0, b = 0;

                        for (int ky = 0; ky < kernelHeight; ky++)
                        {
                            int sy = Math.Clamp(y + ky - kernelOffsetY, 0, height - 1);

                            for (int kx = 0; kx < kernelWidth; kx++)
                            {
                                int sx = Math.Clamp(x + kx - kernelOffsetX, 0, width - 1);
                                int offset = sy * stride + sx * 4;

                                float kv = kernel[ky, kx];
                                b += sourcePtr[offset] * kv;
                                g += sourcePtr[offset + 1] * kv;
                                r += sourcePtr[offset + 2] * kv;
                            }
                        }

                        int resultOffset = y * stride + x * 4;
                        resultPtr[resultOffset] = (byte)Math.Clamp((int)b, 0, 255);
                        resultPtr[resultOffset + 1] = (byte)Math.Clamp((int)g, 0, 255);
                        resultPtr[resultOffset + 2] = (byte)Math.Clamp((int)r, 0, 255);
                        resultPtr[resultOffset + 3] = sourcePtr[y * stride + x * 4 + 3]; // Alpha
                    }
                }
            }

            source.UnlockBits(sourceData);
            result.UnlockBits(resultData);

            return result;
        }

        /// <summary>
        /// Конвертировать System.Drawing.Image в WPF BitmapSource
        /// </summary>
        public System.Windows.Media.Imaging.BitmapSource ConvertToBitmapSource(Image image)
        {
            using var bitmap = new Bitmap(image);
            var hBitmap = bitmap.GetHbitmap();

            try
            {
                return System.Windows.Interop.Imaging.CreateBitmapSourceFromHBitmap(
                    hBitmap,
                    IntPtr.Zero,
                    System.Windows.Int32Rect.Empty,
                    System.Windows.Media.Imaging.BitmapSizeOptions.FromEmptyOptions());
            }
            finally
            {
                DeleteObject(hBitmap);
            }
        }

        [System.Runtime.InteropServices.DllImport("gdi32.dll")]
        private static extern bool DeleteObject(IntPtr hObject);
    }
}
