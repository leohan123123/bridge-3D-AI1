// Placeholder for static/js/svg_viewer.js

class SVGViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`SVGViewer: Container with id '${containerId}' not found.`);
            return;
        }
        this.svgElement = null;
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;

        // Basic styling for the container
        this.container.style.overflow = 'hidden'; // Important for panning
        this.container.style.position = 'relative'; // For absolute positioning of controls
        this.container.style.border = '1px solid #ccc';
    }

    loadSVG(svgString) {
        if (this.svgElement) {
            this.container.removeChild(this.svgElement);
        }
        // Create a temporary div to parse the SVG string
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = svgString;
        this.svgElement = tempDiv.querySelector('svg');

        if (this.svgElement) {
            this.container.appendChild(this.svgElement);
            this.svgElement.style.transformOrigin = '0 0'; // Set transform origin for zooming
            this.resetView();
            this.setupEventListeners();
        } else {
            console.error("SVGViewer: No SVG element found in the provided string.");
            this.container.innerHTML = "<p>Error loading SVG.</p>";
        }
    }

    updateTransform() {
        if (this.svgElement) {
            this.svgElement.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.zoomLevel})`;
        }
    }

    zoom(factor) {
        this.zoomLevel *= factor;
        this.updateTransform();
        console.log(`Zoom level: ${this.zoomLevel}`);
    }

    pan(deltaX, deltaY) {
        this.panX += deltaX;
        this.panY += deltaY;
        this.updateTransform();
        console.log(`Pan: X=${this.panX}, Y=${this.panY}`);
    }

    resetView() {
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
        if (this.svgElement) {
            // Attempt to fit SVG to container - very basic
            const containerWidth = this.container.clientWidth;
            const containerHeight = this.container.clientHeight;
            const svgWidth = this.svgElement.width.baseVal.value;
            const svgHeight = this.svgElement.height.baseVal.value;

            if (svgWidth > 0 && svgHeight > 0) {
                const scaleX = containerWidth / svgWidth;
                const scaleY = containerHeight / svgHeight;
                this.zoomLevel = Math.min(scaleX, scaleY) * 0.95; // Add a little padding
            }
        }
        this.updateTransform();
    }

    measureDistance() {
        // Placeholder for measurement logic
        alert("Measurement tool: Click two points to measure distance (not implemented).");
        console.log("Measurement tool activated (placeholder).");
    }

    printSVG() {
        if (!this.svgElement) {
            alert("No SVG loaded to print.");
            return;
        }
        // This is a very basic print. More sophisticated printing might involve rendering to canvas.
        const printWindow = window.open('', '_blank');
        printWindow.document.write('<html><head><title>Print SVG</title></head><body>');
        printWindow.document.write(this.svgElement.outerHTML);
        printWindow.document.write('</body></html>');
        printWindow.document.close(); // Necessary for some browsers.
        printWindow.onload = function() { // Wait for content to load before printing
            printWindow.print();
            printWindow.close();
        };
        console.log("Print function called.");
    }

    exportSVG() {
        if (!this.svgElement) {
            alert("No SVG loaded to export.");
            return;
        }
        const svgData = this.svgElement.outerHTML;
        const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'drawing.svg';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        console.log("Export SVG function called.");
    }

    setupEventListeners() {
        // Placeholder for event listeners (e.g., mouse drag for panning)
        let isPanning = false;
        let lastMouseX, lastMouseY;

        if (!this.svgElement) return;

        this.svgElement.addEventListener('mousedown', (e) => {
            // Pan on middle mouse button or Ctrl + Left Click
            if (e.button === 1 || (e.button === 0 && e.ctrlKey)) {
                isPanning = true;
                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
                this.svgElement.style.cursor = 'grabbing';
                e.preventDefault();
            }
        });

        this.container.addEventListener('mousemove', (e) => {
            if (isPanning) {
                const deltaX = e.clientX - lastMouseX;
                const deltaY = e.clientY - lastMouseY;
                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
                this.pan(deltaX / this.zoomLevel, deltaY / this.zoomLevel); // Adjust pan speed by zoom
            }
        });

        this.container.addEventListener('mouseup', (e) => {
            if (isPanning) {
                isPanning = false;
                this.svgElement.style.cursor = 'grab';
            }
        });

        this.container.addEventListener('mouseleave', (e) => { // Stop panning if mouse leaves container
            if (isPanning) {
                isPanning = false;
                this.svgElement.style.cursor = 'grab';
            }
        });

        this.container.addEventListener('wheel', (e) => {
            e.preventDefault(); // Prevent page scrolling
            const zoomFactor = e.deltaY < 0 ? 1.1 : 1 / 1.1; // Zoom in or out

            // Zoom towards mouse pointer
            const rect = this.svgElement.getBoundingClientRect();
            const mouseX = e.clientX - rect.left; // Mouse X relative to SVG
            const mouseY = e.clientY - rect.top;  // Mouse Y relative to SVG

            // Adjust pan to keep mouse position stable after zoom
            this.panX = mouseX - (mouseX - this.panX) * zoomFactor;
            this.panY = mouseY - (mouseY - this.panY) * zoomFactor;

            this.zoom(zoomFactor);
        });

        // Add basic controls (example)
        this.addControls();
    }

    addControls() {
        const controlsDiv = document.createElement('div');
        controlsDiv.style.position = 'absolute';
        controlsDiv.style.top = '10px';
        controlsDiv.style.left = '10px';
        controlsDiv.style.zIndex = '1000'; // Ensure controls are on top
        controlsDiv.style.background = 'rgba(255,255,255,0.8)';
        controlsDiv.style.padding = '5px';
        controlsDiv.style.borderRadius = '5px';

        const zoomInButton = document.createElement('button');
        zoomInButton.textContent = '+';
        zoomInButton.onclick = () => this.zoom(1.2);
        controlsDiv.appendChild(zoomInButton);

        const zoomOutButton = document.createElement('button');
        zoomOutButton.textContent = '-';
        zoomOutButton.onclick = () => this.zoom(1/1.2);
        controlsDiv.appendChild(zoomOutButton);

        const resetButton = document.createElement('button');
        resetButton.textContent = 'Reset';
        resetButton.onclick = () => this.resetView();
        controlsDiv.appendChild(resetButton);

        const measureButton = document.createElement('button');
        measureButton.textContent = 'Measure';
        measureButton.onclick = () => this.measureDistance();
        controlsDiv.appendChild(measureButton);

        const printButton = document.createElement('button');
        printButton.textContent = 'Print';
        printButton.onclick = () => this.printSVG();
        controlsDiv.appendChild(printButton);

        const exportButton = document.createElement('button');
        exportButton.textContent = 'Export SVG';
        exportButton.onclick = () => this.exportSVG();
        controlsDiv.appendChild(exportButton);

        this.container.appendChild(controlsDiv);
    }
}

// Example Usage (optional, for testing):
// document.addEventListener('DOMContentLoaded', () => {
//     const viewer = new SVGViewer('svgContainer'); // Assuming you have a <div id="svgContainer"></div>
//     const exampleSVG = `
//         <svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
//             <rect x="50" y="50" width="100" height="100" fill="blue" />
//             <circle cx="250" cy="100" r="40" fill="red" />
//             <text x="60" y="180">Sample SVG</text>
//         </svg>`;
//     viewer.loadSVG(exampleSVG);
// });
