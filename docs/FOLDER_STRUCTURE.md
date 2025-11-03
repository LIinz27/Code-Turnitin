# 📁 Code Turnitin - Project Structure

## Current Project Structure

```
Code-Turnitin/
├── app.py                              # Main application entry point
├── main.py                             # Alternative entry point
├── requirements.txt                    # Python dependencies
├── config/
│   ├── .env                           # Environment variables (not in git)
│   └── .env.template                  # Environment template
├── data/
│   ├── cache/                         # Application cache
│   ├── classroom/                     # GitHub Classroom data
│   ├── demo/
│   │   ├── demo_repositories.json     # Demo repository metadata
│   │   ├── demo_repos/               # Java demo repositories
│   │   ├── demo_repos_js_filtered/   # JavaScript demo repositories
│   │   ├── demo_repos_python/        # Python demo repositories
│   │   └── demo_repos_python_filtered/
│   ├── github/                       # GitHub scraping data
│   ├── mahasiswa/                    # Student data
│   └── templates/                    # Data templates
├── docs/                             # Documentation files
│   ├── ENVIRONMENT_SETUP.md
│   ├── FOLDER_STRUCTURE.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── README.MD
│   ├── SIDE_BY_SIDE_COMPARISON_FEATURE.md
│   └── THESIS_DEMO_ROADMAP.md
├── src/                              # Source code
│   ├── __init__.py
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── file_comparison.py        # File-by-file comparison engine
│   │   ├── jaccard_similarity.py     # Jaccard similarity algorithm
│   │   ├── similarity_base.py        # Base similarity interface
│   │   └── winnowing_algorithm.py    # Winnowing algorithm implementation
│   ├── app/
│   │   ├── __init__.py
│   │   ├── app_factory.py           # Flask application factory
│   │   └── web_routes.py            # Web route handlers
│   ├── demo/
│   │   ├── __init__.py
│   │   ├── demo_handler.py          # Demo data management
│   │   └── demo_similarity.py       # Demo similarity analysis
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── classroom_scraper.py     # GitHub Classroom scraper
│   │   └── github_scraper.py        # General GitHub scraper
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py           # File utility functions
│       └── logging_config.py       # Logging configuration
├── static/                          # Static web assets
│   ├── css/
│   │   ├── demo.css               # Demo page styles
│   │   └── style.css              # Main application styles
│   └── js/
│       └── demo.js                # Demo page JavaScript
├── templates/                      # HTML templates
│   ├── classroom.html             # Classroom analysis page
│   ├── demo.html                  # Demo page
│   ├── error.html                 # Error page
│   └── index.html                 # Main page
└── tests/                         # Test files
    ├── advanced_repo_analyzer.py
    ├── test_algorithm_consistency.py
    ├── test_algorithm_improved.py
    ├── test_repo_checker.py
    └── reports/                   # Test reports
```

## Key Components

### �️ **Core Architecture**
- **Flask Application Factory Pattern**: Modular application structure
- **Similarity Algorithms**: File-by-file comparison with Winnowing + Jaccard
- **Demo System**: Pre-loaded repositories for testing (Java, JavaScript, Python)
- **Web Interface**: Interactive demo and classroom analysis pages

### � **Algorithm Components**
- **FileComparisonEngine**: Main comparison engine with configurable thresholds
- **WinnowingAlgorithm**: Code fingerprinting for similarity detection
- **JaccardSimilarity**: Set-based similarity calculation
- **File-by-file Analysis**: Individual file comparison with importance weighting

### 🎯 **Demo Data Structure**
- **Java**: `data/demo_repos/` - Original Java assignment repositories
- **JavaScript**: `data/demo_repos_js_filtered/` - Filtered JavaScript projects
- **Python**: `data/demo_repos_python/` and `data/demo_repos_python_filtered/`
- **Metadata**: `demo_repositories.json` with repository information

### � **Configuration**
- **Environment Variables**: GitHub tokens, API keys in `config/.env`
- **Similarity Thresholds**: Configurable in FileComparisonEngine (default: 0.1)
- **File Type Support**: .java, .js, .py, .html, .css, .json, .md

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
