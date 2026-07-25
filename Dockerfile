# Server-Framework - Web dashboard service
# Production image for the Flask dashboard (Web/Web_Backend.py) on port 5000.
FROM python:3.13-slim

# Do not buffer stdout/stderr; no .pyc files in the container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only the dependencies the web dashboard actually needs.
# Pins mirror requirements.txt (verified on Python 3.13).
# NOTE: bleak/openai (BLE scanning + AI reports) are intentionally omitted:
# they are lazy-imported and require host Bluetooth, which is unavailable in a
# container. Those pages degrade gracefully. See README "Running with Docker".
RUN pip install \
    flask==3.1.3 \
    psutil==7.2.2 \
    requests==2.32.5 \
    websockets==16.0 \
    python-dotenv==1.1.0

# Copy the application source.
COPY . /app

# Create an unprivileged user and hand over the app + writable runtime dirs.
# Data/ holds generated reports; Web/ receives runtime logs.
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/Data /app/Web/WebSpiderBlueLogs \
    && chown -R appuser:appuser /app

USER appuser

# The Flask app resolves templates/static and its imports relative to Web/.
WORKDIR /app/Web

EXPOSE 5000

# Bind to all interfaces inside the container; debug stays off (production).
CMD ["python", "Web_Backend.py", "--host", "0.0.0.0", "--port", "5000"]
