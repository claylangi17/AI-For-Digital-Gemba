# Gemba Digital with AI - Root Cause Suggestion

Sistem AI yang terintegrasi dalam bentuk API untuk mendukung Website dan Mobile App dalam project Gemba Digital with AI. Fokus utama adalah memberikan rekomendasi Root Cause dari masalah yang dilaporkan berdasarkan informasi historis dan pemahaman model AI.

## 🧠 Fitur Utama

- API endpoint untuk mendeteksi root cause berdasarkan area dan problem
- Integrasi dengan database MySQL (menggunakan `gemba_issues` table)
- AI reasoning menggunakan model Gemini dari Google
- Auto-learning dari data historis

## 🔧 Tech Stack

- **Python**: bahasa utama backend
- **Langchain**: integrasi LLM dan prompt chaining
- **FastAPI**: backend framework untuk REST API
- **Gemini API**: model AI untuk reasoning
- **MySQL**: menyimpan data historis

## 📋 Persyaratan

- Python 3.9+
- MySQL/PHPMyAdmin
- Gemini API Key

## 🚀 Instalasi

1. Clone repository ini
2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Setup database MySQL dengan struktur table `gemba_issues` sesuai dokumentasi
4. Copy file `.env.example` ke `.env` dan sesuaikan dengan konfigurasi lokal Anda:

```
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=gemba_digital
DB_PORT=3306

# Gemini API Configuration 
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🏃‍♂️ Menjalankan API

Gunakan salah satu cara berikut:

```bash
# Metode 1: Menggunakan script
python run_api.py

# Metode 2: Menggunakan uvicorn langsung
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API akan berjalan di `http://localhost:8000`

## 📚 API Documentation

### Root Cause Suggestion

**Endpoint:** `/api/root-cause-suggestion`

**Method:** POST

**Request:**

```json
{
  "area": "PRINTING KBA-3 (GCP)",
  "problem": "Cetakan Buram"
}
```

**Response:**

```json
{
  "input_area": "PRINTING KBA-3 (GCP)",
  "input_problem": "Cetakan Buram",
  "suggested_root_causes": [
    "Tinta menetes",
    "Pisau coating aus",
    "Bahan cetak lembab"
  ]
}
```

### Get All Areas

**Endpoint:** `/api/areas`

**Method:** GET

**Response:**

```json
{
  "areas": [
    "PRINTING KBA-3 (GCP)",
    "DC-4",
    "SLOTTER"
  ]
}
```

## 📝 Struktur Database

Table `gemba_issues` dalam database MySQL dengan struktur:

| Field             | Tipe Data | Deskripsi |
|------------------|-----------|-----------|
| id               | INT       | Primary key |
| date             | DATE      | Tanggal kejadian |
| area             | TEXT      | Nama area atau mesin/line |
| problem          | TEXT      | Masalah yang terjadi |
| root_cause       | TEXT      | Akar masalah yang sudah pernah terjadi |
| temporary_action | TEXT      | Tindakan sementara yang pernah dilakukan |
| preventive_action| TEXT      | Tindakan pencegahan |
| source_file      | TEXT      | Asal data (file upload) |

## 🧪 Testing API

Anda dapat menggunakan tools seperti:
- Swagger UI (tersedia di `/docs` setelah API berjalan)
- Postman
- Curl

## 📄 Lisensi

Proyek ini bersifat pribadi dan digunakan untuk keperluan internal.

by: clay steve langi tes lagi halooo 
