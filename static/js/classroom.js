// Global variables
let currentClassroom = null;
let currentAssignment = null;
let downloadedFiles = [];
let assignmentsData = [];

console.log('Classroom.js loaded successfully');

// Test function to verify JavaScript is working
function testFunction() {
    console.log('Test function called - JavaScript is working!');
    alert('JavaScript is working!');
}

// Test fetch function to verify network connectivity
async function testFetch() {
    console.log('Testing fetch...');
    try {
        const response = await fetch('/api/classroom/list');
        console.log('Fetch response:', response);
        const data = await response.json();
        console.log('Fetch data:', data);
        alert(`Fetch test successful! Found ${data.classrooms ? data.classrooms.length : 0} classrooms`);
    } catch (error) {
        console.error('Fetch test error:', error);
        alert(`Fetch test failed: ${error.message}`);
    }
}

async function checkTokenInfo() {
    console.log('Checking token info...');
    showStatus('Checking GitHub token permissions...', 'info');
    
    try {
        const response = await fetch('/api/classroom/token-info');
        const data = await response.json();
        
        if (data.success) {
            const tokenInfo = data.token_info;
            let message = '';
            let detailsHtml = '';
            let statusType = 'info';
            
            if (tokenInfo.status === 'success') {
                message = `GitHub Token Information for: ${tokenInfo.user}`;
                statusType = tokenInfo.can_access_private ? 'success' : 'error';
                
                detailsHtml = `
                    <div class="space-y-3">
                        <div>
                            <strong>User:</strong> ${tokenInfo.user}<br>
                            <strong>Can access private repositories:</strong> ${tokenInfo.can_access_private ? '✅ Yes' : '❌ No'}<br>
                            <strong>Token scopes:</strong> ${tokenInfo.scopes.length > 0 ? tokenInfo.scopes.join(', ') : 'No scopes detected'}
                        </div>
                        
                        <div>
                            <strong>Recommendations:</strong>
                            ${tokenInfo.recommendations.map(rec => `
                                <div class="mt-2 p-2 border-l-4 ${rec.issue.includes('Good') ? 'border-green-400 bg-green-50' : 'border-orange-400 bg-orange-50'}">
                                    <strong>${rec.issue}:</strong> ${rec.description}<br>
                                    <em>${rec.solution}</em>
                                </div>
                            `).join('')}
                        </div>
                        
                        ${!tokenInfo.can_access_private ? `
                            <div class="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                                <strong>⚠️ Limited Access:</strong> Your token cannot access private repositories. 
                                To access private classroom repositories, create a new token with "repo" scope.
                            </div>
                        ` : ''}
                    </div>
                `;
            } else {
                message = '❌ Error checking token';
                statusType = 'error';
                detailsHtml = `<p>Unable to verify token permissions: ${tokenInfo.message}</p>`;
            }
            
            showDetailedStatus(message, detailsHtml, statusType);
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error checking token info:', error);
        showStatus('Error connecting to server', 'error');
    }
}

// Utility functions
function showLoading(elementId) {
    const textElement = document.getElementById(elementId + '-text');
    const loadingElement = document.getElementById(elementId + '-loading');
    
    if (textElement) textElement.classList.add('hidden');
    if (loadingElement) loadingElement.classList.remove('hidden');
}

function hideLoading(elementId) {
    const textElement = document.getElementById(elementId + '-text');
    const loadingElement = document.getElementById(elementId + '-loading');
    
    if (textElement) textElement.classList.remove('hidden');
    if (loadingElement) loadingElement.classList.add('hidden');
}

function showStatus(message, type = 'info') {
    const statusElement = document.getElementById('status-message');
    if (!statusElement) {
        console.log('Status:', message, '(Type:', type + ')');
        return;
    }
    
    statusElement.className = `mt-4 p-3 rounded-md`;
    
    if (type === 'success') {
        statusElement.className += ' bg-green-100 text-green-800 border border-green-200';
    } else if (type === 'error') {
        statusElement.className += ' bg-red-100 text-red-800 border border-red-200';
    } else {
        statusElement.className += ' bg-blue-100 text-blue-800 border border-blue-200';
    }
    
    statusElement.textContent = message;
    statusElement.classList.remove('hidden');
    
    // Auto hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            statusElement.classList.add('hidden');
        }, 5000);
    }
}

function updateProgress(percentage, text) {
    const shell = document.getElementById('progress-shell');
    const fill = document.getElementById('progress-fill');
    const label = document.getElementById('progress-text');
    const percent = document.getElementById('progress-percent');
    
    if (!shell || !fill || !label || !percent) {
        console.log('Progress elements not found, skipping progress update');
        return;
    }
    
    shell.style.display = 'flex';
    fill.style.width = percentage + '%';
    label.textContent = text || 'Processing...';
    percent.textContent = Math.min(100, Math.max(0, Math.round(percentage))) + '%';
    
    if (percentage >= 100) {
        setTimeout(() => { 
            shell.style.display = 'none'; 
        }, 2200);
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
    console.log('loadClassroom function called');
    const classroomUrl = document.getElementById('classroom-url').value.trim();
    console.log('Classroom URL:', classroomUrl);
    
    if (!classroomUrl) {
        showStatus('Please enter a classroom URL or ID', 'error');
        return;
    }
    
    showLoading('load-classroom');
    
    try {
        console.log('Making API request to /api/classroom/load');
        console.log('Request body:', JSON.stringify({ classroom_url: classroomUrl }));
        
        const response = await fetch('/api/classroom/load', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                classroom_url: classroomUrl
            })
        });
        
        console.log('Response received:', response);
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (!response.ok) {
            console.log('Response not OK, status:', response.status);
            const errorText = await response.text();
            console.log('Error response text:', errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            displayClassroomInfo(data.classroom);
            loadAssignments(data.classroom.id);
            showStatus('Classroom loaded successfully', 'success');
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Detailed error in loadClassroom:', error);
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        
        // More specific error messages
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showStatus('Cannot connect to server. Please check if the server is running.', 'error');
        } else if (error.message.includes('NetworkError')) {
            showStatus('Network error. Please check your connection.', 'error');
        } else {
            showStatus(`Error: ${error.message}`, 'error');
        }
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
    
    if (nameElement) {
        nameElement.textContent = classroom.name;
    }
    
    if (descElement) {
        descElement.innerHTML = `
            <strong>ID:</strong> ${classroom.id}<br>
            <strong>Organization:</strong> ${classroom.organization ? classroom.organization.login : 'N/A'}<br>
            <strong>URL:</strong> <a href="${classroom.url}" target="_blank">${classroom.url}</a>
        `;
    }
    
    if (infoElement) {
        infoElement.classList.remove('hidden');
    }
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
        const assignmentsSection = document.getElementById('assignments-section');
        
        if (skeleton) skeleton.style.display = 'none';
        
        if (!assignments || !assignments.length) {
                if (container) {
                    container.innerHTML = '<p class="status-info" style="display:block;">Tidak ada assignment pada classroom ini.</p>';
                }
                if (countBadge && countBadge.classList) { 
                    countBadge.classList.add('hidden'); 
                }
                return;
        }
        
        if (countBadge && countBadge.classList) { 
            countBadge.textContent = assignments.length + ' items'; 
            countBadge.classList.remove('hidden'); 
        }
        
        // Show assignments section
        if (assignmentsSection && assignmentsSection.classList) {
            assignmentsSection.classList.remove('hidden');
        }
        
        if (!container) {
            console.error('assignments-container not found');
            return;
        }
        
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
                            <div class="flex gap-2">
                                <button class="g-btn text-[0.5rem] check-access-btn" type="button" onclick="checkRepositoryAccess('${a.repository?.full_name || ''}', '${a.title}')">Check Access</button>
                                <button class="g-btn text-[0.5rem] pick-btn" type="button">Pilih</button>
                            </div>
                        </div>
                        <div class="subtext mt-2">
                            ${a.slug ? `<span class="chip">${a.slug}</span>` : ''}
                            ${a.language ? `<span class="chip">${a.language}</span>` : ''}
                            ${a.repository?.full_name ? `<span class="chip">📁 ${a.repository.full_name}</span>` : ''}
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
    if (downloadControls) {
        downloadControls.classList.remove('hidden');
    }
    
    // Remove selection from all cards
    document.querySelectorAll('.assignment-card').forEach(card => {
        if (card.classList) {
            card.classList.remove('selected');
        }
    });
    
    // Add selection to current card
    const active = document.querySelector(`.assignment-card[data-id='${assignmentId}']`);
    if (active && active.classList) {
        active.classList.add('selected');
    }
    
    showStatus(`Assignment ${assignmentId} dipilih. Siap untuk proses.`, 'success');
}

async function checkRepositoryAccess(repoFullName, assignmentTitle) {
    if (!repoFullName) {
        showStatus('Repository information not available', 'error');
        return;
    }
    
    console.log('Checking access for repository:', repoFullName);
    showStatus(`Checking access to ${repoFullName}...`, 'info');
    
    try {
        const response = await fetch('/api/classroom/check-access', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repository: repoFullName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayAccessInfo(data, assignmentTitle);
        } else {
            showStatus(`Error checking access: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error checking repository access:', error);
        showStatus('Error connecting to server', 'error');
    }
}

function displayAccessInfo(accessData, assignmentTitle) {
    const accessibility = accessData.accessibility;
    const tokenInfo = accessData.token_info;
    const accessGuide = accessData.access_guide;
    
    let statusClass = 'info';
    let statusMessage = '';
    let detailsHtml = '';
    
    switch (accessibility.status) {
        case 'public':
            statusClass = 'success';
            statusMessage = `✅ Repository "${assignmentTitle}" is accessible (Public)`;
            detailsHtml = '<p>This repository can be downloaded without any issues.</p>';
            break;
            
        case 'private_accessible':
            statusClass = 'success';
            statusMessage = `✅ Repository "${assignmentTitle}" is accessible (Private)`;
            detailsHtml = '<p>You have access to this private repository.</p>';
            break;
            
        case 'private_no_access':
            statusClass = 'error';
            statusMessage = `❌ Repository "${assignmentTitle}" is private and cannot be accessed`;
            detailsHtml = generateAccessGuideHtml(accessGuide);
            break;
            
        case 'not_found':
            statusClass = 'error';
            statusMessage = `❌ Repository "${assignmentTitle}" not found or no access`;
            detailsHtml = generateAccessGuideHtml(accessGuide);
            break;
            
        default:
            statusClass = 'error';
            statusMessage = `❓ Unknown access status for "${assignmentTitle}"`;
            detailsHtml = '<p>Unable to determine repository accessibility.</p>';
    }
    
    // Add token information
    if (tokenInfo.status === 'success') {
        detailsHtml += `
            <div class="mt-4 p-3 bg-gray-100 dark:bg-gray-700 rounded">
                <h4 class="font-semibold">Token Information:</h4>
                <p>User: ${tokenInfo.user}</p>
                <p>Can access private repos: ${tokenInfo.can_access_private ? 'Yes' : 'No'}</p>
                ${tokenInfo.recommendations.map(rec => `
                    <div class="mt-2">
                        <strong>${rec.issue}:</strong> ${rec.description}<br>
                        <em>Solution: ${rec.solution}</em>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Create modal or detailed status display
    showDetailedStatus(statusMessage, detailsHtml, statusClass);
}

function generateAccessGuideHtml(accessGuide) {
    if (!accessGuide) return '<p>No access guide available.</p>';
    
    return `
        <div class="mt-3">
            <h4 class="font-semibold mb-2">How to gain access:</h4>
            ${accessGuide.access_methods.map((method, index) => `
                <div class="mb-3 p-2 border-l-4 border-blue-300">
                    <strong>Method ${index + 1}: ${method.method}</strong>
                    <p class="text-sm">${method.description}</p>
                    <ol class="text-sm mt-1 ml-4">
                        ${method.steps.map(step => `<li>• ${step}</li>`).join('')}
                    </ol>
                </div>
            `).join('')}
            
            <div class="mt-4">
                <h5 class="font-semibold">Troubleshooting:</h5>
                <ul class="text-sm mt-1">
                    ${accessGuide.troubleshooting.map(tip => `<li>• ${tip}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;
}

function showDetailedStatus(message, detailsHtml, type = 'info') {
    const statusElement = document.getElementById('status-message');
    if (!statusElement) {
        console.log('Detailed Status:', message, 'Type:', type);
        console.log('Details:', detailsHtml);
        return;
    }
    
    statusElement.className = `mt-4 p-3 rounded-md max-w-full`;
    
    if (type === 'success') {
        statusElement.className += ' bg-green-100 text-green-800 border border-green-200';
    } else if (type === 'error') {
        statusElement.className += ' bg-red-100 text-red-800 border border-red-200';
    } else {
        statusElement.className += ' bg-blue-100 text-blue-800 border border-blue-200';
    }
    
    statusElement.innerHTML = `
        <div class="font-semibold mb-2">${message}</div>
        <div class="text-sm">${detailsHtml}</div>
    `;
    statusElement.classList.remove('hidden');
    
    // Auto hide success messages after 10 seconds
    if (type === 'success') {
        setTimeout(() => {
            statusElement.classList.add('hidden');
        }, 10000);
    }
}

async function previewRepositories() {
    if (!currentAssignment) {
        showStatus('Please select an assignment first', 'error');
        return;
    }
    
    if (!currentClassroom || !currentClassroom.id) {
        showStatus('Classroom information not available', 'error');
        return;
    }
    
    showLoading('preview');
    
    try {
        const response = await fetch(`/api/classroom/${currentClassroom.id}/assignments/${currentAssignment.id}/preview`);
        const data = await response.json();
        
        if (data.success) {
            showPreviewModal(data.preview);
        } else {
            showStatus(`Preview failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error previewing repositories:', error);
        showStatus(`Preview failed: ${error.message}`, 'error');
    } finally {
        hideLoading('preview');
    }
}

function showPreviewModal(previewData) {
    const modal = document.getElementById('preview-modal');
    const content = document.getElementById('preview-content');
    
    if (!modal || !content) {
        // Create modal if it doesn't exist
        createPreviewModal();
        return showPreviewModal(previewData);
    }
    
    // Safely access data with fallbacks
    const assignment = previewData.assignment || {};
    const repositories = previewData.repositories || [];
    const accessSummary = previewData.access_summary || {};
    
    let accessSummaryHtml = '';
    if (accessSummary && accessSummary.total && accessSummary.total > 0) {
        // Calculate accessible repositories (public + private_accessible)
        const accessible = (accessSummary.public || 0) + (accessSummary.private_accessible || 0);
        const privateNoAccess = accessSummary.private_no_access || 0;
        const notFound = accessSummary.not_found || 0;
        const total = accessSummary.total || 0;
        
        accessSummaryHtml = `
            <div class="access-summary p-4 rounded-lg mb-4">
                <h4 class="font-semibold text-gray-700 dark:text-gray-300 mb-3">Access Summary</h4>
                <div class="space-y-2">
                    <div class="access-summary-item">
                        <span class="text-gray-600 dark:text-gray-400">Total repositories:</span>
                        <span class="font-semibold text-gray-900 dark:text-white">${total}</span>
                    </div>
                    <div class="access-summary-item">
                        <span class="text-gray-600 dark:text-gray-400">Accessible:</span>
                        <span class="font-semibold text-green-600">${accessible}</span>
                    </div>
                    <div class="access-summary-item">
                        <span class="text-gray-600 dark:text-gray-400">Private (no access):</span>
                        <span class="font-semibold text-red-600">${privateNoAccess}</span>
                    </div>
                    <div class="access-summary-item">
                        <span class="text-gray-600 dark:text-gray-400">Not found:</span>
                        <span class="font-semibold text-yellow-600">${notFound}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    let repositoriesHtml = '';
    if (repositories.length > 0) {
        repositoriesHtml = repositories.map(repo => {
            const statusColor = getAccessStatusColor(repo.accessibility.status);
            const studentsList = repo.students ? repo.students.join(', ') : 'Unknown';
            
            return `
                <div class="border rounded-lg p-4 mb-3">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <h4 class="font-semibold text-gray-900">
                                <a href="${repo.html_url}" target="_blank" class="text-blue-600 hover:text-blue-800">
                                    ${repo.full_name}
                                </a>
                            </h4>
                            <p class="text-sm text-gray-600 mt-1">Students: ${studentsList}</p>
                            <p class="text-sm text-gray-500 mt-1">Estimated files: ${repo.estimated_files}</p>
                        </div>
                        <div class="ml-4 flex flex-col items-end gap-1">
                            <span class="${statusColor}">
                                ${getAccessStatusText(repo.accessibility.status)}
                            </span>
                            ${repo.private ? '<span class="repo-status-badge status-private">Private</span>' : '<span class="repo-status-badge status-accessible">Public</span>'}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        repositoriesHtml = '<p class="text-gray-500 text-center py-8">No repositories found for this assignment.</p>';
    }
    
    content.innerHTML = `
        <div class="mb-6">
            <h3 class="text-xl font-bold text-gray-900 mb-2">Preview: ${assignment.title}</h3>
            <p class="text-gray-600">Assignment Type: ${assignment.type}</p>
            <p class="text-gray-600">Discovery Method: ${previewData.method_used}</p>
            <p class="text-gray-600">Total Estimated Files: ${previewData.total_estimated_files}</p>
        </div>
        
        ${accessSummaryHtml}
        
        <div class="mb-6">
            <h4 class="font-semibold text-gray-700 mb-3">Repositories (${repositories.length})</h4>
            <div class="max-h-96 overflow-y-auto">
                ${repositoriesHtml}
            </div>
        </div>
        
        <div class="flex justify-end space-x-3">
            <button onclick="closePreviewModal()" class="px-4 py-2 text-gray-600 bg-gray-200 rounded-lg hover:bg-gray-300">
                Cancel
            </button>
            <button onclick="proceedWithDownload()" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Proceed with Download
            </button>
        </div>
    `;
    
    modal.classList.remove('hidden');
}

function getAccessStatusColor(status) {
    switch (status) {
        case 'public':
        case 'private_accessible':
            return 'repo-status-badge status-accessible';
        case 'private_no_access':
            return 'repo-status-badge status-no-access';
        case 'not_found':
            return 'repo-status-badge status-not-found';
        default:
            return 'repo-status-badge status-private';
    }
}

function getAccessStatusText(status) {
    switch (status) {
        case 'public': return 'Public';
        case 'private_accessible': return 'Accessible';
        case 'private_no_access': return 'No Access';
        case 'not_found': return 'Not Found';
        default: return 'Unknown';
    }
}

function createPreviewModal() {
    const modalHtml = `
        <div id="preview-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 hidden">
            <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-screen overflow-hidden">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-xl font-bold text-gray-900">Repository Preview</h2>
                        <button onclick="closePreviewModal()" class="text-gray-400 hover:text-gray-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div id="preview-content">
                        <!-- Content will be populated by showPreviewModal -->
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closePreviewModal() {
    const modal = document.getElementById('preview-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function proceedWithDownload() {
    closePreviewModal();
    downloadAndAnalyze();
}

async function downloadAndAnalyze() {
    if (!currentAssignment) {
        showStatus('Please select an assignment first', 'error');
        return;
    }
    
    showLoading('download');
    updateProgress(0, 'Starting download...');
    
    try {
        const payload = {
            assignment_id: currentAssignment.id
        };
        if (currentClassroom && currentClassroom.id) {
            payload.classroom_id = currentClassroom.id;
        }

        const response = await fetch('/api/classroom/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
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
    console.log('Page loaded, initializing...');
    
    // Don't auto-discover on page load to avoid showing errors immediately
    // User can click Auto Discover manually if needed
    
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
