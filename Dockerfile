FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# Current app.py is Flask. If main.py with FastAPI is created, the above CMD is correct.
# For the current Flask app (app.py), the CMD would be different, e.g.,
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
# Or using gunicorn for production:
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
