
### 📘 Gemba Digital with AI — Project Plan (AI Root Cause Suggestion)

#### 📌 Project Overview
Membuat sistem AI yang terintegrasi dalam bentuk **API** untuk mendukung **Website dan Mobile App** dalam project _Gemba Digital with AI_. Fokus utama adalah memberikan rekomendasi **Root Cause** dari masalah yang dilaporkan berdasarkan informasi historis dan pemahaman model AI.

#### 🧠 AI #1: Root Cause Suggestion

---

### 🎯 Goal
Menyediakan rekomendasi beberapa **possible Root Cause** berdasarkan:
- Informasi dari user: `area` dan `problem`
- Pembelajaran dari data historis di database MySQL
- Kemampuan reasoning dari model AI (Gemini)

---

### 🔧 Tech Stack
- **Python**: bahasa utama backend
- **Langchain**: integrasi LLM dan prompt chaining
- **FastAPI**: backend framework untuk membangun REST API
- **Gemini API (Model: gemini-2.5-flash-preview-04-17)**: untuk reasoning dan saran berbasis AI
- **MySQL**: menyimpan data historis problem solving (`gemba_issues` table)

---

### 🧩 Database Struktur (`gemba_issues`)
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

---

### 🧭 Alur Kerja AI Root Cause

1. **User Input**:
   - Area
   - Problem

2. **Langkah-Langkah AI**:
   - Query data dari MySQL `gemba_issues` berdasarkan `area`
   - Pelajari semua kombinasi `problem` dan `root_cause` dari area tersebut
   - Bandingkan problem input user dengan pola-pola yang pernah ada
   - Gunakan LLM untuk menyimpulkan dan menyarankan beberapa possible `root_cause`
   - Output dikembalikan sebagai JSON via REST API

3. **Contoh Output**:
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

---

### 🔄 Auto-Learning dari Data Baru
- Setiap data baru yang masuk ke database akan:
  - Di-index secara otomatis untuk dipelajari oleh AI
  - Memperkuat model reasoning agar lebih akurat

---

### 🔌 API Design (FastAPI)

**Endpoint: `/api/root-cause-suggestion`**

- **Method**: POST
- **Input**:
```json
{
  "area": "DC-4",
  "problem": "Miss-Match"
}
```

- **Output**:
```json
{
  "possible_root_causes": [
    "Ukuran material lebih besar",
    "Perbedaan ukuran cetakan"
  ]
}
```

---

### ✅ Target Deliverables
- [ ] API endpoint untuk root cause suggestion
- [ ] Query builder + filter untuk data berdasarkan area
- [ ] LLM reasoning pipeline dengan Gemini API
- [ ] Dokumentasi prompt dan skema pembelajaran data historis
