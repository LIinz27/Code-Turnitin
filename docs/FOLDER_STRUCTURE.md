# 📁 Struktur Folder Classroom Data

## Struktur Folder Baru (Terorganisir)

Sistem sekarang akan menyimpan data classroom dalam struktur folder yang terorganisir berdasarkan nama kelas dan nama tugas:

```
data/
└── classroom/
    ├── Pemrograman_Web_2024/              # Nama Kelas
    │   ├── Lab_Assignment_1/               # Nama Tugas
    │   │   ├── student1_repo/              # Repository Mahasiswa 1
    │   │   │   ├── index.html
    │   │   │   ├── style.css
    │   │   │   └── script.js
    │   │   ├── student2_repo/              # Repository Mahasiswa 2
    │   │   │   ├── index.html
    │   │   │   └── main.js
    │   │   └── student3_repo/
    │   │       ├── home.html
    │   │       └── app.js
    │   │
    │   ├── Lab_Assignment_2/               # Tugas Kedua
    │   │   ├── student1_final_project/
    │   │   ├── student2_final_project/
    │   │   └── student3_final_project/
    │   │
    │   └── Midterm_Project/                # Tugas UTS
    │       ├── group1_ecommerce/
    │       ├── group2_portfolio/
    │       └── group3_blog/
    │
    ├── Algoritma_Struktur_Data_2024/      # Kelas Lain
    │   ├── Sorting_Algorithm/
    │   │   ├── student1_quicksort/
    │   │   ├── student2_mergesort/
    │   │   └── student3_bubblesort/
    │   │
    │   └── Data_Structure_Implementation/
    │       ├── student1_linkedlist/
    │       ├── student2_stack_queue/
    │       └── student3_binary_tree/
    │
    └── Mobile_App_Development_2024/       # Kelas Ketiga
        ├── First_Flutter_App/
        │   ├── student1_calculator/
        │   ├── student2_todo_app/
        │   └── student3_weather_app/
        │
        └── Final_Mobile_Project/
            ├── team1_social_media_app/
            ├── team2_e_learning_app/
            └── team3_fitness_tracker/
```

## Keuntungan Struktur Baru

### 🎯 **Organisasi yang Jelas**
- **Per Kelas**: Semua tugas dari satu kelas dalam satu folder
- **Per Tugas**: Setiap assignment terpisah dengan jelas
- **Per Mahasiswa**: Repository setiap mahasiswa terorganisir rapi

### 🔍 **Mudah Dinavigasi**
- Dosen bisa langsung ke folder kelas yang diinginkan
- Cari tugas spesifik dengan mudah
- Bandingkan pekerjaan mahasiswa dalam satu tugas

### 📊 **Analisis Lebih Mudah**
- Similarity check per assignment lebih fokus
- Perbandingan antar mahasiswa dalam satu kelas
- Tracking progress per kelas dan per tugas

### 💾 **Pengelolaan Storage**
- Hindari duplikasi file
- Backup dan restore per kelas
- Archive tugas lama secara terorganisir

## Contoh Penggunaan

### Download Assignment untuk Kelas "Pemrograman Web"
```json
{
  "assignment_id": "lab-1-html-css",
  "classroom_id": 12345
}
```

**Hasil akan disimpan di:**
```
data/classroom/Pemrograman_Web_2024/Lab_1_HTML_CSS/
├── ahmad_student_repo/
├── budi_student_repo/
├── citra_student_repo/
└── ...
```

### Download Assignment untuk Kelas "Algoritma"
```json
{
  "assignment_id": "sorting-algorithms",
  "classroom_id": 67890
}
```

**Hasil akan disimpan di:**
```
data/classroom/Algoritma_Struktur_Data_2024/Sorting_Algorithms/
├── student1_quicksort_implementation/
├── student2_mergesort_implementation/
├── student3_heapsort_implementation/
└── ...
```

## Fitur Tambahan

### 🔄 **Auto Skip Downloaded**
- Sistem otomatis skip folder yang sudah ada
- Tidak download ulang file yang sama
- Progress tracking yang akurat

### 📈 **Progress Monitoring**
```
[3/15] 📥 Downloading from student-repo (Student: john_doe)
📁 Struktur folder: Pemrograman_Web_2024/Lab_Assignment_1
Progress: 20.0% | Elapsed: 45.2s | ETA: 180.7s
  -> ✅ Downloaded 8 files
```

### 🎯 **Smart Naming**
- Nama folder aman untuk semua OS
- Karakter khusus otomatis dibersihkan
- Konsisten dan mudah dibaca

## Migration dari Struktur Lama

Jika Anda memiliki data lama dengan struktur:
```
data/classroom/
├── repo1/
├── repo2/
└── repo3/
```

Data baru akan disimpan dengan struktur:
```
data/classroom/
├── ClassName/
│   └── AssignmentName/
│       ├── repo1/
│       ├── repo2/
│       └── repo3/
└── [old files tetap aman]
```

Struktur lama tidak akan terhapus, jadi data Anda tetap aman! 🛡️
