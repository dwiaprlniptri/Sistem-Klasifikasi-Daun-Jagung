"""Konfigurasi terpusat aplikasi klasifikasi penyakit daun jagung."""

import os

import streamlit as st

# ==========================================
# IDENTITAS APLIKASI
# ==========================================
APP_TITLE = "Klasifikasi Daun Jagung"
APP_ICON = "🌽"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BG_IMAGE_PATH = os.path.join(BASE_DIR, "assets", "bg.png")


# ==========================================
# MODEL
# ==========================================
MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "best_hybrid_mobilenetv2_lbp59_70_20_10.pth"
)

MODEL_CFG = {
    "path": MODEL_PATH,
    "use_lbp": True,
    "lbp_mode": "uniform",
    "lbp_in_dim": 59,
}


# ==========================================
# KELAS DAN INFORMASI DIAGNOSIS
# ==========================================
CLASS_NAMES = ["Blight", "Common Rus", "Gray Leaf Spot", "Healthy"]

CLASS_DISPLAY = {
    "Blight": "Blight",
    "Common Rus": "Common Rust",
    "Gray Leaf Spotercak": "Gray Leaf Spot",
    "Healthy": "Healthy",
    "Tidak Terdeteksi": "Tidak Terdeteksi",
}

CLASS_COLOR = {
    "Healthy": "result-green",
    "Hawar": "result-red",
    "Common Rus": "result-orange",
    "Gray Leaf Spot": "result-yellow",
}

DEFAULT_COLOR = "result-gray"

CONFIDENCE_THRESHOLD = 0.55
UNDETECTED_LABEL = "Tidak Terdeteksi"

DISEASE_INFO = {
    "Blight": (
        "Blight atau hawar daun biasanya ditandai dengan bercak memanjang "
        "berwarna cokelat hingga keabu-abuan pada daun jagung."
    ),
    "Common Rust": (
        "Common Rust atau karat daun biasanya ditandai dengan bintik-bintik kecil "
        "berwarna cokelat kemerahan seperti karat pada permukaan daun jagung."
    ),
    "Gray Leaf Spot": (
        "Gray Leaf Spot biasanya ditandai dengan bercak memanjang berwarna abu-abu "
        "atau kecokelatan pada daun jagung."
    ),
    "Healthy": (
        "Daun terdeteksi dalam kondisi sehat berdasarkan citra yang dimasukkan."
    ),
}

DEFAULT_INFO = "Informasi diagnosis belum tersedia."

UNDETECTED_INFO = (
    "Gambar tidak terdeteksi sebagai kategori penyakit daun jagung karena nilai "
    "confidence tertinggi berada di bawah "
    f"{CONFIDENCE_THRESHOLD * 100:.0f}%. Gunakan gambar daun jagung yang "
    "lebih jelas, fokus, dan memiliki pencahayaan yang cukup."
)

INVALID_IMAGE_LABEL = "Gambar Tidak Valid"

INVALID_IMAGE_INFO = (
    "Gambar yang diunggah tidak terdeteksi sebagai gambar daun jagung. "
    "Silakan unggah foto daun jagung yang jelas, fokus, dan tidak terlalu "
    "banyak background."
)


# ==========================================
# SUPABASE (PostgreSQL + Storage)
# ==========================================
def get_setting(name, default=""):
    """Ambil konfigurasi dari st.secrets, lalu fallback ke environment variable."""
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        # secrets.toml belum dibuat, abaikan dan lanjut ke environment variable
        pass

    return os.environ.get(name, default).strip()


SUPABASE_URL = get_setting("SUPABASE_URL")
SUPABASE_KEY = get_setting("SUPABASE_KEY")
SUPABASE_BUCKET = get_setting("SUPABASE_BUCKET", "leaf-images")

HISTORY_TABLE = "analysis_history"
DETAIL_TABLE = "prediction_detail"

APP_TIMEZONE = get_setting("APP_TIMEZONE", "Asia/Jakarta")

HISTORY_LIMIT = 100
HISTORY_IMAGE_MAX_SIZE = (500, 500)
