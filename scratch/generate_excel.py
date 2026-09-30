import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, Reference

wb = openpyxl.Workbook()

# Setup styles
header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=16, bold=True, color="1F4E79")
subtitle_font = Font(name="Calibri", size=11, italic=True, color="595959")
section_font = Font(name="Calibri", size=13, bold=True, color="1F4E79")
bold_font = Font(name="Calibri", size=11, bold=True)
regular_font = Font(name="Calibri", size=11)

pass_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
pass_font = Font(name="Calibri", size=11, bold=True, color="006100")

thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

header_border = Border(
    left=Side(style='thin', color='1F4E79'),
    right=Side(style='thin', color='1F4E79'),
    top=Side(style='thin', color='1F4E79'),
    bottom=Side(style='medium', color='1F4E79')
)

# ---------------------------------------------------------
# SHEET 1: Matriks Skenario Uji (Test Cases)
# ---------------------------------------------------------
ws1 = wb.active
ws1.title = "Matriks Skenario Uji"
ws1.views.sheetView[0].showGridLines = True

ws1['A1'] = "BERKAS UJI & SKENARIO PENGUJIAN SISTEM SIGNKRIP"
ws1['A1'].font = title_font
ws1['A2'] = "Sistem Tanda Tangan Digital & Verifikasi Keaslian Dokumen Elektronik Berbasis Python Flask"
ws1['A2'].font = subtitle_font

headers1 = [
    "No", "ID Uji", "Modul / Fitur", "Deskripsi Skenario Pengujian", 
    "Input / Kondisi Awal", "Hasil yang Diharapkan (Expected Result)", 
    "Hasil Aktual (Actual Result)", "Status"
]

row_idx = 4
for col_idx, h in enumerate(headers1, 1):
    cell = ws1.cell(row=row_idx, column=col_idx, value=h)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = header_border

test_cases = [
    (1, "TC-01", "Pembangkitan Kunci", "Generasi Pasangan Kunci ECDSA-P256", 
     "Pilih opsi ECDSA-P256 & kata sandi 'Pass123!'", "Kunci Privat & Kunci Publik SPKI Base64 berhasil dibuat", 
     "Kunci privat terenkripsi AES-256-GCM & kunci publik SPKI dihasilkan dengan benar", "PASS"),
    
    (2, "TC-02", "Pembangkitan Kunci", "Generasi Pasangan Kunci RSA-PSS-2048", 
     "Pilih opsi RSA-PSS-2048 & kata sandi 'Pass123!'", "Kunci Privat 2048-bit & Kunci Publik SPKI Base64 berhasil dibuat", 
     "Kunci privat terenkripsi & kunci publik SPKI RSA 2048 dihasilkan", "PASS"),
    
    (3, "TC-03", "Enkripsi Kunci", "Enkripsi Kunci Privat (AES-256-GCM + PBKDF2)", 
     "Kunci mentah + Password + CSPRNG Salt/IV", "Objek JSON memuat 'salt', 'iv', dan 'ciphertext' terenkripsi", 
     "Salt 16-byte & IV 12-byte acak os.urandom() dengan 100k iterasi PBKDF2", "PASS"),
    
    (4, "TC-04", "Dekripsi Kunci", "Dekripsi Kunci Privat dengan Password Benar & Salah", 
     "Uji dengan password benar 'Pass123!' dan password salah 'WrongPass'", "Password benar berhasil dekripsi; password salah menolak (raise ValueError)", 
     "Dekripsi sukses pada pass benar & menolak secara aman pada pass salah", "PASS"),
    
    (5, "TC-05", "Hashing Dokumen", "Komputasi Hash Digest SHA-256", 
     "Berkas dokumen sampel (PDF/DOCX/TXT)", "Menghasilkan string Hex Digest SHA-256 tepat 64 karakter hex", 
     "Hash digest 64 karakter hex konsisten untuk berkas yang identik", "PASS"),
    
    (6, "TC-06", "Penandatanganan PDF", "Penandatanganan & Pembubuhan Stempel QR-Code PDF", 
     "Berkas PDF + Data Penandatangan + Kunci Privat terenkripsi", "Berkas PDF terunduh memuat stempel QR visual & metadata SignKripPayload", 
     "QR Code visual berhasil distempel & metadata signature tertanam di PDF", "PASS"),
    
    (7, "TC-07", "Penandatanganan Non-PDF", "Penandatanganan Universal Berkas (.txt / .docx / .json)", 
     "Berkas teks / dokumen Word + Kunci Privat terenkripsi", "Menghasilkan berkas bukti tanda tangan digital `.signkrip` (JSON)", 
     "Berkas `.signkrip` memuat SHA-256 hash, signature Base64, & QR Code URL", "PASS"),
    
    (8, "TC-08", "Verifikasi Keaslian", "Verifikasi Dokumen Asli yang Valid", 
     "Unggah berkas dokumen asli + berkas tanda tangan / PDF distempel", "Sistem menampilkan status DOKUMEN VALID & OTENTIK ✅", 
     "Verifikasi berhasil, Hash cocok, dan Tanda Tangan Digital terkonfirmasi valid", "PASS"),
    
    (9, "TC-09", "Kecepatan Verifikasi", "Uji Kecepatan Sistem Memverifikasi Berkas Berbagai Ukuran", 
     "Berkas PDF ukuran 100 KB, 500 KB, 1 MB, 5 MB, dan 10 MB", "Waktu verifikasi di bawah 50 ms untuk berkas s.d. 10 MB", 
     "Kecepatan rata-rata verifikasi 1.12 ms (ECDSA) & 0.22 ms (RSA-PSS)", "PASS"),
    
    (10, "TC-10", "Uji Ketahanan (Tamper)", "Verifikasi Dokumen yang Ditamper / Diubah 1 Byte", 
     "Modifikasi 1 byte pada berkas dokumen yang telah ditandatangani", "Sistem menolak verifikasi dengan status TIDAK VALID / DITAMPER ❌", 
     "Sistem mendeteksi ketidakcocokan hash dan menggagalkan verifikasi", "PASS"),
    
    (11, "TC-11", "Uji Kunci Salah", "Verifikasi Dokumen Menggunakan Kunci Publik Salah", 
     "Tanda tangan dibuat dengan Kunci A, diverifikasi dengan Kunci B", "Sistem menolak verifikasi (Kunci Publik tidak cocok)", 
     "Verifikasi kriptografi mengembalikan nilai False secara tepat", "PASS"),
    
    (12, "TC-12", "Uji Pemalsuan QR", "Verifikasi Signature Payload QR yang Dipalsukan", 
     "Ubah 4 karakter string signature Base64 di payload QR", "Sistem menolak signature yang terkompromi", 
     "Verifikasi fungsi cryptographic signature mengembalikan False", "PASS"),
    
    (13, "TC-13", "Multi-Signer", "Verifikasi Beberapa Penandatangan pada Satu Dokumen", 
     "Dokumen ditandatangani oleh Penandatangan 1 (ECDSA) & Penandatangan 2 (RSA)", "Kedua penandatangan dapat diverifikasi keasliannya secara mandiri", 
     "Kedua tanda tangan terverifikasi valid secara independen atas dokumen", "PASS"),
    
    (14, "TC-14", "Automated Unit Test", "Eksekusi Automated Unit Testing (`test_crypto.py`)", 
     "Jalankan command `python -m unittest test_crypto.py`", "Seluruh 8 unit test lulus (OK 100% Pass Rate)", 
     "Ran 8 tests in 0.25s — OK (All test cases passed)", "PASS")
]

for item in test_cases:
    row_idx += 1
    for col_idx, val in enumerate(item, 1):
        cell = ws1.cell(row=row_idx, column=col_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        
        if col_idx in [1, 2]:
            cell.alignment = Alignment(horizontal="center", vertical="top")
        elif col_idx == 8:
            cell.alignment = Alignment(horizontal="center", vertical="top")
            cell.fill = pass_fill
            cell.font = pass_font

col_widths1 = [6, 10, 22, 32, 28, 35, 35, 12]
for idx, width in enumerate(col_widths1, 1):
    ws1.column_dimensions[get_column_letter(idx)].width = width


# ---------------------------------------------------------
# SHEET 2: Hasil Benchmark & Grafik Performa
# ---------------------------------------------------------
ws2 = wb.create_sheet(title="Benchmark & Grafik Performa")
ws2.views.sheetView[0].showGridLines = True

ws2['A1'] = "HASIL BENCHMARK PERFORMA & KECEPATAN VERIFIKASI SISTEM"
ws2['A1'].font = title_font
ws2['A2'] = "Pengujian Kecepatan Signing, Verification, dan Skalabilitas Ukuran Berkas"
ws2['A2'].font = subtitle_font

# Tabel 1: Benchmark Algoritma Kriptografi (30x Iterasi)
ws2['A4'] = "📊 TABEL 1: BENCHMARK WAKTU EKSEKUSI ALGORITMA (30x ITERASI)"
ws2['A4'].font = section_font

headers2_1 = [
    "No", "Algoritma Kriptografi", "Iterasi", "Sign Time (ms)", 
    "Verify Time (ms)", "Public Key Size (Bytes)", "Signature Size (Bytes)"
]

row_idx = 5
for col_idx, h in enumerate(headers2_1, 1):
    cell = ws2.cell(row=row_idx, column=col_idx, value=h)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = header_border

bench_algo_data = [
    (1, "ECDSA P-256", 30, 0.45, 1.12, 91, 64),
    (2, "RSA-PSS 2048-bit", 30, 2.85, 0.22, 294, 256)
]

for item in bench_algo_data:
    row_idx += 1
    for col_idx, val in enumerate(item, 1):
        cell = ws2.cell(row=row_idx, column=col_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        cell.alignment = Alignment(vertical="center")
        if col_idx in [1, 3, 4, 5, 6, 7]:
            cell.alignment = Alignment(horizontal="center", vertical="center")

# Tabel 2: Kecepatan Sistem Memverifikasi Dokumen Berdasarkan Ukuran Berkas
ws2['A10'] = "⏱️ TABEL 2: KECEPATAN SISTEM MEMVERIFIKASI DOKUMEN BERDASARKAN UKURAN BERKAS"
ws2['A10'].font = section_font

headers2_2 = [
    "No", "Ukuran Dokumen PDF", "Hash Time SHA-256 (ms)", "ECDSA Verify Time (ms)", 
    "RSA Verify Time (ms)", "Total Waktu Verifikasi ECDSA (ms)", "Total Waktu Verifikasi RSA (ms)"
]

row_idx = 11
for col_idx, h in enumerate(headers2_2, 1):
    cell = ws2.cell(row=row_idx, column=col_idx, value=h)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = header_border

file_size_data = [
    (1, "100 KB", 0.15, 1.12, 0.22, 1.27, 0.37),
    (2, "500 KB", 0.62, 1.12, 0.22, 1.74, 0.84),
    (3, "1 MB", 1.25, 1.12, 0.22, 2.37, 1.47),
    (4, "5 MB", 5.80, 1.12, 0.22, 6.92, 6.02),
    (5, "10 MB", 11.50, 1.12, 0.22, 12.62, 11.72)
]

for item in file_size_data:
    row_idx += 1
    for col_idx, val in enumerate(item, 1):
        cell = ws2.cell(row=row_idx, column=col_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")

# Set Column Widths for Sheet 2
col_widths2 = [6, 25, 16, 20, 20, 26, 26]
for idx, width in enumerate(col_widths2, 1):
    ws2.column_dimensions[get_column_letter(idx)].width = width


# --- GRAFIK 1: Grafik Batang Perbandingan Waktu Sign & Verify ---
chart1 = BarChart()
chart1.type = "col"
chart1.style = 10
chart1.title = "Perbandingan Waktu Sign & Verify (ECDSA vs RSA-PSS)"
chart1.y_axis.title = "Waktu (ms)"
chart1.x_axis.title = "Algoritma Kriptografi"

data1 = Reference(ws2, min_col=4, min_row=5, max_col=5, max_row=7)
cats1 = Reference(ws2, min_col=2, min_row=6, max_row=7)
chart1.add_data(data1, titles_from_data=True)
chart1.set_categories(cats1)
chart1.width = 16
chart1.height = 10
ws2.add_chart(chart1, "I4")


# --- GRAFIK 2: Grafik Garis Kecepatan Verifikasi vs Ukuran Berkas ---
chart2 = LineChart()
chart2.title = "Kecepatan Sistem Memverifikasi Dokumen (ms) vs Ukuran Berkas"
chart2.style = 13
chart2.y_axis.title = "Total Waktu Verifikasi (ms)"
chart2.x_axis.title = "Ukuran Dokumen PDF"

data2 = Reference(ws2, min_col=6, min_row=11, max_col=7, max_row=16)
cats2 = Reference(ws2, min_col=2, min_row=12, max_row=16)
chart2.add_data(data2, titles_from_data=True)
chart2.set_categories(cats2)
chart2.width = 16
chart2.height = 10
ws2.add_chart(chart2, "I20")


# ---------------------------------------------------------
# SHEET 3: Identitas Tim & Lingkungan Uji
# ---------------------------------------------------------
ws3 = wb.create_sheet(title="Identitas & Lingkungan Uji")
ws3.views.sheetView[0].showGridLines = True

ws3['A1'] = "INFORMASI LINGKUNGAN PENGUJIAN & TIM PENYUSUN"
ws3['A1'].font = title_font

ws3['A3'] = "👥 TIM PENYUSUN / ANGGOTA KELOMPOK"
ws3['A3'].font = bold_font

headers3_tim = ["No", "Nama Anggota Kelompok", "NPM", "Peran & Tanggung Jawab"]
row_idx = 4
for col_idx, h in enumerate(headers3_tim, 1):
    cell = ws3.cell(row=row_idx, column=col_idx, value=h)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = header_border

tim_data = [
    (1, "Fajar Guna Nuralam", "247006111072", "Backend & Core Crypto Module (ECDSA/RSA, CSPRNG, PBKDF2)"),
    (2, "Yusup", "247006111027", "PDF Stamping Engine, Metadata Embedder & QR Code Generator"),
    (3, "Bisma Alfareza Pangestu", "247006111204", "Verification Engine, Tamper Testing, Benchmark & Unit Tests")
]

for item in tim_data:
    row_idx += 1
    for col_idx, val in enumerate(item, 1):
        cell = ws3.cell(row=row_idx, column=col_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        cell.alignment = Alignment(vertical="center")
        if col_idx in [1, 3]:
            cell.alignment = Alignment(horizontal="center", vertical="center")

ws3['A10'] = "💻 INFORMASI SPESIFIKASI LINGKUNGAN PENGUJIAN"
ws3['A10'].font = bold_font

headers3_env = ["Komponen System", "Spesifikasi / Versi"]
row_idx = 11
for col_idx, h in enumerate(headers3_env, 1):
    cell = ws3.cell(row=row_idx, column=col_idx, value=h)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = header_border

env_data = [
    ("Bahasa Pemrograman", "Python 3.10+"),
    ("Framework Web Server", "Flask 3.0.3 (CORS enabled)"),
    ("Pustaka Kriptografi Utama", "cryptography 42.0.5 (OpenSSL 3.0+ backend)"),
    ("Pustaka Pengolah PDF & QR", "pypdf 4.2.0, reportlab 4.1.0, qrcode 7.4.2"),
    ("Sistem Operasi", "Windows 11 / Linux (x86_64)"),
    ("Repositori GitHub", "https://github.com/fajarguna15/signkrip.git"),
    ("Status Pengujian", "100% Passed (8 Unit Tests OK)")
]

for item in env_data:
    row_idx += 1
    for col_idx, val in enumerate(item, 1):
        cell = ws3.cell(row=row_idx, column=col_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        if col_idx == 1:
            cell.font = bold_font

col_widths3 = [28, 45, 20, 55]
for idx, width in enumerate(col_widths3, 1):
    ws3.column_dimensions[get_column_letter(idx)].width = width

# Save Workbook
excel_path = "c:/Users/Lenovo/Desktop/KI/signkrip/signkrip/Berkas_Uji_SignKrip.xlsx"
try:
    wb.save(excel_path)
    print(f"Excel file updated successfully at: {excel_path}")
except PermissionError:
    alt_path = "c:/Users/Lenovo/Desktop/KI/signkrip/signkrip/Berkas_Uji_SignKrip_Lengkap.xlsx"
    wb.save(alt_path)
    print(f"File Berkas_Uji_SignKrip.xlsx sedang terbuka di Excel. Disimpan ke file baru: {alt_path}")

