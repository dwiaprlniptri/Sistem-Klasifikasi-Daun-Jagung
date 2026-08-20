"""Identitas perangkat agar riwayat tiap pengunjung terpisah."""

import uuid

import streamlit as st

DEVICE_PARAM = "d"
SESSION_KEY = "_device_id"


def get_device_id():
    """
    Kembalikan ID unik untuk perangkat/browser yang sedang membuka aplikasi.

    ID disimpan di parameter URL, jadi tetap sama walau halaman di-refresh
    atau aplikasi di-reboot. Perangkat lain akan mendapat ID berbeda,
    sehingga riwayatnya tidak saling bercampur.
    """
    if SESSION_KEY in st.session_state:
        return st.session_state[SESSION_KEY]

    device_id = st.query_params.get(DEVICE_PARAM)

    if isinstance(device_id, list):
        device_id = device_id[0] if device_id else None

    if not device_id or len(str(device_id)) != 32:
        device_id = uuid.uuid4().hex
        st.query_params[DEVICE_PARAM] = device_id

    st.session_state[SESSION_KEY] = device_id

    return device_id
