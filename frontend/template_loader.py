"""Pemuat file HTML dan CSS dari folder frontend."""

import os
import textwrap

import streamlit as st

BASE_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))


def read_file(relative_path, **kwargs):
    """Baca file template dan ganti placeholder {{key}} dengan nilainya."""
    file_path = os.path.join(BASE_FRONTEND_DIR, relative_path)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    for key, value in kwargs.items():
        content = content.replace("{{" + key + "}}", str(value))

    return textwrap.dedent(content).strip()


def load_html(relative_path, **kwargs):
    """Kembalikan potongan HTML siap dirender oleh st.markdown."""
    return read_file(relative_path, **kwargs)


def render_html(relative_path, **kwargs):
    """Render langsung potongan HTML ke halaman."""
    st.markdown(load_html(relative_path, **kwargs), unsafe_allow_html=True)


def load_css(relative_path, **kwargs):
    """Suntikkan file CSS ke dalam halaman."""
    css = read_file(relative_path, **kwargs)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
