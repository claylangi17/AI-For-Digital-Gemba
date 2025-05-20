# Dokumentasi API Gemba Digital with AI

## Informasi Dasar
- **Base URL**: https://gemba-digital.onrender.com (akan diupdate setelah deployment)
- **Authentication**: Semua request membutuhkan API Key dalam header `X-API-KEY`

## Cara Menggunakan API

### Authentication
Tambahkan header berikut ke setiap request:
```
X-API-KEY: gemba-digital-api-3d9f8e7a1b2c
```

### Endpoint yang Tersedia

#### 1. Get Areas
Mengambil semua area yang tersedia dalam database.

- **URL**: `/api/areas`
- **Method**: GET
- **Headers**: `X-API-KEY: gemba-digital-api-3d9f8e7a1b2c`

**Contoh Response**:
```json
{
  "areas": ["Production Line 1", "Packaging Area", "Warehouse", "Quality Control"]
}
```

#### 2. Suggest Root Causes
Mendapatkan rekomendasi root cause berdasarkan area, masalah, dan kategori.

- **URL**: `/api/root-cause/suggest`
- **Method**: POST
- **Headers**: `X-API-KEY: gemba-digital-api-3d9f8e7a1b2c`

**Request Body**:
```json
{
  "area": "Production Line 1", 
  "problem": "Suhu Mesin Tinggi",
  "category": "Machine"
}
```

**Contoh Response**:
```json
{
  "input_area": "Production Line 1",
  "input_problem": "Suhu Mesin Tinggi",
  "suggested_root_causes": [
    "Filter udara kotor menyebabkan overheating",
    "Low coolant level pada sistem pendingin",
    "Fan tidak berfungsi optimal"
  ]
}
```

#### 3. Merge Root Causes
Menggabungkan root causes yang mirip dari berbagai user.

- **URL**: `/api/root-cause/merge`
- **Method**: POST
- **Headers**: `X-API-KEY: gemba-digital-api-3d9f8e7a1b2c`

**Request Body**:
```json
{
  "root_causes": [
    {
      "root_cause": "Filter udara kotor",
      "user_id": "user1"
    },
    {
      "root_cause": "Air filter kotor dan tersumbat",
      "user_id": "user2"
    },
    {
      "root_cause": "Bearing rusak",
      "user_id": "user3"
    }
  ]
}
```

**Contoh Response**:
```json
{
  "merged_root_causes": [
    {
      "merged_root_cause": "Filter udara kotor dan tersumbat",
      "original_data": [
        {
          "root_cause": "Filter udara kotor",
          "user_id": "user1"
        },
        {
          "root_cause": "Air filter kotor dan tersumbat",
          "user_id": "user2"
        }
      ]
    }
  ],
  "individual_root_causes": [
    {
      "root_cause": "Bearing rusak",
      "user_id": "user3"
    }
  ],
  "all_original_data": [
    {
      "root_cause": "Filter udara kotor",
      "user_id": "user1"
    },
    {
      "root_cause": "Air filter kotor dan tersumbat",
      "user_id": "user2"
    },
    {
      "root_cause": "Bearing rusak",
      "user_id": "user3"
    }
  ]
}
```

#### 4. Suggest Actions
Mendapatkan rekomendasi tindakan sementara dan preventif.

- **URL**: `/api/actions/suggest`
- **Method**: POST
- **Headers**: `X-API-KEY: gemba-digital-api-3d9f8e7a1b2c`

**Request Body**:
```json
{
  "area": "Production Line 1",
  "problem": "Suhu Mesin Tinggi",
  "root_cause": "Filter udara kotor",
  "category": "Machine"
}
```

**Contoh Response**:
```json
{
  "input_area": "Production Line 1",
  "input_problem": "Suhu Mesin Tinggi",
  "input_root_cause": "Filter udara kotor",
  "temporary_actions": [
    "Matikan mesin dan biarkan dingin selama 30 menit",
    "Bersihkan filter dengan air pressure gun",
    "Cek level coolant dan tambahkan jika kurang"
  ],
  "preventive_actions": [
    "Jadwalkan pembersihan filter udara setiap minggu",
    "Pasang sensor suhu dengan alarm",
    "Training untuk operator tentang maintenance dasar"
  ]
}
```

#### 5. Score Root Causes
Menilai kualitas root cause berdasarkan kriteria benchmark.

- **URL**: `/api/root-cause/score`
- **Method**: POST
- **Headers**: `X-API-KEY: gemba-digital-api-3d9f8e7a1b2c`

**Request Body**:
```json
{
  "area": "Production Line 1",
  "problem": "Suhu Mesin Tinggi",
  "category": "Machine",
  "root_causes": [
    "Filter udara kotor menyebabkan overheating",
    "Mesin panas"
  ]
}
```

**Contoh Response**:
```json
{
  "scores": [
    {
      "root_cause": "Filter udara kotor menyebabkan overheating",
      "spesifisitas": 2.3,
      "relevansi": 2.4,
      "kejelasan": 2.2,
      "actionability": 2.1,
      "total_score": 9.0,
      "feedback": "Root cause sangat spesifik dan jelas menunjukkan penyebab. Mudah untuk ditindaklanjuti."
    },
    {
      "root_cause": "Mesin panas",
      "spesifisitas": 0.5,
      "relevansi": 1.2,
      "kejelasan": 0.8,
      "actionability": 0.4,
      "total_score": 2.9,
      "feedback": "Terlalu umum, tidak menjelaskan penyebab sebenarnya. Sulit untuk ditindaklanjuti."
    }
  ],
  "summary": "Root cause 1 memiliki kualitas yang jauh lebih baik karena spesifik dan actionable."
}
```

## Integrasi dengan Frontend

### Contoh JavaScript Fetch
```javascript
// Contoh mengambil data dari endpoint area
fetch('https://gemba-digital.onrender.com/api/areas', {
  method: 'GET',
  headers: {
    'X-API-KEY': 'gemba-digital-api-3d9f8e7a1b2c'
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));

// Contoh POST request untuk root cause suggestion
fetch('https://gemba-digital.onrender.com/api/root-cause/suggest', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-KEY': 'gemba-digital-api-3d9f8e7a1b2c'
  },
  body: JSON.stringify({
    area: "Production Line 1",
    problem: "Suhu Mesin Tinggi",
    category: "Machine"
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### Contoh Axios (untuk React/Vue)
```javascript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'https://gemba-digital.onrender.com',
  headers: {
    'Content-Type': 'application/json',
    'X-API-KEY': 'gemba-digital-api-3d9f8e7a1b2c'
  }
});

// Get areas
apiClient.get('/api/areas')
  .then(response => {
    console.log(response.data);
  })
  .catch(error => {
    console.error('Error:', error);
  });

// Suggest root causes
apiClient.post('/api/root-cause/suggest', {
  area: "Production Line 1",
  problem: "Suhu Mesin Tinggi",
  category: "Machine"
})
  .then(response => {
    console.log(response.data);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

## Notes untuk Developer
- Pastikan selalu menyertakan header `X-API-KEY` di semua request
- Semua request yang gagal akan mengembalikan kode HTTP yang sesuai (400, 401, 500, dll.)
- Untuk testing, gunakan Postman atau curl untuk memastikan API key bekerja dengan benar
