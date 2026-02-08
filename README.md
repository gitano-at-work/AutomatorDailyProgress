# Pelapor Kinerja Harian

Mengotomatisasi pengisian laporan kinerja harian dari Google Doc.

## Persiapan

1.  **Install Python 3.8+**
2.  Jalankan `run.bat` (Ini akan mengatur virtual environment dan menginstall dependensi secara otomatis).

## Cara Penggunaan

1.  Masukkan URL Google Doc Anda (harus dapat diakses oleh Anda).
2.  Masukkan Username dan Password Web App Anda.
3.  Klik **Start Automation**.
4.  Browser akan terbuka.
5.  Jika 2FA diperlukan, otomatisasi akan DIJEDA. Masukkan kode 2FA Anda di browser secara manual.
6.  Setelah login (dashboard terdeteksi), otomatisasi akan berlanjut (di fase mendatang).
7.  Untuk saat ini (Fase 1), browser akan ditutup setelah verifikasi login.

## Konfigurasi

Pengaturan disimpan di `config.json` secara otomatis.

## Catatan Keamanan

Password saat ini disimpan di `config.json` dalam bentuk plain text. Jangan bagikan file ini.
