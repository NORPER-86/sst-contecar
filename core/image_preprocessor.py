"""
Módulo de Preprocesamiento y Control de Calidad de Imágenes (OCR Pre-flight).
Optimiza escaneos manuscritos y fotografías de campo para maximizar la precisión
del motor de visión multimodal Google Gemini 3.X.
"""

from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageOps, ImageEnhance, ImageStat


def preflight_image_enhancement(
    image: Image.Image,
    target_dpi: int = 150
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Aplica una secuencia de optimizaciones no destructivas a la imagen:
    1. Corrección automática de orientación basada en metadatos EXIF (fotos de smartphone).
    2. Evaluación de calidad fotométrica (brillo medio, contraste, resolución).
    3. Realce adaptativo de contraste y nitidez si el manuscrito presenta trazos tenues.
    """
    # 1. Normalización de orientación EXIF (Corrige fotos giradas a 90° / 180° / 270°)
    img = ImageOps.exif_transpose(image)
    if img is None:
        img = image.copy()
    else:
        img = img.copy()

    # Convertir a RGB si viene en RGBA o P
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    applied_enhancements = []

    # 2. Diagnóstico fotométrico
    stat = ImageStat.Stat(img.convert("L"))
    mean_brightness = stat.mean[0]  # 0 (negro) a 255 (blanco)
    stddev_contrast = stat.stddev[0]  # Desviación estándar del contraste

    is_low_res = (width < 600 or height < 600)
    is_faint = (mean_brightness > 235 or stddev_contrast < 38.0)
    is_dark = (mean_brightness < 65.0)

    # 3. Realce adaptativo
    if is_faint:
        # Trazos tenues o lavado de luz: subir contraste y reforzar nitidez
        img = ImageEnhance.Contrast(img).enhance(1.40)
        img = ImageEnhance.Sharpness(img).enhance(1.30)
        applied_enhancements.append("Realce de contraste para trazos tenues")
    elif is_dark:
        # Foto subexpuesta / oscura: equilibrar brillo
        img = ImageEnhance.Brightness(img).enhance(1.25)
        img = ImageEnhance.Contrast(img).enhance(1.20)
        applied_enhancements.append("Ajuste de brillo para imagen oscura")
    else:
        # Escaneo estándar: realce sutil de bordes para delimitar casillas
        img = ImageEnhance.Contrast(img).enhance(1.10)
        applied_enhancements.append("Contraste óptimo")

    status = "OPTIMAL"
    if is_low_res:
        status = "LOW_RESOLUTION"
    elif is_faint or is_dark:
        status = "ENHANCED"

    quality_report: Dict[str, Any] = {
        "width": width,
        "height": height,
        "mean_brightness": round(mean_brightness, 1),
        "contrast_score": round(stddev_contrast, 1),
        "status": status,
        "is_low_res": is_low_res,
        "applied_enhancements": applied_enhancements,
        "advisory": (
            "⚠️ Imagen con resolución baja (<600px)" if is_low_res
            else "✨ Auto-rotación y realce de contraste aplicados" if len(applied_enhancements) > 0
            else "✅ Calidad fotográfica óptima"
        )
    }

    return img, quality_report
