// JavaScript for Document Database Web Interface

const socket = io();

// Query history for arrow key navigation
let queryHistory = [];
let historyIndex = -1;

// Bible books mapping (loaded from API)
let bibleBookMap = {};

// Run when the DOM is ready
document.addEventListener("DOMContentLoaded", function() {
    // Load database info and history for arrow key navigation
    loadDatabaseInfo();
    loadQueryHistory();
    loadBibleBooks();

    // Handle query form submission
    document.getElementById("query-form").addEventListener("submit", handleQuery);
    document.getElementById("clear-btn").addEventListener("click", clearQuery);
    document.getElementById("export-confirm").addEventListener("click", exportResults);
    
    // Add arrow key navigation to query input
    const queryInput = document.getElementById("query-input");
    queryInput.addEventListener("keydown", handleQueryInputKeydown);
    
    // Add event delegation for Bible reference clicks
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('bible-reference')) {
            const reference = event.target.getAttribute('data-verse-ref');
            if (reference) {
                showVersePopup(reference);
            }
        }
    });
});

// Load and display database information
function loadDatabaseInfo() {
    fetch('/api/database-info')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const dbInfo = data.data;
                const databaseName = document.getElementById('database-name');
                if (databaseName) {
                    databaseName.textContent = `${dbInfo.database_name} (${dbInfo.database_id})`;
                    databaseName.title = dbInfo.database_description;
                }
            } else {
                console.error('Failed to load database info:', data.error);
                const databaseName = document.getElementById('database-name');
                if (databaseName) {
                    databaseName.textContent = 'Unknown Database';
                }
            }
        })
        .catch(error => {
            console.error('Error loading database info:', error);
            const databaseName = document.getElementById('database-name');
            if (databaseName) {
                databaseName.textContent = 'Error Loading';
            }
        });
}


// Load query history for arrow key navigation (no visual display)
function loadQueryHistory() {
    fetch("/api/history")
        .then(handleFetchResponse)
        .then(history => {
            // Extract just the query strings for navigation
            queryHistory = history.map(entry => entry.query).reverse(); // Most recent first
            historyIndex = -1; // Reset index
        })
        .catch(error => {
            console.error("Error loading query history:", error);
            queryHistory = [];
        });
}

// Handle arrow key navigation in query input
function handleQueryInputKeydown(event) {
    const queryInput = event.target;
    
    // Only handle arrow keys when cursor is at beginning/end of textarea
    if (event.key === 'ArrowUp') {
        // Navigate to previous query (if at beginning of textarea)
        if (queryInput.selectionStart === 0 && queryInput.selectionEnd === 0) {
            event.preventDefault();
            if (historyIndex < queryHistory.length - 1) {
                historyIndex++;
                queryInput.value = queryHistory[historyIndex];
                // Move cursor to end
                setTimeout(() => {
                    queryInput.setSelectionRange(queryInput.value.length, queryInput.value.length);
                }, 0);
            }
        }
    } else if (event.key === 'ArrowDown') {
        // Navigate to next query (if at end of textarea)
        const atEnd = queryInput.selectionStart === queryInput.value.length && 
                     queryInput.selectionEnd === queryInput.value.length;
        if (atEnd) {
            event.preventDefault();
            if (historyIndex > 0) {
                historyIndex--;
                queryInput.value = queryHistory[historyIndex];
            } else if (historyIndex === 0) {
                historyIndex = -1;
                queryInput.value = ''; // Clear input when going past most recent
            }
            // Move cursor to end
            setTimeout(() => {
                queryInput.setSelectionRange(queryInput.value.length, queryInput.value.length);
            }, 0);
        }
    } else if (event.key === 'Enter' && !event.shiftKey) {
        // Submit form on Enter (without Shift)
        event.preventDefault();
        document.getElementById('query-form').dispatchEvent(new Event('submit'));
    }
}

// Handle query submissions
function handleQuery(event) {
    event.preventDefault();

    // Fetch data
    const queryInput = document.getElementById("query-input").value.trim();
    const useLlm = true;  // Always true like terminal interface
    const topK = 10;  // Fixed value since no user selection

    if (!queryInput) {
        alert("Please enter a query.");
        return;
    }

    // Data - auto_save defaults to true (like terminal interface)
    const requestData = {
        query: queryInput,
        use_llm: useLlm,
        auto_save: true,  // Always auto-save like terminal interface
        top_k: topK
    };

    // Toggle progress
    toggleProgress(true);

    // Fetch API
    fetch("/api/query", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(requestData)
    })
    .then(handleFetchResponse)
    .then(data => {
        displayResults(data);
        // Refresh query history for arrow key navigation
        loadQueryHistory();
        
        // Show auto-save notification if file was saved
        if (data.saved_filename) {
            showAutoSaveNotification(data.saved_filename);
        }
    })
    .catch(error => {
        console.error("Query error:", error);
        alert("An error occurred while processing your query.");
    })
    .finally(() => {
        toggleProgress(false);
    });
}

function clearQuery() {
    document.getElementById("query-input").value = "";
    document.getElementById("results-container").innerHTML = "";
}

function exportResults() {
    const format = document.getElementById("export-format").value;

    // Simulate export confirmation
    alert(`Exporting results as ${format.toUpperCase()} is a placeholder.`);
    $('#exportModal').modal('hide');
}

function handleFetchResponse(response) {
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    return response.json().then(data => {
        if (!data.success) {
            throw new Error(data.error || "Unknown error");
        }
        return data.data;
    });
}

function displayResults(data) {
    const resultsContainer = document.getElementById("results-container");
    resultsContainer.innerHTML = "";

    // AI Response (formatted like terminal interface)
    if (data.llm_response) {
        resultsContainer.innerHTML += `
            <div class="card mb-4 ai-response fade-in">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-robot me-2"></i>AI Response</h5>
                </div>
                <div class="card-body">
                    <div class="ai-response-content">${formatTextWithLineBreaks(data.llm_response)}</div>
                </div>
            </div>
        `;
        
        // Bible references are now handled by our custom popup system
    } else {
        resultsContainer.innerHTML += `
            <div class="alert alert-warning fade-in" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>No results found for your query.
            </div>
        `;
    }
}

function formatBytes(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    let index = 0;
    while (bytes >= 1024 && index < units.length - 1) {
        bytes /= 1024;
        index++;
    }
    return `${parseFloat(bytes.toFixed(2))} ${units[index]}`;
}

function getSimilarityClass(similarity) {
    if (similarity >= 0.75) return "high";
    if (similarity >= 0.5) return "medium";
    return "low";
}

function toggleProgress(show) {
    const container = document.getElementById("progress-container");
    const bar = document.getElementById("progress-bar");
    const text = document.getElementById("progress-text");

    if (show) {
        container.style.display = "block";
        bar.style.width = "100%";
        text.textContent = "Processing your query...";
    } else {
        container.style.display = "none";
        bar.style.width = "0";
        text.textContent = "";
    }
}

// Load Bible books from API
function loadBibleBooks() {
    fetch('/api/bible-books')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                bibleBookMap = data.data;
                console.log('Bible books loaded:', Object.keys(bibleBookMap).length, 'entries');
            } else {
                console.warn('Failed to load Bible books:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading Bible books:', error);
        });
}


// Convert Bible reference to clickable pop-up
function convertBibleReference(match) {
    // Create a clickable span with data attribute instead of onclick
    return `<span class="bible-reference" data-verse-ref="${match}" title="Click to read ${match}">${match}</span>`;
}

// Format text with line breaks for better display
function formatTextWithLineBreaks(text) {
    if (!text) return '';
    
    // Convert line breaks to HTML and escape HTML
    let formattedText = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/\n/g, '<br>')
        .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');

    // Make Bible references clickable (always enabled)
    // Pattern matches: BookName Chapter:Verse or BookName Chapter:Verse-Verse
    // Examples: "John 3:16", "1 Corinthians 13:4-7", "Genesis 1:1", "Psalm 23:1-6"
    const bibleRefPattern = /\b(?:(?:[1-3]\s+)?[A-Za-z]+(?:\s+of\s+[A-Za-z]+)?)\s+\d+:\d+(?:[-–]\d+)?\b/g;
    
    
    formattedText = formattedText.replace(bibleRefPattern, convertBibleReference);
    
    return formattedText;
}

// Show Bible verse in a popup modal
function showVersePopup(reference) {
    // Show loading state
    const existingModal = document.getElementById('verseModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal HTML
    const modalHTML = `
        <div class="modal fade" id="verseModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-book-open me-2"></i>
                            <span id="verseReference">Loading...</span>
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="verseContent" class="text-center">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-2">Fetching verse...</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <small class="text-muted me-auto" id="verseVersion"></small>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="openBibleGateway('${reference}')">
                            <i class="fas fa-external-link-alt me-1"></i>Open in Bible Gateway
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('verseModal'));
    modal.show();
    
    // Fetch verse content
    fetch(`/api/fetch-verse?reference=${encodeURIComponent(reference)}`)
        .then(response => response.json())
        .then(data => {
            const referenceEl = document.getElementById('verseReference');
            const contentEl = document.getElementById('verseContent');
            const versionEl = document.getElementById('verseVersion');
            
            if (data.success) {
                referenceEl.textContent = data.data.reference;
                contentEl.innerHTML = `<div class="verse-text">${data.data.text.replace(/\n/g, '<br>')}</div>`;
                versionEl.textContent = data.data.version;
            } else {
                referenceEl.textContent = reference;
                contentEl.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error: ${data.error}
                    </div>
                `;
                versionEl.textContent = '';
            }
        })
        .catch(error => {
            console.error('Error fetching verse:', error);
            const referenceEl = document.getElementById('verseReference');
            const contentEl = document.getElementById('verseContent');
            
            referenceEl.textContent = reference;
            contentEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to fetch verse. Please try again.
                </div>
            `;
        });
    
    // Clean up modal when hidden
    document.getElementById('verseModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Open Bible Gateway as fallback
function openBibleGateway(reference) {
    const url = `https://www.biblegateway.com/passage/?search=${encodeURIComponent(reference)}&version=ESV`;
    window.open(url, '_blank');
}

// Show auto-save notification
function showAutoSaveNotification(filename) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-check-circle me-2"></i>Results auto-saved to: ${filename}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="modal"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Initialize and show toast
    const toastBootstrap = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    toastBootstrap.show();
    
    // Remove from DOM after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

