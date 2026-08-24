"""
card_generator.py
High-Definition Informative Card Image Generator for WhatsApp / Social Sharing.
Generates an 800x420 dark-slate (#0F172A) informative visual metric card with
dynamic CGWB groundwater status, water table depth, soil moisture, and rain forecasts.
"""

import io
import os
import logging
from typing import Optional, Any
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("ingres_card_generator")

# Font Fallback Resolver
def _get_font(size: int, bold: bool = False) -> Any:
    """Safely loads modern system fonts across macOS, Linux, and Windows with default fallback."""
    font_candidates = []
    if bold:
        font_candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf"
        ]
    else:
        font_candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Supplemental/Verdana.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:\\Windows\\Fonts\\arial.ttf"
        ]

    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    try:
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()

def generate_whatsapp_card(
    district: str,
    status: str,
    depth_str: str,
    moisture_str: str,
    rain_str: str,
    state: Optional[str] = None,
    extraction_pct_str: Optional[str] = None
) -> bytes:
    """
    Generates an 800x420 PNG card for WhatsApp with formatted groundwater metrics.
    """
    w, h = 800, 420
    img = Image.new("RGB", (w, h), color="#0F172A")
    draw = ImageDraw.Draw(img)

    # 1. Top Decorative Accent Bar
    draw.rectangle([(0, 0), (w, 6)], fill="#0284C7")

    # 2. Typography
    font_brand = _get_font(13, bold=True)
    font_title = _get_font(22, bold=True)
    font_sub = _get_font(15, bold=False)
    font_badge = _get_font(13, bold=True)
    font_label = _get_font(13, bold=False)
    font_value = _get_font(17, bold=True)
    font_footer = _get_font(12, bold=False)

    # 3. Header Branding & District Title
    draw.text((32, 22), "JAL SATHI  •  जल साथी (भूजल एवं कृषि सलाहकार)", font=font_brand, fill="#38BDF8")
    
    dist_label = district.strip().title() if district else "District Query"
    if state:
        dist_label += f" ({state.strip().title()})"
    draw.text((32, 45), f"📍 {dist_label}", font=font_title, fill="#F8FAFC")

    # 4. Status Category Badge
    st_clean = (status or "Safe").strip().title()
    if "Over" in st_clean or "Dark" in st_clean:
        badge_bg = "#EF4444"
        badge_text = "OVER-EXPLOITED (DARK ZONE)"
        status_color = "#F87171"
    elif "Critical" in st_clean:
        badge_bg = "#F97316"
        badge_text = "CRITICAL (REGULATED)"
        status_color = "#FB923C"
    elif "Semi" in st_clean:
        badge_bg = "#F59E0B"
        badge_text = "SEMI-CRITICAL (MONITORED)"
        status_color = "#FBBF24"
    else:
        badge_bg = "#10B981"
        badge_text = "SAFE (PERMITTED)"
        status_color = "#34D399"

    # Measure and draw badge pill
    badge_w = 230
    draw.rounded_rectangle([(w - badge_w - 32, 26), (w - 32, 64)], radius=8, fill=badge_bg)
    draw.text((w - badge_w - 18, 37), badge_text, font=font_badge, fill="#FFFFFF")

    # 5. 2x2 Metric Cards Grid
    grid_coords = [
        (32, 95, 385, 225),    # Card 1: Water Table Depth
        (415, 95, 768, 225),   # Card 2: Status / Extraction
        (32, 245, 385, 365),   # Card 3: Soil Moisture
        (415, 245, 768, 365)   # Card 4: 48h Rain Forecast
    ]

    second_card_val = extraction_pct_str if extraction_pct_str else f"{st_clean} Category"

    metric_items = [
        ("💧 Water Table Depth (CGWB DWLR)", depth_str or "N/A", "#38BDF8"),
        ("📊 Extraction Level & Status", second_card_val, status_color),
        ("🌱 Live Topsoil Moisture (Satellite)", moisture_str or "Adequate", "#FBBF24"),
        ("🌧️ 48-Hour Rain Forecast", rain_str or "No Rain Expected", "#6EE7B7")
    ]

    for (label, val, color), (x1, y1, x2, y2) in zip(metric_items, grid_coords):
        # Card Background with Subtle Border
        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=10, fill="#1E293B", outline="#334155", width=1)
        # Label
        draw.text((x1 + 16, y1 + 16), label, font=font_label, fill="#94A3B8")
        # Value (Truncate if excessively long)
        display_val = str(val)
        if len(display_val) > 34:
            display_val = display_val[:32] + "..."
        draw.text((x1 + 16, y1 + 52), display_val, font=font_value, fill=color)

    # 6. Card Footer
    draw.text((32, 385), "Source: INGRES CGWB Aquifer Database  •  Open-Meteo Satellite  •  PMKSY", font=font_footer, fill="#64748B")

    # 7. Output Buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
