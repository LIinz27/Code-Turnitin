// Global variables
let currentClassroom = null;
let currentAssignment = null;
let downloadedFiles = [];

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
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    progressContainer.style.display = 'block';
    progressFill.style.width = percentage + '%';
    progressText.textContent = text;
    
    if (percentage >= 100) {
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 2000);
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
    container.innerHTML = '<p class="status-info" style="display: block;">Loading assignments...</p>';
    
    try {
        const response = await fetch(`/api/classroom/${classroomId}/assignments`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayAssignments(data.assignments);
        } else {
            container.innerHTML = `<p class="status-error" style="display: block;">Error: ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Error loading assignments:', error);
        container.innerHTML = '<p class="status-error" style="display: block;">Error loading assignments</p>';
    }
}

function displayAssignments(assignments) {
    const container = document.getElementById('assignments-container');
    
    if (assignments.length === 0) {
        container.innerHTML = '<p class="status-info" style="display: block;">No assignments found in this classroom.</p>';
        return;
    }
    
    let html = '';
    assignments.forEach(assignment => {
        const deadline = assignment.deadline ? new Date(assignment.deadline).toLocaleDateString() : 'No deadline';
        const students = assignment.accepted || 0;
        
        html += `
            <div class="assignment-card" onclick="selectAssignment(${assignment.id})">
                <div class="assignment-title">${assignment.title}</div>
                <div class="assignment-meta">
                    <strong>Type:</strong> ${assignment.type || 'Individual'} | 
                    <strong>Deadline:</strong> ${deadline} | 
                    <strong>Students:</strong> ${students}
                </div>
                <div class="assignment-description">
                    ${assignment.slug ? `<strong>Slug:</strong> ${assignment.slug}<br>` : ''}
                    <strong>Language:</strong> ${assignment.language || 'Not specified'}
                </div>
                <button class="btn btn-secondary" onclick="event.stopPropagation(); selectAssignment(${assignment.id})">
                    Select This Assignment
                </button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function selectAssignment(assignmentId) {
    // Find assignment in current data
    currentAssignment = { id: assignmentId };
    
    // Show download controls
    const downloadControls = document.getElementById('download-controls');
    downloadControls.classList.remove('hidden');
    
    // Highlight selected assignment
    document.querySelectorAll('.assignment-card').forEach(card => {
        card.style.border = '1px solid #ddd';
    });
    
    event.target.closest('.assignment-card').style.border = '2px solid #667eea';
    
    showStatus(`Assignment ${assignmentId} selected. Ready to download.`, 'success');
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
            
            displayResults(data);
            showStatus(`Successfully downloaded ${downloadedFiles.length} files`, 'success');
            
            document.getElementById('view-results-btn').style.display = 'inline-block';
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
        <div class="grid">
            <div>
                <h4>Download Summary</h4>
                <p><strong>Assignment ID:</strong> ${currentAssignment.id}</p>
                <p><strong>Total Files:</strong> ${data.files ? data.files.length : 0}</p>
                <p><strong>Download Time:</strong> ${new Date().toLocaleString()}</p>
            </div>
            <div>
                <h4>Next Steps</h4>
                <p>Files have been downloaded to the server. You can now:</p>
                <ul>
                    <li>Run similarity analysis</li>
                    <li>Export results</li>
                    <li>View individual files</li>
                </ul>
            </div>
        </div>
    `;
    
    // Files list
    if (data.files && data.files.length > 0) {
        const filesHtml = data.files.map(file => 
            `<div class="file-item">📄 ${file}</div>`
        ).join('');
        filesElement.innerHTML = filesHtml;
    } else {
        filesElement.innerHTML = '<p>No files were downloaded.</p>';
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
