# Etapa 1: Builder (Construcción)
# Usar la imagen de Python 3.110 más ligera, rápida y segura
FROM python:3.11-slim-bookworm AS builder

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/usr/local/lib/playwright \
    HF_HOME=/root/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/root/.cache/torch/sentence_transformers   

# Establecer directorio de trabajo
WORKDIR /app

# Crear y activar entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependencias necesarias para PostgreSQL, Python, archivos web, repositorios Git y certificados SSL
    libpq-dev gcc python3-dev wget git ca-certificates openssl \
    # Limpieza de caché para reducir el tamaño de la imagen
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates \
    && mkdir -p /usr/local/share/ca-certificates/extra

# Copiar y preparar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    # Versión Torch con CPU más ligera
    pip install --no-cache-dir torch==2.2.1+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \  
    pip install --no-cache-dir "git+https://github.com/huggingface/smolagents.git"

# Desacargar modelor
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copiar resto de archivos
COPY . .

# Etapa 2: Runtime (Ejecución)
FROM python:3.11-slim-bookworm

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/usr/local/lib/playwright \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    HF_HOME=/root/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/root/.cache/torch/sentence_transformers

# Copiar entorno virtual
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Dependencias necesarias para Chromium y certificados SSL
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 libatspi2.0-0 libx11-6 libxcb1 libxext6 libxshmfence1 \
    libpq5 ca-certificates openssl \
    # Limpieza de caché para reducir el tamaño de la imagen
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Copiar Chromium, entorno virtual y binarios
COPY --from=builder /usr/local/lib/playwright /usr/local/lib/playwright
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar modelo descargado y caché de Hugging Face y Sentence Transformers
COPY --from=builder /root/.cache/ /root/.cache/

# Copiar código fuente
COPY --from=builder /app /app

# Establecer directorio de trabajo
WORKDIR /app

# Establecer comando de ejecución
CMD ["python", "main.py"]