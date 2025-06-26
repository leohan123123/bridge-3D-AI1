# Bridge Intelligent Design System

This project is a web-based system for intelligent bridge design, leveraging modern web technologies and (conceptually) AI for design generation.

## Project Structure

- `app.py`: Main Flask application file, serves the frontend and mock API endpoints. (Future: May become FastAPI or be split).
- `templates/index.html`: Main HTML file for the user interface.
- `static/`: Contains CSS (`bridge_design.css`) and JavaScript (`app.js`, `design_workflow.js`).
- `requirements.txt`: Python dependencies.
- `Dockerfile`: For containerizing the application.
- `README.md`: This file.

## Running the Application

### Local Development (using Flask)

1.  **Set up a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Flask development server:**
    ```bash
    python app.py
    ```
    The application will be accessible at `http://127.0.0.1:5000`.

### Docker Deployment

1.  **Build the Docker image:**
    ```bash
    docker build -t bridge-design-system .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 bridge-design-system
    ```
    The application will be accessible at `http://localhost:8000`. Note that the Docker container runs Gunicorn, which is more production-ready than the Flask dev server, and maps to port 8000 as specified in the Dockerfile.

## Testing (Conceptual - Placeholders)

Currently, the system is in a foundational stage with a UI and mock backend. Formal testing infrastructure is yet to be implemented.

### 1. End-to-End Functional Testing
   - **Manual Testing:**
     - Open the web application in a browser.
     - Interact with the UI:
       - Click through tabs (需求分析, 设计方案, 工程图纸, 3D模型).
       - Enter values in the "需求输入" panel (e.g., Span, Load).
       - Click the "开始设计流程 (Test)" button.
       - Verify that the different tabs get populated with (mock) data from the backend.
       - Test the "加载历史" button and loading a version to see if input fields update.
       - Test the "导出" buttons (they should log to the console).
       - Check basic responsiveness by resizing the browser window.
   - **Automated E2E Testing (Future):**
     - Tools like Selenium, Cypress, or Playwright could be used to automate browser interactions and verify UI behavior and content.

### 2. API Testing (Future - when FastAPI is implemented)
   - Once the backend is implemented (e.g., with FastAPI), API endpoints can be tested directly using tools like `pytest` with `httpx`, or Postman/Insomnia.
   - Tests would cover:
     - Correct responses for valid inputs.
     - Error handling for invalid inputs.
     - Authentication/authorization (if applicable).

### 3. Unit Testing (Future)
   - **Python Backend:**
     - Use `pytest` to test individual functions and modules (e.g., calculation logic, data transformation, specific parts of API handlers).
   - **JavaScript Frontend:**
     - Use frameworks like Jest or Mocha to test individual JavaScript functions and components (e.g., parts of `DesignWorkflow`, UI update logic if separated).

### 4. Performance Testing (Future)
   - Tools like Apache JMeter, Locust, or k6 could be used to simulate multiple users and measure:
     - Response times of API endpoints.
     - System behavior under load.
     - Identify bottlenecks.

### 5. User Experience (UX) Testing (Ongoing)
   - Gather feedback from potential users on the ease of use, clarity of the interface, and overall workflow.

## Deployment Notes (Beyond Docker)

- The provided `Dockerfile` uses Gunicorn, a production-ready WSGI server for the current Flask app. If `main.py` with FastAPI is used, the `CMD` in the Dockerfile should be updated to use `uvicorn`.
- For a full production deployment, consider:
  - A managed container orchestration service (e.g., Kubernetes, AWS ECS, Google Cloud Run).
  - Setting up HTTPS.
  - Centralized logging and monitoring.
  - A robust database for persistent storage (if not already part of the backend).
  - CI/CD pipelines for automated testing and deployment.

---
*This README provides initial guidance. As the project evolves, these sections should be updated with more specific details and commands.*
