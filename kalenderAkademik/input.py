from kalender.models import Kategori

kategori_list = [
    "Pembayaran SPP",
    "Jadwal Kuliah",
    "Registrasi KRS",
    "Cuti Kuliah",
    "Tes Mahasiswa Baru",
    "Perkuliahan",
    "Revisi KRS",
    "Ujian Tengah Semester",
    "Evaluasi PBM",
    "Minggu Tenang",
    "Ujian Akhir Semester",
    "Input Nilai",
    "Liburan Semester",
    "Semester Remidi dan PPK",
    "Semester Sela",
    "Yudisium SKL",
    "Wisuda",
    "Rapat Kerja Pimpinan",
    "TOEP REGULER",
    "TOEP REMIDI",
    "EIC Batch",
    "PreTest TOEP"
]

for nama in kategori_list:
    Kategori.objects.get_or_create(nama=nama)
print("Kategori berhasil ditambahkan.")
