document.addEventListener('DOMContentLoaded', () => {
  const studentInput = document.getElementById('studentRepoUrlInput');
  const studentAddBtn = document.getElementById('addStudentRepoUrl');
  const studentList = document.getElementById('studentRepoUrlList');

  const githubInput = document.getElementById('githubUrlInput');
  const githubAddBtn = document.getElementById('addGithubUrl');
  const githubList = document.getElementById('githubUrlList');

  const runBtn = document.getElementById('runAnalysisButton');
  const loading = document.getElementById('loadingIndicator');
  const resultSection = document.getElementById('results-section');
  const tableBody = document.getElementById('mhVsGhResults');
  const noResult = document.getElementById('noResults');

  const modal = document.getElementById('codeCompareModal');
  const codeMhs = document.getElementById('code-mhs');
  const codeGh = document.getElementById('code-gh');

  let studentUrls = [];
  let githubUrls = [];
  let lastResults = [];

  function updateList(listEl, urls) {
    listEl.innerHTML = urls.length ? '' : '<p class="italic">Belum ada URL ditambahkan</p>';
    urls.forEach((url, idx) => {
      const p = document.createElement('p');
      p.className = "text-sm flex justify-between items-center border-b py-1";
      p.innerHTML = `<span>${url}</span><button class="text-red-500" data-index="${idx}">&times;</button>`;
      p.querySelector('button').onclick = () => {
        urls.splice(idx, 1);
        updateList(listEl, urls);
      };
      listEl.appendChild(p);
    });
  }

  studentAddBtn.onclick = () => {
    const url = studentInput.value.trim();
    if (url && !studentUrls.includes(url)) {
      studentUrls.push(url);
      studentInput.value = '';
      updateList(studentList, studentUrls);
    }
  };

  githubAddBtn.onclick = () => {
    const url = githubInput.value.trim();
    if (url && !githubUrls.includes(url)) {
      githubUrls.push(url);
      githubInput.value = '';
      updateList(githubList, githubUrls);
    }
  };

  runBtn.onclick = async () => {
    if (!studentUrls.length) {
      alert('Tambahkan minimal satu URL mahasiswa.');
      return;
    }

    loading.classList.remove('hidden');
    resultSection.classList.add('hidden');
    tableBody.innerHTML = '';
    noResult.classList.add('hidden');

    const formData = new FormData();
    formData.append('student_repo_urls', JSON.stringify(studentUrls));
    formData.append('github_urls', JSON.stringify(githubUrls));

    try {
      const res = await fetch('/analyze_code', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      lastResults = data.mh_vs_gh_results || [];
      displayResults(lastResults);
    } catch (err) {
      console.error(err);
      alert('Gagal menjalankan analisis.');
    } finally {
      loading.classList.add('hidden');
    }
  };

  function displayResults(results) {
    if (!results.length) {
      noResult.classList.remove('hidden');
      return;
    }

    const sortedResults = results.slice().sort((a, b) => b.score - a.score);

    sortedResults.forEach((r, idx) => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td class="p-2">${r.source_file}</td>
        <td class="p-2">${r.compared_file}</td>
        <td class="p-2">${r.score}%</td>
        <td class="p-2 text-right"><button class="bg-blue-500 text-white px-3 py-1 rounded text-sm" data-idx="${idx}">Lihat</button></td>
      `;
      row.querySelector('button').onclick = () => openModal(results.indexOf(r));
      tableBody.appendChild(row);
    });

    resultSection.classList.remove('hidden');
  }

  async function openModal(index) {
    const result = lastResults[index];
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.classList.remove('opacity-0', 'scale-95');
    requestAnimationFrame(() => modal.classList.add('opacity-100', 'scale-100'));
    codeMhs.innerHTML = 'Memuat...';
    codeGh.innerHTML = 'Memuat...';

    try {
      const [resM, resG] = await Promise.all([
        fetch('/get_code_content', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: result.source_file, file_type: 'mahasiswa' })
        }),
        fetch('/get_code_content', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: result.compared_file, file_type: 'github' })
        })
      ]);
      const dataM = await resM.json();
      const dataG = await resG.json();

      displayAndHighlightCode(dataM.content, result.similar_blocks_mhs, codeMhs);
      displayAndHighlightCode(dataG.content, result.similar_blocks_gh, codeGh);
    } catch (err) {
      console.error(err);
      codeMhs.textContent = 'Gagal memuat.';
      codeGh.textContent = 'Gagal memuat.';
    }
  }

  function displayAndHighlightCode(codeContent, blocks, target) {
    const lines = codeContent.split('\n');
    let html = '';

    lines.forEach((line, index) => {
      const lineNum = index + 1;
      const isHighlighted = blocks.some(block => lineNum >= block.start && lineNum <= block.end);
      const lineClass = isHighlighted ? 'highlight-code-line' : '';
      html += `<span class="line-number">${lineNum}.</span><span class="line-content ${lineClass}">${escapeHtml(line)}</span>\n`;
    });

    target.innerHTML = html;
    target.parentElement.scrollTop = 0;
  }

  function escapeHtml(text) {
    const map = {
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }

  function closeModal() {
    modal.classList.remove('opacity-100', 'scale-100');
    modal.classList.add('opacity-0', 'scale-95');
    setTimeout(() => {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }, 200);
  }

  document.querySelector('.close-button').addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  let isScrollingMhs = false;
  let isScrollingGh = false;

  codeMhs.parentElement.addEventListener('scroll', () => {
    if (!isScrollingGh) {
      isScrollingMhs = true;
      codeGh.parentElement.scrollTop = codeMhs.parentElement.scrollTop;
    }
    isScrollingMhs = false;
  });

  codeGh.parentElement.addEventListener('scroll', () => {
    if (!isScrollingMhs) {
      isScrollingGh = true;
      codeMhs.parentElement.scrollTop = codeGh.parentElement.scrollTop;
    }
    isScrollingGh = false;
  });
});
