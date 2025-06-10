// app.js
// Logika Frontend untuk Aplikasi Deteksi Plagiarisme Kode

document.addEventListener('DOMContentLoaded', () => {
    // === 1. DOM Elements (Elemen Antarmuka Pengguna) ===
    // Elemen input dan daftar URL repositori
    const studentRepoUrlInput = document.getElementById('studentRepoUrlInput');
    const addStudentRepoUrlButton = document.getElementById('addStudentRepoUrl');
    const studentRepoUrlList = document.getElementById('studentRepoUrlList');

    const githubUrlInput = document.getElementById('githubUrlInput');
    const addGithubUrlButton = document.getElementById('addGithubUrl');
    const githubUrlList = document.getElementById('githubUrlList');

    // Elemen tombol aksi dan indikator loading
    const runAnalysisButton = document.getElementById('runAnalysisButton');
    const loadingIndicator = document.getElementById('loadingIndicator');

    // Elemen bagian hasil
    const resultsSection = document.getElementById('results-section');
    const mhVsGhResultsTableBody = document.querySelector('#mhVsGhResults tbody');
    const noResultsDiv = document.getElementById('noResults');

    // Elemen tombol clear file
    const clearStudentFilesBtn = document.getElementById('clearStudentFilesBtn');
    const clearGithubFilesBtn = document.getElementById('clearGithubFilesBtn');

    // Elemen modal perbandingan kode
    const codeCompareModal = document.getElementById('codeCompareModal');
    const modalFilenameMhs = document.getElementById('modal-filename-mhs');
    const modalFilenameGh = document.getElementById('modal-filename-gh');
    const codeMhsPre = document.getElementById('code-mhs');
    const codeGhPre = document.getElementById('code-gh');
    const closeButton = document.querySelector('.close-button'); // Tombol tutup modal


    // === 2. Scroll Synchronization (Sinkronisasi Scroll Panel Kode) ===
    // Ini memastikan kedua panel kode (mahasiswa & GitHub) menggulir bersamaan
    const codePaneMhsPre = document.querySelector('#code-mhs');
    const codePaneGhPre = document.querySelector('#code-gh');
    let isScrollingMhs = false;
    let isScrollingGh = false;

    codePaneMhsPre.addEventListener('scroll', () => {
        if (!isScrollingGh) {
            isScrollingMhs = true;
            codePaneGhPre.scrollTop = codePaneMhsPre.scrollTop;
        }
        isScrollingMhs = false;
    });

    codePaneGhPre.addEventListener('scroll', () => {
        if (!isScrollingMhs) {
            isScrollingGh = true;
            codePaneMhsPre.scrollTop = codePaneGhPre.scrollTop;
        }
        isScrollingGh = false;
    });


    // === 3. Data Storage (Penyimpanan Data di Frontend) ===
    let studentRepoUrls = []; // Menyimpan URL repositori mahasiswa
    let githubUrls = [];      // Menyimpan URL repositori pembanding GitHub
    let lastAnalysisResults = []; // Menyimpan hasil analisis terakhir untuk ditampilkan di modal


    // === 4. Core Functions (Fungsi Inti) ===

    // Fungsi untuk memperbarui daftar URL repositori mahasiswa di UI
    function updateStudentRepoList() {
        studentRepoUrlList.innerHTML = ''; // Kosongkan daftar sebelumnya
        if (studentRepoUrls.length === 0) {
            studentRepoUrlList.innerHTML = '<p class="text-gray-500 italic">Belum ada URL repositori mahasiswa ditambahkan.</p>';
            clearStudentFilesBtn.classList.add('hidden'); // Sembunyikan tombol clear jika kosong
        } else {
            studentRepoUrls.forEach((url, index) => {
                const p = document.createElement('p');
                // Tambahkan kelas Tailwind untuk styling
                p.className = 'flex justify-between items-center bg-gray-100 border border-gray-200 rounded-md py-2 px-3 mb-2';
                p.textContent = url;
                const removeBtn = document.createElement('button');
                removeBtn.textContent = 'X';
                removeBtn.className = 'text-red-500 hover:text-red-700 font-bold ml-4'; // Kelas Tailwind untuk tombol hapus
                removeBtn.addEventListener('click', () => {
                    studentRepoUrls.splice(index, 1); // Hapus URL dari array
                    updateStudentRepoList(); // Perbarui UI
                });
                p.appendChild(removeBtn);
                studentRepoUrlList.appendChild(p);
            });
            clearStudentFilesBtn.classList.remove('hidden'); // Tampilkan tombol clear jika ada item
        }
    }

    // Fungsi untuk memperbarui daftar URL repositori pembanding GitHub di UI
    function updateGithubUrlList() {
        githubUrlList.innerHTML = ''; // Kosongkan daftar sebelumnya
        if (githubUrls.length === 0) {
            githubUrlList.innerHTML = '<p class="text-gray-500 italic">Belum ada URL repositori pembanding ditambahkan.</p>';
            clearGithubFilesBtn.classList.add('hidden'); // Sembunyikan tombol clear jika kosong
        } else {
            githubUrls.forEach((url, index) => {
                const p = document.createElement('p');
                // Tambahkan kelas Tailwind untuk styling
                p.className = 'flex justify-between items-center bg-gray-100 border border-gray-200 rounded-md py-2 px-3 mb-2';
                p.textContent = url;
                const removeBtn = document.createElement('button');
                removeBtn.textContent = 'X';
                removeBtn.className = 'text-red-500 hover:text-red-700 font-bold ml-4'; // Kelas Tailwind untuk tombol hapus
                removeBtn.addEventListener('click', () => {
                    githubUrls.splice(index, 1); // Hapus URL dari array
                    updateGithubUrlList(); // Perbarui UI
                });
                p.appendChild(removeBtn);
                githubUrlList.appendChild(p);
            });
            clearGithubFilesBtn.classList.remove('hidden'); // Tampilkan tombol clear jika ada item
        }
    }

    // Fungsi untuk menampilkan hasil deteksi kemiripan dalam tabel
    function displayResults(mhVsGhData) {
        mhVsGhResultsTableBody.innerHTML = ''; // Kosongkan tabel sebelumnya

        let hasSignificantResults = false;
        lastAnalysisResults = mhVsGhData; // Simpan hasil untuk akses dari modal

        // Urutkan hasil berdasarkan skor kemiripan (tertinggi ke terendah)
        mhVsGhData.sort((a, b) => b.score - a.score);

        // Iterasi melalui hasil dan tambahkan ke tabel
        mhVsGhData.forEach((result, index) => {
            if (result.score > 0) { // Hanya tampilkan jika skor > 0
                hasSignificantResults = true;
                const row = mhVsGhResultsTableBody.insertRow();
                row.className = 'hover:bg-blue-50 transition duration-150 ease-in-out'; // Kelas Tailwind untuk efek hover pada baris
                
                // Tambahkan kelas khusus berdasarkan skor kemiripan untuk visual feedback
                if (result.score >= 70) {
                    row.classList.add('bg-red-100', 'text-red-800'); // Peringatan kuat (merah)
                } else if (result.score >= 40) {
                    row.classList.add('bg-yellow-100', 'text-yellow-800'); // Peringatan sedang (kuning)
                }

                // Tambahkan sel dan konten ke baris
                let cellClass = 'px-6 py-4 whitespace-nowrap text-sm text-gray-800'; // Kelas dasar untuk sel

                row.insertCell().className = cellClass;
                row.cells[0].textContent = result.source_file;
                
                row.insertCell().className = cellClass;
                row.cells[1].textContent = result.compared_file;
                
                row.insertCell().className = cellClass + ' font-medium';
                row.cells[2].textContent = `${result.score}%`;
                
                // Tambahkan tombol "Lihat Kode"
                const actionCell = row.insertCell();
                actionCell.className = cellClass + ' text-right font-medium';
                const viewCodeBtn = document.createElement('button');
                viewCodeBtn.textContent = 'Lihat Kode';
                // Kelas Tailwind untuk styling tombol
                viewCodeBtn.className = 'px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2';
                viewCodeBtn.setAttribute('data-index', index); // Simpan indeks hasil untuk diambil nanti
                viewCodeBtn.onclick = () => openCodeCompareModal(index); // Tambahkan event listener
                actionCell.appendChild(viewCodeBtn);
            }
        });

        // Tampilkan/sembunyikan pesan "Tidak ada kemiripan..."
        if (!hasSignificantResults) {
            noResultsDiv.classList.remove('hidden');
        } else {
            noResultsDiv.classList.add('hidden');
        }
        resultsSection.classList.remove('hidden'); // Tampilkan bagian hasil
    }

    // Fungsi untuk membuka modal perbandingan kode
    async function openCodeCompareModal(resultIndex) {
        const result = lastAnalysisResults[resultIndex];
        if (!result) return;

        // Isi nama file di header modal
        modalFilenameMhs.textContent = result.source_file;
        modalFilenameGh.textContent = result.compared_file;
        
        // Tampilkan pesan loading di panel kode
        codeMhsPre.innerHTML = 'Memuat kode...'; 
        codeGhPre.innerHTML = 'Memuat kode...'; 
        
        // --- LOGIKA TAMPILKAN MODAL DENGAN TRANSDISI ---
        // 1. Pastikan modal memiliki display:flex (mengoverride hidden)
        codeCompareModal.classList.remove('hidden'); 
        // 2. Aktifkan pointer-events agar modal bisa diklik
        codeCompareModal.classList.add('pointer-events-auto');

        // 3. Tambahkan kelas opacity-100 untuk memicu transisi fade-in (delay 10ms untuk reflow browser)
        setTimeout(() => {
            codeCompareModal.classList.add('opacity-100'); 
            const modalContent = codeCompareModal.querySelector('.modal-content');
            // Pastikan kelas opacity-0 dan scale-95 dihapus sebelum menambahkan kelas show (opacity-100, scale-100)
            modalContent.classList.remove('scale-95', 'opacity-0'); 
            modalContent.classList.add('scale-100', 'opacity-100'); 
        }, 10); 
        // --- AKHIR LOGIKA TAMPILKAN MODAL ---

        try {
            // Ambil konten kode untuk file mahasiswa dari backend
            const responseMhs = await fetch('/get_code_content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: result.source_file, file_type: 'mahasiswa' })
            });
            const dataMhs = await responseMhs.json();
            const codeMhs = dataMhs.content;

            // Ambil konten kode untuk file GitHub dari backend
            const responseGh = await fetch('/get_code_content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: result.compared_file, file_type: 'github' })
            });
            const dataGh = await responseGh.json();
            const codeGh = dataGh.content;

            // Tampilkan dan highlight kode
            displayAndHighlightCode(codeMhs, result.similar_blocks_mhs, codeMhsPre);
            displayAndHighlightCode(codeGh, result.similar_blocks_gh, codeGhPre);

            // Terapkan Highlight.js setelah konten dimuat dan di-render
            setTimeout(() => {
                hljs.highlightElement(codeMhsPre);
                hljs.highlightElement(codeGhPre);
                // Reset scroll posisi ke atas setelah memuat kode
                codeMhsPre.scrollTop = 0;
                codeGhPre.scrollTop = 0;
            }, 50); // Delay kecil untuk memastikan rendering DOM sebelum highlight.js

        } catch (error) {
            console.error("Error fetching code content:", error);
            codeMhsPre.textContent = "Gagal memuat kode.";
            codeGhPre.textContent = "Gagal memuat kode.";
            alert("Gagal memuat konten kode. Pastikan file ada di server.");
        }
    }

    // Fungsi untuk menampilkan kode dengan nomor baris dan highlight bagian yang mirip
    function displayAndHighlightCode(codeContent, similarBlocks, preElement) {
        let highlightedHtml = '';
        const lines = codeContent.split('\n');
        
        lines.forEach((line, index) => {
            const lineNumber = index + 1;
            let lineClass = '';
            
            // Cek apakah baris ini termasuk dalam blok yang mirip
            for (const block of similarBlocks) {
                if (lineNumber >= block.start && lineNumber <= block.end) {
                    lineClass = 'highlight-code-line'; // Tambahkan kelas highlight
                    break;
                }
            }
            
            // Bangun HTML untuk setiap baris dengan nomor baris dan konten
            highlightedHtml += `<span class="line-number">${lineNumber}.</span><span class="line-content ${lineClass}">${escapeHtml(line)}</span>\n`;
        });
        
        preElement.innerHTML = highlightedHtml; // Masukkan HTML ke elemen <pre>
    }

    // Helper: Fungsi untuk meng-escape karakter HTML (penting untuk keamanan)
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    // Fungsi untuk menutup modal
    function closeModal() {
        const modalContent = codeCompareModal.querySelector('.modal-content');
        
        // --- LOGIKA TUTUP MODAL DENGAN TRANSDISI ---
        // 1. Mulai transisi fade-out dan scale-down
        modalContent.classList.remove('scale-100', 'opacity-100');
        modalContent.classList.add('scale-95', 'opacity-0');

        codeCompareModal.classList.remove('opacity-100', 'pointer-events-auto'); 
        codeCompareModal.classList.add('opacity-0', 'pointer-events-none'); // Nonaktifkan klik pada backdrop

        // 2. Setelah transisi selesai, sembunyikan modal sepenuhnya (display:none)
        //    Gunakan 'once: true' agar listener hanya berjalan sekali
        codeCompareModal.addEventListener('transitionend', function handler() {
            codeCompareModal.classList.add('hidden'); // Sembunyikan modal secara total
            codeCompareModal.removeEventListener('transitionend', handler); // Hapus listener setelah dieksekusi
        }, { once: true }); 
        // --- AKHIR LOGIKA TUTUP MODAL ---

        // Kosongkan konten kode saat modal ditutup
        codeMhsPre.innerHTML = ''; 
        codeGhPre.innerHTML = ''; 
    }


    // === 5. Event Listeners (Penanganan Event) ===

    // Event listener untuk tombol tutup modal (X)
    if (closeButton) { 
        closeButton.addEventListener('click', closeModal);
    }
    
    // Event listener untuk menutup modal ketika mengklik di luar konten modal
    codeCompareModal.addEventListener('click', (event) => {
        // Hanya tutup modal jika klik langsung pada backdrop (bukan pada modal-content itu sendiri)
        if (event.target === codeCompareModal) { 
            closeModal();
        }
    });

    // Event listener untuk tombol "Tambah URL" repositori mahasiswa
    addStudentRepoUrlButton.addEventListener('click', () => {
        const url = studentRepoUrlInput.value.trim();
        // Validasi URL dasar
        if (!url.startsWith('https://github.com/')) {
            alert('Mohon masukkan URL repositori GitHub yang valid (diawali dengan https://github.com/).');
            return;
        }
        if (url && !studentRepoUrls.includes(url)) {
            studentRepoUrls.push(url);
            studentRepoUrlInput.value = ''; // Kosongkan input
            updateStudentRepoList(); // Perbarui tampilan daftar
        } else if (url && studentRepoUrls.includes(url)) {
            alert('URL repositori ini sudah ada dalam daftar.');
        } else {
            alert('Silakan masukkan URL repositori mahasiswa yang valid.');
        }
    });

    // Event listener untuk tombol "Tambah URL" repositori pembanding GitHub
    addGithubUrlButton.addEventListener('click', () => {
        const url = githubUrlInput.value.trim();
        // Validasi URL dasar
        if (!url.startsWith('https://github.com/')) {
            alert('Mohon masukkan URL repositori GitHub yang valid (diawali dengan https://github.com/).');
            return;
        }
        if (url && !githubUrls.includes(url)) {
            githubUrls.push(url);
            githubUrlInput.value = ''; // Kosongkan input
            updateGithubUrlList(); // Perbarui tampilan daftar
        } else if (url && githubUrls.includes(url)) {
            alert('URL ini sudah ada dalam daftar.');
        } else {
            alert('Silakan masukkan URL repositori GitHub yang valid.');
        }
    });

    // Event listener untuk tombol "Jalankan Deteksi Kemiripan"
    runAnalysisButton.addEventListener('click', async () => {
        // Validasi input
        if (studentRepoUrls.length === 0) {
            alert('Mohon tambahkan setidaknya satu URL repositori mahasiswa.');
            return;
        }

        // Tampilkan indikator loading dan sembunyikan hasil sebelumnya
        loadingIndicator.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        noResultsDiv.classList.add('hidden');
        mhVsGhResultsTableBody.innerHTML = '';

        try {
            // Siapkan FormData untuk mengirim data ke backend
            const formData = new FormData();
            formData.append('student_repo_urls', JSON.stringify(studentRepoUrls));
            formData.append('github_urls', JSON.stringify(githubUrls));

            // Kirim permintaan POST ke backend
            const response = await fetch('/analyze_code', {
                method: 'POST',
                body: formData
            });

            // Periksa apakah respons HTTP berhasil
            if (!response.ok) {
                const errorData = await response.json(); // Coba parsing error JSON
                const errorMessage = errorData.error || `Kesalahan tidak diketahui (Status: ${response.status})`;
                throw new Error(errorMessage);
            }

            const data = await response.json(); // Parsing respons JSON dari backend

            displayResults(data.mh_vs_gh_results); // Tampilkan hasil analisis
        } catch (error) {
            console.error('Error during analysis:', error);
            alert(`Terjadi kesalahan saat analisis: ${error.message}`);
        } finally {
            loadingIndicator.classList.add('hidden'); // Selalu sembunyikan indikator loading
        }
    });

    // Event listener untuk tombol "Hapus Semua File Mahasiswa"
    clearStudentFilesBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/clear_mahasiswa_files', { method: 'POST' });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! Status: ${response.status}. Message: ${errorData.error || 'Unknown error'}`);
            }
            alert('Semua file mahasiswa di server berhasil dihapus.');
            studentRepoUrls = []; // Kosongkan array di frontend
            updateStudentRepoList(); // Perbarui UI
            resultsSection.classList.add('hidden'); // Sembunyikan hasil
        } catch (error) {
            console.error('Error clearing student files:', error);
            alert(`Gagal menghapus file mahasiswa: ${error.message}.`);
        }
    });

    // Event listener untuk tombol "Hapus Semua File GitHub"
    clearGithubFilesBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/clear_github_files', { method: 'POST' });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! Status: ${response.status}. Message: ${errorData.error || 'Unknown error'}`);
            }
            alert('Semua file GitHub di server berhasil dihapus.');
            githubUrls = []; // Kosongkan array di frontend
            updateGithubUrlList(); // Perbarui UI
            resultsSection.classList.add('hidden'); // Sembunyikan hasil
        } catch (error) {
            console.error('Error clearing GitHub files:', error);
            alert(`Gagal menghapus file GitHub: ${e.message}.`);
        }
    });

    // === 6. Initial UI Setup (Pengaturan UI Awal) ===
    // Panggil fungsi update untuk menampilkan status awal daftar URL
    updateStudentRepoList();
    updateGithubUrlList();
});