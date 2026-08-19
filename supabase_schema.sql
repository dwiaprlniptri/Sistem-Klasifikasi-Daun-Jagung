-- =====================================================================
-- Jalankan skrip ini satu kali di Supabase -> SQL Editor -> New query
-- =====================================================================

-- 1. Tabel riwayat analisis
create table if not exists public.analysis_history (
    id          bigint generated always as identity primary key,
    created_at  timestamptz  not null default now(),
    method      text         not null,
    label       text         not null,
    confidence  numeric(6,2) not null,
    image_path  text,
    image_url   text
);

-- 2. Tabel rincian confidence tiap kelas
create table if not exists public.prediction_detail (
    id          bigint generated always as identity primary key,
    history_id  bigint       not null
                references public.analysis_history(id) on delete cascade,
    class_name  text         not null,
    confidence  numeric(6,2) not null
);

create index if not exists idx_prediction_detail_history_id
    on public.prediction_detail (history_id);

create index if not exists idx_analysis_history_created_at
    on public.analysis_history (created_at desc);

-- 3. Row Level Security
-- Policy di bawah mengizinkan akses penuh memakai anon key.
-- Cocok untuk aplikasi skripsi/demo. Untuk aplikasi publik yang serius,
-- ganti dengan policy berbasis auth.uid().
alter table public.analysis_history  enable row level security;
alter table public.prediction_detail enable row level security;

drop policy if exists "public access history" on public.analysis_history;
create policy "public access history"
    on public.analysis_history
    for all using (true) with check (true);

drop policy if exists "public access detail" on public.prediction_detail;
create policy "public access detail"
    on public.prediction_detail
    for all using (true) with check (true);

-- 4. Bucket penyimpanan gambar daun (public agar bisa ditampilkan di <img>)
insert into storage.buckets (id, name, public)
values ('leaf-images', 'leaf-images', true)
on conflict (id) do update set public = true;

drop policy if exists "public access leaf images" on storage.objects;
create policy "public access leaf images"
    on storage.objects
    for all using (bucket_id = 'leaf-images')
    with check (bucket_id = 'leaf-images');
