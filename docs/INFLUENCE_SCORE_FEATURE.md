# Influence Score Feature Documentation

## Overview

**Influence Score** adalah fitur baru dalam Code Turnitin yang mengukur **seberapa signifikan/berpengaruh setiap baris kode** dalam konteks plagiarism detection. Fitur ini membantu membedakan antara line yang benar-benar plagiarism dengan line yang kebetulan sama karena umum/standar.

---

## Definisi

**Influence Score** = Skor dampak sebuah baris kode (0.0 - 1.0 atau 0% - 100%) yang menunjukkan seberapa penting line tersebut jika ditemukan sama dengan repository lain.

### Interpretasi Skor:
- **0.0 - 0.4 (0% - 40%)**: Kurang Berpengaruh (GREEN 🟢)
- **0.4 - 0.7 (40% - 70%)**: Cukup Berpengaruh (ORANGE 🟠)
- **0.7 - 1.0 (70% - 100%)**: Sangat Berpengaruh (RED 🔴)

---

## Parameter yang Mempengaruhi Influence Score

### 1. **Similarity Score** (60% bobot)

**Definisi**: Tingkat kesamaan line antara source dan target repository.

**Cara Perhitungan**:
```
similarity = (matching_hashes / total_hashes_in_line)
```

**Rentang**: 0.0 - 1.0

**Contoh**:
| Source | Target | Matching Hashes | Total | Similarity |
|--------|--------|-----------------|-------|-----------|
| `int count = 0;` | `int count = 0;` | 5 | 5 | 1.0 (100%) |
| `int count = 0;` | `int counter = 0;` | 4 | 5 | 0.8 (80%) |
| `int count = 0;` | `int x = 5;` | 1 | 5 | 0.2 (20%) |

**Impact**:
- Similarity 100% = line identik = VERY HIGH influence contribution
- Similarity 50% = line setengah mirip = MEDIUM influence contribution
- Similarity < 20% = line sangat berbeda = MINIMAL contribution

---

### 2. **Code Complexity** (20% bobot)

**Definisi**: Tingkat kompleksitas sebuah baris berdasarkan panjang dan struktur kode.

**Cara Perhitungan**:
```
length_bonus = min(max(len(stripped_line) - 10, 0) / 90, 1.0) * 0.2
```

**Parameter**:
- **Minimum Length**: 10 karakter
- **Maximum Length**: 100 karakter (saturate)
- **Maximum Bonus**: 0.2 (20% dari total influence)

**Contoh Panjang Line**:
| Line | Length | Bonus | Complexity Level |
|------|--------|-------|------------------|
| `}` | 1 | 0.0 | Very Low |
| `int x = 0;` | 11 | 0.001 | Low |
| `public void processUser(String id) {` | 37 | 0.06 | Medium |
| `private static final Map<String, List<Object>> complexMapping = initializeMap();` | 80 | 0.18 | High |

**Impact**:
- **Simple Lines** (e.g., `{`, `}`, `int x;`): Minimal bonus
- **Complex Lines** (e.g., method signatures, algorithms): Maksimal bonus

**Alasan**: Line panjang biasanya mengandung logic spesifik, bukan boilerplate

---

### 3. **Uniqueness Score** (15% bobot)

**Definisi**: Seberapa unik/jarang sebuah line muncul dalam file keseluruhan.

**Cara Perhitungan**:
```
identical_count = sum(1 for all_lines if line.strip() == other_line.strip())
uniqueness_bonus = (1 - min(identical_count - 1, 10) / 10) * 0.15
```

**Parameter**:
- **Count Base**: Jumlah line identik dalam file
- **Saturation Point**: 10 kemunculan
- **Maximum Bonus**: 0.15 (15% dari total influence)

**Contoh Identik Count**:
| Line Content | Identical Count | Uniqueness Bonus | Meaning |
|--------------|-----------------|------------------|---------|
| `}` | 50+ | ~0.0 | Sangat umum (closing brace) |
| `return result;` | 5 | 0.09 | Cukup umum |
| `initializeComplexAlgorithm();` | 1 | 0.15 | Sangat unik |

**Impact**:
- **Umum** (muncul >10x): Minimal bonus, karena sering ada di banyak file
- **Unik** (muncul 1x): Maksimal bonus, karena jarang ada line seperti ini

**Alasan**: Jika sebuah line muncul hanya sekali di file, dan sama dengan target, berarti sangat suspicious

---

### 4. **Code Meaningfulness** (5% bobot)

**Definisi**: Apakah line adalah kode substantif atau hanya struktural (bracket, comment).

**Tipe-tipe Line**:
| Type | Meaningfulness | Bonus |
|------|----------------|-------|
| Comment: `// calculate total` | Low | 0.0 |
| Bracket: `{` atau `}` | Very Low | 0.0 |
| Operator: `;` atau `,` | Very Low | 0.0 |
| Substantive: `int result = calculate();` | High | +0.1 |

**Cara Perhitungan**:
```python
if (stripped and 
    not stripped.startswith('//') and     # bukan comment
    not stripped.startswith('#') and      # bukan comment Python
    stripped not in ['{', '}', '(', ')', ';', ',']):  # bukan bracket/operator
    influence += 0.1
```

**Impact**:
- **Code Logic**: Mendapat bonus (e.g., assignments, function calls)
- **Structural**: Tidak mendapat bonus (e.g., brackets, empty lines)

**Alasan**: Structural code adalah boilerplate yang sering sama, bukan indikasi plagiarism

---

## Rumus Lengkap Influence Score

```
influence = similarity
          + length_bonus                    (0.0 - 0.2)
          + uniqueness_bonus                (0.0 - 0.15)
          + meaningfulness_bonus            (0.0 - 0.1)

influence = min(influence, 1.0)  # Cap at 1.0
```

### Contoh Perhitungan Lengkap:

**Scenario 1: Simple Assignment**
```java
int x = 5;
```
- Similarity: 1.0 (line identik)
- Length: 10 char → bonus = 0.0
- Uniqueness: muncul 8x → bonus = (1 - 7/10) * 0.15 = 0.045
- Meaningfulness: substantif → bonus = 0.1
- **Total: 1.0 + 0.0 + 0.045 + 0.1 = 1.145 → CAP = 1.0 (100%)**
- **⚠️ Tapi karena line sederhana, influence praktis tetap MEDIUM**

**Scenario 2: Method Signature**
```java
public static String calculateUserDiscount(int age, double salary) {
```
- Similarity: 1.0 (line identik)
- Length: 63 char → bonus = (63-10)/90 * 0.2 = 0.118
- Uniqueness: muncul 1x → bonus = 1.0 * 0.15 = 0.15
- Meaningfulness: substantif → bonus = 0.1
- **Total: 1.0 + 0.118 + 0.15 + 0.1 = 1.368 → CAP = 1.0 (100%)**
- **✅ VERY HIGH INFLUENCE (RED)**

**Scenario 3: Closing Bracket**
```
}
```
- Similarity: 1.0 (line identik)
- Length: 1 char → bonus = 0.0
- Uniqueness: muncul 100x → bonus = 0.0
- Meaningfulness: not substantif → bonus = 0.0
- **Total: 1.0 → but capped by other factors = LOW influence**
- **❌ MINIMAL INFLUENCE (GREEN)**

---

## UI Display

### Di Code Comparison Panel

Setiap baris kode ditampilkan dengan format:
```
[Line Number] [Code Content] [Influence Score Badge]
```

**Contoh Visual**:
```
847  public static String calculateTotal() {    ↑85 (RED)
848      int sum = 0;                           ↑45 (ORANGE)
849      return sum;                             ↑15 (GREEN)
850  }                                           ↑5  (GREEN)
```

### Influence Score Badge:

| Badge | Color | Range | Meaning |
|-------|-------|-------|---------|
| ↑85 | 🔴 RED | 70-100 | Sangat Berpengaruh - Fokuskan investigasi di sini |
| ↑45 | 🟠 ORANGE | 40-70 | Cukup Berpengaruh - Perlu dilihat dalam konteks |
| ↑15 | 🟢 GREEN | 0-40 | Kurang Berpengaruh - Standar/boilerplate |

### Hover Tooltip

Saat hover ke line, tampil informasi detail:
```
Similarity: 80.0% | Influence: 85%
```

---

## Use Cases

### ✅ Untuk Deteksi Plagiarism Lebih Baik:

1. **Filter Noise**: Abaikan line dengan influence < 20%
   - Bracket, boilerplate, standar syntax
   
2. **Risk Assessment**: Fokus ke line dengan influence > 70%
   - Method signature, algoritma, logic unik
   
3. **Composite Score**: Hitung weighted plagiarism score
   ```
   plagiarism_score = sum(similarity_i * influence_i) / sum(influence_i)
   ```

### ✅ Untuk Presentasi Laporan:

```
Plagiarism Analysis Report:
- Overall Similarity: 35%
- Weighted Plagiarism Score: 45%  (lebih akurat)
  
Top Suspicious Lines (by influence):
1. Line 42: calculateUserDiscount() - Similarity: 100%, Influence: 92%
2. Line 15: processPayment() - Similarity: 95%, Influence: 88%
3. Line 28: validateInput() - Similarity: 80%, Influence: 75%
```

---

## Implementation Details

### Backend (Python)

**File**: `src/demo/demo_similarity.py`

**Method**: `_calculate_line_influence_score()`
```python
def _calculate_line_influence_score(self, line_content: str, all_lines: List[str], 
                                   similarity: float) -> float:
    """Calculate influence score for a line based on complexity and uniqueness."""
    # 1. Base influence from similarity (60% weight)
    influence = similarity
    
    # 2. Length bonus (20% weight)
    stripped = line_content.strip()
    if stripped:
        length_bonus = min(max(len(stripped) - 10, 0) / 90, 1.0) * 0.2
        influence += length_bonus
    
    # 3. Uniqueness bonus (15% weight)
    identical_count = sum(1 for l in all_lines if l.strip() == stripped)
    if identical_count > 0:
        uniqueness_bonus = (1 - min(identical_count - 1, 10) / 10) * 0.15
        influence += uniqueness_bonus
    
    # 4. Meaningfulness bonus (5% weight)
    if stripped and not stripped.startswith('//') and not stripped.startswith('#') and stripped not in ['{', '}', '(', ')', ';', ',']:
        influence += 0.1
    
    # Cap at 1.0
    return min(influence, 1.0)
```

### Frontend (HTML/JavaScript)

**File**: `templates/demo.html`

Setiap baris di code panel menampilkan:
```html
<div class="flex hover:bg-gray-50 group">
    <!-- Line number -->
    <div class="line-number">847</div>
    
    <!-- Code content -->
    <div class="flex-1">public static String calculateTotal() {</div>
    
    <!-- Influence score badge -->
    <div class="influence-badge" 
         :class="line.influence >= 0.7 ? 'text-red-600' : line.influence >= 0.4 ? 'text-orange-600' : 'text-green-600'">
        ↑{{ Math.round(line.influence * 100) }}
    </div>
</div>
```

### CSS Styling

**File**: `static/css/demo.css`

```css
.influence-score.high {
    color: #dc2626;          /* Red */
    background-color: #fee2e2;
    border: 1px solid #fecaca;
}

.influence-score.medium {
    color: #ea580c;          /* Orange */
    background-color: #fed7aa;
    border: 1px solid #fdba74;
}

.influence-score.low {
    color: #16a34a;          /* Green */
    background-color: #dbeafe;
    border: 1px solid #bfdbfe;
}
```

---

## Testing & Validation

### Manual Test Cases:

1. **Simple Variable Assignment**
   ```java
   int count = 0;
   ```
   Expected Influence: 30-40% (GREEN)
   - Simple, short, common = low influence

2. **Complex Method Signature**
   ```java
   private static synchronized List<String> processComplexUserData(Map<String, Object> params) throws IOException {
   ```
   Expected Influence: 85-95% (RED)
   - Complex, long, unique = high influence

3. **Closing Bracket**
   ```
   }
   ```
   Expected Influence: 5-10% (GREEN)
   - Universal, trivial = minimal influence

4. **Comment Line**
   ```java
   // TODO: refactor this function
   ```
   Expected Influence: 0-5% (GREEN)
   - Not substantive code = low influence

---

## Future Enhancements

Possible improvements:
1. **Domain-Specific Weighting**: Adjust weights based on programming language
2. **Variable Name Importance**: Track if variables are domain-specific vs generic
3. **Pattern Recognition**: Identify common design patterns (e.g., singleton, factory)
4. **Library Detection**: Distinguish between library calls vs custom code
5. **ML-Based Weighting**: Learn optimal weights from historical plagiarism cases

---

## Configuration Parameters

Current hardcoded parameters (can be made configurable):

```python
# Code Complexity
MIN_LENGTH_THRESHOLD = 10       # chars
MAX_LENGTH_THRESHOLD = 100      # chars
LENGTH_BONUS_WEIGHT = 0.2       # 20%

# Uniqueness
UNIQUENESS_SATURATION = 10      # occurrence count
UNIQUENESS_BONUS_WEIGHT = 0.15  # 15%

# Meaningfulness
MEANINGFULNESS_BONUS_WEIGHT = 0.1  # 10%

# Similarity weight (implicit)
SIMILARITY_WEIGHT = 0.6         # 60%

# Overall
MAX_INFLUENCE_SCORE = 1.0       # cap
```

---

## Summary Table

| Aspect | Weight | Factor | Impact |
|--------|--------|--------|--------|
| **Similarity** | 60% | Line match rate | Direct correlation |
| **Complexity** | 20% | Code length | Longer = more important |
| **Uniqueness** | 15% | Occurrence count | Rarer = more suspicious |
| **Meaningfulness** | 5% | Code type | Logic > structure |
| **TOTAL** | **100%** | Combined | 0.0 - 1.0 |

---

**Last Updated**: January 2026  
**Version**: 1.0  
**Status**: Implemented in Demo Mode
