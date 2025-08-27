// Global variables
let currentClassroom = null;
let currentAssignment = null;
let downloadedFiles = [];
let assignmentsData = [];

// Utility functions
function showLoading(elementId) {
    document.getElementById(elementId + '-text').classList.add('hidden');
    document.getElementById(elementId + '-loading').classList.remove('hidden');
}

function hideLoading(elementId) {
    document.getElementById(elementId + '-text').classList.remove('hidden');
    document.getElementById(elementId + '-loading').classList.add('hidden');
}

function showStatus(message, type = 'info') {
    const statusElement = document.getElementById('status-message');
    statusElement.className = `status-message status-${type}`;
    statusElement.textContent = message;
    statusElement.style.display = 'block';
    
    // Auto hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 5000);
    }
}

function updateProgress(percentage, text) {
    const shell = document.getElementById('progress-shell');
    const fill = document.getElementById('progress-fill');
    const label = document.getElementById('progress-text');
    const percent = document.getElementById('progress-percent');
    if (!shell) return;
    shell.style.display = 'flex';
    fill.style.width = percentage + '%';
    label.textContent = text || 'Processing...';
    percent.textContent = Math.min(100, Math.max(0, Math.round(percentage))) + '%';
    if (percentage >= 100) {
        setTimeout(()=> { shell.style.display = 'none'; }, 2200);
    }
}

// Main functions
async function autoDiscoverClassrooms() {
    showLoading('auto-discover');
    
    try {
        const response = await fetch('/api/classroom/list', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            populateClassroomSelect(data.classrooms);
            showStatus(`Found ${data.classrooms.length} accessible classrooms`, 'success');
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error auto-discovering classrooms:', error);
        showStatus('Error connecting to server', 'error');
    } finally {
        hideLoading('auto-discover');
    }
}

function populateClassroomSelect(classrooms) {
    const select = document.getElementById('classroom-select');
    select.innerHTML = '<option value="">-- Pilih Classroom --</option>';
    
    classrooms.forEach(classroom => {
        const option = document.createElement('option');
        option.value = classroom.id;
        option.textContent = `${classroom.name} (ID: ${classroom.id})`;
        option.dataset.classroom = JSON.stringify(classroom);
        select.appendChild(option);
    });
}

async function loadClassroom() {
    const classroomUrl = document.getElementById('classroom-url').value.trim();
    
    if (!classroomUrl) {
        showStatus('Please enter a classroom URL or ID', 'error');
        return;
    }
    
    showLoading('load-classroom');
    
    try {
        const response = await fetch('/api/classroom/load', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                classroom_url: classroomUrl
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayClassroomInfo(data.classroom);
            loadAssignments(data.classroom.id);
            showStatus('Classroom loaded successfully', 'success');
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error loading classroom:', error);
        showStatus('Error connecting to server', 'error');
    } finally {
        hideLoading('load-classroom');
    }
}

function selectClassroom() {
    const select = document.getElementById('classroom-select');
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption.value) {
        const classroom = JSON.parse(selectedOption.dataset.classroom);
        displayClassroomInfo(classroom);
        loadAssignments(classroom.id);
        
        // Update URL input for consistency
        document.getElementById('classroom-url').value = classroom.id;
    }
}

function displayClassroomInfo(classroom) {
    currentClassroom = classroom;
    
    const infoElement = document.getElementById('classroom-info');
    const nameElement = document.getElementById('classroom-name');
    const descElement = document.getElementById('classroom-description');
    
    nameElement.textContent = classroom.name;
    descElement.innerHTML = `
        <strong>ID:</strong> ${classroom.id}<br>
        <strong>Organization:</strong> ${classroom.organization ? classroom.organization.login : 'N/A'}<br>
        <strong>URL:</strong> <a href="${classroom.url}" target="_blank">${classroom.url}</a>
    `;
    
    infoElement.classList.remove('hidden');
}

async function loadAssignments(classroomId) {
    const container = document.getElementById('assignments-container');
    const skeleton = document.getElementById('assignments-placeholder');
    const hint = document.getElementById('assignments-hint');
    if (skeleton) skeleton.style.display = 'grid';
    if (hint) { hint.style.display = 'none'; }
    
    try {
        const response = await fetch(`/api/classroom/${classroomId}/assignments`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
                if (data.success) {
                        assignmentsData = data.assignments || [];
                        displayAssignments(assignmentsData);
        } else {
                        if (skeleton) skeleton.style.display = 'none';
                        container.innerHTML = `<p class="status-error status-message" style="display:block;">Error: ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Error loading assignments:', error);
                if (skeleton) skeleton.style.display = 'none';
                container.innerHTML = '<p class="status-error status-message" style="display:block;">Error loading assignments</p>';
    }
}

function displayAssignments(assignments) {
        const container = document.getElementById('assignments-container');
        const skeleton = document.getElementById('assignments-placeholder');
        const countBadge = document.getElementById('assignmentCount');
        if (skeleton) skeleton.style.display = 'none';
        if (!assignments || !assignments.length) {
                container.innerHTML = '<p class="status-info" style="display:block;">Tidak ada assignment pada classroom ini.</p>';
                if (countBadge) { countBadge.classList.add('hidden'); }
                return;
        }
        if (countBadge) { countBadge.textContent = assignments.length + ' items'; countBadge.classList.remove('hidden'); }
        const frag = document.createDocumentFragment();
        assignments.forEach(a => {
                const card = document.createElement('div');
                card.className = 'assignment-card fade-in-up';
                card.dataset.id = a.id;
                const deadline = a.deadline ? new Date(a.deadline).toLocaleDateString() : 'No deadline';
                card.innerHTML = `
                        <div class="flex items-start justify-between gap-4">
                            <div>
                                <div class="assignment-title">${a.title}</div>
                                <div class="assignment-meta subtext">
                                     ${a.type || 'Individual'} • ${deadline} • ${a.accepted || 0} students
                                </div>
                            </div>
                            <button class="g-btn text-[0.5rem] pick-btn" type="button">Pilih</button>
                        </div>
                        <div class="subtext mt-2">
                            ${a.slug ? `<span class="chip">${a.slug}</span>` : ''}
                            ${a.language ? `<span class="chip">${a.language}</span>` : ''}
                        </div>`;
                card.addEventListener('click', () => selectAssignment(a.id));
                card.querySelector('.pick-btn').addEventListener('click', (e)=> { e.stopPropagation(); selectAssignment(a.id); });
                frag.appendChild(card);
        });
        // clear previous (preserve container wrapper & hint removal already done)
        container.querySelectorAll('.assignment-card').forEach(n=> n.remove());
        container.appendChild(frag);
}

function selectAssignment(assignmentId) {
    const chosen = assignmentsData.find(a => a.id === assignmentId) || { id: assignmentId };
    currentAssignment = { id: chosen.id };
    const downloadControls = document.getElementById('download-controls');
    if (downloadControls) downloadControls.classList.remove('hidden');
    document.querySelectorAll('.assignment-card').forEach(card => card.classList.remove('selected'));
    const active = document.querySelector(`.assignment-card[data-id='${assignmentId}']`);
    if (active) active.classList.add('selected');
    showStatus(`Assignment ${assignmentId} dipilih. Siap untuk proses.`, 'success');
}

async function downloadAndAnalyze() {
    if (!currentAssignment) {
        showStatus('Please select an assignment first', 'error');
        return;
    }
    
    showLoading('download');
    updateProgress(0, 'Starting download...');
    
    try {
        const response = await fetch('/api/classroom/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                assignment_id: currentAssignment.id
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateProgress(100, 'Download completed!');
            downloadedFiles = data.files || [];
            document.getElementById('quick-sim-btn').style.display = 'inline-block';
            document.getElementById('view-results-btn').style.display = 'inline-block';
            displayResults(data);
            showStatus(`Successfully downloaded ${downloadedFiles.length} files`, 'success');
        } else {
            updateProgress(0, 'Download failed');
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error downloading assignment:', error);
        updateProgress(0, 'Download failed');
        showStatus('Error connecting to server', 'error');
    } finally {
        hideLoading('download');
    }
}

function displayResults(data) {
    const resultsSection = document.getElementById('results-section');
    const summaryElement = document.getElementById('analysis-summary');
    const filesElement = document.getElementById('downloaded-files');
    
    // Summary
        summaryElement.innerHTML = `
                <div class="grid gap-6 md:grid-cols-2">
                    <div class="subtext space-y-1">
                        <p><strong>Assignment:</strong> ${currentAssignment.id}</p>
                        <p><strong>Total Files:</strong> ${data.files ? data.files.length : 0}</p>
                        <p><strong>Downloaded:</strong> ${new Date().toLocaleTimeString()}</p>
                    </div>
                    <div class="subtext space-y-1">
                        <p>Next:</p>
                        <p>1. Jalankan similarity</p>
                        <p>2. Buka hasil utama</p>
                        <p>3. Export JSON</p>
                    </div>
                </div>`;
    
    // Files list
    if (data.files && data.files.length > 0) {
        const filesHtml = data.files.map(file => {
            const ext = file.split('.').pop().toLowerCase();
            return `<div class="file-item">📄 <span>${file}</span><span class="ext">${ext}</span></div>`;
        }).join('');
        filesElement.innerHTML = filesHtml;
    } else {
        filesElement.innerHTML = '<p class="subtext">No files were downloaded.</p>';
    }
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function viewAnalysisResults() {
    // Redirect to main analysis page with classroom data
    const params = new URLSearchParams({
        source: 'classroom',
        assignment_id: currentAssignment.id,
        files_count: downloadedFiles.length
    });
    
    window.open(`/?${params.toString()}`, '_blank');
}

async function runSimilarityCheck() {
    if (downloadedFiles.length === 0) {
        showStatus('No files to analyze. Download assignment files first.', 'error');
        return;
    }
    
    showStatus('Starting similarity analysis...', 'info');
    
    try {
        const response = await fetch('/api/similarity/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source: 'classroom',
                assignment_id: currentAssignment.id
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('Similarity analysis completed! Redirecting to results...', 'success');
            setTimeout(() => {
                viewAnalysisResults();
            }, 1000);
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error running similarity check:', error);
        showStatus('Error running similarity analysis', 'error');
    }
}

function exportResults() {
    if (downloadedFiles.length === 0) {
        showStatus('No data to export', 'error');
        return;
    }
    
    // Create export data
    const exportData = {
        classroom: currentClassroom,
        assignment: currentAssignment,
        files: downloadedFiles,
        timestamp: new Date().toISOString()
    };
    
    // Download as JSON
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `classroom_export_${currentAssignment.id}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    showStatus('Export downloaded successfully', 'success');
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Auto-discover classrooms on page load
    autoDiscoverClassrooms();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            if (currentAssignment) {
                downloadAndAnalyze();
            } else if (document.getElementById('classroom-url').value) {
                loadClassroom();
            }
        }
    });
});
