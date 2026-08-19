"""Akses data riwayat analisis ke Supabase (PostgreSQL + Storage)."""

import uuid
from datetime import datetime, timezone
from io import BytesIO

import streamlit as st
from PIL import Image
from supabase import Client, create_client

from config import (
    APP_TIMEZONE,
    DETAIL_TABLE,
    HISTORY_IMAGE_MAX_SIZE,
    HISTORY_TABLE,
    SUPABASE_BUCKET,
    SUPABASE_KEY,
    SUPABASE_URL,
)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


class StorageNotConfigured(Exception):
    """Dilempar saat kredensial Supabase belum diisi."""


# ==========================================
# KONEKSI
# ==========================================
@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    """Buat satu koneksi Supabase yang dipakai ulang selama aplikasi berjalan."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise StorageNotConfigured(
            "SUPABASE_URL dan SUPABASE_KEY belum diisi. "
            "Lengkapi file .streamlit/secrets.toml terlebih dahulu."
        )

    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================================
# SUPABASE STORAGE (FILE GAMBAR)
# ==========================================
def upload_history_image(image: Image.Image):
    """Unggah gambar daun ke Supabase Storage, kembalikan (object_path, public_url)."""
    client = get_client()

    img = image.copy()
    img.thumbnail(HISTORY_IMAGE_MAX_SIZE)

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    object_path = (
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
    )

    bucket = client.storage.from_(SUPABASE_BUCKET)
    bucket.upload(
        object_path,
        buffer.getvalue(),
        {"content-type": "image/png", "upsert": "false"},
    )

    return object_path, bucket.get_public_url(object_path)


def remove_history_images(object_paths):
    """Hapus daftar file gambar dari Supabase Storage."""
    paths = [p for p in object_paths if p]

    if not paths:
        return

    client = get_client()
    client.storage.from_(SUPABASE_BUCKET).remove(paths)


# ==========================================
# POSTGRESQL (TABEL RIWAYAT)
# ==========================================
def add_history(method, label, confidence, image, prediction_details=None):
    """Simpan satu hasil analisis beserta rincian confidence tiap kelas."""
    client = get_client()

    object_path, public_url = upload_history_image(image)

    history_row = (
        client.table(HISTORY_TABLE)
        .insert(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "method": method,
                "label": label,
                "confidence": round(confidence * 100, 2),
                "image_path": object_path,
                "image_url": public_url,
            }
        )
        .execute()
    )

    history_id = history_row.data[0]["id"]

    if prediction_details:
        client.table(DETAIL_TABLE).insert(
            [
                {
                    "history_id": history_id,
                    "class_name": class_name,
                    "confidence": round(conf * 100, 2),
                }
                for class_name, conf in prediction_details
            ]
        ).execute()

    return history_id


def get_history(limit=10):
    """Ambil riwayat analisis terbaru."""
    client = get_client()

    response = (
        client.table(HISTORY_TABLE)
        .select("id, created_at, method, label, confidence, image_path, image_url")
        .order("id", desc=True)
        .limit(limit)
        .execute()
    )

    rows = response.data or []

    for row in rows:
        row["created_at"] = format_created_at(row.get("created_at"))

    return rows


def get_history_count():
    """Hitung total analisis tanpa perlu mengunduh seluruh baris."""
    client = get_client()

    response = (
        client.table(HISTORY_TABLE)
        .select("id", count="exact")
        .limit(1)
        .execute()
    )

    return response.count or 0


def get_prediction_details(history_id):
    """Ambil rincian confidence tiap kelas untuk satu riwayat."""
    client = get_client()

    response = (
        client.table(DETAIL_TABLE)
        .select("class_name, confidence")
        .eq("history_id", history_id)
        .order("confidence", desc=True)
        .execute()
    )

    return response.data or []


def clear_history():
    """Kosongkan seluruh riwayat beserta file gambarnya."""
    client = get_client()

    response = client.table(HISTORY_TABLE).select("image_path").execute()
    remove_history_images(row.get("image_path") for row in (response.data or []))

    # prediction_detail ikut terhapus lewat ON DELETE CASCADE
    client.table(HISTORY_TABLE).delete().gt("id", 0).execute()


# ==========================================
# UTILITAS
# ==========================================
def format_created_at(value):
    """Ubah timestamp UTC dari PostgreSQL menjadi waktu lokal yang mudah dibaca."""
    if not value:
        return "-"

    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return str(value)

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)

    if ZoneInfo is not None:
        try:
            moment = moment.astimezone(ZoneInfo(APP_TIMEZONE))
        except Exception:
            moment = moment.astimezone()
    else:
        moment = moment.astimezone()

    return moment.strftime("%d-%m-%Y %H:%M:%S")
