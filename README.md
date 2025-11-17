# Part Monitoring System

Aplikasi Streamlit untuk monitoring penggantian part mesin dengan fitur lengkap.

## Fitur Utama

### ✅ Input Data
- Nomor Part
- Kode Part  
- Nama Mesin
- Material Mesin
- Tanggal Pemasangan
- Rekomendasi Penggunaan (jam)
- Kategori Part (Mechanical, Electrical, Pneumatic)

### ✅ Output & Monitoring
- Tanggal Penggantian
- Sisa Usia Pakai (jam)
- Status Part dengan warna:
  - 🟢 Normal (hijau) - sisa usia > 500 jam
  - 🟡 Warning (kuning) - sisa usia < 500 jam
  - 🔴 Harus Ganti (merah blinking) - sisa usia = 0 jam

### ✅ Fitur Tambahan
- Upload data dari CSV
- Filter data (mesin, material, kategori)
- Manual Book (Indonesia & English)
- Save & Edit data
- Tandai part sudah diganti
- Download data ke CSV

## Cara Menjalankan

### 1. Install Dependencies
```bash
pip install -r requirements.txt