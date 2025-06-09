document.addEventListener('DOMContentLoaded', () => {
    // === DOM Elements === (No new changes, just a reminder)
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
    const noResultsDiv = document.getElementById('noResults');

    const clearStudentFilesBtn = document.getElementById('clearStudentFilesBtn');
    const clearGithubFilesBtn = document.getElementById('clearGithubFilesBtn');

    // NEW: Modal related DOM elements
    const codeCompareModal = document.getElementById('codeCompareModal');
    const modalFilenameMhs = document.getElementById('modal-filename-mhs');
    const modalFilenameGh = document.getElementById('modal-filename-gh');
    const codeMhsPre = document.getElementById('code-mhs');
    const codeGhPre = document.getElementById('code-gh');
    // NEW: Get the close button
    const closeButton = document.querySelector('.close-button');


    // NEW: Scroll synchronization for code panes
    const codePaneMhs = document.querySelector('.code-pane:nth-child(1)');
    const codePaneGh = document.querySelector('.code-pane:nth-child(2)');
    let isScrollingMhs = false;
    let isScrollingGh = false;

    codePaneMhs.addEventListener('scroll', () => {
        if (!isScrollingGh) {
            isScrollingMhs = true;
            codePaneGh.scrollTop = codePaneMhs.scrollTop;
        }
        isScrollingGh = false;
    });

    codePaneGh.addEventListener('scroll', () => {
        if (!isScrollingMhs) {
            isScrollingGh = true;
            codeMhsPre.scrollTop = codePaneGh.scrollTop; // Fix: use codeMhsPre.scrollTop
        }
        isScrollingMhs = false;
    });


    // === Data Storage ===
    let studentRepoUrls = [];
    let githubUrls = [];
    // Store full results with similar blocks for later display
    let lastAnalysisResults = [];

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

    // Function to display results in tables (UPDATED to include "Lihat Kode" button)
    function displayResults(mhVsGhData) {
        mhVsGhResultsTableBody.innerHTML = '';

        let hasSignificantResults = false;
        lastAnalysisResults = mhVsGhData; // Save results for modal access

        mhVsGhData.sort((a, b) => b.score - a.score);
        mhVsGhData.forEach((result, index) => {
            if (result.score > 0) {
                hasSignificantResults = true;
                const row = mhVsGhResultsTableBody.insertRow();
                if (result.score >= 70) {
                    row.classList.add('high-similarity');
                }
                row.insertCell().textContent = result.source_file;
                row.insertCell().textContent = result.compared_file;
                row.insertCell().textContent = `${result.score}%`;
                
                // Add "Lihat Kode" button
                const actionCell = row.insertCell();
                const viewCodeBtn = document.createElement('button');
                viewCodeBtn.textContent = 'Lihat Kode';
                viewCodeBtn.classList.add('view-code-btn');
                viewCodeBtn.setAttribute('data-index', index); // Store index to retrieve full result
                viewCodeBtn.onclick = () => openCodeCompareModal(index); // Attach event listener
                actionCell.appendChild(viewCodeBtn);
            }
        });

        if (!hasSignificantResults) {
            noResultsDiv.classList.remove('hidden');
        } else {
            noResultsDiv.classList.add('hidden');
        }
        resultsSection.classList.remove('hidden');
    }

    // NEW: Function to open code comparison modal
    async function openCodeCompareModal(resultIndex) {
        const result = lastAnalysisResults[resultIndex];
        if (!result) return;

        modalFilenameMhs.textContent = result.source_file;
        modalFilenameGh.textContent = result.compared_file;
        
        codeMhsPre.innerHTML = 'Memuat kode...';
        codeGhPre.innerHTML = 'Memuat kode...';
        codeCompareModal.style.display = 'block'; // Show the modal

        try {
            // Fetch code content for student file
            const responseMhs = await fetch('/get_code_content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: result.source_file, file_type: 'mahasiswa' })
            });
            const dataMhs = await responseMhs.json();
            const codeMhs = dataMhs.content;

            // Fetch code content for GitHub file
            const responseGh = await fetch('/get_code_content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: result.compared_file, file_type: 'github' })
            });
            const dataGh = await responseGh.json();
            const codeGh = dataGh.content;

            // Display and highlight code
            displayAndHighlightCode(codeMhs, result.similar_blocks_mhs, codeMhsPre);
            displayAndHighlightCode(codeGh, result.similar_blocks_gh, codeGhPre);

            // Apply highlight.js
            hljs.highlightElement(codeMhsPre);
            hljs.highlightElement(codeGhPre);

        } catch (error) {
            console.error("Error fetching code content:", error);
            codeMhsPre.textContent = "Gagal memuat kode.";
            codeGhPre.textContent = "Gagal memuat kode.";
            alert("Gagal memuat konten kode. Pastikan file ada di server.");
        }
    }

    // NEW: Function to display code with line numbers and highlighting
    function displayAndHighlightCode(codeContent, similarBlocks, preElement) {
        let highlightedHtml = '';
        const lines = codeContent.split('\n');
        
        lines.forEach((line, index) => {
            const lineNumber = index + 1;
            let lineClass = '';
            
            // Check if this line falls within any similar block
            for (const block of similarBlocks) {
                if (lineNumber >= block.start && lineNumber <= block.end) {
                    lineClass = 'highlight-code-line';
                    break;
                }
            }
            
            // Add line numbers (optional, if you want it)
            highlightedHtml += `<span class="line-number">${lineNumber}.</span><span class="line-content ${lineClass}">${escapeHtml(line)}</span>\n`;
        });
        
        preElement.innerHTML = highlightedHtml;
    }

    // Helper to escape HTML for security when setting innerHTML
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

    // NEW: Function to close modal
    function closeModal() {
        codeCompareModal.style.display = 'none';
        // Clear code content when closing
        codeMhsPre.innerHTML = ''; // Changed from textContent to innerHTML for hljs
        codeGhPre.innerHTML = ''; // Changed from textContent to innerHTML for hljs
    }

    // === Event Listeners === (NO CONFIRMATION PROMPT)

    // Add event listener for the close button
    closeButton.addEventListener('click', closeModal);

    // Also close modal if user clicks outside of modal content
    window.addEventListener('click', (event) => {
        if (event.target == codeCompareModal) {
            closeModal();
        }
    });

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

    // Handle Run Analysis Button click (UPDATED to store full results)
    runAnalysisButton.addEventListener('click', async () => {
        if (studentRepoUrls.length === 0) {
            alert('Mohon tambahkan setidaknya satu URL repositori mahasiswa.');
            return;
        }

        loadingIndicator.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        noResultsDiv.classList.add('hidden');
        mhVsGhResultsTableBody.innerHTML = '';

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

            displayResults(data.mh_vs_gh_results); // This now internally saves results
        } catch (error) {
            console.error('Error during analysis:', error);
            alert(`Terjadi kesalahan saat analisis: ${error.message}`);
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    });

    // Clear Buttons Logic - REMOVED CONFIRMATION
    clearStudentFilesBtn.addEventListener('click', async () => {
        // Confirmation prompt removed
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
        // Confirmation prompt removed
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

    // Initial UI updates
    updateStudentRepoList();
    updateGithubUrlList();
});
