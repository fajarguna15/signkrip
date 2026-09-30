# 🔏 SignKrip — Digital Signature System (Python Flask Edition)

Sistem Tanda Tangan Digital & Verifikasi Keaslian Dokumen Elektronik Berbasis Kriptografi Asimetris (**RSA-PSS 2048-bit** dan **ECDSA P-256**), Hash **SHA-256**, Enkripsi Kunci Privat **AES-256-GCM + PBKDF2HMAC**, Pembangkit Bilangan Acak Aman Kriptografis (**CSPRNG** `os.urandom`), dan Pembaca/Pembuat **QR-Code**.

---

## 👥 Tim Penyusun / Anggota Kelompok

* 👤 **Fajar Guna Nuralam** — **NPM**: `247006111072`  
  *(Backend & Core Crypto Module — ECDSA/RSA, CSPRNG, PBKDF2)*
* 👤 **Yusup** — **NPM**: `247006111027`  
  *(PDF Stamping Engine, Metadata Embedder & QR Code Generator)*
* 👤 **Bisma Alfareza Pangestu** — **NPM**: `247006111204`  
  *(Verification Engine, Tamper Testing, Benchmark & Unit Tests)*

---

## 📖 Deskripsi Proyek

SignKrip dirancang untuk menjamin 3 pilar utama keamanan dokumen digital: **Otentisitas** (*authenticity*), **Integritas** (*integrity*), dan **Nir-penyangkalan** (*non-repudiation*). Aplikasi ini dibangun menggunakan **Python Flask** sebagai backend server web, pustaka `cryptography` standar industri untuk operasi kriptografi tingkat tinggi, serta frontend Vanilla JS & CSS yang responsif.

### 🛡️ Fitur Keamanan & Arsitektur Utama:
1. **Pembangkitan Pasangan Kunci Asimetris**: Mendukung skema **RSA-PSS 2048-bit** (MGF1 SHA-256) dan **ECDSA P-256** (`secp256r1`).
2. **Enkripsi Kunci Privat (Zero Hardcode Secrets)**: Kunci privat dienkripsi dengan **AES-256-GCM** dan derivasi kunci **PBKDF2HMAC** (SHA-256, 100.000 iterasi). Kunci privat tidak pernah ditulis polos di kode sumber maupun disimpan mentah di server.
3. **Pengacak Kriptografis Aman (CSPRNG)**: Salt (16 byte) dan IV (12 byte) dihasilkan menggunakan `os.urandom()` (CSPRNG).
4. **Hashing & Digital Signature**: Menghitung *digest* **SHA-256** dokumen dan menandatanganinya menggunakan Kunci Privat.
5. **Verifikasi Keaslian & Anti-Tamper**: Memvalidasi tanda tangan terhadap Kunci Publik dan secara tegas menolak dokumen yang telah diubah walau hanya **1 byte** (*tampered*).
6. **QR Code Payload Generator & PDF Stamping**: Menghasilkan gambaran QR Code base64 dan menyisipkan metadata signature langsung ke dalam berkas PDF.
7. **Pengujian & Benchmark 30x**: Fitur otomatis menguji performa penandatanganan & verifikasi 30 iterasi serta pengujian keamanan (Uji Tamper 1-byte, Uji Kunci Salah, dan Uji Pemalsuan QR-Code).

---

## 📸 Cara Menggunakan Aplikasi Web

### 1. Membuat Pasangan Kunci Baru (Generate Keypair)
1. Buka menu **🔑 Generate Kunci** pada peramban web (`http://localhost:5000`).
2. Pilih algoritma kriptografi yang diinginkan (`ECDSA P-256` atau `RSA-PSS 2048-bit`).
3. Masukkan kata sandi pengunci (misal: `KataSandiAman123!`).
4. Klik **⚡ Generasi Pasangan Kunci**.
5. Simpan / salin **Kunci Publik** (`.pub`) dan simpan **Kunci Privat Terenkripsi** (berformat JSON memuat `salt`, `iv`, dan `ciphertext`).

### 2. Menandatangani Dokumen (Sign Document)
1. Buka menu **✍️ Tanda Tangan Dokumen**.
2. Unggah berkas dokumen yang ingin ditandatangani (PDF, DOCX, TXT, dll.).
3. Isi data Penandatangan (*Nama, Jabatan, Institusi*).
4. Masukkan **Kata Sandi** dan tempelkan data **Kunci Privat Terenkripsi** Anda.
5. Klik **✍️ Tandatangani Dokumen**. 
6. Sistem akan mengunduh berkas PDF yang sudah terstempel QR-Code visual dan tertanam metadata signature (atau berkas `.signkrip` / `.json` untuk dokumen non-PDF).

### 3. Memverifikasi Keaslian Dokumen (Verify Document)
1. Buka menu **🔍 Verifikasi Dokumen**.
2. Unggah berkas dokumen yang telah distempel / ditandatangani (beserta berkas `.signkrip` jika non-PDF).
3. Klik **🔍 Verifikasi Keaslian**.
4. Sistem akan memberikan status:
   * **VALID & OTENTIK ✅**: Jika dokumen asli, hash cocok, dan tanda tangan digital terverifikasi sah.
   * **TIDAK VALID / DITAMPER ❌**: Jika dokumen telah dimodifikasi walau 1 byte, atau menggunakan kunci publik yang salah.

### 4. Menjalankan Benchmark & Uji Keamanan Interaktif
1. Buka menu **⚡ Benchmark & Security Test**.
2. Klik **🚀 Jalankan Benchmark 30x** untuk mengukur kecepatan perbandingan ECDSA vs RSA-PSS.
3. Klik tombol **🧪 Uji Tamper 1-Byte**, **🔑 Uji Kunci Salah**, atau **🔍 Uji Pemalsuan QR** untuk melihat simulasi penolakan sistem terhadap serangan secara langsung di web UI.

---

## 🚀 Cara Instalasi

### 1. Prasyarat
* **Python 3.8+** (Direkomendasikan Python 3.10+)
* **pip** (Python package manager)
* **Git**

### 2. Kloning Repositori GitHub
```bash
git clone https://github.com/fajarguna15/signkrip.git
cd signkrip/signkrip
```

### 3. Instalasi Dependensi
Jalankan perintah berikut di terminal:
```bash
pip install -r requirements.txt
```

---

## 💻 Cara Menjalankan Aplikasi

### Menjalankan Server Flask
Jalankan perintah berikut di terminal:
```bash
python app.py
```
Aplikasi web akan aktif di **http://localhost:5000** atau **http://127.0.0.1:5000**.  
Buka alamat tersebut di peramban web (Google Chrome, Microsoft Edge, atau Mozilla Firefox).

---

## 🧪 Eksekusi Pengujian & Berkas Uji (Unit Test & Excel)

### 1. Menjalankan Automated Unit Test (8 Unit Test Cases)
Untuk memastikan seluruh 8 unit test fungsi inti lolos pengujian 100%:
```bash
python -m unittest test_crypto.py
```
*Output yang diharapkan:*
```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.25s

OK
```

### 2. Berkas Uji Excel & Tabel Grafik Performa (`Berkas_Uji_SignKrip_Lengkap.xlsx`)
Proyek ini dilengkapi dengan berkas uji Excel terstruktur [**`Berkas_Uji_SignKrip_Lengkap.xlsx`**](Berkas_Uji_SignKrip_Lengkap.xlsx) yang memuat:
* **Sheet 1 (Matriks Skenario Uji)**: 14 Test Cases (TC-01 s.d. TC-14) mencakup modul generasi kunci, enkripsi AES-GCM, hashing, stempel QR, verifikasi tamper, hingga unit test.
* **Sheet 2 (Benchmark & Grafik Performa)**:
  * **Tabel 1**: Perbandingan Signing & Verification Time (30x Iterasi) antara ECDSA P-256 vs RSA-PSS 2048-bit.
  * **Tabel 2**: Kecepatan Sistem Memverifikasi Dokumen (ms) untuk berbagai ukuran berkas PDF (100 KB, 500 KB, 1 MB, 5 MB, dan 10 MB).
  * **Grafik Visual Native Excel**: *Bar Chart* (Perbandingan Algoritma) & *Line Chart* (Kecepatan Verifikasi vs Ukuran Berkas).
* **Sheet 3 (Identitas & Lingkungan Uji)**: Data anggota kelompok, NPM, spesifikasi lingkungan Python, Flask, OpenSSL, dan repositori GitHub.

---
