namespace EasyPrinter.Models
{
    /// <summary>
    /// Настройки обработки изображения (яркость, контраст, резкость, гамма)
    /// </summary>
    public class ImageAdjustments
    {
        /// <summary>
        /// Яркость (-100 до +100)
        /// </summary>
        public int Brightness { get; set; } = 0;

        /// <summary>
        /// Контрастность (-100 до +100)
        /// </summary>
        public int Contrast { get; set; } = 0;

        /// <summary>
        /// Резкость (0 до 100)
        /// </summary>
        public int Sharpness { get; set; } = 0;

        /// <summary>
        /// Гамма (0.1 до 3.0)
        /// </summary>
        public double Gamma { get; set; } = 1.0;

        /// <summary>
        /// Проверяет, есть ли изменения относительно значений по умолчанию
        /// </summary>
        public bool HasChanges =>
            Brightness != 0 ||
            Contrast != 0 ||
            Sharpness != 0 ||
            Math.Abs(Gamma - 1.0) > 0.01;

        /// <summary>
        /// Сбросить все настройки к значениям по умолчанию
        /// </summary>
        public void Reset()
        {
            Brightness = 0;
            Contrast = 0;
            Sharpness = 0;
            Gamma = 1.0;
        }

        /// <summary>
        /// Создает копию настроек
        /// </summary>
        public ImageAdjustments Clone()
        {
            return new ImageAdjustments
            {
                Brightness = Brightness,
                Contrast = Contrast,
                Sharpness = Sharpness,
                Gamma = Gamma
            };
        }
    }
}
