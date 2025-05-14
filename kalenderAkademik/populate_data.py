import datetime
import re
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import IntegrityError

try:
    from userAuth.models import CustomUser
    User = CustomUser
except ImportError:
    User = get_user_model()

from kalender.models import TahunAkademik, Kategori, Kegiatan, COLOR_CHOICES # Pastikan COLOR_CHOICES diimpor jika belum

# --- Definisi Data Kategori (Sama seperti sebelumnya) ---
kategori_data_master = [
    {'nama': 'Pengumuman', 'warna': '#ffcc00'},
    {'nama': 'Pembayaran SPP', 'warna': '#00205b'},
    {'nama': 'Jadwal Kuliah & KRS', 'warna': '#00c853'},
    {'nama': 'Registrasi Umum', 'warna': '#32cd32'},
    {'nama': 'Tes & Seleksi Awal', 'warna': '#6b8e23'},
    {'nama': 'Masa Kuliah', 'warna': '#00ff00'},
    {'nama': 'Ujian Semester', 'warna': '#ff8c00'}, # Oranye Tua
    {'nama': 'Evaluasi & Input Nilai', 'warna': '#ff7f50'},
    {'nama': 'Periode Khusus', 'warna': '#daa520'}, # Emas Batangan
    {'nama': 'Liburan', 'warna': '#c0c0c0'},
    {'nama': 'Yudisium & Wisuda', 'warna': '#ffd700'},
    {'nama': 'Rapat & Administrasi', 'warna': '#4682b4'},
    {'nama': 'Kegiatan Tambahan (TOEP/EIC)', 'warna': '#9932cc'},
]

# Validasi warna master
valid_hex_colors = [choice[0] for choice in COLOR_CHOICES]
for kat in kategori_data_master:
    if kat['warna'] not in valid_hex_colors:
        print(f"PERINGATAN PENTING: Warna '{kat['warna']}' untuk master kategori '{kat['nama']}' TIDAK ADA dalam COLOR_CHOICES. Harap perbaiki.")


# --- Helper untuk Parsing Tanggal (Sama seperti sebelumnya) ---
MONTH_MAP = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12
}

def parse_date(date_str, default_year_ganjil=None, default_year_genap=None, semester=None):
    date_str_lower = date_str.lower()
    parts = re.split(r'\s*-\s*|\s*&\s*|\s*,\s*', date_str_lower)

    start_day_str, start_month_str, start_year_str = "", "", ""
    end_day_str, end_month_str, end_year_str = "", "", ""

    first_part_elements = parts[0].strip().split()
    if not first_part_elements:
        raise ValueError(f"Bagian tanggal awal kosong pada string: '{date_str}'")

    start_day_str = first_part_elements[0]
    if len(first_part_elements) >= 2: # Bisa "DD Bulan" atau "DD Bulan Tahun"
        start_month_str = first_part_elements[1]
        if len(first_part_elements) == 3:
            start_year_str = first_part_elements[2]

    if len(parts) > 1:
        last_part_strip = parts[-1].strip()
        if not last_part_strip: # Jika formatnya "DD Bulan - "
            if len(first_part_elements) == 3: # Ambil bulan dan tahun dari bagian pertama jika lengkap
                end_day_str = start_day_str # Placeholder, mungkin ini tanggal tunggal yang salah format
                end_month_str = start_month_str
                end_year_str = start_year_str
            else:
                raise ValueError(f"Bagian tanggal akhir kosong dan awal tidak lengkap pada string: '{date_str}'")
        else:
            second_part_elements = last_part_strip.split()
            end_day_str = second_part_elements[0]
            if len(second_part_elements) >= 2: # Bisa "DD Bulan" atau "DD Bulan Tahun"
                end_month_str = second_part_elements[1]
                if len(second_part_elements) == 3:
                    end_year_str = second_part_elements[2]
    else: # Tanggal tunggal
        end_day_str = start_day_str
        end_month_str = start_month_str
        end_year_str = start_year_str

    # Logic untuk mengisi tahun default jika tidak ada
    current_default_year = default_year_ganjil if semester == "Ganjil" else default_year_genap
    if not start_year_str and current_default_year:
        start_year_str = str(current_default_year)
    if not end_year_str and current_default_year:
        end_year_str = str(current_default_year)
    
    # Jika salah satu tahun ada, samakan dengan yang lain jika kosong
    if start_year_str and not end_year_str: end_year_str = start_year_str
    if end_year_str and not start_year_str: start_year_str = end_year_str

    # Jika salah satu bulan ada, samakan dengan yang lain jika kosong (untuk format "DD - DD Bulan Tahun")
    if start_month_str and not end_month_str: end_month_str = start_month_str
    if end_month_str and not start_month_str: start_month_str = end_month_str
    
    # Jika bulan masih kosong dan semester serta tahun default ada, coba infer
    # Ini mungkin tidak diperlukan jika data input selalu lengkap bulannya
    if not start_month_str and semester and default_year_ganjil: # asumsi darurat
        start_month_str = "agustus" if semester == "Ganjil" else "februari"
    if not end_month_str and semester and default_year_ganjil:
        end_month_str = start_month_str


    if not all([start_day_str, start_month_str, start_year_str, end_day_str, end_month_str, end_year_str]):
        raise ValueError(f"Komponen tanggal tidak lengkap: '{date_str}' -> Start({start_day_str}-{start_month_str}-{start_year_str}), End({end_day_str}-{end_month_str}-{end_year_str})")

    try:
        s_day = int(start_day_str)
        s_month = MONTH_MAP[start_month_str.lower()]
        s_year = int(start_year_str)
        naive_tgl_mulai = datetime.datetime(s_year, s_month, s_day, 0, 0, 0)
        tgl_mulai = timezone.make_aware(naive_tgl_mulai, timezone.get_default_timezone())

        e_day = int(end_day_str)
        e_month = MONTH_MAP[end_month_str.lower()]
        e_year = int(end_year_str)
        naive_tgl_selesai = datetime.datetime(e_year, e_month, e_day, 23, 59, 59)
        tgl_selesai = timezone.make_aware(naive_tgl_selesai, timezone.get_default_timezone())
        
        # Pastikan tgl_selesai tidak lebih awal dari tgl_mulai
        if tgl_selesai < tgl_mulai:
            # Jika hanya hari yang berbeda dan bulan tahun sama, mungkin format "DD - DD Bulan Tahun"
            # Atau jika tahun berbeda dan bulan Januari ke Desember, bisa jadi跨年
            if e_year == s_year and e_month == s_month and e_day < s_day:
                 # Ini bisa jadi error input atau butuh penanganan khusus, untuk sekarang anggap error
                 raise ValueError(f"Tanggal selesai ({tgl_selesai.date()}) lebih awal dari tanggal mulai ({tgl_mulai.date()}) dengan bulan dan tahun yang sama pada string '{date_str_lower}'")
            # Jika tgl selesai tahunnya lebih kecil, itu pasti error kecuali ada logika lintas tahun yang sangat spesifik
            # (misal Desember ke Januari tahun berikutnya, tapi parse_date harusnya sudah handle ini jika tahun benar)
            # Untuk sementara, error jika tgl_selesai < tgl_mulai
            # raise ValueError(f"Tanggal selesai ({tgl_selesai.date()}) lebih awal dari tanggal mulai ({tgl_mulai.date()}) pada string '{date_str_lower}'")
            # Jika ada kasus seperti "13 November 2023 - 13 Januari 2024", ini valid.
            # Cek ulang kondisi error:
            if e_year < s_year:
                 raise ValueError(f"Tahun selesai ({e_year}) lebih awal dari tahun mulai ({s_year}) pada string '{date_str_lower}'")
            if e_year == s_year and e_month < s_month:
                 raise ValueError(f"Bulan selesai ({e_month}) lebih awal dari bulan mulai ({s_month}) di tahun yang sama pada string '{date_str_lower}'")
            if e_year == s_year and e_month == s_month and e_day < s_day:
                 raise ValueError(f"Hari selesai ({e_day}) lebih awal dari hari mulai ({s_day}) di bulan dan tahun yang sama pada string '{date_str_lower}'")


    except KeyError as e:
        print(f"Error: Nama bulan tidak dikenal '{e}' dalam string '{date_str_lower}'")
        raise
    except ValueError as e:
        print(f"Error: Format tanggal tidak valid atau komponen hilang '{e}' dalam string '{date_str_lower}'")
        raise
    return tgl_mulai, tgl_selesai


# --- Definisi Data Kegiatan ---
# 'tahun_akademik_str' ditambahkan untuk identifikasi tahun ajaran
# 'default_year_ganjil' dan 'default_year_genap' untuk membantu parse_date jika tahun tidak ada di string tanggal
all_kegiatan_data = [
    # === TAHUN AKADEMIK 2023/2024 ===
    # --- SEMESTER GANJIL 2023/2024 ---
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Pembayaran SPP", "deskripsi": "Cicilan I", "tgl_str": "7 - 19 Agustus 2023", "kategori": "Pembayaran SPP"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Pembayaran SPP", "deskripsi": "Cicilan II", "tgl_str": "23 Oktober - 4 November 2023", "kategori": "Pembayaran SPP"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Registrasi dan Konsultasi KRS KRS online", "deskripsi": "", "tgl_str": "7 - 19 Agustus 2023", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Registrasi Selang/Cuti Kuliah", "deskripsi": "", "tgl_str": "21 Agustus - 21 Oktober 2023", "kategori": "Registrasi Umum"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Tes Baca-Tulis Al-Qur'an, Praktik Shalat, dan Pretest-TOEP Mahasiswa Baru", "deskripsi": "", "tgl_str": "27 - 29 Agustus 2023", "kategori": "Tes & Seleksi Awal"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "MASA KULIAH I", "deskripsi": "", "tgl_str": "4 September - 28 Oktober 2023", "kategori": "Masa Kuliah"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Revisi KRS", "deskripsi": "", "tgl_str": "18 - 20 September 2023", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Ujian Tengah Semester", "deskripsi": "", "tgl_str": "30 Oktober - 11 November 2023", "kategori": "Ujian Semester"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "MASA KULIAH II", "deskripsi": "", "tgl_str": "13 November 2023 - 13 Januari 2024", "kategori": "Masa Kuliah"}, # Akhir di 2024
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Evaluasi PBM oleh Mahasiswa", "deskripsi": "", "tgl_str": "2 - 6 Januari 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Input data mahasiswa yang berhak mengikuti ujian akhir", "deskripsi": "minimal 75 % kehadiran", "tgl_str": "2 - 6 Januari 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Minggu Tenang, Pencetakan Kartu Ujian", "deskripsi": "", "tgl_str": "8 - 13 Januari 2024", "kategori": "Periode Khusus"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Ujian Akhir Semester", "deskripsi": "", "tgl_str": "15 - 27 Januari 2024", "kategori": "Ujian Semester"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "TOEP Remidi", "deskripsi": "", "tgl_str": "29 Januari - 1 Februari 2024", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Input Nilai dan Yudisium Semester", "deskripsi": "", "tgl_str": "17 Januari - 1 Februari 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Libur Jeda Semester", "deskripsi": "", "tgl_str": "2 - 3 Februari 2024", "kategori": "Liburan"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Semester Sela/Antara, Remidi dan PPK", "deskripsi": "Paling Lambat 17 Februari", "tgl_str": "4 Februari - 17 Februari 2024", "kategori": "Periode Khusus"}, # Asumsi mulai setelah libur
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Input Nilai Semester Pendek", "deskripsi": "", "tgl_str": "13 - 17 Februari 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Yudisium SKL", "deskripsi": "Periode I (Ganjil 23/24)", "tgl_str": "1 Juni - 19 Agustus 2023", "kategori": "Yudisium & Wisuda"}, # Rentang ini aneh untuk Ganjil 23/24, tapi sesuai gambar
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Yudisium SKL", "deskripsi": "Periode II (Ganjil 23/24)", "tgl_str": "2 Oktober - 20 November 2023", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode I (Wisuda Sept 23)", "tgl_str": "22 Agustus 2023", "kategori": "Yudisium & Wisuda"}, # Tanggal tunggal
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode II (Wisuda Des 23)", "tgl_str": "22 November 2023", "kategori": "Yudisium & Wisuda"}, # Tanggal tunggal
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Wisuda", "deskripsi": "Periode I", "tgl_str": "23 September 2023", "kategori": "Yudisium & Wisuda"}, # Tanggal tunggal
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Ganjil", "nama": "Wisuda", "deskripsi": "Periode II", "tgl_str": "23 Desember 2023", "kategori": "Yudisium & Wisuda"}, # Tanggal tunggal

    # --- SEMESTER GENAP 2023/2024 ---
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Pembayaran SPP", "deskripsi": "Cicilan III", "tgl_str": "5 - 17 Februari 2024", "kategori": "Pembayaran SPP"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Pembayaran SPP", "deskripsi": "Cicilan IV", "tgl_str": "6 - 18 Mei 2024", "kategori": "Pembayaran SPP"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Registrasi dan Konsultasi KRS KRS online", "deskripsi": "", "tgl_str": "5 - 17 Februari 2024", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Registrasi Selang/Cuti Kuliah", "deskripsi": "", "tgl_str": "6 Februari - 30 Maret 2024", "kategori": "Registrasi Umum"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "MASA KULIAH I", "deskripsi": "", "tgl_str": "19 Februari - 6 April 2024", "kategori": "Masa Kuliah"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Revisi KRS", "deskripsi": "", "tgl_str": "6 - 8 Maret 2024", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Ujian Tengah Semester", "deskripsi": "", "tgl_str": "22 April - 4 Mei 2024", "kategori": "Ujian Semester"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "MASA KULIAH II", "deskripsi": "", "tgl_str": "6 Mei - 13 Juli 2024", "kategori": "Masa Kuliah"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Evaluasi PBM oleh Mahasiswa", "deskripsi": "", "tgl_str": "24 Juni - 6 Juli 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Input data mahasiswa yang berhak mengikuti ujian akhir", "deskripsi": "minimal 75 % kehadiran", "tgl_str": "24 Juni - 6 Juli 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Minggu Tenang, Pencetakan Kartu Ujian", "deskripsi": "", "tgl_str": "9 - 13 Juli 2024", "kategori": "Periode Khusus"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Ujian Akhir Semester", "deskripsi": "", "tgl_str": "15 - 27 Juli 2024", "kategori": "Ujian Semester"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "TOEP Reguler", "deskripsi": "", "tgl_str": "29 Juli - 1 Agustus 2024", "kategori": "Kegiatan Tambahan (TOEP/EIC)"}, # Disesuaikan 29 Juli
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Input Nilai dan Yudisium Semester", "deskripsi": "", "tgl_str": "14 Juli - 1 Agustus 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Libur Jeda Semester", "deskripsi": "", "tgl_str": "2 - 3 Agustus 2024", "kategori": "Liburan"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Semester Sela/Antara, Remidi dan PPK", "deskripsi": "Paling Lambat 16 Agustus", "tgl_str": "4 Agustus - 16 Agustus 2024", "kategori": "Periode Khusus"}, # Asumsi mulai setelah libur
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Input Nilai Semester Pendek", "deskripsi": "", "tgl_str": "12 - 16 Agustus 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Yudisium SKL", "deskripsi": "Periode III (Genap 23/24)", "tgl_str": "2 Januari - 21 Februari 2024", "kategori": "Yudisium & Wisuda"}, # Rentang aneh, sesuai gambar
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Yudisium SKL", "deskripsi": "Periode IV (Genap 23/24)", "tgl_str": "1 April - 18 Mei 2024", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode III (Wisuda Mar 24)", "tgl_str": "23 Februari 2024", "kategori": "Yudisium & Wisuda"}, # Tanggal tunggal
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode IV (Wisuda Jun 24)", "tgl_str": "21 Mei 2024", "kategori": "Yudisium & Wisuda"}, # Tanggal tunggal
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Wisuda", "deskripsi": "Periode III", "tgl_str": "23 Maret 2024", "kategori": "Yudisium & Wisuda"}, # Tanggal tunggal
    {"tahun_akademik_str": "2023/2024", "default_year_ganjil": 2023, "default_year_genap": 2024, "semester": "Genap", "nama": "Wisuda", "deskripsi": "Periode IV", "tgl_str": "22 Juni 2024", "kategori": "Yudisium & Wisuda"}, # Tanggal tunggal

    # === TAHUN AKADEMIK 2024/2025 === (Data dari permintaan sebelumnya)
    # --- SEMESTER GANJIL 2024/2025 ---
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Pembayaran SPP", "deskripsi": "Cicilan I", "tgl_str": "5 - 24 Agustus 2024", "kategori": "Pembayaran SPP"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Pembayaran SPP", "deskripsi": "Cicilan II", "tgl_str": "21 Oktober - 2 November 2024", "kategori": "Pembayaran SPP"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Jadwal Kuliah", "deskripsi": "Sesi 1", "tgl_str": "8 - 10 Agustus 2024", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Jadwal Kuliah", "deskripsi": "Sesi 2", "tgl_str": "26 - 28 Agustus 2024", "kategori": "Jadwal Kuliah & KRS"},
    # ... (Sisa data 2024/2025 lainnya) ...
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Registrasi dan Konsultasi KRS KRS online", "deskripsi": "", "tgl_str": "12 - 24 Agustus 2024", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Registrasi Selang/Cuti Kuliah", "deskripsi": "", "tgl_str": "19 Agustus - 26 Oktober 2024", "kategori": "Registrasi Umum"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Tes Baca-Tulis Al-Qur'an dan Praktik Shalat Mahasiswa Baru", "deskripsi": "", "tgl_str": "30 - 31 Agustus 2024", "kategori": "Tes & Seleksi Awal"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "MASA KULIAH I", "deskripsi": "", "tgl_str": "2 September - 26 Oktober 2024", "kategori": "Masa Kuliah"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Revisi KRS", "deskripsi": "", "tgl_str": "16 - 18 September 2024", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Ujian Tengah Semester", "deskripsi": "", "tgl_str": "28 Oktober - 9 November 2024", "kategori": "Ujian Semester"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "MASA KULIAH II", "deskripsi": "", "tgl_str": "11 November 2024 - 4 Januari 2025", "kategori": "Masa Kuliah"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Evaluasi PBM oleh Mahasiswa & Input data peserta ujian akhir", "deskripsi": "minimal 75 % kehadiran", "tgl_str": "23 - 28 Desember 2024", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Minggu Tenang, Pencetakan Kartu Ujian", "deskripsi": "", "tgl_str": "30 Desember 2024 - 4 Januari 2025", "kategori": "Periode Khusus"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Ujian Akhir Semester", "deskripsi": "", "tgl_str": "6 - 18 Januari 2025", "kategori": "Ujian Semester"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Input Nilai dan Yudisium Semester", "deskripsi": "", "tgl_str": "8 - 23 Januari 2025", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Liburan Semester", "deskripsi": "", "tgl_str": "24 - 25 Januari 2025", "kategori": "Liburan"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Semester Remidi dan PPK", "deskripsi": "", "tgl_str": "26 Januari - 8 Februari 2025", "kategori": "Periode Khusus"}, 
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Input Nilai Semester Remidi, PPK dan Sela", "deskripsi": "", "tgl_str": "14 - 15 Februari 2025", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Yudisium SKL Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode I", "tgl_str": "16 - 17 Agustus 2024", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Yudisium SKL Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode II", "tgl_str": "21 - 23 November 2024", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Wisuda", "deskripsi": "Periode I", "tgl_str": "21 September 2024", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "Wisuda", "deskripsi": "Periode II", "tgl_str": "21 Desember 2024", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "RAPAT KERJA PIMPINAN", "deskripsi": "", "tgl_str": "22 - 24 Agustus 2024", "kategori": "Rapat & Administrasi"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "TOEP REMIDI", "deskripsi": "", "tgl_str": "20 - 22 Januari 2025", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "EIC Batch III Mahasiswa Angkatan 2023/2024", "deskripsi": "", "tgl_str": "5 - 30 Agustus 2024", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Ganjil", "nama": "PreTest TOEP Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "29 - 31 Agustus 2024", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},

    # --- SEMESTER GENAP 2024/2025 ---
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Pembayaran SPP", "deskripsi": "Cicilan III", "tgl_str": "27 Januari - 5 Februari 2025", "kategori": "Pembayaran SPP"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Pembayaran SPP", "deskripsi": "Cicilan IV", "tgl_str": "28 April - 10 Mei 2025", "kategori": "Pembayaran SPP"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Jadwal Kuliah", "deskripsi": "Sesi 1", "tgl_str": "27 - 30 Januari 2025", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Jadwal Kuliah", "deskripsi": "Sesi 2", "tgl_str": "6 - 8 Februari 2025", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Registrasi dan Konsultasi KRS KRS online", "deskripsi": "", "tgl_str": "28 Januari - 6 Februari 2025", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Registrasi Selang/Cuti Kuliah", "deskripsi": "", "tgl_str": "6 Februari - 12 April 2025", "kategori": "Registrasi Umum"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "MASA KULIAH I", "deskripsi": "", "tgl_str": "10 Februari - 12 April 2025", "kategori": "Masa Kuliah"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Revisi KRS", "deskripsi": "", "tgl_str": "24 - 26 Februari 2025", "kategori": "Jadwal Kuliah & KRS"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Ujian Tengah Semester", "deskripsi": "", "tgl_str": "14 - 26 April 2025", "kategori": "Ujian Semester"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "MASA KULIAH II", "deskripsi": "", "tgl_str": "28 April - 21 Juni 2025", "kategori": "Masa Kuliah"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Evaluasi PBM oleh Mahasiswa & Input data peserta ujian akhir", "deskripsi": "minimal 75 % kehadiran", "tgl_str": "9 - 14 Juni 2025", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Minggu Tenang, Pencetakan Kartu Ujian", "deskripsi": "", "tgl_str": "18 - 21 Juni 2025", "kategori": "Periode Khusus"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Ujian Akhir Semester", "deskripsi": "", "tgl_str": "23 Juni - 5 Juli 2025", "kategori": "Ujian Semester"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Input Nilai dan Yudisium Semester", "deskripsi": "", "tgl_str": "27 Juni - 10 Juli 2025", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Liburan Semester", "deskripsi": "", "tgl_str": "11 - 12 Juli 2025", "kategori": "Liburan"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Semester Sela", "deskripsi": "", "tgl_str": "7 Juli - 30 Agustus 2025", "kategori": "Periode Khusus"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Input Nilai Semester Remidi, PPK dan Sela", "deskripsi": "", "tgl_str": "29 - 30 Agustus 2025", "kategori": "Evaluasi & Input Nilai"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Yudisium SKL Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode III", "tgl_str": "21 - 22 Februari 2025", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Yudisium SKL Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode IV", "tgl_str": "14 - 15 Mei 2025", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Wisuda", "deskripsi": "Periode III", "tgl_str": "22 Maret 2025", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "Wisuda", "deskripsi": "Periode IV", "tgl_str": "14 Juni 2025", "kategori": "Yudisium & Wisuda"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "RAPAT KERJA PIMPINAN", "deskripsi": "", "tgl_str": "21 - 23 Agustus 2025", "kategori": "Rapat & Administrasi"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "TOEP REGULER", "deskripsi": "", "tgl_str": "7 - 9 Juli 2025", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "EIC Batch I Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "27 Januari - 8 Februari 2025", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "EIC Batch IIA Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "7 - 12 April 2025", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "EIC Batch IIB Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "16 - 21 Juni 2025", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"tahun_akademik_str": "2024/2025", "default_year_ganjil": 2024, "default_year_genap": 2025, "semester": "Genap", "nama": "EIC Batch III Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "14 Juli - 9 Agustus 2025", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
]


class Command(BaseCommand):
    help = 'Populates the database with initial and updated calendar data for multiple academic years.'

    def handle(self, *args, **options):
        self.stdout.write("Memulai proses populate data kalender...")

        # Ambil atau buat user
        user = User.objects.first()
        if not user:
            try:
                username = "kalender_admin" # Ubah jika perlu
                email = "kalender_admin@example.com" # Ubah jika perlu
                password = "password123" # GANTI DENGAN PASSWORD YANG AMAN!
                if not User.objects.filter(username=username).exists():
                    user_creation_fields = {
                        'username': username,
                        'password': password,
                    }
                    if 'email' in [f.name for f in User._meta.get_fields() if hasattr(User, 'REQUIRED_FIELDS') and 'email' in User.REQUIRED_FIELDS]:
                         user_creation_fields['email'] = email
                    
                    user = User.objects.create_superuser(**user_creation_fields)
                    self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' berhasil dibuat."))
                else:
                    user = User.objects.get(username=username)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Gagal membuat user default: {e}"))
                self.stderr.write(self.style.ERROR("Pastikan ada setidaknya satu user di database atau sesuaikan logika pembuatan user."))
                return
        
        self.stdout.write(f"Menggunakan user: {user.username}")

        # Buat Kategori (jika belum ada atau update warna)
        kategori_objects = {}
        for kat_item in kategori_data_master:
            try:
                kategori_obj, created = Kategori.objects.get_or_create(
                    nama=kat_item["nama"],
                    defaults={'warna': kat_item["warna"]}
                )
                if created:
                    self.stdout.write(f"Kategori '{kat_item['nama']}' (warna: {kat_item['warna']}) berhasil dibuat.")
                else:
                    if kategori_obj.warna != kat_item["warna"]:
                        self.stdout.write(f"Kategori '{kat_item['nama']}' sudah ada, memperbarui warna dari '{kategori_obj.warna}' ke '{kat_item['warna']}'.")
                        kategori_obj.warna = kat_item["warna"]
                        kategori_obj.save()
                    else:
                        self.stdout.write(f"Kategori '{kat_item['nama']}' (warna: {kat_item['warna']}) sudah ada.")
                kategori_objects[kat_item["nama"]] = kategori_obj
            except IntegrityError as e: # Jika warna sudah dipakai kategori lain (unique=True)
                self.stderr.write(self.style.ERROR(f"Error Integrity saat memproses kategori '{kat_item['nama']}': {e}"))
                self.stderr.write(self.style.ERROR(f"Kemungkinan warna '{kat_item['warna']}' sudah digunakan oleh kategori lain. Pastikan warna unik atau perbaiki data master kategori."))
                # Coba ambil berdasarkan warna jika error karena nama beda tapi warna sama
                existing_kat_with_color = Kategori.objects.filter(warna=kat_item['warna']).first()
                if existing_kat_with_color:
                    self.stderr.write(self.style.WARNING(f"Warna '{kat_item['warna']}' sudah dipakai oleh kategori '{existing_kat_with_color.nama}'. Menggunakan kategori tersebut untuk '{kat_item['nama']}'."))
                    kategori_objects[kat_item["nama"]] = existing_kat_with_color
                else: # Jika tidak bisa diselamatkan, lewati
                    continue

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error saat memproses kategori '{kat_item['nama']}': {e}"))
                continue


        # Buat Kegiatan per Tahun Akademik
        for keg_item in all_kegiatan_data:
            # Dapatkan atau buat Tahun Akademik
            tahun_akademik_obj, ta_created = TahunAkademik.objects.get_or_create(
                tahun_akademik=keg_item["tahun_akademik_str"]
            )
            if ta_created:
                self.stdout.write(f"Tahun Akademik '{tahun_akademik_obj}' berhasil dibuat.")

            try:
                tgl_mulai, tgl_selesai = parse_date(
                    keg_item["tgl_str"],
                    default_year_ganjil=keg_item.get("default_year_ganjil"),
                    default_year_genap=keg_item.get("default_year_genap"),
                    semester=keg_item["semester"]
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Gagal memproses tanggal untuk kegiatan '{keg_item['nama']}' ({keg_item['tahun_akademik_str']}): {e}. Kegiatan dilewati."))
                continue

            if keg_item["kategori"] not in kategori_objects:
                self.stderr.write(self.style.ERROR(f"Kategori '{keg_item['kategori']}' untuk kegiatan '{keg_item['nama']}' tidak ditemukan. Kegiatan dilewati."))
                continue
            
            kegiatan_obj, keg_created = Kegiatan.objects.get_or_create(
                tahun_akademik=tahun_akademik_obj,
                semester=keg_item["semester"],
                nama=keg_item["nama"],
                tgl_mulai=tgl_mulai, # Kunci utama untuk get_or_create selain FK dan semester
                defaults={
                    'deskripsi': keg_item.get("deskripsi", ""),
                    'tgl_selesai': tgl_selesai,
                    'user_fk': user,
                    'kategori_fk': kategori_objects[keg_item["kategori"]]
                }
            )

            if keg_created:
                self.stdout.write(f"Kegiatan '{keg_item['nama']}' ({tahun_akademik_obj.tahun_akademik} - {keg_item['semester']}) berhasil ditambahkan.")
            else:
                # Logika update jika perlu (jika ada field di defaults yang mungkin berubah)
                updated_fields = False
                if kegiatan_obj.deskripsi != keg_item.get("deskripsi", ""):
                    kegiatan_obj.deskripsi = keg_item.get("deskripsi", "")
                    updated_fields = True
                if kegiatan_obj.tgl_selesai != tgl_selesai:
                    kegiatan_obj.tgl_selesai = tgl_selesai
                    updated_fields = True
                if kegiatan_obj.kategori_fk != kategori_objects[keg_item["kategori"]]:
                    kegiatan_obj.kategori_fk = kategori_objects[keg_item["kategori"]]
                    updated_fields = True
                
                if updated_fields:
                    kegiatan_obj.save()
                    self.stdout.write(f"Kegiatan '{keg_item['nama']}' ({tahun_akademik_obj.tahun_akademik} - {keg_item['semester']}) sudah ada dan diperbarui.")
                else:
                    self.stdout.write(f"Kegiatan '{keg_item['nama']}' ({tahun_akademik_obj.tahun_akademik} - {keg_item['semester']}) sudah ada, tidak ada perubahan.")

        self.stdout.write(self.style.SUCCESS("\nProses populate data kalender selesai."))