FROM python:3.11-slim

WORKDIR /app

# Install uv for faster package management
RUN pip install --no-cache-dir uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with uv (much faster than pip)
# Use --system to install to system Python, no virtualenv needed in container
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Create static directory if it doesn't exist
RUN mkdir -p static

# Expose port
EXPOSE 80

# Command to run the application
CMD ["python", "app.py"]