// Ensure Three.js and OrbitControls are loaded before this script
if (typeof THREE === 'undefined') {
    console.error("THREE.js is not loaded!");
}
if (typeof THREE.OrbitControls === 'undefined') {
    console.error("THREE.OrbitControls is not loaded!");
}

let scene, camera, renderer, controls;
let currentModel = null; // To keep track of the currently added model group

const viewerContainer = document.getElementById('viewer-container');
const modelInfoContent = document.getElementById('modelInfoContent');
const generateModelBtn = document.getElementById('generateModelBtn');
const bridgeDesignText = document.getElementById('bridgeDesignText');
const modelRequirementsText = document.getElementById('modelRequirementsText');
const loadingIndicator = document.getElementById('loading-indicator');

function initThreeJS() {
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xeeeeee); // Default background

    // Camera
    camera = new THREE.PerspectiveCamera(75, viewerContainer.clientWidth / viewerContainer.clientHeight, 0.1, 1000);
    camera.position.set(10, 20, 50); // Default camera position
    camera.lookAt(0, 0, 0);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
    viewerContainer.appendChild(renderer.domElement);

    // Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    controls.screenSpacePanning = true; // Allow right-click panning

    // Lighting (basic setup, can be overridden by generated scene)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(50, 50, 50);
    scene.add(directionalLight);

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    animate();

    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);
}

function onWindowResize() {
    // Note: If the generated script creates its own renderer, this might target the old one
    // or a new one if 'renderer' global var is updated by the script.
    // For robust resizing, the active renderer instance needs to be targeted.
    // The current ThreeJSGenerator creates a local 'renderer', so this might only resize
    // the initial placeholder canvas, not the one created by the loaded script.
    // This is a known limitation of the current script injection method.
    const currentCanvas = viewerContainer.querySelector('canvas');
    if (camera && currentCanvas && viewerContainer) { // Check if a canvas is present
        camera.aspect = viewerContainer.clientWidth / viewerContainer.clientHeight;
        camera.updateProjectionMatrix();
        // The renderer associated with currentCanvas should be resized.
        // If the `renderer` global variable is correctly updated by the loaded script, this is fine.
        // Otherwise, this resize might not affect the dynamically loaded scene's renderer.
        if (renderer) { // Check if global renderer is available
             renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
        }
    }
}

// clearScene is not strictly needed anymore if each loaded script completely replaces the canvas
// and its associated scene, camera, renderer. The `handleGenerateModel` clears the container.
// However, if we had a mechanism to *add* to an existing scene, it would be useful.
// For now, its main use (disposing old model resources) is good practice.
function clearOldModelResources() {
    if (currentModel) { // currentModel would need to be set by the loaded script if we want this
        scene.remove(currentModel); // Assuming 'scene' is the active scene
        currentModel.traverse(object => {
            if (object.isMesh) {
                if (object.geometry) object.geometry.dispose();
                if (object.material) {
                    if (Array.isArray(object.material)) {
                        object.material.forEach(material => material.dispose());
                    } else {
                        object.material.dispose();
                    }
                }
            }
        });
        currentModel = null;
    }
}

async function loadAndDisplayModel(threejsCode) {
    // `handleGenerateModel` already clears viewerContainer.
    // `clearOldModelResources()` could be called here if `currentModel` was managed.

    try {
        // The generated code from `ThreeJSGenerator` creates its own scene, camera, renderer, controls,
        // and its own animation loop. It also appends its renderer's canvas.
        // Our goal is to ensure this new canvas is placed inside `viewerContainer`.

        const originalBodyAppendChild = document.body.appendChild;
        document.body.appendChild = (element) => {
            if (element instanceof HTMLCanvasElement) {
                viewerContainer.appendChild(element);
                // The generated code also creates renderer, camera, scene, controls.
                // We need to make sure our global vars point to these new ones.
                // This is hacky due to the current generator output.
            } else {
                originalBodyAppend.call(document.body, element);
            }
        };

        // The script will define its own `scene`, `camera`, `renderer`, `controls`
        // We will need to re-assign our global references if we want our `animate` loop to work with them.
        // This is getting very hacky. The generator should be refactored.

        // --- This is a placeholder for a better loading mechanism ---
        // For now, let's assume the generated code is self-contained and will run,
        // replacing the canvas and setting up its own animation loop.
        // This means our `initThreeJS` becomes more of a fallback if no code is loaded.

        // Create a new script element
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.text = threejsCode;
        document.head.appendChild(script); // Add to head to execute
        document.head.removeChild(script); // Clean up

        // Restore original appendChild
        document.body.appendChild = originalBodyAppend;

        // The global scene, camera, renderer, controls are now those from the executed script.
        // Our initial `animate` loop might conflict or target the old objects.
        // The generated script has its own `animate()` loop. This is probably the best outcome for now.

        // If the generated code does NOT have an animate loop, or we want to use our controls:
        // We would need to find the new scene/camera from the script (e.g. if it assigns them to window)
        // and update our renderer and controls.
        // e.g., if (window.generatedScene) scene = window.generatedScene;
        // if (window.generatedCamera) camera = window.generatedCamera;
        // if (window.generatedRenderer) renderer = window.generatedRenderer; // Careful with multiple renderers
        // if (window.generatedControls) controls = window.generatedControls;

        // For the current `ThreeJSGenerator`, it *does* create its own animation loop.
        // So, `initThreeJS` is mostly for the placeholder view.
        // When new code is loaded, it takes over the rendering.

        modelInfoContent.textContent = "Model loaded. (Details would go here)";

    } catch (error) {
        console.error("Error loading or executing Three.js code:", error);
        modelInfoContent.textContent = `Error: ${error.message}`;
        // Restore basic scene if loading fails
        if (renderer && renderer.domElement && !renderer.domElement.parentElement) {
            viewerContainer.appendChild(renderer.domElement); // Re-add our renderer
        }
    }
}


async function handleGenerateModel() {
    const designDesc = bridgeDesignText.value.trim();
    const modelReqs = modelRequirementsText.value.trim();

    if (!designDesc || !modelReqs) {
        alert("Please enter both bridge design description and model requirements.");
        return;
    }

    loadingIndicator.style.display = 'block';
    modelInfoContent.textContent = "Generating model...";

    try {
        const response = await fetch('/api/generate_3d_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                design: { design_description: designDesc },
                model_options: { requirements_description: modelReqs }
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
            throw new Error(`API Error (${response.status}): ${errorData.detail || JSON.stringify(errorData)}`);
        }

        const data = await response.json();

        if (data.threejs_code) {
            // Clear previous canvas / renderer before loading new one
            while (viewerContainer.firstChild) {
                viewerContainer.removeChild(viewerContainer.firstChild);
            }
            // Re-add loading indicator temporarily if it was removed
            viewerContainer.appendChild(loadingIndicator);


            await loadAndDisplayModel(data.threejs_code);
            modelInfoContent.textContent = "Model generated and loaded successfully.\n\n" +
                                          `Scene Config: ${JSON.stringify(data.scene_config, null, 2)}\n\n` +
                                          `Geometry Summary: (see console for full data)\n` +
                                          `  Girders: ${data.geometry_data.girders ? data.geometry_data.girders.length : 0}\n` +
                                          `  Piers: ${data.geometry_data.piers ? data.geometry_data.piers.length : 0}\n` +
                                          `  Foundations: ${data.geometry_data.foundations ? data.geometry_data.foundations.length : 0}`;
            console.log("Received Geometry Data:", data.geometry_data);
            console.log("Received Material Data:", data.material_data);
        } else if (data.error) {
            throw new Error(`Generation Error: ${data.error} - ${data.details}`);
        } else {
            throw new Error("No Three.js code received from API.");
        }

    } catch (error) {
        console.error("Failed to generate or load model:", error);
        modelInfoContent.textContent = `Error: ${error.message}`;
    } finally {
        loadingIndicator.style.display = 'none';
    }
}


// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initThreeJS(); // Initialize a basic Three.js scene on page load

    if (generateModelBtn) {
        generateModelBtn.addEventListener('click', handleGenerateModel);
    } else {
        console.error("Generate Model button not found.");
    }

    // Populate text areas with example data from main.py for convenience
    if (bridgeDesignText) {
        bridgeDesignText.value = "A 50m long box girder bridge with two cylindrical piers and spread footings.";
    }
    if (modelRequirementsText) {
        modelRequirementsText.value = "Render with standard concrete materials and basic lighting. Ensure dimensions are accurate.";
    }
});
```
