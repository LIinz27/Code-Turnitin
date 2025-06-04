document.addEventListener('DOMContentLoaded', () => {
    // === DOM Elements ===
    const studentRepoUrlInput = document.getElementById('studentRepoUrlInput');
    const addStudentRepoUrlButton = document.getElementById('addStudentRepoUrl');
    const studentRepoUrlList = document.getElementById('studentRepoUrlList');

    const githubUrlInput = document.getElementById('githubUrlInput');
    const addGithubUrlButton = document.getElementById('addGithubUrl');
    const githubUrlList = document.getElementById('githubUrlList');
    const runAnalysisButton = document.getElementById('runAnalysisButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('results-section');
    const mhVsGhResultsTableBody = document.querySelector('#mhVsGhResults tbody');
    // REMOVED: const mhVsMhResultsTableBody = document.querySelector('#mhVsMhResults tbody');
    const noResultsDiv = document.getElementById('noResults');

    const clearStudentFilesBtn = document.getElementById('clearStudentFilesBtn');
    const clearGithubFilesBtn = document.getElementById('clearGithubFilesBtn');

    // === Data Storage ===
    let studentRepoUrls = [];
    let githubUrls = [];

    // === Functions ===

    // updateStudentRepoList - NO CHANGES
    function updateStudentRepoList() {
        studentRepoUrlList.innerHTML = '';
        if (studentRepoUrls.length === 0) {
            studentRepoUrlList.innerHTML = '<p style="color: #6c757d;">Belum ada URL repositori mahasiswa yang ditambahkan.</p>';
            clearStudentFilesBtn.classList.add('hidden');
        } else {
            studentRepoUrls.forEach((url, index) => {
                const p = document.createElement('p');
                p.textContent = url;
                const removeBtn = document.createElement('button');
                removeBtn.textContent = 'X';
                removeBtn.classList.add('remove-file-btn');
                removeBtn.addEventListener('click', () => {
                    studentRepoUrls.splice(index, 1);
                    updateStudentRepoList();
                });
                p.appendChild(removeBtn);
                studentRepoUrlList.appendChild(p);
            });
            clearStudentFilesBtn.classList.remove('hidden');
        }
    }

    // updateGithubUrlList - NO CHANGES
    function updateGithubUrlList() {
        githubUrlList.innerHTML = '';
        if (githubUrls.length === 0) {
            githubUrlList.innerHTML = '<p style="color: #6c757d;">Belum ada URL repositori GitHub yang ditambahkan.</p>';
            clearGithubFilesBtn.classList.add('hidden');
        } else {
            githubUrls.forEach((url, index) => {
                const p = document.createElement('p');
                p.textContent = url;
                const removeBtn = document.createElement('button');
                removeBtn.textContent = 'X';
                removeBtn.classList.add('remove-file-btn');
                removeBtn.addEventListener('click', () => {
                    githubUrls.splice(index, 1);
                    updateGithubUrlList();
                });
                p.appendChild(removeBtn);
                githubUrlList.appendChild(p);
            });
            clearGithubFilesBtn.classList.remove('hidden');
        }
    }

    // Function to display results in tables (UPDATED)
    function displayResults(mhVsGhData) { // REMOVED mhVsMhData parameter
        mhVsGhResultsTableBody.innerHTML = ''; // Clear previous results
        // REMOVED: mhVsMhResultsTableBody.innerHTML = ''; // Clear previous results

        let hasSignificantResults = false;

        // Mahasiswa vs GitHub
        mhVsGhData.sort((a, b) => b.score - a.score);
        mhVsGhData.forEach(result => {
            if (result.score > 0) {
                hasSignificantResults = true;
                const row = mhVsGhResultsTableBody.insertRow();
                if (result.score >= 70) {
                    row.classList.add('high-similarity');
                }
                row.insertCell().textContent = result.source_file;
                row.insertCell().textContent = result.compared_file;
                row.insertCell().textContent = `${result.score}%`;
            }
        });

        // REMOVED: Mahasiswa vs Mahasiswa section
        // mhVsMhData.sort((a, b) => b.score - a.score);
        // mhVsMhData.forEach(result => {
        //     if (result.score > 0) {
        //         hasSignificantResults = true;
        //         const row = mhVsMhResultsTableBody.insertRow();
        //         if (result.score >= 70) {
        //             row.classList.add('high-similarity');
        //         }
        //         row.insertCell().textContent = result.file1;
        //         row.insertCell().textContent = result.file2;
        //         row.insertCell().textContent = `${result.score}%`;
        //     }
        // });

        if (!hasSignificantResults) {
            noResultsDiv.classList.remove('hidden');
        } else {
            noResultsDiv.classList.add('hidden');
        }
        resultsSection.classList.remove('hidden');
    }

    // === Event Listeners ===

    // addStudentRepoUrlButton - NO CHANGES
    addStudentRepoUrlButton.addEventListener('click', () => {
        const url = studentRepoUrlInput.value.trim();
        if (!url.startsWith('https://github.com/')) {
            alert('Mohon masukkan URL repositori GitHub yang valid (diawali dengan https://github.com/).');
            return;
        }
        if (url && !studentRepoUrls.includes(url)) {
            studentRepoUrls.push(url);
            studentRepoUrlInput.value = '';
            updateStudentRepoList();
        } else if (url && studentRepoUrls.includes(url)) {
            alert('URL repositori ini sudah ada dalam daftar.');
        } else {
            alert('Silakan masukkan URL repositori mahasiswa yang valid.');
        }
    });

    // addGithubUrlButton - NO CHANGES
    addGithubUrlButton.addEventListener('click', () => {
        const url = githubUrlInput.value.trim();
        if (!url.startsWith('https://github.com/')) {
            alert('Mohon masukkan URL repositori GitHub yang valid (diawali dengan https://github.com/).');
            return;
        }
        if (url && !githubUrls.includes(url)) {
            githubUrls.push(url);
            githubUrlInput.value = '';
            updateGithubUrlList();
        } else if (url && githubUrls.includes(url)) {
            alert('URL ini sudah ada dalam daftar.');
        } else {
            alert('Silakan masukkan URL repositori GitHub yang valid.');
        }
    });

    // Handle Run Analysis Button click (UPDATED displayResults CALL)
    runAnalysisButton.addEventListener('click', async () => {
        if (studentRepoUrls.length === 0) {
            alert('Mohon tambahkan setidaknya satu URL repositori mahasiswa.');
            return;
        }

        loadingIndicator.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        noResultsDiv.classList.add('hidden');
        mhVsGhResultsTableBody.innerHTML = '';
        // REMOVED: mhVsMhResultsTableBody.innerHTML = '';

        try {
            const formData = new FormData();
            formData.append('student_repo_urls', JSON.stringify(studentRepoUrls));
            formData.append('github_urls', JSON.stringify(githubUrls));

            const response = await fetch('/analyze_code', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData.error || `Kesalahan tidak diketahui (Status: ${response.status})`;
                throw new Error(errorMessage);
            }

            const data = await response.json();

            displayResults(data.mh_vs_gh_results); // ONLY PASS ONE PARAMETER
        } catch (error) {
            console.error('Error during analysis:', error);
            alert(`Terjadi kesalahan saat analisis: ${error.message}`);
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    });

    // Clear Buttons Logic - NO CHANGES
    clearStudentFilesBtn.addEventListener('click', async () => {
        if (!confirm('Apakah Anda yakin ingin menghapus SEMUA file mahasiswa yang diunduh ke server? Ini tidak menghapus repositori GitHub asli.')) {
            return;
        }
        try {
            const response = await fetch('/clear_mahasiswa_files', { method: 'POST' });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! Status: ${response.status}. Message: ${errorData.error || 'Unknown error'}`);
            }
            alert('Semua file mahasiswa di server berhasil dihapus.');
            studentRepoUrls = [];
            updateStudentRepoList();
            resultsSection.classList.add('hidden');
        } catch (error) {
            console.error('Error clearing student files:', error);
            alert(`Gagal menghapus file mahasiswa: ${error.message}.`);
        }
    });

    clearGithubFilesBtn.addEventListener('click', async () => {
        if (!confirm('Apakah Anda yakin ingin menghapus SEMUA file GitHub yang diunduh ke server? Ini tidak menghapus repositori GitHub asli.')) {
            return;
        }
        try {
            const response = await fetch('/clear_github_files', { method: 'POST' });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! Status: ${response.status}. Message: ${errorData.error || 'Unknown error'}`);
            }
            alert('Semua file GitHub di server berhasil dihapus.');
            githubUrls = [];
            updateGithubUrlList();
            resultsSection.classList.add('hidden');
        } catch (error) {
            console.error('Error clearing GitHub files:', error);
            alert(`Gagal menghapus file GitHub: ${error.message}.`);
        }
    });

    // Initial UI updates - NO CHANGES
    updateStudentRepoList();
    updateGithubUrlList();
});