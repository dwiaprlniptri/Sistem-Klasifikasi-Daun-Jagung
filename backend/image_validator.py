"""Validasi sederhana untuk menyaring gambar yang jelas bukan daun jagung."""

import numpy as np

IMG_SIZE = 224
MIN_LEAF_RATIO = 0.12


def is_likely_leaf_image(pil_img, min_leaf_ratio=MIN_LEAF_RATIO):
    """
    Cek proporsi piksel berwarna daun (hijau atau cokelat penyakit) pada gambar.

    Tujuannya agar screenshot, wajah, tangan, atau objek lain tidak langsung
    masuk ke model klasifikasi penyakit.
    """
    img = pil_img.resize((IMG_SIZE, IMG_SIZE)).convert("RGB")
    arr = np.array(img).astype(np.float32)

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    max_c = np.maximum.reduce([r, g, b])
    min_c = np.minimum.reduce([r, g, b])
    saturation = max_c - min_c

    # Buang area putih/abu-abu seperti layar, dinding, kertas, UI screenshot
    not_white_gray = ~(
        (np.abs(r - g) < 18)
        & (np.abs(g - b) < 18)
        & (max_c > 120)
    )

    # Buang area gelap pekat
    not_dark = max_c > 45

    # Hijau daun
    green_leaf = (
        (g > r + 12)
        & (g > b + 12)
        & (g > 55)
        & (saturation > 20)
        & not_white_gray
        & not_dark
    )

    # Cokelat/kuning daun sakit, dibuat ketat agar warna kulit atau oranye UI
    # tidak mudah lolos
    brown_diseased_leaf = (
        (r > 70)
        & (g > 45)
        & (b < 135)
        & (r >= g * 0.85)
        & (g >= b * 1.05)
        & ((r - b) > 35)
        & (saturation > 30)
        & not_white_gray
        & not_dark
    )

    leaf_ratio = (green_leaf | brown_diseased_leaf).mean()

    return bool(leaf_ratio >= min_leaf_ratio)
