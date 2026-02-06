# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
# Use 0.0.0.0 to listen on all interfaces within the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
