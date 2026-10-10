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

# 5. Copy only what training needs (data, training script, shared feature code).
COPY app/__init__.py app/features.py app/
COPY training/ training/

# 6. Train the model at build time: the model artifact is baked into the image.
#    This layer is cached, so app-only changes (step 7) don't retrain.
RUN python training/train.py

# 7. Copy the rest of the application code.
COPY app/ app/

# 8. Do not run as root inside the container.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# 9. Document the port. Hosting platforms (e.g. Render) override it via $PORT.
ENV PORT=8000
EXPOSE 8000

# 10. Start the web server, listening on all interfaces so traffic from outside the container reaches it.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
