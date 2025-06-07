-- Configuración de la estructura de la base de datos --

-- Habilitar extensión pgvector en PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear tabla relacional de convocatorias
CREATE TABLE IF NOT EXISTS convocatorias (
    id SERIAL PRIMARY KEY,
    organismo TEXT NOT NULL,
    nombre TEXT,
    linea TEXT,
    fecha_inicio TEXT,
    fecha_fin TEXT,
    objetivo TEXT,
    beneficiarios TEXT,
    anio TEXT,
    area TEXT,
    presupuesto_minimo TEXT,
    presupuesto_maximo TEXT,
    duracion_minima TEXT,
    duracion_maxima TEXT,
    intensidad_subvencion TEXT,
    intensidad_prestamo TEXT,
    tipo_financiacion TEXT,
    forma_plazo_cobro TEXT,
    minimis TEXT,
    region_aplicacion TEXT,
    tipo_consorcio TEXT,
    costes_elegibles TEXT,
    enlace_ficha_tecnica TEXT,
    enlace_orden_bases TEXT,
    enlace_convocatoria TEXT NOT NULL,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Europe/Madrid')
);

-- Crear tabla relacional de documentos
CREATE TABLE IF NOT EXISTS documentos (
    id SERIAL PRIMARY KEY,
    titulo TEXT,
    tipo_mime TEXT NOT NULL,
    tipo_documento TEXT,
    numero_paginas INTEGER,
    tamano_bytes BIGINT,
    hash_sha256 TEXT NOT NULL,
    es_comun TEXT DEFAULT 'no',
    enlace_documento TEXT NOT NULL,
    ultima_modificacion TIMESTAMP WITH TIME ZONE,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Europe/Madrid'),
    CONSTRAINT unique_hash UNIQUE (hash_sha256)
);

-- Crear tabla relacional de convocatorias_documentos
CREATE TABLE IF NOT EXISTS convocatorias_documentos (
    convocatoria_id INTEGER NOT NULL REFERENCES convocatorias(id) ON DELETE CASCADE,
    documento_id INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    fecha_asociacion TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Europe/Madrid'),
    PRIMARY KEY (convocatoria_id, documento_id)
);

-- Crear tabla vectorial de documentos_chunks
CREATE TABLE IF NOT EXISTS documentos_chunks (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    chunk_texto TEXT NOT NULL,
    chunk_vector VECTOR(384),
    titulo_seccion TEXT,
    numero_pagina INTEGER,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Europe/Madrid')
);

-- Crear índices de optimización
CREATE INDEX IF NOT EXISTS idx_documentos_comunes ON documentos(es_comun);
CREATE INDEX IF NOT EXISTS idx_convocatorias_documentos ON convocatorias_documentos(convocatoria_id, documento_id);
CREATE INDEX IF NOT EXISTS idx_documentos_chunks_documento ON documentos_chunks(documento_id);

-- Crear tabla relacional de metricas_extraccion
CREATE TABLE IF NOT EXISTS metricas_extraccion (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Europe/Madrid'),
    cobertura_organismos FLOAT,
    tasa_exito FLOAT,
    tiempo_promedio FLOAT,
    tasa_deteccion_pdf FLOAT,
    urls_procesadas INTEGER,
    urls_exitosas INTEGER,
    urls_fallidas INTEGER,
    documentos_detectados INTEGER,
    paginas_analizadas INTEGER
);

-- Crear tabla relacional de metricas_procesamiento
CREATE TABLE IF NOT EXISTS metricas_procesamiento (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Europe/Madrid'),
    tasa_texto_principal FLOAT,
    tasa_tablas FLOAT,
    tasa_metadatos FLOAT,
    tamano_promedio_chunks FLOAT,
    tiempo_promedio_procesamiento FLOAT,
    total_documentos INTEGER,
    total_chunks INTEGER
);

-- Crear tabla relacional de metricas_llm
CREATE TABLE IF NOT EXISTS metricas_llm (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Europe/Madrid'),
    tiempo_respuesta_texto_corto FLOAT,
    tiempo_respuesta_texto_medio FLOAT,
    tiempo_respuesta_texto_largo FLOAT,
    tiempo_respuesta_tablas FLOAT,
    llamadas_totales INTEGER
);

-- Crear tabla relacional de metricas_busqueda
CREATE TABLE IF NOT EXISTS metricas_busqueda (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Europe/Madrid'),
    tiempo_respuesta_vectorial FLOAT,
    tiempo_respuesta_hibrida FLOAT,
    busquedas_vectoriales INTEGER,
    busquedas_hibridas INTEGER
);

-- Crear índice IVFFlat
CREATE OR REPLACE FUNCTION crear_indice_vectorial() RETURNS void AS $$
BEGIN
    -- Verificar si hay datos antes de crear el índice
    IF EXISTS (SELECT 1 FROM documentos_chunks LIMIT 1) THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_documentos_chunks_vector ON documentos_chunks USING ivfflat (chunk_vector vector_cosine_ops) WITH (lists = 100)';
    END IF;
END;
$$ LANGUAGE plpgsql;