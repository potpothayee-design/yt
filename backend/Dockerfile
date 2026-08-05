# AI Kids Video Studio — backend image
# Includes a self-contained ffmpeg (via imageio-ffmpeg): no system packages required.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY pytest.ini ./
COPY tests ./tests

# Fonts: DejaVu is bundled inside the python:slim base via fontconfig? Not always.
# The renderer falls back through a font search path; mount fonts if you want custom ones.
RUN useradd -r -u 10001 studio && mkdir -p /data && chown -R studio /data /app
USER studio

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=8s --start-period=25s --retries=5 \
  CMD python -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=4).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
