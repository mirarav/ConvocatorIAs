# ConvocatorIAs 👋🤖

Este proyecto desarrolla un sistema multiagente inteligente para la identificación, indexación y síntesis de ayudas públicas en el sector I+D+i. Es capaz de:

* Rastrear y analizar páginas web de organismos oficiales (*).
* Extraer y procesar documentos PDF asociados.
* Generar embeddings vectoriales del contenido
* Utilizar modelos de lenguaje (LLM) para completar información.
* Proporcionar interfaz conversacional para consultas.

## Requisitos

| Componente       | Especificación                 |
| ---------------- | -----------------------------: |
| Docker           | 20.10+ con Compose v2.20+      |
| CPU              | 4 núcleos (recomendado)        |
| RAM              | 4 GB mínimo (8 GB recomendado) |
| Almacenamiento   | 10 GB libres                   |
| Conexión         | Internet estable                |


## Organismos

Actualmente el sistema soporta convocatorias de:

| Organismo             | Enlace        |
| --------------------- | -------------:|
| ADER                  | [ADER](https://www.ader.es/ayudas/ayudas-por-areas/i-d/) |
| CDTO                  | [CDTI](https://www.cdti.es/matriz-de-ayudas) |
| Comunidad de Madrid   | [Comunidad de Madrid](https://sede.comunidad.madrid/investigacion-tecnologia/investigacion-desarrollo-e-innovacion-idi) |
| TRADE                 | [TRADE](https://www.andaluciatrade.es/financiacion-empresarial/incentivos-para-las-empresas/) |

## Instalación

1. Clonar el repositorio

```
git clone https://github.com/mirarav/ConvocatorIAs
cd ConvocatorIAs
```

2. Configurar las variables de entorno (ver sección Configuración)

2. Construir los contenedores

```
docker-compose build
```

3. Iniciar los servicios

```
docker-compose up -d
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto con:

```
# Scraping
SCRAPING_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
SCRAPING_TIMEOUT=30
SCRAPING_MAX_RETRIES=3
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_SLOW_MO=50

# PostgreSQL
POSTGRES_DB=convocatorias
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[CONTRASEÑA]
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Azure OpenAI
AZURE_OPENAI_API_KEY=[CLAVE]
AZURE_OPENAI_ENDPOINT=https://[RECURSO].openai.azure.com
AZURE_OPENAI_API_VERSION=[VERSIÓN]
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

## Uso

### Interacción con el sistema

Conectar al contenedor en modo interativo:

```
docker attach app
```

### Comandos disponibles

1. Registrar nueva convocatoria

Ejemplo:

```
Registra la convocatoria https://www.cdti.es/ayudas/proyectos-de-i-d
```

2. Consultar convocatorias

Ejemplos:

```
Muestra todas las convocatorias
Busca convocatorias de ADER
```

3. Buscar consulta específica

Ejemplos:

```
¿Qué requisitos hay para la convocatoria de Proyectos de I+D de Transferencia Tecnológica?
¿Qué costes tiene la convocatoria de Proyectos de I+D de CDTI?
¿Qué beneficiarios tiene la Línea Directa de Expansión?
¿Cuál es el presupuesto para los Cheques de ADER?
```

4. Pedir ayuda

```
Ayuda
```

5. Cerrar sesión

```
Salir
```

### Generación de reportes

```
docker exec app python reportes.py
```

## Arquitectura

El sistema se compone de los siguientes archivos:

1. Agentes

* `rastreador/`: Extracción y validación de URLs y documentos
* `fragmentador/`: Procesamiento y vectorización de contenido
* `lLM/`: Completado de información con modelos de lenguaje
* `orquestador/`: Interfaz de usuario y coordinación

2. Núcleo

* `configuración/`: Gestión centralizada de parámetros
* `base_datos/`: Modelos y operaciones con PostgreSQL

3. Servicios

* `monitoreo/`: Recolección de métricas y generación de reportes
* `utilidades/`: Adaptadores y herramientas auxiliares

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta `LICENSE` para más información.

------

*Nota*: Para cualquier problema o consulta, por favor abra un issue en el repositorio del proyecto.