document.addEventListener('DOMContentLoaded', () => {
    // === DOM Elements ===
    const studentCodeInput = document.getElementById('studentCodeInput');
    const fileList = document.getElementById('fileList');
    const githubUrlInput = document.getElementById('githubUrlInput');
    const addGithubUrlButton = document.getElementById('addGithubUrl');
    const githubUrlList = document.getElementById('githubUrlList');
    const runAnalysisButton = document.getElementById('runAnalysisButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('results-section');
    const mhVsGhResultsTableBody = document.querySelector('#mhVsGhResults tbody');
    const mhVsMhResultsTableBody = document.querySelector('#mhVsMhResults tbody');
    const noResultsDiv = document.getElementById('noResults');

    // === Data Storage ===
    let studentFiles = []; // Stores File objects
    let githubUrls = [];   // Stores string URLs

    // === Functions ===

    // Function to update student file list in UI
    function updateFileList() {
        fileList.innerHTML = ''; // Clear current list
        if (studentFiles.length === 0) {
            fileList.innerHTML = '<p style="color: #6c757d;">Belum ada file yang dipilih.</p>';
            return;
        }
        studentFiles.forEach((file, index) => {
            const p = document.createElement('p');
            p.textContent = file.name;
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'X';
            removeBtn.classList.add('remove-file-btn');
            removeBtn.addEventListener('click', () => {
                studentFiles.splice(index, 1); // Remove from array
                updateFileList(); // Update UI
            });
            p.appendChild(removeBtn);
            fileList.appendChild(p);
        });
    }

    // Function to update GitHub URL list in UI
    function updateGithubUrlList() {
        githubUrlList.innerHTML = ''; // Clear current list
        if (githubUrls.length === 0) {
            githubUrlList.innerHTML = '<p style="color: #6c757d;">Belum ada URL GitHub yang ditambahkan.</p>';
            return;
        }
        githubUrls.forEach((url, index) => {
            const p = document.createElement('p');
            p.textContent = url;
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'X';
            removeBtn.classList.add('remove-file-btn');
            removeBtn.addEventListener('click', () => {
                githubUrls.splice(index, 1); // Remove from array
                updateGithubUrlList(); // Update UI
            });
            p.appendChild(removeBtn);
            githubUrlList.appendChild(p);
        });
    }

    // Function to display results in tables
    function displayResults(mhVsGhData, mhVsMhData) {
        mhVsGhResultsTableBody.innerHTML = ''; // Clear previous results
        mhVsMhResultsTableBody.innerHTML = ''; // Clear previous results

        let hasSignificantResults = false;

        // Mahasiswa vs GitHub
        mhVsGhData.sort((a, b) => b.score - a.score); // Sort by score descending
        mhVsGhData.forEach(result => {
            if (result.score > 0) { // Only show results with score > 0%
                hasSignificantResults = true;
                const row = mhVsGhResultsTableBody.insertRow();
                if (result.score >= 70) { // Highlight high similarity
                    row.classList.add('high-similarity');
                }
                row.insertCell().textContent = result.source_file;
                row.insertCell().textContent = result.compared_file;
                row.insertCell().textContent = `${result.score}%`;
            }
        });

        // Mahasiswa vs Mahasiswa
        mhVsMhData.sort((a, b) => b.score - a.score); // Sort by score descending
        mhVsMhData.forEach(result => {
            if (result.score > 0) { // Only show results with score > 0%
                hasSignificantResults = true;
                const row = mhVsMhResultsTableBody.insertRow();
                if (result.score >= 70) { // Highlight high similarity
                    row.classList.add('high-similarity');
                }
                row.insertCell().textContent = result.file1;
                row.insertCell().textContent = result.file2;
                row.insertCell().textContent = `${result.score}%`;
            }
        });

        if (!hasSignificantResults) {
            noResultsDiv.classList.remove('hidden');
        } else {
            noResultsDiv.classList.add('hidden');
        }
        resultsSection.classList.remove('hidden'); // Show results section
    }

    // === Event Listeners ===

    // Handle student file input change
    studentCodeInput.addEventListener('change', (event) => {
        // Convert FileList to Array and add to studentFiles
        studentFiles = Array.from(event.target.files);
        updateFileList();
    });

    // Handle add GitHub URL button click
    addGithubUrlButton.addEventListener('click', () => {
        const url = githubUrlInput.value.trim();
        if (url && !githubUrls.includes(url)) { // Check if URL is not empty and not a duplicate
            githubUrls.push(url);
            githubUrlInput.value = ''; // Clear input
            updateGithubUrlList();
        } else if (url && githubUrls.includes(url)) {
            alert('URL ini sudah ada dalam daftar.');
        } else {
            alert('Silakan masukkan URL GitHub yang valid.');
        }
    });

    // Handle Run Analysis Button click
    runAnalysisButton.addEventListener('click', async () => {
        if (studentFiles.length === 0) {
            alert('Mohon unggah setidaknya satu file kode mahasiswa.');
            return;
        }

        // if (githubUrls.length === 0) {
        //     alert('Mohon tambahkan setidaknya satu URL GitHub.');
        //     return;
        // }

        loadingIndicator.classList.remove('hidden');
        resultsSection.classList.add('hidden'); // Hide previous results
        noResultsDiv.classList.add('hidden'); // Hide no results message
        mhVsGhResultsTableBody.innerHTML = ''; // Clear any residual data
        mhVsMhResultsTableBody.innerHTML = ''; // Clear any residual data

        try {
            const formData = new FormData();
            studentFiles.forEach(file => {
                formData.append('student_files', file); // 'student_files' adalah nama field di backend
            });
            formData.append('github_urls', JSON.stringify(githubUrls)); // Kirim URL sebagai JSON string

            // Mengirim permintaan POST ke backend Flask Anda
            const response = await fetch('/analyze_code', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) { // Check for HTTP errors (e.g., 404, 500)
                const errorData = await response.json(); // Coba parse error response
                throw new Error(`HTTP error! Status: ${response.status}. Message: ${errorData.error || 'Unknown error'}`);
            }

            const data = await response.json(); // Parse respons JSON dari backend

            displayResults(data.mh_vs_gh_results, data.mh_vs_mh_results); // Tampilkan data NYATA
        } catch (error) {
            console.error('Error during analysis:', error);
            alert(`Terjadi kesalahan saat analisis: ${error.message}. Silakan cek konsol browser untuk detail.`);
        } finally {
            loadingIndicator.classList.add('hidden'); // Selalu sembunyikan indikator loading
        }
    });

    // Initial UI updates
    updateFileList();
    updateGithubUrlList();
});