class DesignWorkflow {
    constructor() {
        // Assuming Flask runs on port 5000 and serves static files.
        // API calls will be to the same origin.
        this.apiBaseUrl = '/api/v1';
        console.log("DesignWorkflow class instantiated.");
    }

    async _callApi(endpoint, method = 'POST', body = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            if (body && (method === 'POST' || method === 'PUT')) {
                options.body = JSON.stringify(body);
            }

            console.log(`Calling API: ${method} ${this.apiBaseUrl}/${endpoint} with body:`, body);
            const response = await fetch(`${this.apiBaseUrl}/${endpoint}`, options);

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { message: response.statusText };
                }
                console.error(`API Error (${response.status}):`, errorData);
                throw new Error(`API Error (${response.status}): ${errorData.message || response.statusText}`);
            }

            const responseData = await response.json();
            console.log(`API response for ${endpoint}:`, responseData);
            return responseData;

        } catch (error) {
            console.error(`Error in DesignWorkflow API call to ${this.apiBaseUrl}/${endpoint}:`, error);
            // Ensure showUserMessage is available or handle error display appropriately
            if (typeof showUserMessage === 'function') {
                showUserMessage(`Error: ${error.message}`, 'error');
            }
            throw error; // Re-throw to be handled by the caller
        }
    }

    async analyzeRequirements(userInput) {
        console.log("Step 1: Analyzing Requirements...", userInput);
        if (typeof showUserMessage === 'function') showUserMessage('Analyzing requirements...', 'info');

        const result = await this._callApi('analyze_requirements', 'POST', userInput);
        console.log("Requirements analysis result:", result);

        if (document.getElementById('requirements-content') && result.summary) {
            document.getElementById('requirements-content').innerHTML =
                `<h3>需求分析内容</h3><p>${result.summary}</p><p><small>Input received: ${JSON.stringify(result.received_input)}</small></p>`;
        }
        return result;
    }

    async generateDesign(requirements) {
        console.log("Step 2: Generating Design Scheme...", requirements);
        if (typeof showUserMessage === 'function') showUserMessage('Generating design scheme...', 'info');
        const result = await this._callApi('generate_design', 'POST', { requirements_id: requirements.analysis_id });
        console.log("Design scheme generation result:", result);
        if (document.getElementById('design-content') && result.details) {
            document.getElementById('design-content').innerHTML =
                `<h3>设计方案内容</h3><p>${result.details}</p><p><small>Based on: ${result.based_on}</small></p>`;
        }
        return result;
    }

    async generate2DDrawings(design) {
        console.log("Step 3: Generating 2D Engineering Drawings...", design);
        if (typeof showUserMessage === 'function') showUserMessage('Generating 2D drawings...', 'info');
        const result = await this._callApi('generate_2d_drawings', 'POST', { design_id: design.design_id });
        console.log("2D Drawings generation result:", result);
        if (document.getElementById('drawings-content') && result.url) {
            document.getElementById('drawings-content').innerHTML =
                `<h3>工程图纸内容</h3><p><a href="${result.url}" target="_blank">View Drawing (${result.format})</a></p><p><small>Based on: ${result.based_on}</small></p>`;
        }
        return result;
    }

    async generate3DModel(design) {
        console.log("Step 4: Generating 3D Model...", design);
        if (typeof showUserMessage === 'function') showUserMessage('Generating 3D model...', 'info');
        const result = await this._callApi('generate_3d_model', 'POST', { design_id: design.design_id });
        console.log("3D Model generation result:", result);
        if (document.getElementById('model3d-content') && result.url) {
            document.getElementById('model3d-content').innerHTML =
                `<h3>3D模型内容</h3><p><a href="${result.url}" target="_blank">View Model (${result.format})</a></p><p><small>Based on: ${result.based_on}</small></p>`;
        }
        return result;
    }

    // --- Additional methods for interactivity ---

    async getDesignHistory() {
        console.log("Fetching design history...");
        if (typeof showUserMessage === 'function') showUserMessage('Fetching design history...', 'info');
        const history = await this._callApi('designs/history', 'GET');
        const historyList = document.getElementById('design-history-list');
        if (historyList) {
            historyList.innerHTML = history.map(item =>
                `<li>${item.name} (${item.date})
                 <button class="load-version-button" data-version="${item.id}">Load</button>
                 </li>`).join('');

            // Add event listeners to newly created load buttons
            document.querySelectorAll('.load-version-button').forEach(button => {
                button.addEventListener('click', async (event) => {
                    const versionId = event.target.dataset.version;
                    await this.loadDesignVersion(versionId);
                });
            });
        }
        return history;
    }

    async loadDesignVersion(versionId) {
        console.log(`Loading design version: ${versionId}...`);
        if (typeof showUserMessage === 'function') showUserMessage(`Loading design version ${versionId}...`, 'info');
        const versionData = await this._callApi(`designs/${versionId}`, 'GET');

        if (document.getElementById('span-input') && versionData.data) document.getElementById('span-input').value = versionData.data.span;
        if (document.getElementById('load-input') && versionData.data) document.getElementById('load-input').value = versionData.data.load;

        // Optionally, re-populate other parts of the UI or trigger a new analysis/design run
        if (typeof showUserMessage === 'function') showUserMessage(`Loaded version ${versionData.name}. Input fields updated.`, 'success');
        console.log("Loaded version data:", versionData);
        return versionData;
    }
}

let workflowInstance; // Make workflow instance accessible for history setup

document.addEventListener('DOMContentLoaded', () => {
    workflowInstance = new DesignWorkflow(); // Assign to the accessible variable
    const startButton = document.getElementById('start-design-button');

    if (startButton) {
        startButton.addEventListener('click', async () => {
            try {
                // Clear previous results
                document.getElementById('requirements-content').innerHTML = '<h3>需求分析内容</h3>';
                document.getElementById('design-content').innerHTML = '<h3>设计方案内容</h3>';
                document.getElementById('drawings-content').innerHTML = '<h3>工程图纸内容</h3>';
                document.getElementById('model3d-content').innerHTML = '<h3>3D模型内容</h3>';

                if (typeof showUserMessage === 'function') showUserMessage('Starting design workflow...', 'info');

                const span = document.getElementById('span-input').value;
                const load = document.getElementById('load-input').value;
                const userInput = { span: parseFloat(span), load: parseFloat(load) };

                const analysis = await workflow.analyzeRequirements(userInput);
                // Switch to requirements tab
                document.querySelector('.tab[data-tab="requirements"]').click();


                const design = await workflow.generateDesign(analysis);
                 // Switch to design tab after a short delay
                setTimeout(() => document.querySelector('.tab[data-tab="design"]').click(), 500);


                const drawings = await workflow.generate2DDrawings(design);
                // Switch to drawings tab
                setTimeout(() => document.querySelector('.tab[data-tab="drawings"]').click(), 1000);

                const model = await workflow.generate3DModel(design);
                // Switch to model tab
                setTimeout(() => document.querySelector('.tab[data-tab="model3d"]').click(), 1500);

                console.log("Full design workflow completed.", { analysis, design, drawings, model });
                if (typeof showUserMessage === 'function') showUserMessage('Design process complete!', 'success');
            } catch (error) {
                console.error("Error in design workflow:", error);
                if (typeof showUserMessage === 'function') showUserMessage(`Workflow error: ${error.message}`, 'error');
           }
        });
    }
});

console.log("design_workflow.js parsed.");
