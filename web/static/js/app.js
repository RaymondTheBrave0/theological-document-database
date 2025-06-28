// JavaScript for Document Database Web Interface

const socket = io();

// Run when the DOM is ready
document.addEventListener("DOMContentLoaded", function() {
    // Load database info and initial history
    loadDatabaseInfo();
    updateHistory();

    // Handle query form submission
    document.getElementById("query-form").addEventListener("submit", handleQuery);
    document.getElementById("clear-btn").addEventListener("click", clearQuery);
    document.getElementById("export-confirm").addEventListener("click", exportResults);
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


// Update query history
function updateHistory() {
    fetch("/api/history")
        .then(handleFetchResponse)
        .then(history => {
            const container = document.getElementById("history-container");
            if (history.length === 0) {
                container.innerHTML = "<small class='text-muted'>No query history available</small>";
            } else {
                container.innerHTML = history.map(entry => `
                    <div class="history-item">
                        <div class="history-query"><strong>${entry.query}</strong></div>
                        <div class="history-meta">
                            ${entry.results_count} results • ${entry.execution_time.toFixed(2)}s
                        </div>
                    </div>
                `).join("");
            }
        })
        .catch(error => {
            console.error("Error fetching history:", error);
        });
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
        updateHistory();
        
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

// Format text with line breaks for better display
function formatTextWithLineBreaks(text) {
    if (!text) return '';
    
    // Convert line breaks to HTML and escape HTML
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/\n/g, '<br>')
        .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
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
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
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

