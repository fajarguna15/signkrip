# 🔏 SignKrip — Digital Signature System (Python Flask Edition)

System Tanda Tangan Digital & Verifikasi Keaslian Dokumen Elektronik Berbasis Kriptografi Asimetris (**RSA-PSS 2048-bit** dan **ECDSA P-256**), Hash **SHA-256**, Enkripsi Kunci Privat **AES-256-GCM + PBKDF2**, dan Pembaca/Pembuat **QR-Code**.

---

## 👥 Tim Penyusun / Anggota Kelompok
* **Nama Anggota 1**: [Nama Anda] — **NPM**: [NPM Anda]
* **Nama Anggota 2**: [Nama Anggota 2] — **NPM**: [NPM 2]
* *(Silakan sesuaikan nama & NPM anggota kelompok Anda)*

---

## 📖 Deskripsi Proyek
SignKrip dirancang untuk menjamin otentisitas, integritas, dan anti-penyangkalan (*non-repudiation*) pada dokumen digital. Aplikasi ini dibangun menggunakan **Python Flask** sebagai backend web server, pustaka `cryptography` untuk operasi kriptografi tingkat lanjut, dan frontend Vanilla JS & CSS yang responsif.

### 🛡️ Fitur Keamanan Utama:
1. **Pembangkitan Pasangan Kunci**: Mendukung skema **RSA-PSS 2048-bit** dan **ECDSA P-256** (`secp256r1`).
2. **Enkripsi Kunci Privat**: Kunci privat dienkripsi dengan **AES-256-GCM** dan derivasi kunci **PBKDF2HMAC** (SHA-256, 100,000 iterasi). Kunci privat tidak pernah ditulis polos di kode sumber maupun diunggah.
3. **Pengacak Kriptografis Aman**: Salt dan IV dihasilkan menggunakan `os.urandom()` (CSPRNG).
4. **Hashing & Digital Signature**: Menghitung digest **SHA-256** dokumen dan menandatanganinya menggunakan Kunci Privat.
5. **Verifikasi Keaslian**: Memvalidasi tanda tangan terhadap Kunci Publik dan menolak dokumen yang telah diubah walau hanya **1 byte** (*tampered*).
6. **QR Code Payload Generator**: Menghasilkan gambaran QR Code base64 berisikan metadata penandatanganan dan nilai tanda tangan.
7. **Pengujian & Benchmark 30x**: Fitur otomatis menguji performa penandatanganan 30 iterasi serta pengujian keamanan (Uji Tamper 1-byte, Uji Kunci Salah, dan Uji Pemalsuan QR-Code).

---

## 🚀 Cara Instalasi

### 1. Prasyarat
* Python 3.8+ (Direkomendasikan Python 3.10+)
* `pip` (Python package manager)

### 2. Kloning / Unduh Repositori
```bash
git clone <URL_REPOSITORI_GITHUB>
cd signkrip
```

### 3. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

---

## 💻 Cara Menjalankan Aplikasi

### 1. Menjalankan Server Flask
Jalankan perintah berikut di terminal:
```bash
python app.py
```
Aplikasi akan aktif di **http://localhost:5000** atau **http://127.0.0.1:5000**.
Buka alamat tersebut di peramban web (Chrome/Edge/Firefox).

### 2. Menjalankan Pengujian Unit (Unit Test)
Untuk memastikan seluruh 7 unit test fungsi inti lolos pengujian:
```bash
python -m unittest test_crypto.py
```

---

## 📸 Contoh Penggunaan

### 1. Membuat Pasangan Kunci Baru
1. Buka menu **🔑 Generate Kunci**.
2. Pilih algoritma (`ECDSA P-256` atau `RSA-PSS 2048-bit`).
3. Masukkan kata sandi pengunci (misal: `KataSandiAman123!`).
4. Klik **⚡ Generasi Pasangan Kunci**. Simpan / unduh Kunci Publik (`.pub`).

### 2. Menandatangani Dokumen
1. Buka menu **✍️ Tanda Tangan**.
2. Unggah berkas dokumen (PDF, gambar, atau teks).
3. Isi data Penandatangan (*Nama, Jabatan, Institusi*).
4. Masukkan Kata Sandi Kunci Privat Anda.
5. Klik **✍️ Tandatangani Dokumen**. Unduh berkas tanda tangan (`.sign.json`) dan QR-Code.

### 3. Memverifikasi Keaslian Dokumen
1. Buka menu **🔍 Verifikasi Dokumen**.
2. Unggah berkas dokumen asli.
3. Unggah berkas tanda tangan (`.sign.json`).
4. Klik **🔍 Verifikasi Keaslian**. Sistem akan memberikan status **VALID ✅** jika dokumen otentik, atau **TIDAK VALID ❌** jika dokumen telah dimodifikasi.

---

## 📋 Checklist Kepatuhan Ketentuan Ketat (UTS / Tugas Proyek)

* [x] **Tanpa Hardcode Secret**: Kunci privat, kata sandi, dan salt tidak pernah ditulis langsung di kode sumber.
* [x] **CSPRNG**: Menggunakan `os.urandom()` dan OpenSSL CSPRNG untuk pembuatan Salt, IV, dan Kunci.
* [x] **Tanpa Mode/Algoritma Usang**: Menggunakan AES-GCM (bukan ECB), SHA-256 & RSA-PSS/ECDSA (tanpa MD5/SHA-1/DES).
* [x] **Unit Testing**: Memiliki **7 unit test** di `test_crypto.py` (Lolos pengujian 100%).
* [x] **Dokumentasi LENGKAP**: `README.md` memuat deskripsi, fitur, instalasi, cara menjalankan, contoh penggunaan, dan identitas kelompok.
