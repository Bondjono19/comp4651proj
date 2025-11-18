# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirement.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Copy application code
COPY *.py .

# Expose port 8000
EXPOSE 8000

# Health check using curl (wget is not available in python:slim)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
