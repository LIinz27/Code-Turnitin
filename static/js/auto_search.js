document.addEventListener('DOMContentLoaded', () => {
  const studentInput = document.getElementById('studentRepoUrlInput');
  const addBtn = document.getElementById('addStudentRepoUrl');
  const listEl = document.getElementById('studentRepoUrlList');
  const runBtn = document.getElementById('runAutoSearch');
  const loading = document.getElementById('autoSearchLoading');
  const candidatesSection = document.getElementById('candidatesSection');
  const candidatesContainer = document.getElementById('candidatesContainer');
  const candidatesForm = document.getElementById('candidatesForm');
  const confirmBtn = document.getElementById('confirmSelection');
  const resultsSection = document.getElementById('autoResultsSection');
  const resultsBody = document.getElementById('autoResultsBody');
  const exportBtn = document.getElementById('exportJsonBtn');
  const compareModal = document.getElementById('autoCompareModal');
  const autoCodeMhs = document.getElementById('autoCodeMhs');
  const autoCodeGh = document.getElementById('autoCodeGh');
  const autoModalTitle = document.getElementById('autoModalTitle');

  let studentUrls = [];
  let cacheId = null;
  let candidates = [];
  let lastAutoResults = [];

  function updateList() {
    listEl.innerHTML = studentUrls.length ? '' : '<p class="italic">Belum ada URL ditambahkan</p>';
    studentUrls.forEach((u, i) => {
      const p = document.createElement('p');
      p.className = 'text-sm flex justify-between items-center border-b py-1';
      p.innerHTML = `<span>${u}</span><button class="text-red-500" data-i="${i}">&times;</button>`;
      p.querySelector('button').onclick = () => { studentUrls.splice(i,1); updateList(); };
      listEl.appendChild(p);
    });
  }

  addBtn.onclick = () => {
    const url = studentInput.value.trim();
    if (url && !studentUrls.includes(url)) {
      studentUrls.push(url);
      studentInput.value = '';
      updateList();
    }
  };

  runBtn.onclick = async () => {
    if (!studentUrls.length) {
      alert('Tambahkan minimal satu URL mahasiswa.');
      return;
    }
    loading.classList.remove('hidden');
    candidatesSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    candidatesContainer.innerHTML = '';
    try {
      const res = await fetch('/auto_search/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_repo_urls: studentUrls })
      });
      const data = await res.json();
      cacheId = data.cache_id;
      candidates = data.candidates || [];
      if (!candidates.length) {
        alert('Tidak ada kandidat ditemukan.');
        return;
      }
      renderCandidates();
    } catch (e) {
      console.error(e);
      alert('Gagal melakukan pencarian otomatis.');
    } finally {
      loading.classList.add('hidden');
    }
  };

  function renderCandidates() {
    candidatesContainer.innerHTML = '';
    candidatesSection.classList.remove('hidden');
    candidates.forEach((c, idx) => {
      const div = document.createElement('div');
      div.className = 'border p-3 rounded flex flex-col gap-1 bg-gray-50';
      div.innerHTML = `
        <label class="flex items-start gap-2">
          <input type="checkbox" class="mt-1" data-idx="${idx}" checked />
          <div>
            <p class="font-semibold">${c.full_name} <span class="text-xs text-gray-500">(skor: ${(c.score*100).toFixed(1)}%)</span></p>
            <p class="text-xs text-gray-600">Tokens: ${Object.keys(c.matched_tokens).slice(0,8).join(', ') || '-'} </p>
            <p class="text-xs text-gray-600">Files hit: ${c.files.length} | Size: ${c.size_kb} KB | Stars: ${c.stars}</p>
          </div>
        </label>`;
      candidatesContainer.appendChild(div);
    });
  }

  candidatesForm.onsubmit = async (e) => {
    e.preventDefault();
    if (!cacheId) return;
    const selected = [];
    candidatesContainer.querySelectorAll('input[type=checkbox]').forEach((cb) => {
      if (cb.checked) {
        const idx = parseInt(cb.getAttribute('data-idx'));
        selected.push(candidates[idx].full_name);
      }
    });
    if (!selected.length) {
      alert('Pilih minimal satu repositori.');
      return;
    }
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Memproses...';
    try {
      const res = await fetch('/auto_search/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cache_id: cacheId, selected_repos: selected })
      });
      const data = await res.json();
      const results = data.mh_vs_auto_results || [];
      renderResults(results);
    } catch (err) {
      console.error(err);
      alert('Gagal mengunduh dan menganalisis repositori terpilih');
    } finally {
      confirmBtn.disabled = false;
      confirmBtn.textContent = 'Konfirmasi & Unduh';
    }
  };

  function renderResults(results) {
    resultsBody.innerHTML = '';
    if (!results.length) {
      resultsBody.innerHTML = '<tr><td colspan="3" class="p-3 text-center italic text-gray-500">Tidak ada hasil.</td></tr>';
    } else {
      results.sort((a,b)=> b.score - a.score).forEach((r, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td class="p-2">${r.source_file}</td><td class="p-2">${r.compared_file}</td><td class="p-2">${r.score}%</td><td class="p-2"><button class="px-2 py-1 bg-blue-500 text-white rounded text-xs" data-idx="${idx}">Lihat</button></td>`;
        tr.querySelector('button').onclick = ()=> openCompare(idx, results);
        resultsBody.appendChild(tr);
      });
    }
    resultsSection.classList.remove('hidden');
    lastAutoResults = results;
  }
  function openCompare(index, arr){
    const r = arr[index];
    if(!r) return;
    autoModalTitle.textContent = `${r.source_file} vs ${r.compared_file} (${r.score}%)`;
    autoCodeMhs.textContent = 'Memuat...';
    autoCodeGh.textContent = 'Memuat...';
    compareModal.classList.remove('hidden');
    fetch('/get_code_content', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ filename: r.source_file, file_type: 'mahasiswa' })})
      .then(res=>res.json()).then(d=> displayHighlighted(d.content, r.similar_blocks_mhs, autoCodeMhs));
    fetch('/get_code_content', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ filename: r.compared_file, file_type: 'github' })})
      .then(res=>res.json()).then(d=> displayHighlighted(d.content, r.similar_blocks_gh, autoCodeGh));
  }
  function displayHighlighted(content, blocks, target){
    if(!content){ target.textContent='(kosong)'; return; }
    const lines = content.split('\n');
    let html='';
    lines.forEach((line,i)=>{
      const ln = i+1;
      const highlight = blocks && blocks.some(b=> ln>=b.start && ln<=b.end);
      html += `<span class='line-number'>${ln}.</span><span class='line-content ${highlight?'highlight-code-line':''}'>${escapeHtml(line)}</span>\n`;
    });
    target.innerHTML = html;
    target.parentElement.scrollTop = 0;
  }
  function escapeHtml(text){
    const m={'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#039;'};
    return text.replace(/[&<>"']/g, c=> m[c]);
  }
  document.querySelector('.auto-close-modal')?.addEventListener('click', ()=> compareModal.classList.add('hidden'));
  compareModal?.addEventListener('click', e=> { if(e.target===compareModal) compareModal.classList.add('hidden'); });
  document.addEventListener('keydown', e=> { if(e.key==='Escape') compareModal.classList.add('hidden'); });
  exportBtn?.addEventListener('click', ()=>{
    if(!lastAutoResults.length){ alert('Belum ada hasil.'); return; }
    const blob = new Blob([JSON.stringify({generated_at: new Date().toISOString(), results: lastAutoResults}, null, 2)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'auto_search_results.json';
    a.click();
    URL.revokeObjectURL(a.href);
  });
});
