# Klasifikasi Penyakit Daun Jagung

Aplikasi web klasifikasi citra daun jagung menggunakan model hybrid
MobileNetV2 + Local Binary Pattern (LBP).

## Teknologi

| Bagian | Teknologi |
|---|---|
| Bahasa pemrograman | Python |
| Framework web | Streamlit |
| Struktur tampilan | HTML (`frontend/**/*.html`) |
| Desain tampilan | CSS (`frontend/**/*.css`) |
| Cloud | Supabase |
| Database riwayat | PostgreSQL di Supabase |
| Penyimpanan gambar | Supabase Storage (bucket `leaf-images`) |

## Struktur folder

```
app/
├── app.py                  # Halaman, routing, dan alur aplikasi
├── config.py               # Semua konfigurasi terpusat
├── requirements.txt
├── supabase_schema.sql     # Skrip pembuatan tabel + bucket
├── .streamlit/
│   └── secrets.toml        # Kredensial Supabase (dibuat sendiri)
├── assets/bg.png           # Gambar latar
├── models/*.pth            # File bobot model
├── backend/
│   ├── model_service.py    # Arsitektur model, LBP, dan prediksi
│   ├── image_validator.py  # Validasi gambar daun
│   └── storage.py          # Supabase: PostgreSQL + Storage
└── frontend/
    ├── template_loader.py  # Pembaca file HTML/CSS
    ├── components.py       # Perakit komponen tampilan
    ├── common/             # CSS global + background
    ├── sidebar/
    ├── dashboard/
    ├── result/
    └── history/
```

## Cara menjalankan

1. Install dependensi:

   ```bash
   pip install -r requirements.txt
   ```

2. Buat project di [supabase.com](https://supabase.com), lalu buka
   **SQL Editor** dan jalankan isi file `supabase_schema.sql`.

3. Salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml`
   dan isi `SUPABASE_URL` serta `SUPABASE_KEY` (anon public key) dari
   **Project Settings → API**.

4. Pastikan file `assets/bg.png` dan
   `models/best_hybrid_mobilenetv2_lbp59_80_10_10.pth` tersedia.

5. Jalankan aplikasi dari dalam folder `app/`:

   ```bash
   streamlit run app.py
   ```

## Deploy ke Streamlit Community Cloud

Isi kredensial melalui menu **Settings → Secrets** dengan format yang sama
seperti `secrets.toml`. Tidak perlu perubahan kode.
