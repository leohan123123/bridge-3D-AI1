document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Deactivate all tabs and panes
            tabs.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            // Activate clicked tab and corresponding pane
            this.classList.add('active');
            const targetPaneId = this.dataset.tab + '-content';
            document.getElementById(targetPaneId).classList.add('active');

            console.log(`Switched to tab: ${this.dataset.tab}`);
        });
    });

    // Activate the first tab by default (or based on a saved state)
    if (tabs.length > 0) {
        tabs[0].click(); // Simulate a click on the first tab
    }

    console.log("app.js loaded and initialized.");

    // Placeholder for future interactive elements
    // Example: initializeWebSocket();
    // Example: setupParameterInputs();
    setupExportButtons();
    setupHistoryButtons(); // We will call a function that might be in design_workflow.js or app.js
});

function setupExportButtons() {
    const pdfButton = document.getElementById('export-pdf-button');
    const dwgButton = document.getElementById('export-dwg-button');
    const modelButton = document.getElementById('export-model-button');

    if (pdfButton) pdfButton.addEventListener('click', exportPDF);
    if (dwgButton) dwgButton.addEventListener('click', exportDWG);
    if (modelButton) modelButton.addEventListener('click', exportModel);
}

function setupHistoryButtons() {
    const loadHistoryButton = document.getElementById('load-history-button');
    if (loadHistoryButton) {
        loadHistoryButton.addEventListener('click', async () => {
            if (workflowInstance) { // workflowInstance is defined in design_workflow.js
                await workflowInstance.getDesignHistory();
            } else {
                console.error("Workflow instance not available.");
                showUserMessage("Error: Workflow module not ready for history.", "error");
            }
        });
    }
}

// Placeholder for WebSocket or polling functions
function initializeWebSocket() {
    // const socket = new WebSocket('ws://localhost:8000/ws'); // Example WebSocket URL
    // socket.onmessage = function(event) {
    //     console.log('WebSocket message received:', event.data);
    //     // Update UI with progress or results
    // };
    // socket.onopen = function(event) {
    //     console.log('WebSocket connection established.');
    // };
    // socket.onerror = function(error) {
    //     console.error('WebSocket error:', error);
    // };
}

// Placeholder for parameter adjustment and regeneration logic
function setupParameterInputs() {
    // const regenerateButton = document.getElementById('regenerate-button');
    // if (regenerateButton) {
    //     regenerateButton.addEventListener('click', () => {
    //         const params = collectParameters();
    //         // Call a DesignWorkflow method or API endpoint
    //         console.log('Regenerating with parameters:', params);
    //     });
    // }
}

function collectParameters() {
    // Collect values from input fields in the requirements-panel or properties-panel
    // const param1 = document.getElementById('param1-input').value;
    // return { param1 /*, ... */ };
    return {};
}

// Placeholder for export functions
function exportPDF() {
    console.log('Exporting PDF report...');
    // Logic to call backend API for PDF generation
}

function exportDWG() {
    console.log('Exporting DWG drawings...');
    // Logic to call backend API for DWG generation
}

function exportModel() {
    console.log('Exporting 3D model file...');
    // Logic to call backend API for model file generation
}

// Placeholder for model view interactions (zoom, rotate)
// These would typically involve a 3D library like Three.js or similar
function setupModelViewControls() {
    // const modelView = document.getElementById('model-view-container');
    // if (modelView) {
    //     // Initialize 3D viewer and controls
    // }
}

// Error handling and user feedback
function showUserMessage(message, type = 'info') {
    // A simple way to show messages, could be a dedicated div or a more sophisticated notification system
    const messageArea = document.getElementById('user-message-area'); // Assuming such an element exists
    if (messageArea) {
        messageArea.textContent = message;
        messageArea.className = `message ${type}`; // e.g., 'message error', 'message success'
    } else {
        alert(`${type.toUpperCase()}: ${message}`);
    }
}

console.log("app.js parsed.");
