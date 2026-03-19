"""Logo compositing utility for DK and CoreTAP branding."""

import os
from io import BytesIO

import numpy as np
from PIL import Image

LOGOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos")


def composite_logos(
    base_image_bytes: bytes,
    logos: str = "both",
    dk_width: int = 220,
    ct_width: int = 150,
    padding: int = 24,
    bar_height_extra: int = 60,
) -> bytes:
    """Composite real DK and CoreTAP logos onto a base image.

    Adds a Void Black (#0A0E1A) bar at the bottom with gradient fade.
    DK logo goes bottom-left, CoreTAP logo goes bottom-right.

    Args:
        base_image_bytes: Raw PNG/JPG bytes of the base image.
        logos: Which logos to add: "both", "dk", "coretap", "none".
        dk_width: Width to scale DK logo to.
        ct_width: Width to scale CoreTAP logo to.
        padding: Padding from edges in pixels.
        bar_height_extra: Extra height for the gradient fade zone.

    Returns:
        PNG bytes of the final composited image.
    """
    if logos == "none":
        return base_image_bytes

    dk_logo_path = os.path.join(LOGOS_DIR, "dk-logo.png")
    ct_logo_path = os.path.join(LOGOS_DIR, "coretap-logo.png")

    base = Image.open(BytesIO(base_image_bytes)).convert("RGB")
    w, h = base.size

    # Load and scale logos as needed
    dk_sm = None
    ct_sm = None

    if logos in ("both", "dk"):
        dk_logo = Image.open(dk_logo_path)
        dk_h = int(dk_logo.height * dk_width / dk_logo.width)
        dk_sm = dk_logo.resize((dk_width, dk_h), Image.LANCZOS)
        dk_sm = _remove_dark_bg(dk_sm)
    else:
        dk_h = 0

    if logos in ("both", "coretap"):
        ct_logo = Image.open(ct_logo_path)
        ct_h = int(ct_logo.height * ct_width / ct_logo.width)
        ct_sm = ct_logo.resize((ct_width, ct_h), Image.LANCZOS)
        ct_sm = _remove_dark_bg(ct_sm)
    else:
        ct_h = 0

    # Calculate bar dimensions
    logo_zone = max(dk_h, ct_h) + padding * 2
    fade_zone = bar_height_extra
    void_black = np.array([10, 14, 26], dtype=np.float64)

    # Apply Void Black bar + gradient fade
    base_np = np.array(base, dtype=np.float64)
    base_np[h - logo_zone :, :] = void_black
    for y in range(fade_zone):
        row_idx = h - logo_zone - fade_zone + y
        if row_idx < 0:
            continue
        t = (y / fade_zone) ** 2
        base_np[row_idx, :] = base_np[row_idx, :] * (1 - t) + void_black * t

    final = Image.fromarray(base_np.astype(np.uint8)).convert("RGBA")

    # Composite DK logo bottom-left
    if dk_sm is not None:
        dk_layer = Image.new("RGBA", final.size, (0, 0, 0, 0))
        dk_layer.paste(dk_sm, (padding, h - dk_h - padding))
        final = Image.alpha_composite(final, dk_layer)

    # Composite CoreTAP logo bottom-right
    if ct_sm is not None:
        ct_layer = Image.new("RGBA", final.size, (0, 0, 0, 0))
        ct_layer.paste(ct_sm, (w - ct_width - padding, h - ct_h - padding))
        final = Image.alpha_composite(final, ct_layer)

    output = BytesIO()
    final.convert("RGB").save(output, "PNG")
    output.seek(0)
    return output.read()


def _remove_dark_bg(img: Image.Image, threshold: int = 40) -> Image.Image:
    """Remove dark background pixels by setting them to transparent."""
    arr = np.array(img.convert("RGBA"))
    brightness = arr[:, :, :3].mean(axis=2)
    arr[brightness < threshold, 3] = 0
    return Image.fromarray(arr)
