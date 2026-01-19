# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt ./

# Install Python dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with system dependencies
# Use PLAYWRIGHT_BROWSERS_PATH to install to a specific location
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output jobs data

# Expose port (Cloud Run uses PORT environment variable)
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8080"]
