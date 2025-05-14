// Variabel untuk elemen DOM
const calendarEl = document.getElementById('calendar');
const agendaContainer = document.getElementById('agenda-container');
const customAlertBar = document.getElementById('customAlertBar');
const customAlertMessage = document.getElementById('customAlertMessage');
const customAlertCloseBtn = document.getElementById('customAlertCloseBtn');
const modal = document.getElementById('eventModal');
const eventForm = document.getElementById('eventForm');
const eventStart = document.getElementById('eventStart');
const eventEnd = document.getElementById('eventEnd');
const eventDays = document.getElementById('eventDays');
const eventCategory = document.getElementById('eventCategory');
const closeEventModalBtn = document.getElementById('closeEventModalBtn');
const editModal = document.getElementById('editEventModal');
const editEventForm = document.getElementById('editEventForm');
const editEventId = document.getElementById('editEventId');
const editEventTitle = document.getElementById('editEventTitle');
const editEventStart = document.getElementById('editEventStart');
const editEventEnd = document.getElementById('editEventEnd');
const editEventDays = document.getElementById('editEventDays');
const editEventCategory = document.getElementById('editEventCategory');
const editEventDescription = document.getElementById('editEventDescription');
const closeEditEventModalBtn = document.getElementById('closeEditEventModalBtn');
const deleteConfirmModal = document.getElementById('deleteConfirmModal');
const deleteConfirmMessage = document.getElementById('deleteConfirmMessage');
const deleteEventId = document.getElementById('deleteEventId');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const closeDeleteConfirmModalBtn = document.getElementById('closeDeleteConfirmModalBtn');
const notificationModal = document.getElementById('notificationModal');
const closeNotificationModalBtn = document.getElementById('closeNotificationModalBtn');
const notificationForm = document.getElementById('notificationForm');
const notificationEventTitle = document.getElementById('notificationEventTitle');
const notificationEventIdInput = document.getElementById('notificationEventId');

// Variabel untuk konfigurasi
const currentUserId = {{ user_id|default:'null' }};
const KATEGORI_PENGUMUMAN_LOWERCASE = "pengumuman";
let alertTimeout;

// Fungsi untuk menampilkan alert kustom
function showCustomAlert(message, type = 'error', duration = 5000) {
    if (!customAlertBar || !customAlertMessage) {
        console.warn('Custom alert elements not found. Falling back to default alert.');
        alert(message);
        return;
    }

    if (alertTimeout) {
        clearTimeout(alertTimeout);
    }

    customAlertMessage.textContent = message;
    customAlertBar.className = 'custom-alert-bar';
    customAlertBar.classList.add(type);
    customAlertBar.classList.add('show');

    alertTimeout = setTimeout(() => {
        hideCustomAlert();
    }, duration);
}

// Fungsi untuk menyembunyikan alert kustom
function hideCustomAlert() {
    if (!customAlertBar) return;
    customAlertBar.classList.remove('show');
}

// Fungsi untuk memformat ulang tanggal ke format YYYY-MM-DD
function formatDateString(dateStr) {
    if (!dateStr) return null;
    const parts = dateStr.split('-');
    if (parts.length !== 3) return null;
    const year = parts[0];
    const month = parts[1].padStart(2, '0');
    const day = parts[2].padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Fungsi untuk menghitung jumlah hari pada modal tambah
function calculateDays() {
    const startVal = eventStart.value;
    const endVal = eventEnd.value;

    if (!startVal) {
        eventDays.value = '';
        return;
    }
    const startDate = new Date(startVal);

    if (!endVal) {
        eventDays.value = "1 hari";
        return;
    }
    const endDate = new Date(endVal);

    if (!isNaN(startDate) && !isNaN(endDate) && endDate >= startDate) {
        const diff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
        eventDays.value = diff + " hari";
    } else if (!isNaN(startDate) && (isNaN(endDate) || startDate.getTime() === endDate.getTime())) {
        eventDays.value = "1 hari";
    } else {
        eventDays.value = '';
    }
}

// Fungsi untuk menghitung jumlah hari pada modal edit
function calculateEditDays() {
    const startVal = editEventStart.value;
    const endVal = editEventEnd.value;

    if (!startVal) {
        editEventDays.value = '';
        return;
    }
    const startDate = new Date(startVal);

    if (!endVal) {
        editEventDays.value = "1 hari";
        return;
    }
    const endDate = new Date(endVal);

    if (!isNaN(startDate) && !isNaN(endDate) && endDate >= startDate) {
        const diff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
        editEventDays.value = diff + " hari";
    } else if (!isNaN(startDate) && (isNaN(endDate) || startDate.getTime() === endDate.getTime())) {
        editEventDays.value = "1 hari";
    } else {
        editEventDays.value = '';
    }
}

// Fungsi untuk memuat kategori dari API
async function loadCategories(targetSelect) {
    try {
        const response = await fetch('/api/categories/');
        if (!response.ok) throw new Error('Gagal memuat kategori');
        const categories = await response.json();
        targetSelect.innerHTML = '<option value="">Pilih Kategori</option>';
        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.nama;
            targetSelect.appendChild(option);
        });
    } catch (err) {
        console.error('Error memuat kategori:', err);
        showCustomAlert('Gagal memuat kategori. Silakan coba lagi.', 'error');
    }
}

// Fungsi untuk memuat agenda berdasarkan rentang tanggal
async function loadAgenda(start, end) {
    try {
        const year = start.getFullYear();
        const [eventsResponse, holidaysResponse] = await Promise.all([
            fetch('/api/events/'),
            fetch(`https://api-harilibur.vercel.app/api?year=${year}`)
        ]);
        const eventsData = await eventsResponse.json();
        const holidaysData = await holidaysResponse.json();

        const filteredEvents = eventsData.filter(event => {
            const eventStart = new Date(event.start);
            const eventEnd = event.end ? new Date(event.end) : new Date(event.start);
            const adjustedEnd = new Date(eventEnd);
            adjustedEnd.setDate(eventEnd.getDate() - 1);
            return (eventStart <= end && adjustedEnd >= start);
        });

        const filteredHolidays = holidaysData
            .filter(holiday => holiday.is_national_holiday)
            .map(holiday => ({
                title: holiday.holiday_name,
                start: formatDateString(holiday.holiday_date),
                end: formatDateString(holiday.holiday_date),
                backgroundColor: '#ff0000',
                isHoliday: true,
                id: `holiday-${formatDateString(holiday.holiday_date)}`,
                deskripsi: 'Hari Libur Nasional'
            }))
            .filter(holiday => {
                const holidayDate = new Date(holiday.start);
                return holiday.start && !isNaN(holidayDate) && holidayDate >= start && holidayDate <= end;
            });

        const sortedAgenda = [...filteredEvents, ...filteredHolidays].sort((a, b) => {
            return new Date(a.start) - new Date(b.start);
        });

        renderAgenda(sortedAgenda);
    } catch (err) {
        console.error('Error memuat agenda:', err);
        agendaContainer.innerHTML = '<p>Gagal memuat agenda.</p>';
        showCustomAlert('Gagal memuat data agenda.', 'error');
    }
}

// Fungsi untuk merender daftar agenda
function renderAgenda(agendaList) {
    agendaContainer.innerHTML = '';

    const filteredAgendaList = agendaList.filter(agenda => {
        return !agenda.kategori || agenda.kategori.toLowerCase() !== KATEGORI_PENGUMUMAN_LOWERCASE;
    });

    if (filteredAgendaList.length === 0) {
        agendaContainer.innerHTML = '<p>Tidak ada agenda kegiatan yang sesuai dengan pencarian atau periode ini.</p>';
        return;
    }

    filteredAgendaList.forEach(agenda => {
        const startDate = new Date(agenda.start);
        let endDate = agenda.end && !agenda.isHoliday ? new Date(agenda.end) : null;

        const formatTanggal = (date) => {
            return date.toLocaleDateString('id-ID', {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });
        };

        const formatTanggalTanpaTahun = (date) => {
            return date.toLocaleDateString('id-ID', {
                day: 'numeric',
                month: 'long'
            });
        };

        let tanggalText = '';
        if (!endDate || startDate.getTime() >= new Date(endDate).getTime()) {
            tanggalText = formatTanggal(startDate);
        } else {
            const displayEndDate = new Date(endDate);
            displayEndDate.setDate(displayEndDate.getDate() - 1);

            if (startDate.toDateString() === displayEndDate.toDateString()) {
                tanggalText = formatTanggal(startDate);
            } else if (displayEndDate < startDate) {
                tanggalText = formatTanggal(startDate);
            } else {
                const startTahun = startDate.getFullYear();
                const endTahun = displayEndDate.getFullYear();
                const startBulan = startDate.getMonth();
                const endBulan = displayEndDate.getMonth();

                if (startTahun !== endTahun) {
                    tanggalText = `${formatTanggal(startDate)} - ${formatTanggal(displayEndDate)}`;
                } else if (startBulan !== endBulan) {
                    tanggalText = `${formatTanggalTanpaTahun(startDate)} - ${formatTanggal(displayEndDate)}`;
                } else {
                    tanggalText = `${startDate.getDate()} - ${displayEndDate.getDate()} ${startDate.toLocaleDateString('id-ID', { month: 'long', year: 'numeric' })}`;
                }
            }
        }

        const agendaEl = document.createElement('div');
        agendaEl.className = 'kalender-agenda-item';
        agendaEl.style.borderLeftColor = agenda.backgroundColor || '#ff0000';

        let bellButtonHTML = '';
        let actionButtonsHTML = '';

        actionButtonsHTML += `
            <button class="kalender-action-btn gcal" title="Tambahkan ke Google Calendar" onclick="addToGoogleCalendar('${agenda.title.replace(/'/g, "\\'")}', '${agenda.start}', '${agenda.end || agenda.start}')">
                <img src="https://img.icons8.com/?size=100&id=WKF3bm1munsk&format=png&color=000000" alt="Google Calendar">
            </button>
        `;

        if ('{{ user.is_authenticated }}' === 'True' && !agenda.isHoliday) {
            bellButtonHTML = `
                <button class="kalender-btn-bell-icon" title="Setel Notifikasi" onclick="showNotificationPopup('${agenda.title.replace(/'/g, "\\'")}', '${agenda.start}', ${agenda.id})">
                    <i class="fa-regular fa-bell"></i>
                </button>`;

            if (currentUserId && agenda.user_fk === currentUserId) {
                actionButtonsHTML += `
                    <button class="kalender-action-btn edit" title="Edit Kegiatan" onclick="openEditModal(${agenda.id}, '${agenda.title.replace(/'/g, "\\'")}', '${agenda.start}', '${agenda.end || ''}', ${agenda.kategori_id}, '${agenda.deskripsi ? agenda.deskripsi.replace(/'/g, "\\'") : ''}')">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                    <button class="kalender-action-btn delete" title="Hapus Kegiatan" onclick="openDeleteConfirmModal(${agenda.id}, '${agenda.title.replace(/'/g, "\\'")}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                `;
            }
        }

        agendaEl.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="kalender-agenda-item-title">${agenda.title}</div>
                    <div class="kalender-agenda-date">Tanggal: ${tanggalText}</div>
                    ${agenda.deskripsi ? `<div class="kalender-agenda-location">Deskripsi: ${agenda.deskripsi}</div>` : ''}
                </div>
                ${bellButtonHTML}
            </div>
            <div class="kalender-agenda-actions">
                ${actionButtonsHTML}
            </div>
        `;
        agendaContainer.appendChild(agendaEl);
    });
}

// Fungsi untuk membuka modal tambah kegiatan
window.openModal = function () {
    loadCategories(eventCategory);
    eventForm.reset();
    eventDays.value = '';
    modal.classList.add('show');
}

// Fungsi untuk menutup modal tambah kegiatan
function closeModal() {
    modal.classList.remove('show');
}

// Fungsi untuk membuka modal edit kegiatan
window.openEditModal = function (id, title, start, end, kategoriId, deskripsi) {
    editEventId.value = id;
    editEventTitle.value = title || '';

    const startDate = new Date(start);
    if (!isNaN(startDate)) {
        editEventStart.value = startDate.toISOString().split('T')[0];
    } else {
        editEventStart.value = '';
    }

    if (end) {
        const endDate = new Date(end);
        endDate.setDate(endDate.getDate() - 1);
        if (!isNaN(endDate)) {
            editEventEnd.value = endDate.toISOString().split('T')[0];
        } else {
            editEventEnd.value = '';
        }
    } else {
        editEventEnd.value = '';
    }

    editEventDescription.value = deskripsi || '';
    calculateEditDays();

    loadCategories(editEventCategory).then(() => {
        editEventCategory.value = kategoriId || '';
    }).catch(err => {
        console.error('Error loading categories:', err);
        showCustomAlert('Gagal memuat kategori untuk edit.', 'error');
    });

    editModal.classList.add('show');
}

// Fungsi untuk menutup modal edit kegiatan
function closeEditModal() {
    if (editModal) {
        editModal.classList.remove('show');
    }
}

// Fungsi untuk membuka modal konfirmasi hapus
window.openDeleteConfirmModal = function (id, title) {
    deleteEventId.value = id;
    deleteConfirmMessage.textContent = `Apakah Anda yakin ingin menghapus kegiatan "${title}"?`;
    deleteConfirmModal.classList.add('show');
}

// Fungsi untuk menutup modal konfirmasi hapus
function closeDeleteConfirmModal() {
    deleteConfirmModal.classList.remove('show');
}

// Fungsi untuk membuka modal notifikasi
function openNotificationModal(title, kegiatanId) {
    notificationEventTitle.textContent = title;
    notificationEventIdInput.value = kegiatanId;
    document.getElementById('notifMethodEmail').checked = true;
    notificationModal.classList.add('show');
}

// Fungsi untuk menutup modal notifikasi
function closeNotificationModal() {
    notificationModal.classList.remove('show');
}

// Fungsi untuk menyimpan notifikasi
async function saveNotification(kegiatanId, method) {
    try {
        const response = await fetch('/api/save-notification/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({
                kegiatan_id: kegiatanId,
                metode: method
            })
        });
        const result = await response.json();
        if (result.success) {
            showCustomAlert('Notifikasi berhasil disimpan!', 'success');
        } else {
            showCustomAlert('Gagal menyimpan notifikasi: ' + (result.error || 'Kesalahan tidak diketahui.'), 'error');
        }
    } catch (error) {
        console.error('Error saving notification:', error);
        showCustomAlert('Terjadi kesalahan koneksi saat menyimpan notifikasi.', 'error');
    }
}

// Fungsi untuk memfilter agenda berdasarkan pencarian
window.filterAgenda = function () {
    const q = document.getElementById('search').value.toLowerCase();
    const viewStart = calendar.view.activeStart;
    const viewEnd = calendar.view.activeEnd;

    Promise.all([
        fetch('/api/events/'),
        fetch(`https://api-harilibur.vercel.app/api?year=${viewStart.getFullYear()}`)
    ])
        .then(([eventsResponse, holidaysResponse]) => Promise.all([eventsResponse.json(), holidaysResponse.json()]))
        .then(([eventsData, holidaysData]) => {
            const filtered = [...eventsData, ...holidaysData
                .filter(holiday => holiday.is_national_holiday)
                .map(holiday => ({
                    title: holiday.holiday_name,
                    start: formatDateString(holiday.holiday_date),
                    end: formatDateString(holiday.holiday_date),
                    backgroundColor: '#ff0000',
                    isHoliday: true,
                    id: `holiday-${formatDateString(holiday.holiday_date)}`,
                    deskripsi: 'Hari Libur Nasional'
                }))
                .filter(holiday => holiday.start)]
                .filter(a => {
                    const eventStart = new Date(a.start);
                    const eventEnd = a.end ? new Date(a.end) : new Date(a.start);
                    const adjustedEnd = new Date(eventEnd);
                    adjustedEnd.setDate(eventEnd.getDate() - 1);
                    return (
                        ((a.title && a.title.toLowerCase().includes(q)) ||
                        (a.deskripsi && a.deskripsi.toLowerCase().includes(q))) &&
                        (eventStart <= viewEnd && adjustedEnd >= viewStart)
                    );
                })
                .sort((a, b) => {
                    return new Date(a.start) - new Date(b.start);
                });
            renderAgenda(filtered);
        })
        .catch(err => {
            console.error('Error filtering agenda:', err);
            showCustomAlert('Gagal memfilter agenda.', 'error');
        });
};

// Fungsi untuk menambahkan kegiatan ke Google Calendar
window.addToGoogleCalendar = function (title, start, end) {
    const startDate = new Date(start);
    let endDateForGCal;

    if (end) {
        endDateForGCal = new Date(end);
    } else {
        endDateForGCal = new Date(startDate);
        endDateForGCal.setDate(startDate.getDate() + 1);
    }

    const formatDateForGCal = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}${month}${day}`;
    };

    const datesParam = `${formatDateForGCal(startDate)}/${formatDateForGCal(endDateForGCal)}`;

    const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${datesParam}`;
    window.open(url, '_blank');
};

// Fungsi untuk menampilkan popup notifikasi
window.showNotificationPopup = function (title, startDateUnused, kegiatanId) {
    openNotificationModal(title, kegiatanId);
};

// Inisiasi saat DOM selesai dimuat
document.addEventListener('DOMContentLoaded', function () {
    // Inisialisasi FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        initialDate: new Date(),
        locale: 'id',
        headerToolbar: {
            left: 'title',
            center: '',
            right: 'today prev,next'
        },
        buttonText: {
            today: 'Hari Ini',
        },
        eventClick: function (info) {
            const message = `Agenda: ${info.event.title} - Tanggal: ${info.event.start.toLocaleDateString('id-ID')}`;
            showCustomAlert(message, 'info', 7000);
        },
        height: 'auto',
        fixedWeekCount: false,
        datesSet: function (info) {
            const start = info.view.activeStart;
            const end = info.view.activeEnd;
            loadAgenda(start, end);
        },
        events: function (fetchInfo, successCallback, failureCallback) {
            Promise.all([
                fetch(`/api/events/?start=${fetchInfo.startStr}&end=${fetchInfo.endStr}`).then(res => res.json()),
                fetch(`https://api-harilibur.vercel.app/api?year=${fetchInfo.start.getFullYear()}`).then(res => res.json())
            ])
                .then(([eventsData, holidaysData]) => {
                    const filteredEvents = eventsData.filter(event => {
                        return event.kategori && event.kategori.toLowerCase() !== KATEGORI_PENGUMUMAN_LOWERCASE;
                    });
                    const holidayEvents = holidaysData
                        .filter(holiday => holiday.is_national_holiday)
                        .map(holiday => ({
                            title: holiday.holiday_name,
                            start: formatDateString(holiday.holiday_date),
                            end: formatDateString(holiday.holiday_date),
                            backgroundColor: '#ff0000',
                            borderColor: '#ff0000',
                            allDay: true,
                            isHoliday: true
                        }))
                        .filter(holiday => holiday.start);
                    successCallback([...filteredEvents, ...holidayEvents]);
                })
                .catch(err => {
                    console.error('Error loading events for FullCalendar:', err);
                    failureCallback(err);
                });
        }
    });
    calendar.render();

    // Event listener untuk resize window
    window.addEventListener('resize', function () {
        calendar.updateSize();
    });

    // Event listener untuk alert kustom
    if (customAlertCloseBtn) {
        customAlertCloseBtn.addEventListener('click', hideCustomAlert);
    }

    // Event listener untuk modal tambah kegiatan
    if (closeEventModalBtn) {
        closeEventModalBtn.addEventListener('click', closeModal);
    }

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    eventStart.addEventListener('change', calculateDays);
    eventEnd.addEventListener('change', calculateDays);

    eventForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const nama = document.getElementById('eventTitle').value.trim();
        const start = document.getElementById('eventStart').value;
        let end = document.getElementById('eventEnd').value;
        const kategori_id = document.getElementById('eventCategory').value;
        const deskripsi = document.getElementById('eventDescription').value.trim();

        if (!nama || !start || !kategori_id) {
            showCustomAlert('Nama kegiatan, tanggal mulai, dan kategori wajib diisi.', 'error');
            return;
        }

        if (!end) {
            end = start;
        }

        const startDate = new Date(start + 'T00:00:00+07:00');
        const endDateForFC = new Date(end + 'T00:00:00+07:00');
        endDateForFC.setDate(endDateForFC.getDate() + 1);

        const newEvent = {
            nama,
            start: startDate.toISOString(),
            end: endDateForFC.toISOString(),
            kategori_id,
            deskripsi
        };

        try {
            const response = await fetch('/api/events/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                body: JSON.stringify(newEvent)
            });

            if (response.ok) {
                showCustomAlert('Kegiatan berhasil ditambahkan!', 'success');
                calendar.refetchEvents();
                loadAgenda(calendar.view.activeStart, calendar.view.activeEnd);
                closeModal();
            } else {
                const errorData = await response.json();
                showCustomAlert('Gagal menambahkan kegiatan: ' + (errorData.error || JSON.stringify(errorData)), 'error');
            }
        } catch (err) {
            console.error('Error saat submit event:', err);
            showCustomAlert('Terjadi kesalahan koneksi saat menambahkan kegiatan.', 'error');
        }
    });

    // Event listener untuk modal edit kegiatan
    if (closeEditEventModalBtn) {
        closeEditEventModalBtn.addEventListener('click', closeEditModal);
    }

    if (editModal) {
        editModal.addEventListener('click', (e) => {
            if (e.target === editModal) {
                closeEditModal();
            }
        });
    }

    editEventStart.addEventListener('change', calculateEditDays);
    editEventEnd.addEventListener('change', calculateEditDays);

    editEventForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = editEventId.value;
        const nama = editEventTitle.value.trim();
        const start = editEventStart.value;
        let end = editEventEnd.value;
        const kategori_id = editEventCategory.value;
        const deskripsi = editEventDescription.value.trim();

        if (!nama || !start || !kategori_id) {
            showCustomAlert('Nama kegiatan, tanggal mulai, dan kategori wajib diisi.', 'error');
            return;
        }

        if (!end) {
            end = start;
        }

        const startDate = new Date(start + 'T00:00:00+07:00');
        const endDateForFC = new Date(end + 'T23:59:58+07:00');

        const updatedEvent = {
            nama,
            start: startDate.toISOString(),
            end: endDateForFC.toISOString(),
            kategori_id,
            deskripsi
        };

        try {
            const response = await fetch(`/api/events/update/${id}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                body: JSON.stringify(updatedEvent)
            });

            if (response.ok) {
                showCustomAlert('Kegiatan berhasil diperbarui!', 'success');
                calendar.refetchEvents();
                loadAgenda(calendar.view.activeStart, calendar.view.activeEnd);
                closeEditModal();
            } else {
                const errorData = await response.json();
                showCustomAlert('Gagal memperbarui kegiatan: ' + (errorData.error || JSON.stringify(errorData)), 'error');
            }
        } catch (err) {
            console.error('Error saat update event:', err);
            showCustomAlert('Terjadi kesalahan koneksi saat memperbarui kegiatan.', 'error');
        }
    });

    // Event listener untuk modal konfirmasi hapus
    if (closeDeleteConfirmModalBtn) {
        closeDeleteConfirmModalBtn.addEventListener('click', closeDeleteConfirmModal);
    }

    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', closeDeleteConfirmModal);
    }

    if (deleteConfirmModal) {
        deleteConfirmModal.addEventListener('click', (e) => {
            if (e.target === deleteConfirmModal) {
                closeDeleteConfirmModal();
            }
        });
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            const id = deleteEventId.value;

            try {
                const response = await fetch(`/api/events/delete/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}'
                    }
                });

                if (response.ok) {
                    showCustomAlert('Kegiatan berhasil dihapus!', 'success');
                    calendar.refetchEvents();
                    loadAgenda(calendar.view.activeStart, calendar.view.activeEnd);
                    closeDeleteConfirmModal();
                } else {
                    const errorData = await response.json();
                    showCustomAlert('Gagal menghapus kegiatan: ' + (errorData.error || JSON.stringify(errorData)), 'error');
                }
            } catch (err) {
                console.error('Error saat delete event:', err);
                showCustomAlert('Terjadi kesalahan koneksi saat menghapus kegiatan.', 'error');
            }
        });
    }

    // Event listener untuk modal notifikasi
    if (closeNotificationModalBtn) {
        closeNotificationModalBtn.addEventListener('click', closeNotificationModal);
    }

    if (notificationModal) {
        notificationModal.addEventListener('click', (e) => {
            if (e.target === notificationModal) {
                closeNotificationModal();
            }
        });
    }

    if (notificationForm) {
        notificationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const kegiatanId = notificationEventIdInput.value;
            const selectedMethodRadio = document.querySelector('input[name="notifMethod"]:checked');

            if (!selectedMethodRadio) {
                showCustomAlert('Silakan pilih metode notifikasi.', 'error');
                return;
            }
            const selectedMethod = selectedMethodRadio.value;

            if (kegiatanId && selectedMethod) {
                await saveNotification(kegiatanId, selectedMethod);
                closeNotificationModal();
            } else {
                showCustomAlert('Terjadi kesalahan, ID kegiatan atau metode tidak ditemukan.', 'error');
            }
        });
    }

    // Memuat agenda awal
    loadAgenda(calendar.view.activeStart, calendar.view.activeEnd);
});