/**
 * Demo Interface JavaScript
 * Handles all client-side functionality for the Code Turnitin demo presentation
 */

function demoApp() {
    return {
        // Data properties
        selectedLanguage: '',
        searchQuery: '',
        repositories: [],
        selectedRepo: null,
        selectedAlgorithm: 'jaccard',
        candidates: [],
        selectedCandidates: [],
        analysisResults: null,
        statistics: null,
        isAnalyzing: false,
        isLoadingCandidates: false,
        enableCrossLanguage: false,  // New property for cross-language toggle

        // Detail modal properties
        showDetailModal: false,
        detailLoading: false,
        detailData: null,
        activeDetailTab: 'files',

        // File-by-file comparison properties
        selectedSourceFile: '',
        selectedTargetFile: '',
        currentFilePairData: null,
        isLoadingFilePair: false,

        // Helper functions for templates



        // Algorithm descriptions
        algorithmDescriptions: {
            'jaccard': 'Uses winnowing algorithm with Jaccard similarity from existing codebase',
            'cosine': 'Demo implementation of cosine similarity',
            'levenshtein': 'Demo implementation of edit distance'
        },

        // Initialize the app
        async init() {
            await this.loadRepositories();
            await this.refreshStatistics();
            
            // Load sample repositories on startup
            if (this.repositories.length > 0) {
                this.selectRepository(this.repositories[0]);
            }
        },

        // Load repositories based on current filters
        async loadRepositories() {
            try {
                const params = new URLSearchParams();
                if (this.selectedLanguage) params.append('language', this.selectedLanguage);
                if (this.searchQuery) params.append('search', this.searchQuery);

                const response = await fetch(`/demo/api/repositories?${params}`);
                const data = await response.json();
                
                this.repositories = data.repositories || [];
            } catch (error) {
                console.error('Error loading repositories:', error);
                this.showNotification('Error loading repositories', 'error');
            }
        },

        // Search repositories
        async searchRepositories() {
            // Debounce search
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(async () => {
                await this.loadRepositories();
            }, 300);
        },

        // Select a repository
        async selectRepository(repo) {
            this.selectedRepo = repo;
            this.selectedCandidates = [];
            this.analysisResults = null;
            
            await this.loadCandidates();
        },

        // Load comparison candidates for selected repository
        async loadCandidates() {
            if (!this.selectedRepo) return;

            this.isLoadingCandidates = true;
            try {
                const params = new URLSearchParams({
                    repo_id: this.selectedRepo.id,
                    limit: 50,
                    cross_language: this.enableCrossLanguage.toString()
                });
                
                const response = await fetch(`/demo/api/candidates?${params}`);
                const data = await response.json();
                
                this.candidates = data.candidates || [];
                
                // Auto-select first few candidates for demo
                if (this.candidates.length > 0) {
                    this.selectedCandidates = this.candidates.slice(0, Math.min(5, this.candidates.length))
                                                             .map(c => c.id);
                }
                
                // Show notification about cross-language mode
                if (this.enableCrossLanguage && data.candidates) {
                    const crossLangCount = data.candidates.filter(c => c.is_cross_language).length;
                    if (crossLangCount > 0) {
                        this.showNotification(`Found ${crossLangCount} cross-language repositories`, 'info');
                    }
                }
            } catch (error) {
                console.error('Error loading candidates:', error);
                this.showNotification('Error loading comparison candidates', 'error');
            } finally {
                this.isLoadingCandidates = false;
            }
        },

        // Handle cross-language toggle change
        handleCrossLanguageToggle() {
            // Clear current selections when toggling
            this.selectedCandidates = [];
            this.candidates = [];
            
            // Reload candidates with new setting
            if (this.selectedRepo) {
                this.loadCandidates();
            }
            
            // Show appropriate message
            if (this.enableCrossLanguage) {
                this.showNotification('Cross-language comparison enabled', 'success');
            } else {
                this.showNotification('Cross-language comparison disabled', 'info');
            }
        },

        // Perform similarity analysis
        async performAnalysis() {
            if (!this.selectedRepo || this.selectedCandidates.length === 0) {
                this.showNotification('Please select a repository and comparison candidates', 'warning');
                return;
            }

            this.isAnalyzing = true;
            this.analysisResults = null;

            try {
                const requestData = {
                    source_repo_id: this.selectedRepo.id,
                    target_repo_ids: this.selectedCandidates,
                    algorithm: this.selectedAlgorithm
                };

                const response = await fetch('/demo/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });

                if (!response.ok) {
                    throw new Error(`Analysis failed: ${response.statusText}`);
                }

                this.analysisResults = await response.json();

                // Show success notification
                const avgSimilarity = (this.analysisResults.summary.average_similarity * 100).toFixed(1);
                this.showNotification(`Analysis completed! Average similarity: ${avgSimilarity}%`, 'success');

                // Refresh statistics after analysis
                await this.refreshStatistics();

            } catch (error) {
                console.error('Error during analysis:', error);
                this.showNotification(`Analysis failed: ${error.message}`, 'error');
            } finally {
                this.isAnalyzing = false;
            }
        },

        // Refresh session statistics
        async refreshStatistics() {
            try {
                const response = await fetch('/demo/api/statistics');
                this.statistics = await response.json();
            } catch (error) {
                console.error('Error refreshing statistics:', error);
            }
        },

        // Get algorithm description
        getAlgorithmDescription() {
            return this.algorithmDescriptions[this.selectedAlgorithm] || 
                   'Advanced similarity detection algorithm';
        },

        // Get language color for display
        getLanguageColor(language) {
            const colors = {
                'Java': 'bg-red-500',
                'JavaScript': 'bg-yellow-500',
                'Python': 'bg-green-500',
                'TypeScript': 'bg-blue-500',
                'HTML': 'bg-orange-500',
                'CSS': 'bg-purple-500'
            };
            return colors[language] || 'bg-gray-500';
        },

        // Get similarity score color (neutral - always blue)
        getSimilarityColor(score) {
            return 'text-blue-600';
        },

        // Get similarity badge color (neutral - always blue)
        getSimilarityBadgeColor(level) {
            return 'bg-blue-100 text-blue-800';
        },

        // Get similarity bar color (neutral - always blue)
        getSimilarityBarColor(score) {
            return 'bg-blue-500';
        },

        // Format uptime display
        formatUptime(uptime) {
            if (!uptime) return '0:00:00';
            
            // Parse uptime string (format: H:MM:SS)
            const parts = uptime.split(':');
            if (parts.length === 3) {
                const hours = parseInt(parts[0]);
                const minutes = parseInt(parts[1]);
                const seconds = parseInt(parts[2]);
                
                if (hours > 0) {
                    return `${hours}h ${minutes}m`;
                } else if (minutes > 0) {
                    return `${minutes}m ${seconds}s`;
                } else {
                    return `${seconds}s`;
                }
            }
            
            return uptime;
        },

        // Show notification to user
        showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 ${this.getNotificationColor(type)}`;
            notification.innerHTML = `
                <div class="flex items-center">
                    <i class="fas ${this.getNotificationIcon(type)} mr-3"></i>
                    <span>${message}</span>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-current opacity-70 hover:opacity-100">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 5000);
        },

        // Get notification color classes
        getNotificationColor(type) {
            const colors = {
                'success': 'bg-green-500 text-white',
                'error': 'bg-red-500 text-white',
                'warning': 'bg-yellow-500 text-white',
                'info': 'bg-blue-500 text-white'
            };
            return colors[type] || colors.info;
        },

        // Get notification icon
        getNotificationIcon(type) {
            const icons = {
                'success': 'fa-check-circle',
                'error': 'fa-exclamation-circle',
                'warning': 'fa-exclamation-triangle',
                'info': 'fa-info-circle'
            };
            return icons[type] || icons.info;
        },

        // Export results (for presentation purposes)
        exportResults() {
            if (!this.analysisResults) {
                this.showNotification('No analysis results to export', 'warning');
                return;
            }

            const exportData = {
                timestamp: new Date().toISOString(),
                source_repository: this.analysisResults.source_repository,
                algorithm: this.analysisResults.algorithm,
                summary: this.analysisResults.summary,
                comparisons: this.analysisResults.comparisons,
                session_statistics: this.statistics
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `similarity_analysis_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showNotification('Analysis results exported successfully', 'success');
        },

        // Select all candidates
        selectAllCandidates() {
            this.selectedCandidates = this.candidates.map(candidate => candidate.id);
            this.showNotification(`Selected all ${this.candidates.length} candidates`, 'success');
        },

        // Deselect all candidates
        deselectAllCandidates() {
            this.selectedCandidates = [];
            this.showNotification('Deselected all candidates', 'info');
        },

        // Get repository count info based on current filter
        getRepositoryCountInfo() {
            if (!this.selectedLanguage) {
                return `${this.repositories.length} repositories (all languages)`;
            }
            return `${this.repositories.length} ${this.selectedLanguage} repositories`;
        },

        // Clear all selections (reset demo)
        resetDemo() {
            this.selectedRepo = null;
            this.selectedCandidates = [];
            this.analysisResults = null;
            this.searchQuery = '';
            this.selectedLanguage = '';
            this.loadRepositories();
            this.showNotification('Demo reset successfully', 'info');
        },

        // View detailed comparison between repositories
        async viewComparisonDetail(comparison) {
            try {
                this.showDetailModal = true;
                this.detailLoading = true;
                this.detailData = null;
                this.activeDetailTab = 'comparison';  // Set to comparison tab by default

                const sourceId = this.selectedRepo.id;
                const targetId = comparison.target_repository.id;

                const response = await fetch(`/demo/api/comparison-detail/${sourceId}/${targetId}`);
                
                if (!response.ok) {
                    throw new Error(`Failed to load detailed comparison: ${response.statusText}`);
                }

                this.detailData = await response.json();

            } catch (error) {
                console.error('Error loading detailed comparison:', error);
                this.showNotification(`Failed to load detailed comparison: ${error.message}`, 'error');
            } finally {
                this.detailLoading = false;
            }
        },

        // Close detail modal
        closeDetailModal() {
            this.showDetailModal = false;
            this.detailData = null;
            this.activeDetailTab = 'comparison';
            this.selectedSourceFile = '';
            this.selectedTargetFile = '';
            this.currentFilePairData = null;
        },

        // Initialize file-by-file comparison when detail modal opens
        initializeFileComparison() {
            if (this.detailData && this.detailData.side_by_side_comparison && 
                this.detailData.side_by_side_comparison.mode === 'file_by_file') {
                
                // Set default file pair if available
                const defaultPair = this.detailData.side_by_side_comparison.default_file_pair;
                if (defaultPair) {
                    this.selectedSourceFile = defaultPair.source_file;
                    this.selectedTargetFile = defaultPair.target_file;
                    this.currentFilePairData = defaultPair;
                }
            }
        },

        // Update file comparison when file selection changes
        async updateFileComparison() {
            if (!this.selectedSourceFile || !this.selectedTargetFile) {
                this.currentFilePairData = null;
                return;
            }

            if (!this.detailData) {
                return;
            }

            try {
                this.isLoadingFilePair = true;
                
                const sourceId = this.detailData.source_repository.id;
                const targetId = this.detailData.target_repository.id;
                
                // Use query parameters for file paths to avoid URL parsing issues
                const params = new URLSearchParams({
                    source_file: this.selectedSourceFile,
                    target_file: this.selectedTargetFile
                });

                const response = await fetch(`/demo/api/file-pair-comparison/${sourceId}/${targetId}?${params}`);
                
                if (!response.ok) {
                    throw new Error(`Failed to load file pair comparison: ${response.statusText}`);
                }

                this.currentFilePairData = await response.json();

            } catch (error) {
                console.error('Error loading file pair comparison:', error);
                this.showNotification(`Failed to load file comparison: ${error.message}`, 'error');
                this.currentFilePairData = null;
            } finally {
                this.isLoadingFilePair = false;
            }
        },

        // Select a specific file pair from quick selection
        selectFilePair(sourceFile, targetFile) {
            this.selectedSourceFile = sourceFile;
            this.selectedTargetFile = targetFile;
            this.updateFileComparison();
        },

        // Copy detailed comparison results to clipboard
        async copyDetailToClipboard() {
            if (!this.detailData) return;

            try {
                const summary = `Code Similarity Analysis Results
=============================================

Source Repository: ${this.detailData.source_repository.name}
Target Repository: ${this.detailData.target_repository.name}
Similarity: ${this.detailData.similarity.percentage.toFixed(1)}% (${this.detailData.similarity.level.toUpperCase()})
Algorithm: ${this.detailData.similarity.algorithm_name}

Statistics:
- Source Lines: ${this.detailData.comparison_stats ? this.detailData.comparison_stats.source_lines || 'N/A' : 'N/A'}
- Target Lines: ${this.detailData.comparison_stats ? this.detailData.comparison_stats.target_lines || 'N/A' : 'N/A'}
- Similar Lines: ${this.detailData.comparison_stats ? this.detailData.comparison_stats.similar_line_count || 'N/A' : 'N/A'}

Similar Blocks Found: ${this.detailData.code_comparison && this.detailData.code_comparison.similar_blocks ? this.detailData.code_comparison.similar_blocks.length : 0}

Analysis Date: ${new Date().toLocaleString()}
Generated by Code Turnitin Demo System`;

                await navigator.clipboard.writeText(summary);
                this.showNotification('Comparison results copied to clipboard!', 'success');
            } catch (error) {
                console.error('Error copying to clipboard:', error);
                this.showNotification('Failed to copy to clipboard', 'error');
            }
        },

        // Get similarity level class - neutral blue styling
        getSimilarityLevelClass(level) {
            // Return neutral blue styling for all levels
            return 'bg-blue-100 text-blue-800 border-blue-200';
        },

        // Get line highlight class - neutral blue styling
        getLineHighlightClass(highlightLevel) {
            const classes = {
                'high': 'bg-blue-50 border-l-4 border-blue-300',
                'medium': 'bg-blue-50 border-l-4 border-blue-300',
                'low': 'bg-blue-50 border-l-4 border-blue-300',
                'none': ''
            };
            return classes[highlightLevel] || '';
        },

        // Format similarity percentage for display
        formatSimilarityPercentage(similarity) {
            return (similarity * 100).toFixed(1) + '%';
        }
    };
}

// Global utility functions for demo
window.demoUtils = {
    // Format file size for display
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Failed to copy text: ', err);
            return false;
        }
    },

    // Download data as file
    downloadFile(data, filename, type = 'text/plain') {
        const blob = new Blob([data], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    // View detailed comparison between repositories
    async viewComparisonDetail(comparison) {
        try {
            this.showDetailModal = true;
            this.detailLoading = true;
            this.detailData = null;
            this.activeDetailTab = 'files';

            const sourceId = this.selectedRepo.id;
            const targetId = comparison.target_repository.id;

            const response = await fetch(`/demo/api/comparison-detail/${sourceId}/${targetId}`);
            
            if (!response.ok) {
                throw new Error(`Failed to load detailed comparison: ${response.statusText}`);
            }

            this.detailData = await response.json();
            
            // Initialize file-by-file comparison if available
            this.initializeFileComparison();

        } catch (error) {
            console.error('Error loading detailed comparison:', error);
            this.showNotification(`Failed to load detailed comparison: ${error.message}`, 'error');
        } finally {
            this.detailLoading = false;
        }
    },

    // Close detail modal
    closeDetailModal() {
        this.showDetailModal = false;
        this.detailData = null;
        this.activeDetailTab = 'files';
    },

    // Select file for comparison preview
    selectFileForComparison(file, type) {
        // Handle file selection
        const fileName = (typeof file === 'string') ? file : (file.path || file.name || 'Unnamed file');
        
        if (type === 'source') {
            this.selectedSourceFile = fileName;
        } else if (type === 'target') {
            this.selectedTargetFile = fileName;
        }
        
        // Show notification about file selection
        this.showNotification(`Selected ${type} file: ${fileName}`, 'info');
        
        // If both files are selected, could trigger comparison
        if (this.selectedSourceFile && this.selectedTargetFile && 
            this.detailData?.source_repository?.id && this.detailData?.target_repository?.id) {
            
            // Auto-trigger file pair comparison
            this.updateFileComparison();
        }
    },

    // Copy detailed comparison results to clipboard
    async copyDetailToClipboard() {
        if (!this.detailData) return;

        try {
            const summary = `Code Similarity Analysis Results
=============================================

Source Repository: ${this.detailData.source_repository.name}
Target Repository: ${this.detailData.target_repository.name}
Similarity: ${this.detailData.similarity.percentage.toFixed(1)}% (${this.detailData.similarity.level.toUpperCase()})
Algorithm: ${this.detailData.similarity.algorithm_name}

Statistics:
- Source Lines: ${this.detailData.comparison_stats.source_lines}
- Target Lines: ${this.detailData.comparison_stats.target_lines}
- Similar Lines: ${this.detailData.comparison_stats.similar_line_count}

Similar Blocks Found: ${this.detailData.code_comparison.similar_blocks?.length || 0}

Analysis Date: ${new Date().toLocaleString()}
Generated by Code Turnitin Demo System`;

            await navigator.clipboard.writeText(summary);
            this.showNotification('Comparison results copied to clipboard!', 'success');
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            this.showNotification('Failed to copy to clipboard', 'error');
        }
    }
};

// Initialize demo when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + R for reset (prevent default browser refresh)
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            if (window.Alpine && window.Alpine.raw) {
                const demoComponent = window.Alpine.raw(document.querySelector('[x-data="demoApp()"]').__x.$data);
                if (demoComponent && demoComponent.resetDemo) {
                    demoComponent.resetDemo();
                }
            }
        }
    });
});
