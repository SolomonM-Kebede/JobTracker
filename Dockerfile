# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create data directory for token cache
RUN mkdir -p /app/data

# Expose Streamlit port
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8501 || exit 1

# Default command — runs dashboard
CMD ["streamlit", "run", "dashboard.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]