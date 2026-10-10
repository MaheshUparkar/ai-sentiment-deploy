# 1. Start from a small official Python image (OS + Python already installed).
FROM python:3.13-slim

# 2. Sensible Python defaults for containers: no .pyc files, logs appear immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 3. All following commands run inside /app in the image.
WORKDIR /app

# 4. Install dependencies first so Docker can cache this layer when only code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

# 5. Copy the training script + data, and the application code.
COPY training/ training/
COPY app/ app/

# 6. Train the model at build time: the model artifact is baked into the image.
RUN python training/train.py

# 7. Do not run as root inside the container.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# 8. Document the port. Hosting platforms (e.g. Render) override it via $PORT.
ENV PORT=8000
EXPOSE 8000

# 9. Start the web server, listening on all interfaces so traffic from outside the container reaches it.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
