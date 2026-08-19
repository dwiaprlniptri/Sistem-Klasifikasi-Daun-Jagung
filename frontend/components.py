"""Komponen tampilan yang dirakit dari file HTML dan CSS di folder frontend."""

import base64

import streamlit as st

from config import CONFIDENCE_THRESHOLD
from frontend.template_loader import load_css, load_html, render_html

CSS_FILES = [
    "common/common.css",
    "sidebar/sidebar.css",
    "dashboard/dashboard.css",
    "result/result.css",
    "history/history.css",
]


def load_all_css():
    """Muat seluruh stylesheet aplikasi."""
    for css_file in CSS_FILES:
        load_css(css_file)


def set_page_background(image_path):
    """Pasang gambar latar halaman dari file PNG lokal."""
    try:
        with open(image_path, "rb") as f:
            bg_data = base64.b64encode(f.read()).decode()
    except OSError:
        st.warning(f"File background tidak ditemukan: {image_path}")
        return

    load_css("common/background.css", bg_data=bg_data)


# ==========================================
# HALAMAN HASIL
# ==========================================
def render_result_box(display_label, confidence, result_class):
    render_html(
        "result/result.html",
        display_label=display_label,
        confidence=f"{confidence * 100:.2f}",
        result_class=result_class,
    )


def render_invalid_result_box(display_label):
    render_html("result/result_invalid.html", display_label=display_label)


def render_confidence_row(label, confidence):
    render_html(
        "result/confidence_row.html",
        label=label,
        confidence=f"{confidence * 100:.2f}",
    )


def render_undetected_box():
    render_html(
        "result/undetected.html",
        threshold=f"{CONFIDENCE_THRESHOLD * 100:.0f}",
    )


def render_info_box(info_text):
    render_html("result/info_box.html", info_text=info_text)


# ==========================================
# HALAMAN RIWAYAT
# ==========================================
def render_history_item(item):
    image_url = item.get("image_url")

    image_html = (
        load_html("history/history_thumb.html", image_url=image_url)
        if image_url
        else ""
    )

    render_html(
        "history/history_item.html",
        image_html=image_html,
        label=item.get("label", "-"),
        confidence=f"{float(item.get('confidence') or 0):.2f}",
        method=item.get("method", "-"),
        created_at=item.get("created_at", "-"),
    )
