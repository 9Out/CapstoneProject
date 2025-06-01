// Variabel untuk elemen DOM
const pengumumanListElement = document.getElementById('pengumuman-list');
const kegiatanListElement = document.getElementById('kegiatan-list');

// Variabel untuk konfigurasi API
const eventsApiUrl = '/api/events/';
const userOrmawaApiUrl = '/api/user-ormawa/';
const KATEGORI_NAMA_PENGUMUMAN = "Pengumuman";

// Variabel untuk menyimpan data ormawa pengguna
let userManagedOrmawa = [];

// Fungsi untuk memformat tanggal ke format Indonesia (contoh: 14 Mei 2025)
function formatDateIndonesia(date) {
    if (!date) return '';
    return date.toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

// Fungsi untuk membuat elemen list item
function createListItem(text, isNoDataMessage = false) {
    const li = document.createElement('li');
    li.textContent = text;
    if (isNoDataMessage) {
        li.classList.add('no-data');
    }
    return li;
}

// Fungsi untuk memuat data ormawa pengguna
async function loadUserOrmawa() {
    try {
        const response = await fetch(userOrmawaApiUrl, {
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
            }
        });
        if (!response.ok) {
            throw new Error(`Gagal memuat daftar Ormawa: ${response.status} - ${response.statusText}`);
        }
        const data = await response.json();
        // Simpan ID Ormawa yang diikuti pengguna (anggota, ketua, atau sekretaris)
        userManagedOrmawa = data.ormawa_list.map(ormawa => ormawa.id);
    } catch (err) {
        console.error('Gagal memuat data ormawa:', err);
        userManagedOrmawa = [];
    }
}

// Fungsi utama untuk mengambil dan merender data pengumuman dan kegiatan
async function fetchAndRenderData() {
    try {
        // Muat data ormawa pengguna terlebih dahulu
        await loadUserOrmawa();

        // Muat data kegiatan dari API
        const response = await fetch(eventsApiUrl);
        if (!response.ok) {
            throw new Error(`Gagal mengambil data dari API: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();

        pengumumanListElement.innerHTML = '';
        kegiatanListElement.innerHTML = '';

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const thirtyDaysLater = new Date(today);
        thirtyDaysLater.setDate(today.getDate() + 30);
        thirtyDaysLater.setHours(23, 59, 59, 999);

        let pengumumanDitemukan = false;
        let kegiatanDitemukan = false;

        // Urutkan data berdasarkan start_date
        data.sort((a, b) => new Date(a.start) - new Date(b.start));

        data.forEach(item => {
            // Konversi start_date dan end_date ke objek Date
            const startDate = new Date(item.start);
            startDate.setHours(0, 0, 0, 0);

            let endDate = null;
            if (item.end) {
                endDate = new Date(item.end);
                endDate.setHours(23, 59, 59, 999);
            } else {
                endDate = new Date(startDate);
                endDate.setHours(23, 59, 59, 999);
            }

            // Bagian Pengumuman
            if (item.kategori === KATEGORI_NAMA_PENGUMUMAN) {
                // Hanya tampilkan pengumuman yang belum berakhir
                if (endDate >= today) {
                    // Jika kegiatan bersifat publik, tampilkan ke semua pengguna
                    if (item.is_public) {
                        let displayText = `${item.title}`;
                        if (item.deskripsi) {
                            displayText += ` - ${item.deskripsi}`;
                        }
                        pengumumanListElement.appendChild(createListItem(displayText));
                        pengumumanDitemukan = true;
                    }
                    // Jika kegiatan tidak publik dan terkait ormawa, hanya tampilkan ke anggota ormawa
                    else if (item.ormawa_fk && userManagedOrmawa.includes(item.ormawa_fk)) {
                        let displayText = `${item.title}`;
                        if (item.deskripsi) {
                            displayText += ` - ${item.deskripsi}`;
                        }
                        pengumumanListElement.appendChild(createListItem(displayText));
                        pengumumanDitemukan = true;
                    }
                }
            }
            // Bagian Kegiatan Terdekat
            else {
                let displayText = null;

                // Cek apakah start_date atau end_date dalam rentang 30 hari
                if (startDate >= today && startDate <= thirtyDaysLater) {
                    // Jika start_date belum lewat dan dalam 30 hari ke depan
                    displayText = `Kegiatan ${item.title} dimulai pada ${formatDateIndonesia(startDate)}.`;
                    kegiatanDitemukan = true;
                } else if (startDate < today && endDate >= today && endDate <= thirtyDaysLater) {
                    // Jika start_date sudah lewat tetapi end_date masih dalam 30 hari
                    displayText = `Kegiatan ${item.title} berakhir pada ${formatDateIndonesia(endDate)}.`;
                    kegiatanDitemukan = true;
                }

                if (displayText) {
                    kegiatanListElement.appendChild(createListItem(displayText));
                }
            }
        });

        // Tampilkan pesan jika tidak ada data
        if (!pengumumanDitemukan) {
            pengumumanListElement.appendChild(createListItem("Tidak ada pengumuman terkini.", true));
        }
        if (!kegiatanDitemukan) {
            kegiatanListElement.appendChild(createListItem("Tidak ada kegiatan terjadwal dalam 30 hari ke depan.", true));
        }
    } catch (error) {
        console.error("Error:", error);
        pengumumanListElement.innerHTML = '';
        kegiatanListElement.innerHTML = '';
        pengumumanListElement.appendChild(createListItem("Gagal memuat pengumuman.", true));
        kegiatanListElement.appendChild(createListItem("Gagal memuat kegiatan.", true));
    }
}

// Inisiasi saat DOM selesai dimuat
document.addEventListener('DOMContentLoaded', fetchAndRenderData);