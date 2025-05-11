import datetime
import re
from userAuth.models import CustomUser 
from kalender.models import TahunAkademik, Kategori, Kegiatan 

# Jika Anda menggunakan model User kustom, impor dengan benar.
# Jika menggunakan model User standar Django:
from django.contrib.auth import get_user_model
from django.utils import timezone # Impor timezone

User = get_user_model() # Menggunakan model User yang aktif

# --- Definisi Data Kategori ---
# Pastikan warna (hex code) unik dan ada dalam choices model Kategori Anda
kategori_data = [
    {'nama': 'Pembayaran SPP', 'warna': '#00205b'},          # Biru Tua
    {'nama': 'Jadwal Kuliah & KRS', 'warna': '#00c853'},     # Hijau
    {'nama': 'Registrasi Umum', 'warna': '#32cd32'},         # Hijau Lime
    {'nama': 'Tes & Seleksi Awal', 'warna': '#6b8e23'},      # Hijau Zaitun Gelap
    {'nama': 'Masa Kuliah', 'warna': '#00ff00'},             # Hijau Terang
    {'nama': 'Ujian Semester', 'warna': '#b22222'},          # Merah Bata
    {'nama': 'Evaluasi & Input Nilai', 'warna': '#ff7f50'},  # Koral
    {'nama': 'Periode Khusus', 'warna': '#ffcc00'},          # Kuning (Minggu Tenang, Remidi, Sela)
    {'nama': 'Liburan', 'warna': '#c0c0c0'},                 # Perak
    {'nama': 'Yudisium & Wisuda', 'warna': '#ffd700'},       # Emas
    {'nama': 'Rapat & Administrasi', 'warna': '#4682b4'},    # Biru Baja
    {'nama': 'Kegiatan Tambahan (TOEP/EIC)', 'warna': '#9932cc'}, # Ungu Gelap
]

# --- Helper untuk Parsing Tanggal ---
MONTH_MAP = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12
}

def parse_date(date_str):
    """
    Mengurai string tanggal dari kalender menjadi tuple (tgl_mulai, tgl_selesai)
    yang sudah timezone-aware.
    Contoh input: "5 - 24 Agustus 2024", "21 September 2024"
    """
    date_str_lower = date_str.lower()
    # Memisahkan berdasarkan '-', '&', atau ',' dengan spasi opsional di sekitarnya
    parts = re.split(r'\s*-\s*|\s*&\s*|\s*,\s*', date_str_lower)

    start_day_str, start_month_str, start_year_str = "", "", ""
    end_day_str, end_month_str, end_year_str = "", "", ""

    # Mencoba mengurai bagian awal (tanggal mulai)
    first_part_elements = parts[0].strip().split()
    if not first_part_elements: # Handle empty string after split if date_str starts with separator
        raise ValueError(f"Bagian tanggal awal kosong pada string: '{date_str}'")
    
    start_day_str = first_part_elements[0]
    if len(first_part_elements) == 3: # Format "DD Bulan YYYY"
        start_month_str = first_part_elements[1]
        start_year_str = first_part_elements[2]
    elif len(first_part_elements) == 2: # Format "DD Bulan" (tahun diasumsikan dari bagian akhir atau sama)
        start_month_str = first_part_elements[1]
    # else: Hanya hari, bulan dan tahun dari bagian selanjutnya atau error jika tidak lengkap

    if len(parts) > 1: # Ada rentang tanggal
        # Ambil bagian terakhir untuk tanggal selesai, pastikan tidak kosong
        last_part_strip = parts[-1].strip()
        if not last_part_strip:
             raise ValueError(f"Bagian tanggal akhir kosong pada string: '{date_str}'")
        second_part_elements = last_part_strip.split()
        
        end_day_str = second_part_elements[0]
        if len(second_part_elements) == 3: # "DD Bulan YYYY"
            end_month_str = second_part_elements[1]
            end_year_str = second_part_elements[2]
        elif len(second_part_elements) == 2: # "DD Bulan"
            end_month_str = second_part_elements[1]
            # Tahun selesai diisi nanti jika start_year_str ada, atau error jika keduanya tidak ada
        # else: Hanya "DD", bulan dan tahun diisi nanti

        # Mengisi tahun mulai jika kosong dan tahun selesai ada
        if not start_year_str and end_year_str:
            start_year_str = end_year_str
        # Mengisi tahun selesai jika kosong dan tahun mulai ada
        if not end_year_str and start_year_str:
            end_year_str = start_year_str
        
        # Mengisi bulan mulai jika kosong dan bulan selesai ada
        if not start_month_str and end_month_str:
            start_month_str = end_month_str
        # Mengisi bulan selesai jika kosong dan bulan mulai ada
        if not end_month_str and start_month_str:
            end_month_str = start_month_str

    else: # Tanggal tunggal
        end_day_str = start_day_str
        end_month_str = start_month_str
        end_year_str = start_year_str

    # Validasi akhir bahwa semua komponen tanggal terisi
    if not all([start_day_str, start_month_str, start_year_str, end_day_str, end_month_str, end_year_str]):
        raise ValueError(f"Komponen tanggal tidak lengkap setelah parsing: '{date_str}' -> Start({start_day_str}-{start_month_str}-{start_year_str}), End({end_day_str}-{end_month_str}-{end_year_str})")

    try:
        s_day = int(start_day_str)
        s_month = MONTH_MAP[start_month_str]
        s_year = int(start_year_str)
        # Buat datetime naive dulu
        naive_tgl_mulai = datetime.datetime(s_year, s_month, s_day, 0, 0, 0)
        # Jadikan aware menggunakan timezone default Django
        tgl_mulai = timezone.make_aware(naive_tgl_mulai, timezone.get_default_timezone())


        e_day = int(end_day_str)
        e_month = MONTH_MAP[end_month_str]
        e_year = int(end_year_str)
        # Buat datetime naive dulu
        naive_tgl_selesai = datetime.datetime(e_year, e_month, e_day, 23, 59, 59)
        # Jadikan aware menggunakan timezone default Django
        tgl_selesai = timezone.make_aware(naive_tgl_selesai, timezone.get_default_timezone())

    except KeyError as e:
        print(f"Error: Nama bulan tidak dikenal '{e}' dalam string '{date_str}'")
        raise
    except ValueError as e: # Untuk error konversi int() atau jika ada komponen tanggal yg masih kosong
        print(f"Error: Format tanggal tidak valid atau komponen hilang '{e}' dalam string '{date_str}'")
        raise
        
    return tgl_mulai, tgl_selesai

# --- Definisi Data Kegiatan ---
# 'tgl_str' adalah string tanggal mentah yang akan diparsing
# 'deskripsi' bersifat opsional
kegiatan_data = [
    # SEMESTER GASAL (AGUSTUS 2024 - JANUARI 2025)
    {"nama": "Pembayaran SPP", "deskripsi": "Cicilan I", "tgl_str": "5 - 24 Agustus 2024", "semester": "Ganjil", "kategori": "Pembayaran SPP"},
    {"nama": "Pembayaran SPP", "deskripsi": "Cicilan II", "tgl_str": "21 Oktober - 2 November 2024", "semester": "Ganjil", "kategori": "Pembayaran SPP"},
    {"nama": "Jadwal Kuliah", "deskripsi": "Sesi 1", "tgl_str": "8 - 10 Agustus 2024", "semester": "Ganjil", "kategori": "Jadwal Kuliah & KRS"},
    {"nama": "Jadwal Kuliah", "deskripsi": "Sesi 2", "tgl_str": "26 - 28 Agustus 2024", "semester": "Ganjil", "kategori": "Jadwal Kuliah & KRS"},
    {"nama": "Registrasi dan Konsultasi KRS KRS online", "deskripsi": "", "tgl_str": "12 - 24 Agustus 2024", "semester": "Ganjil", "kategori": "Jadwal Kuliah & KRS"},
    {"nama": "Registrasi Selang/Cuti Kuliah", "deskripsi": "", "tgl_str": "19 Agustus - 26 Oktober 2024", "semester": "Ganjil", "kategori": "Registrasi Umum"},
    {"nama": "Tes Baca-Tulis Al-Qur'an dan Praktik Shalat Mahasiswa Baru", "deskripsi": "", "tgl_str": "30 - 31 Agustus 2024", "semester": "Ganjil", "kategori": "Tes & Seleksi Awal"},
    {"nama": "MASA KULIAH I", "deskripsi": "", "tgl_str": "2 September - 26 Oktober 2024", "semester": "Ganjil", "kategori": "Masa Kuliah"},
    {"nama": "Revisi KRS", "deskripsi": "", "tgl_str": "16 - 18 September 2024", "semester": "Ganjil", "kategori": "Jadwal Kuliah & KRS"},
    {"nama": "Ujian Tengah Semester", "deskripsi": "", "tgl_str": "28 Oktober - 9 November 2024", "semester": "Ganjil", "kategori": "Ujian Semester"},
    {"nama": "MASA KULIAH II", "deskripsi": "", "tgl_str": "11 November 2024 - 4 Januari 2025", "semester": "Ganjil", "kategori": "Masa Kuliah"},
    {"nama": "Evaluasi PBM oleh Mahasiswa & Input data peserta ujian akhir", "deskripsi": "minimal 75 % kehadiran", "tgl_str": "23 - 28 Desember 2024", "semester": "Ganjil", "kategori": "Evaluasi & Input Nilai"},
    {"nama": "Minggu Tenang, Pencetakan Kartu Ujian", "deskripsi": "", "tgl_str": "30 Desember 2024 - 4 Januari 2025", "semester": "Ganjil", "kategori": "Periode Khusus"},
    {"nama": "Ujian Akhir Semester", "deskripsi": "", "tgl_str": "6 - 18 Januari 2025", "semester": "Ganjil", "kategori": "Ujian Semester"},
    {"nama": "Input Nilai dan Yudisium Semester", "deskripsi": "", "tgl_str": "8 - 23 Januari 2025", "semester": "Ganjil", "kategori": "Evaluasi & Input Nilai"},
    {"nama": "Liburan Semester", "deskripsi": "", "tgl_str": "24 - 25 Januari 2025", "semester": "Ganjil", "kategori": "Liburan"},
    {"nama": "Semester Remidi dan PPK", "deskripsi": "", "tgl_str": "26 Januari - 8 Februari 2025", "semester": "Ganjil", "kategori": "Periode Khusus"}, # Asumsi mulai setelah libur, berakhir maks 8 Feb
    {"nama": "Input Nilai Semester Remidi, PPK dan Sela", "deskripsi": "", "tgl_str": "14 - 15 Februari 2025", "semester": "Ganjil", "kategori": "Evaluasi & Input Nilai"},
    {"nama": "Yudisium SKL Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode I", "tgl_str": "16 - 17 Agustus 2024", "semester": "Ganjil", "kategori": "Yudisium & Wisuda"},
    {"nama": "Yudisium SKL Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode II", "tgl_str": "21 - 23 November 2024", "semester": "Ganjil", "kategori": "Yudisium & Wisuda"},
    {"nama": "Wisuda", "deskripsi": "Periode I", "tgl_str": "21 September 2024", "semester": "Ganjil", "kategori": "Yudisium & Wisuda"},
    {"nama": "Wisuda", "deskripsi": "Periode II", "tgl_str": "21 Desember 2024", "semester": "Ganjil", "kategori": "Yudisium & Wisuda"},
    {"nama": "RAPAT KERJA PIMPINAN", "deskripsi": "", "tgl_str": "22 - 24 Agustus 2024", "semester": "Ganjil", "kategori": "Rapat & Administrasi"},
    {"nama": "TOEP REMIDI", "deskripsi": "", "tgl_str": "20 - 22 Januari 2025", "semester": "Ganjil", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"nama": "EIC Batch III Mahasiswa Angkatan 2023/2024", "deskripsi": "", "tgl_str": "5 - 30 Agustus 2024", "semester": "Ganjil", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"nama": "PreTest TOEP Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "29 - 31 Agustus 2024", "semester": "Ganjil", "kategori": "Kegiatan Tambahan (TOEP/EIC)"}, # Diubah dari "29, 30, 31"

    # SEMESTER GENAP (FEBRUARI - JULI 2025)
    {"nama": "Pembayaran SPP", "deskripsi": "Cicilan III", "tgl_str": "27 Januari - 5 Februari 2025", "semester": "Genap", "kategori": "Pembayaran SPP"},
    {"nama": "Pembayaran SPP", "deskripsi": "Cicilan IV", "tgl_str": "28 April - 10 Mei 2025", "semester": "Genap", "kategori": "Pembayaran SPP"},
    {"nama": "Jadwal Kuliah", "deskripsi": "Sesi 1", "tgl_str": "27 - 30 Januari 2025", "semester": "Genap", "kategori": "Jadwal Kuliah & KRS"},
    {"nama": "Jadwal Kuliah", "deskripsi": "Sesi 2", "tgl_str": "6 - 8 Februari 2025", "semester": "Genap", "kategori": "Jadwal Kuliah & KRS"},
    {"nama": "Registrasi dan Konsultasi KRS KRS online", "deskripsi": "", "tgl_str": "28 Januari - 6 Februari 2025", "semester": "Genap", "kategori": "Jadwal Kuliah & KRS"},
    {"nama": "Registrasi Selang/Cuti Kuliah", "deskripsi": "", "tgl_str": "6 Februari - 12 April 2025", "semester": "Genap", "kategori": "Registrasi Umum"},
    {"nama": "MASA KULIAH I", "deskripsi": "", "tgl_str": "10 Februari - 12 April 2025", "semester": "Genap", "kategori": "Masa Kuliah"},
    {"nama": "Revisi KRS", "deskripsi": "", "tgl_str": "24 - 26 Februari 2025", "semester": "Genap", "kategori": "Jadwal Kuliah & KRS"},
    {"nama": "Ujian Tengah Semester", "deskripsi": "", "tgl_str": "14 - 26 April 2025", "semester": "Genap", "kategori": "Ujian Semester"},
    {"nama": "MASA KULIAH II", "deskripsi": "", "tgl_str": "28 April - 21 Juni 2025", "semester": "Genap", "kategori": "Masa Kuliah"},
    {"nama": "Evaluasi PBM oleh Mahasiswa & Input data peserta ujian akhir", "deskripsi": "minimal 75 % kehadiran", "tgl_str": "9 - 14 Juni 2025", "semester": "Genap", "kategori": "Evaluasi & Input Nilai"},
    {"nama": "Minggu Tenang, Pencetakan Kartu Ujian", "deskripsi": "", "tgl_str": "18 - 21 Juni 2025", "semester": "Genap", "kategori": "Periode Khusus"},
    {"nama": "Ujian Akhir Semester", "deskripsi": "", "tgl_str": "23 Juni - 5 Juli 2025", "semester": "Genap", "kategori": "Ujian Semester"},
    {"nama": "Input Nilai dan Yudisium Semester", "deskripsi": "", "tgl_str": "27 Juni - 10 Juli 2025", "semester": "Genap", "kategori": "Evaluasi & Input Nilai"},
    {"nama": "Liburan Semester", "deskripsi": "", "tgl_str": "11 - 12 Juli 2025", "semester": "Genap", "kategori": "Liburan"},
    {"nama": "Semester Sela", "deskripsi": "", "tgl_str": "7 Juli - 30 Agustus 2025", "semester": "Genap", "kategori": "Periode Khusus"},
    {"nama": "Input Nilai Semester Remidi, PPK dan Sela", "deskripsi": "", "tgl_str": "29 - 30 Agustus 2025", "semester": "Genap", "kategori": "Evaluasi & Input Nilai"},
    {"nama": "Yudisium SKL Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode III", "tgl_str": "21 - 22 Februari 2025", "semester": "Genap", "kategori": "Yudisium & Wisuda"},
    {"nama": "Yudisium SKL Batas Akhir Penyerahan Berkas Wisuda", "deskripsi": "Periode IV", "tgl_str": "14 - 15 Mei 2025", "semester": "Genap", "kategori": "Yudisium & Wisuda"},
    {"nama": "Wisuda", "deskripsi": "Periode III", "tgl_str": "22 Maret 2025", "semester": "Genap", "kategori": "Yudisium & Wisuda"},
    {"nama": "Wisuda", "deskripsi": "Periode IV", "tgl_str": "14 Juni 2025", "semester": "Genap", "kategori": "Yudisium & Wisuda"},
    {"nama": "RAPAT KERJA PIMPINAN", "deskripsi": "", "tgl_str": "21 - 23 Agustus 2025", "semester": "Genap", "kategori": "Rapat & Administrasi"},
    {"nama": "TOEP REGULER", "deskripsi": "", "tgl_str": "7 - 9 Juli 2025", "semester": "Genap", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"nama": "EIC Batch I Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "27 Januari - 8 Februari 2025", "semester": "Genap", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"nama": "EIC Batch IIA Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "7 - 12 April 2025", "semester": "Genap", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"nama": "EIC Batch IIB Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "16 - 21 Juni 2025", "semester": "Genap", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
    {"nama": "EIC Batch III Mahasiswa Angkatan 2024/2025", "deskripsi": "", "tgl_str": "14 Juli - 9 Agustus 2025", "semester": "Genap", "kategori": "Kegiatan Tambahan (TOEP/EIC)"},
]

# --- Fungsi Populate Data (sesuai permintaan Anda, dengan penyesuaian) ---
def populate_data():
    # Ambil user pertama. Sesuaikan jika Anda menggunakan model User kustom.
    user = CustomUser.objects.first()

    if not user:
        print("Tidak ada user di database. Buat user terlebih dahulu.")
        return

    # Buat Tahun Akademik
    tahun_akademik, created = TahunAkademik.objects.get_or_create(tahun_akademik="2024/2025")
    if created:
        print(f"Tahun Akademik '{tahun_akademik}' berhasil dibuat.")
    else:
        print(f"Tahun Akademik '{tahun_akademik}' sudah ada.")

    # Buat Kategori
    kategori_dict = {}
    for kat_item in kategori_data: # Mengganti nama variabel loop agar tidak konflik
        kategori_obj, created = Kategori.objects.get_or_create(
            nama=kat_item["nama"],
            defaults={'warna': kat_item["warna"]} 
        )
        if not created and kategori_obj.warna != kat_item["warna"]:
             print(f"Peringatan: Kategori '{kat_item['nama']}' sudah ada dengan warna '{kategori_obj.warna}', "
                   f"diminta '{kat_item['warna']}'. Tidak diubah karena warna unik.")
        elif created:
             print(f"Kategori '{kat_item['nama']}' berhasil dibuat dengan warna '{kat_item['warna']}'.")
        else:
             print(f"Kategori '{kat_item['nama']}' (warna: {kat_item['warna']}) sudah ada.")
        kategori_dict[kat_item["nama"]] = kategori_obj


    # Buat Kegiatan
    for keg_item in kegiatan_data: # Mengganti nama variabel loop
        try:
            tgl_mulai, tgl_selesai = parse_date(keg_item["tgl_str"])
        except Exception as e:
            print(f"Gagal memproses tanggal untuk kegiatan '{keg_item['nama']}': {e}. Kegiatan dilewati.")
            continue
        
        kegiatan_obj, created = Kegiatan.objects.get_or_create(
            tahun_akademik=tahun_akademik,
            semester=keg_item["semester"],
            nama=keg_item["nama"],
            tgl_mulai=tgl_mulai, 
            defaults={
                'deskripsi': keg_item.get("deskripsi", ""), 
                'tgl_selesai': tgl_selesai,
                'user_fk': user,
                'kategori_fk': kategori_dict[keg_item["kategori"]]
            }
        )
        if created:
            print(f"Kegiatan '{keg_item['nama']}' ({keg_item['semester']}) berhasil ditambahkan.")
        else:
            print(f"Kegiatan '{keg_item['nama']}' ({keg_item['semester']} mulai {tgl_mulai.date()}) sudah ada.")

    print("\nProses populate data selesai.")

# --- Untuk menjalankan di Django Shell ---
# Pastikan semua impor model di atas sudah benar
# Salin semua kode di atas ini ke Django shell, lalu jalankan:
# populate_data()
# ---------------------------------------

# Contoh pemanggilan di shell setelah semua kode di atas di-paste:
# >>> populate_data()
