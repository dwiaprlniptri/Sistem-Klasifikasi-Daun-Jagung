"""Aplikasi web Streamlit untuk klasifikasi penyakit daun jagung."""

import hashlib
from io import BytesIO

import streamlit as st
from PIL import Image

from backend.image_validator import is_likely_leaf_image
from backend.model_service import load_model_from_path, predict_image
from backend.storage import (
    StorageNotConfigured,
    add_history,
    clear_history,
    get_history,
    get_history_count,
)
from config import (
    APP_ICON,
    APP_TITLE,
    BG_IMAGE_PATH,
    CLASS_COLOR,
    CLASS_DISPLAY,
    CONFIDENCE_THRESHOLD,
    DEFAULT_COLOR,
    DEFAULT_INFO,
    DISEASE_INFO,
    HISTORY_LIMIT,
    INVALID_IMAGE_INFO,
    INVALID_IMAGE_LABEL,
    MODEL_CFG,
    UNDETECTED_INFO,
    UNDETECTED_LABEL,
)
from frontend.components import (
    load_all_css,
    render_confidence_row,
    render_history_item,
    render_info_box,
    render_invalid_result_box,
    render_result_box,
    render_undetected_box,
    set_page_background,
)
from frontend.template_loader import render_html

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)

set_page_background(BG_IMAGE_PATH)
load_all_css()


# ==========================================
# 2. SESSION STATE
# ==========================================
DEFAULT_STATE = {
    "last_analysis_key": None,
    "input_method": None,
    "method_selector": None,
    "last_page": None,
    "reset_counter": 0,
    "current_upload_bytes": None,
    "current_upload_name": None,
    "current_upload_size": None,
    "current_camera_bytes": None,
    "show_upload_result": False,
    "show_camera_result": False,
}

for key, value in DEFAULT_STATE.items():
    st.session_state.setdefault(key, value)


def reset_input_state():
    """Kosongkan gambar dan hasil analisis saat berpindah halaman."""
    for key, value in DEFAULT_STATE.items():
        if key not in ("reset_counter", "last_page"):
            st.session_state[key] = value

    st.session_state.reset_counter += 1


# ==========================================
# 3. MODEL
# ==========================================
@st.cache_resource(show_spinner=False)
def get_model():
    return load_model_from_path(
        MODEL_CFG["path"],
        MODEL_CFG["use_lbp"],
        MODEL_CFG["lbp_in_dim"],
    )


# ==========================================
# 4. CALLBACK UPLOAD DAN KAMERA
# ==========================================
def on_upload_change(upload_key):
    file_obj = st.session_state.get(upload_key)

    st.session_state.show_upload_result = False
    st.session_state.current_upload_bytes = file_obj.getvalue() if file_obj else None
    st.session_state.current_upload_name = file_obj.name if file_obj else None
    st.session_state.current_upload_size = file_obj.size if file_obj else None


def on_camera_change(camera_key):
    file_obj = st.session_state.get(camera_key)

    st.session_state.show_camera_result = False

    if file_obj is None:
        st.session_state.current_camera_bytes = None
        return

    camera_bytes = file_obj.getvalue()

    if camera_bytes:
        st.session_state.current_camera_bytes = camera_bytes


# ==========================================
# 5. HASIL PREDIKSI
# ==========================================
def build_diagnosis(results):
    """Tentukan label tampilan, warna, dan teks informasi dari hasil prediksi."""
    raw_label, top_conf = results[0]

    if top_conf < CONFIDENCE_THRESHOLD:
        return UNDETECTED_LABEL, DEFAULT_COLOR, UNDETECTED_INFO, top_conf, True

    display_label = CLASS_DISPLAY.get(raw_label, raw_label)
    result_class = CLASS_COLOR.get(raw_label, DEFAULT_COLOR)
    info_text = DISEASE_INFO.get(raw_label, DEFAULT_INFO)

    return display_label, result_class, info_text, top_conf, False


def display_results(image, input_method, analysis_key):
    st.markdown("<br>", unsafe_allow_html=True)

    if not is_likely_leaf_image(image):
        col1, col2 = st.columns([4, 8], gap="large")

        with col1:
            st.image(image, caption="Input Gambar", use_container_width=True)

        with col2:
            render_invalid_result_box(INVALID_IMAGE_LABEL)
            render_info_box(INVALID_IMAGE_INFO)

        return

    try:
        model = get_model()
    except Exception as e:
        st.error("Model gagal dimuat. Periksa file model dan path model.")
        st.code(str(e))
        return

    results = predict_image(image, model, MODEL_CFG)
    display_label, result_class, info_text, top_conf, is_undetected = build_diagnosis(results)

    if st.session_state.last_analysis_key != analysis_key:
        try:
            add_history(
                method=input_method,
                label=display_label,
                confidence=top_conf,
                image=image,
                prediction_details=results,
            )
            st.session_state.last_analysis_key = analysis_key
        except StorageNotConfigured as e:
            st.warning(str(e))
        except Exception as e:
            st.warning("Riwayat gagal disimpan ke Supabase.")
            st.code(str(e))

    col1, col2 = st.columns([4, 8], gap="large")

    with col1:
        st.image(image, caption="Input Gambar", use_container_width=True)

    with col2:
        render_result_box(display_label, top_conf, result_class)

        for label, conf in results:
            render_confidence_row(CLASS_DISPLAY.get(label, label), conf)
            st.progress(float(conf))

        if is_undetected:
            render_undetected_box()

        render_info_box(info_text)


# ==========================================
# 6. HALAMAN DASHBOARD
# ==========================================
def display_dashboard_page():
    render_html("dashboard/dashboard.html")

    _, method_col, _ = st.columns([1.35, 2, 1.35])

    with method_col:
        selected_method = st.radio(
            "Pilih metode input",
            ["📂 Upload File", "📷 Kamera"],
            index=None,
            horizontal=True,
            key="method_selector",
            label_visibility="collapsed",
        )

    if selected_method == "📂 Upload File":
        st.session_state.input_method = "Upload File"
        st.session_state.show_camera_result = False
    elif selected_method == "📷 Kamera":
        st.session_state.input_method = "Kamera"
        st.session_state.show_upload_result = False

    if st.session_state.input_method == "Upload File":
        display_upload_section()
    elif st.session_state.input_method == "Kamera":
        display_camera_section()


def display_upload_section():
    counter = st.session_state.reset_counter
    upload_key = f"upload_input_{counter}"

    st.file_uploader(
        "Unggah gambar",
        type=["jpg", "jpeg", "png"],
        key=upload_key,
        on_change=on_upload_change,
        args=(upload_key,),
    )

    if st.button("Analisis gambar", use_container_width=True, key=f"analyze_upload_{counter}"):
        if st.session_state.current_upload_bytes is None:
            st.warning("Silakan upload gambar terlebih dahulu.")
        else:
            st.session_state.show_upload_result = True

    if st.session_state.show_upload_result and st.session_state.current_upload_bytes:
        image = Image.open(BytesIO(st.session_state.current_upload_bytes)).convert("RGB")

        analysis_key = (
            f"upload_{st.session_state.current_upload_name}_"
            f"{st.session_state.current_upload_size}_{counter}"
        )

        display_results(image, "Upload File", analysis_key)


def display_camera_section():
    counter = st.session_state.reset_counter
    camera_key = f"camera_input_{counter}"

    st.camera_input(
        "Ambil foto daun jagung",
        key=camera_key,
        on_change=on_camera_change,
        args=(camera_key,),
        label_visibility="collapsed",
    )

    if st.button("Analisis gambar", use_container_width=True, key=f"analyze_camera_{counter}"):
        if st.session_state.current_camera_bytes is None:
            st.warning("Silakan ambil foto daun jagung terlebih dahulu.")
        else:
            st.session_state.show_camera_result = True

    if st.session_state.show_camera_result and st.session_state.current_camera_bytes:
        camera_bytes = st.session_state.current_camera_bytes
        image = Image.open(BytesIO(camera_bytes)).convert("RGB")

        digest = hashlib.md5(camera_bytes).hexdigest()[:12]
        display_results(image, "Kamera", f"camera_{digest}_{counter}")


# ==========================================
# 7. HALAMAN RIWAYAT
# ==========================================
def display_history_page():
    render_html("history/history.html")

    try:
        history_items = get_history(limit=HISTORY_LIMIT)
    except StorageNotConfigured as e:
        st.warning(str(e))
        return
    except Exception as e:
        st.error("Riwayat gagal dimuat dari Supabase.")
        st.code(str(e))
        return

    if not history_items:
        st.info("Belum ada riwayat analisis.")
        return

    for item in history_items:
        render_history_item(item)

    if st.button("Hapus Riwayat", use_container_width=True):
        clear_history()
        st.session_state.last_analysis_key = None
        st.rerun()


# ==========================================
# 8. SIDEBAR
# ==========================================
with st.sidebar:
    render_html("sidebar/sidebar.html")

    page = st.radio(
        "Pilih Halaman",
        ["Dashboard", "Riwayat Analisis"],
        key="page_navigation",
    )

    try:
        history_count = get_history_count()
    except Exception:
        history_count = 0

    st.markdown("---")
    st.metric("Total Analisis", history_count)

    st.markdown(
        """
### Model
MobileNetV2 + LBP

### Kelas
4 Kelas Penyakit
"""
    )


# ==========================================
# 9. ROUTING HALAMAN
# ==========================================
if page == "Dashboard":
    if st.session_state.last_page != "Dashboard":
        reset_input_state()

    st.session_state.last_page = "Dashboard"
    display_dashboard_page()

elif page == "Riwayat Analisis":
    st.session_state.last_page = "Riwayat Analisis"
    display_history_page()
