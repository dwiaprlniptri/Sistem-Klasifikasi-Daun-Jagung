"""
Identitas perangkat agar riwayat tiap pengunjung terpisah.

Urutan penyimpanan ID:
1. Cookie browser  -> paling melekat, bertahan walau URL diketik polos
2. Parameter URL   -> cadangan bila cookie belum siap atau diblokir
3. Session state   -> menjaga ID tetap sama antar rerun

Butuh paket tambahan di requirements.txt:
    streamlit-cookies-manager
"""

import uuid

import streamlit as st

COOKIE_NAME = "daun_jagung_device"
DEVICE_PARAM = "d"
SESSION_KEY = "_device_id"

try:
    from streamlit_cookies_manager import CookieManager

    COOKIE_AVAILABLE = True
except ImportError:
    COOKIE_AVAILABLE = False


def _get_cookie_manager():
    """Satu CookieManager per sesi browser."""
    if not COOKIE_AVAILABLE:
        return None

    if "_cookie_manager" not in st.session_state:
        try:
            st.session_state._cookie_manager = CookieManager()
        except Exception:
            st.session_state._cookie_manager = None

    return st.session_state._cookie_manager


def _is_valid(value):
    return bool(value) and len(str(value)) == 32


def _read_from_url():
    value = st.query_params.get(DEVICE_PARAM)

    if isinstance(value, list):
        value = value[0] if value else None

    return value if _is_valid(value) else None


def get_device_id():
    """Kembalikan ID unik untuk perangkat/browser yang sedang membuka aplikasi."""
    if SESSION_KEY in st.session_state:
        return st.session_state[SESSION_KEY]

    cookies = _get_cookie_manager()

    try:
        cookie_ready = cookies is not None and cookies.ready()
    except Exception:
        cookie_ready = False

    device_id = None

    # 1. Coba baca dari cookie
    if cookie_ready:
        try:
            candidate = cookies.get(COOKIE_NAME)
            if _is_valid(candidate):
                device_id = candidate
        except Exception:
            pass

    # 2. Coba baca dari URL
    if device_id is None:
        device_id = _read_from_url()

    # 3. Belum ada di mana pun, buat baru
    if device_id is None:
        device_id = uuid.uuid4().hex

    # Simpan ke cookie supaya kunjungan berikutnya langsung dikenali
    if cookie_ready:
        try:
            if cookies.get(COOKIE_NAME) != device_id:
                cookies[COOKIE_NAME] = device_id
                cookies.save()
        except Exception:
            pass

    # Simpan juga ke URL sebagai cadangan bila cookie diblokir browser
    try:
        if st.query_params.get(DEVICE_PARAM) != device_id:
            st.query_params[DEVICE_PARAM] = device_id
    except Exception:
        pass

    st.session_state[SESSION_KEY] = device_id

    return device_id
