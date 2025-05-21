# Dokumentasi Fitur Absensi QR Code

## Ringkasan
Fitur absensi QR code pada proyek Digital Gemba memungkinkan pencatatan kehadiran peserta secara otomatis, cepat, dan aman dengan memanfaatkan QR code unik untuk setiap sesi.

---

## 1. Alur Kerja Fitur QR Absensi

### a. Pembuatan QR Code
- Sistem backend membuat QR code yang berisi **QR token** unik.
- Format token: `SESSION_YYYY_MM_DD_TXYZ`
  - `YYYY_MM_DD` = tanggal sesi
  - `TXYZ` = ID sesi (misal: T1 untuk session id 1)

### b. Proses Absensi
1. **Peserta scan QR code** melalui aplikasi mobile/web.
2. Aplikasi mengirim request ke endpoint:
   - `POST /api/attendance/qr`
   - Body JSON:
     ```json
     {
       "user_id": "1",
       "qr_token": "SESSION_2025_05_21_T1"
     }
     ```
3. Backend melakukan validasi:
   - Format QR token
   - Cek session aktif di database
   - Cek user valid
   - Cek apakah user sudah absen di sesi tersebut
4. Jika valid, backend mencatat kehadiran ke database dan menambah poin ke user.
5. Backend mengirim response ke aplikasi:
   - Contoh sukses:
     ```json
     {
       "status": "success",
       "message": "Presence recorded successfully",
       "data": {
         "user_id": "1",
         "timestamp": "2025-05-21T10:37:16.315651",
         "status": "present",
         "time_in": "2025-05-21T10:37:16.315651",
         "time_out": null,
         "user_name": "John Smith",
         "role": "admin"
       }
     }
     ```
   - Contoh error: token tidak valid, user tidak ditemukan, dsb.

---

## 2. Struktur Database Terkait
- **users**: Data user (id, nama, role, point, dll)
- **gemba_sessions**: Data sesi (id, nama, area, status, dll)
- **presences**: Data absensi (userid, session_id, status, time_in, time_out, dll)
- **point_history**: Riwayat penambahan poin

---

## 3. Keamanan & Validasi
- QR token hanya berlaku untuk sesi yang aktif.
- User tidak bisa absen dua kali di sesi yang sama.
- Semua request ke API harus menyertakan API key (untuk keamanan).

---

## 4. Endpoint Utama
- `POST /api/attendance/qr` — Mencatat kehadiran via QR code
- `GET /api/session/{session_id}/attendees` — Melihat daftar peserta hadir di suatu sesi

---

## 5. Contoh Alur Penggunaan
1. Admin membuka sesi dan menampilkan QR code di layar.
2. Peserta datang, membuka aplikasi, dan scan QR code.
3. Sistem otomatis mencatat kehadiran dan waktu scan.
4. Admin bisa melihat laporan kehadiran secara real-time.

---

## 6. Catatan Teknis
- Backend dibangun dengan **FastAPI** (Python)
- Database menggunakan **MySQL**
- Tidak ada fitur face recognition pada sistem ini
- Penambahan poin otomatis setiap absen sukses (10 poin)

---

## 7. Format QR Token
```
SESSION_YYYY_MM_DD_TXYZ
```
- `SESSION_` : prefix tetap
- `YYYY_MM_DD` : tanggal sesi
- `TXYZ` : kode sesi unik (ID sesi)

---

## 8. Keuntungan
- Proses absensi cepat, akurat, dan minim human error
- Data kehadiran dan poin langsung tercatat otomatis
- Mudah diintegrasikan dengan aplikasi mobile/web

---

Jika ada pertanyaan lebih lanjut atau ingin penjelasan kode lebih detail, silakan hubungi tim developer.
