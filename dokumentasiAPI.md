# Dokumentasi API - Kalender Akademik

API ini menyediakan endpoint untuk mengelola kegiatan akademik dalam sistem kalender yang dibangun dengan Django dan Django Rest Framework (DRF). API ini mendukung operasi CRUD untuk kegiatan, pengambilan kategori, dan penyimpanan notifikasi, dengan kemampuan filter untuk mengurangi beban di sisi klien.

## URL Dasar
Semua endpoint berada di bawah URL dasar: `/api/`

## Autentikasi
- Beberapa endpoint memerlukan autentikasi (misalnya, menambah, memperbarui, menghapus kegiatan, dan menyimpan notifikasi). Gunakan autentikasi berbasis sesi Django atau autentikasi berbasis token (jika dikonfigurasi).
- Pastikan untuk menyertakan header `X-CSRFToken` pada permintaan POST, PUT, dan DELETE saat autentikasi dilakukan.

## Daftar Endpoint

### 1. Daftar Kegiatan
Mengambil daftar kegiatan akademik dengan opsi filter.

- **URL:** `/events/`
- **Metode:** `GET`
- **Autentikasi:** Tidak diperlukan
- **Parameter Query:**
  - `start` (opsional): String datetime ISO 8601 (contoh: `2025-01-01T00:00:00Z`). Memfilter kegiatan yang berakhir setelah tanggal ini.
  - `end` (opsional): String datetime ISO 8601 (contoh: `2025-01-31T23:59:59Z`). Memfilter kegiatan yang dimulai sebelum tanggal ini.
  - `year` (opsional): Angka (contoh: `2025`). Memfilter kegiatan pada tahun tertentu.
  - `month` (opsional): Angka (1-12, contoh: `1`). Memfilter kegiatan pada bulan tertentu di tahun yang ditentukan. Harus digunakan bersama `year`.
  - `academic_year` (opsional): String (contoh: `2024/2025`). Memfilter kegiatan berdasarkan tahun akademik.
- **Catatan:**
  - Jika `start` dan `end` diberikan, parameter ini akan diutamakan, dan API akan mengembalikan kegiatan yang tumpang tindih dengan rentang tanggal tersebut.
  - Jika `start` dan `end` tidak diberikan:
    - Dengan `year` dan `month`, memfilter kegiatan pada bulan dan tahun tersebut.
    - Dengan hanya `year`, memfilter kegiatan pada tahun tersebut.
    - Dengan `academic_year`, memfilter kegiatan pada tahun akademik tersebut.
    - Tanpa parameter, default ke kegiatan pada tahun berjalan (misalnya, 2025).
  - Kegiatan dengan kategori "pengumuman" tidak disertakan.
- **Respon:**
  - **Status:** `200 OK`
  - **Content-Type:** `application/json`
  - **Isi:**
    ```json
    [
        {
            "id": 32,
            "tahun_akademik": "2024/2025",
            "title": "Registrasi Selang/Cuti Kuliah",
            "start": "2025-02-06",
            "end": "2025-04-13",
            "deskripsi": "",
            "kategori": "Registrasi Umum",
            "kategori_id": 3,
            "backgroundColor": "#32cd32",
            "borderColor": "#32cd32",
            "user_fk": 1
        }
    ]
    ```

- **Contoh Permintaan:**
  - Mengambil semua kegiatan di tahun berjalan (2025):
    ```
    GET /api/events/
    ```
  - Mengambil kegiatan di bulan Januari 2025:
    ```
    GET /api/events/?year=2025&month=1
    ```
  - Mengambil kegiatan di tahun akademik 2024/2025:
    ```
    GET /api/events/?academic_year=2024/2025
    ```
  - Mengambil kegiatan yang tumpang tindih dengan Januari 2025 (rentang FullCalendar):
    ```
    GET /api/events/?start=2025-01-01T00:00:00Z&end=2025-01-31T23:59:59Z
    ```

### 2. Tambah Kegiatan
Membuat kegiatan akademik baru.

- **URL:** `/events/add/`
- **Metode:** `POST`
- **Autentikasi:** Diperlukan
- **Izin:** Pengguna harus terautentikasi
- **Header Permintaan:**
  - `Content-Type: application/json`
  - `X-CSRFToken: <csrf-token>`
- **Isi Permintaan:**
  ```json
  {
      "nama": "Registrasi Selang/Cuti Kuliah",
      "deskripsi": "",
      "start": "2025-02-06T00:00:00Z",
      "end": "2025-04-13T23:59:59Z",
      "kategori_id": 3,
      "tahun_akademik_id": 1,
      "semester": "Genap"
  }
  ```
  - `nama` (wajib): String, nama kegiatan.
  - `deskripsi` (opsional): String, deskripsi kegiatan.
  - `start` (wajib): Datetime ISO 8601, tanggal mulai kegiatan.
  - `end` (opsional): Datetime ISO 8601, tanggal selesai kegiatan. Default ke `start` jika tidak diberikan.
  - `kategori_id` (wajib): Angka, ID kategori.
  - `tahun_akademik_id` (opsional): Angka, ID tahun akademik. Default ke tahun akademik pertama jika tidak diberikan.
  - `semester` (opsional): String ("Ganjil" atau "Genap"). Default ke "Ganjil".
- **Respon:**
  - **Sukses:**
    - **Status:** `201 Created`
    - **Isi:**
      ```json
      {
          "success": true,
          "message": "Kegiatan berhasil ditambahkan"
      }
      ```
  - **Error:**
    - **Status:** `400 Bad Request` (field wajib tidak ada atau tanggal tidak valid)
    - **Isi:**
      ```json
      {
          "success": false,
          "error": "Nama, tanggal mulai, dan kategori wajib diisi"
      }
      ```
    - **Status:** `404 Not Found` (kategori atau tahun akademik tidak ditemukan)
    - **Isi:**
      ```json
      {
          "success": false,
          "error": "Kategori tidak ditemukan"
      }
      ```

### 3. Perbarui Kegiatan
Memperbarui kegiatan akademik yang sudah ada.

- **URL:** `/events/update/<id>/`
- **Metode:** `PUT`
- **Autentikasi:** Diperlukan
- **Izin:** Hanya pembuat kegiatan yang dapat memperbarui
- **Header Permintaan:**
  - `Content-Type: application/json`
  - `X-CSRFToken: <csrf-token>`
- **Isi Permintaan:**
  ```json
  {
      "nama": "Registrasi Selang/Cuti Kuliah (Updated)",
      "deskripsi": "Deskripsi diperbarui",
      "start": "2025-02-07T00:00:00Z",
      "end": "2025-04-14T23:59:59Z",
      "kategori_id": 3
  }
  ```
  - Field sama seperti pada endpoint Tambah Kegiatan.
- **Respon:**
  - **Sukses:**
    - **Status:** `200 OK`
    - **Isi:**
      ```json
      {
          "success": true,
          "message": "Kegiatan berhasil diperbarui"
      }
      ```
  - **Error:**
    - **Status:** `403 Forbidden` (pengguna bukan pembuat kegiatan)
    - **Isi:**
      ```json
      {
          "success": false,
          "error": "Anda tidak memiliki izin untuk mengedit kegiatan ini"
      }
      ```
    - **Status:** `404 Not Found` (kegiatan atau kategori tidak ditemukan)
    - **Isi:**
      ```json
      {
          "success": false,
          "error": "Kegiatan tidak ditemukan"
      }
      ```

### 4. Hapus Kegiatan
Menghapus kegiatan akademik yang sudah ada.

- **URL:** `/events/delete/<id>/`
- **Metode:** `DELETE`
- **Autentikasi:** Diperlukan
- **Izin:** Hanya pembuat kegiatan yang dapat menghapus
- **Header Permintaan:**
  - `X-CSRFToken: <csrf-token>`
- **Respon:**
  - **Sukses:**
    - **Status:** `200 OK`
    - **Isi:**
      ```json
      {
          "success": true,
          "message": "Kegiatan berhasil dihapus"
      }
      ```
  - **Error:**
    - **Status:** `403 Forbidden` (pengguna bukan pembuat kegiatan)
    - **Isi:**
      ```json
      {
          "success": false,
          "error": "Anda tidak memiliki izin untuk menghapus kegiatan ini"
      }
      ```
    - **Status:** `404 Not Found` (kegiatan tidak ditemukan)
    - **Isi:**
      ```json
      {
          "success": false,
          "error": "Kegiatan tidak ditemukan"
      }
      ```

### 5. Daftar Kategori
Mengambil daftar kategori kegiatan.

- **URL:** `/categories/`
- **Metode:** `GET`
- **Autentikasi:** Tidak diperlukan
- **Respon:**
  - **Status:** `200 OK`
  - **Isi:**
    ```json
    [
        {
            "id": 3,
            "nama": "Registrasi Umum",
            "warna": "#32cd32"
        }
    ]
    ```

### 6. Simpan Notifikasi
Menyimpan notifikasi untuk suatu kegiatan.

- **URL:** `/save-notification/`
- **Metode:** `POST`
- **Autentikasi:** Diperlukan
- **Header Permintaan:**
  - `Content-Type: application/json`
  - `X-CSRFToken: <csrf-token>`
- **Isi Permintaan:**
  ```json
  {
      "kegiatan_id": 32,
      "metode": "email"
  }
  ```
  - `kegiatan_id` (wajib): Angka, ID kegiatan.
  - `metode` (wajib): String, "email" atau "whatsapp".
- **Respon:**
  - **Sukses:**
    - **Status:** `200 OK`
    - **Isi:**
      ```json
      {
          "success": true,
          "message": "Notifikasi berhasil disimpan"
      }
      ```
  - **Error:**
    - **Status:** `400 Bad Request` (metode tidak valid atau notifikasi sudah ada)
    - **Isi:**
      ```json
      {
          "success": false,
          "error": "Notifikasi sudah ada untuk agenda ini"
      }
      ```
    - **Status:** `404 Not Found` (kegiatan tidak ditemukan)
    - **Isi:**
      ```json
      {
          "success": false,
          "error": "Kegiatan tidak ditemukan"
      }
      ```

## Penanganan Error
- Semua endpoint mengembalikan respon JSON dengan `success` (boolean) dan `error` (pesan) jika gagal.
- Kode status HTTP yang umum:
  - `200 OK`: Permintaan berhasil.
  - `201 Created`: Sumber daya berhasil dibuat.
  - `400 Bad Request`: Parameter atau data permintaan tidak valid.
  - `403 Forbidden`: Pengguna tidak memiliki izin.
  - `404 Not Found`: Sumber daya tidak ditemukan.
  - `500 Internal Server Error`: Kesalahan di sisi server.

## Catatan untuk Pengembang
- API ini dirancang untuk mengurangi beban di sisi klien dengan mendukung filter di sisi server (misalnya, berdasarkan rentang tanggal, tahun, bulan, atau tahun akademik).
- Tanggal dalam respon disesuaikan ke WIB (UTC+7).
- Tanggal `end` dalam respon kegiatan bersifat inklusif untuk kompatibilitas dengan FullCalendar.
- Pastikan untuk menangani token CSRF pada permintaan yang memerlukan autentikasi.

## Contoh Penggunaan dengan Fetch API
```javascript
// Mengambil kegiatan untuk bulan Januari 2025
fetch('/api/events/?year=2025&month=1')
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));

// Menambahkan kegiatan baru
fetch('/api/events/add/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': '<csrf-token>'
    },
    body: JSON.stringify({
        nama: "Kegiatan Baru",
        deskripsi: "Deskripsi kegiatan",
        start: "2025-05-15T00:00:00Z",
        end: "2025-05-16T23:59:59Z",
        kategori_id: 3,
        tahun_akademik_id: 1,
        semester: "Genap"
    })
})
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
```

---
