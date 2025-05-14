// Variabel untuk elemen DOM
const pengumumanListElement = document.getElementById('pengumuman-list');
const kegiatanListElement = document.getElementById('kegiatan-list');

// Variabel untuk konfigurasi API
const apiUrl = '/api/events/';
const KATEGORI_NAMA_PENGUMUMAN = "Pengumuman";

// Fungsi untuk memformat tanggal ke format Indonesia (contoh: 14 Mei 2025)
function formatDateIndonesia(dateString) {
    if (!dateString) return '';
    const [year, month, day] = dateString.split('-').map(Number);
    const date = new Date(year, month - 1, day);
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

// Fungsi utama untuk mengambil dan merender data pengumuman dan kegiatan
function fetchAndRenderData() {
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Gagal mengambil data dari API: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            pengumumanListElement.innerHTML = '';
            kegiatanListElement.innerHTML = '';

            const today = new Date();
            today.setHours(0, 0, 0, 0);

            const thirtyDaysLater = new Date(today);
            thirtyDaysLater.setDate(today.getDate() + 30);
            thirtyDaysLater.setHours(23, 59, 59, 999);

            let pengumumanDitemukan = false;
            let kegiatanDitemukan = false;

            data.sort((a, b) => new Date(a.start) - new Date(b.start));

            data.forEach(item => {
                const [startYear, startMonth, startDay] = item.start.split('-').map(Number);
                const startDate = new Date(startYear, startMonth - 1, startDay);
                startDate.setHours(0, 0, 0, 0);

                let actualEndDate = null;
                if (item.end) {
                    const [endYear, endMonth, endDay] = item.end.split('-').map(Number);
                    actualEndDate = new Date(endYear, endMonth - 1, endDay);
                    actualEndDate.setDate(actualEndDate.getDate() - 1);
                } else {
                    actualEndDate = new Date(startDate);
                }
                actualEndDate.setHours(23, 59, 59, 999);

                if (item.kategori === KATEGORI_NAMA_PENGUMUMAN) {
                    if (actualEndDate >= today) {
                        let displayText = `${item.title}`;
                        if (item.deskripsi) {
                            displayText += ` - ${item.deskripsi}`;
                        }
                        pengumumanListElement.appendChild(createListItem(displayText));
                        pengumumanDitemukan = true;
                    }
                } else {
                    let displayText = null;

                    if (startDate >= today && startDate <= thirtyDaysLater) {
                        displayText = `${item.title}: ${formatDateIndonesia(item.start)}`;
                    } else if (startDate < today && actualEndDate >= today && actualEndDate <= thirtyDaysLater) {
                        displayText = `Akhir ${item.title}: ${formatDateIndonesia(actualEndDate.toISOString().slice(0, 10))}`;
                    }

                    if (displayText) {
                        kegiatanListElement.appendChild(createListItem(displayText));
                        kegiatanDitemukan = true;
                    }
                }
            });

            if (!pengumumanDitemukan) {
                pengumumanListElement.appendChild(createListItem("Tidak ada pengumuman terkini.", true));
            }
            if (!kegiatanDitemukan) {
                kegiatanListElement.appendChild(createListItem("Tidak ada kegiatan terjadwal dalam 30 hari ke depan.", true));
            }
        })
        .catch(error => {
            console.error("Error:", error);
            pengumumanListElement.innerHTML = '';
            kegiatanListElement.innerHTML = '';
            pengumumanListElement.appendChild(createListItem("Gagal memuat pengumuman.", true));
            kegiatanListElement.appendChild(createListItem("Gagal memuat kegiatan.", true));
        });
}

// Inisiasi saat DOM selesai dimuat
document.addEventListener('DOMContentLoaded', fetchAndRenderData);