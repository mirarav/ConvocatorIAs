"""
Agente que coordina la todas las interacciones entre el usuario y los diferentes componentes del sistema.
"""

import json
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer

from nucleo.configuracion.configuracion import Config
from nucleo.base_datos.modelos import Database
from agentes.rastreador.gestor_extraccion import CrawlerAgent
from agentes.llm.gestor_llm import LLMAgent
from servicios.monitoreo.recolector_metricas import MetricasManager

class PromptManager:
    """Gestiona los prompts para cada tipo de consulta."""

    SYSTEM_PROMPTS = {
        'bienvenida': {
            "role": "system",
            "content": """Eres ConvocatorIAs, asistente experto en convocatorias públicas de ayudas en el ámbito español
            para proyectos de I+D+i. Tu misión es ayudar a emprendedores, investigadores y empresas a encontrar la 
            financiación adecuada para proyectos innovadores. Genera un menú de bienvenida para el usuario con:
            1. Mensaje de bienvenida: '👋🤖 ¡Hola! Soy ConvocatorIAs, tu asistente para encontrar ayudas públicas.'
            2. Breve descripción de tu propósito (1 párrafo)
            3. Mensaje de inicio: '¡Vamos a empezar! Primero, escribe 'ayuda' para conocer mis funcionalidades.'
            3. Mensaje de cierre: 'Recuerda que en cualquier momento puedes escribir 'salir' para cerrar la sesión.'
            Formato: Crea un mensaje claro y amigable de máximo 200 palabras. Haz saltos de línea para separar 
            las secciones. No uses MD, HTML o caracteres especiales."""
        },
        'ayuda': {
            "role": "system",
            "content": """Eres ConvocatorIAs, asistente experto en convocatorias públicas de ayudas en el ámbito español
            para proyectos de I+D+i. Tu misión es ayudar a emprendedores, investigadores y empresas a encontrar la 
            financiación adecuada para proyectos innovadores. Genera un menú de ayuda para el usuario con:
            1. Mensaje de bienvenida: '👋🤖 ¡Hola! Soy ConvocatorIAs, ...'
            2. Breve descripción de tu propósito (1 párrafo)
            3. Breve descripción de la tecnología que usas (1 párrafo)
            4. Breve listado de organismos que cubres (ADER, CDTI, Comunidad de Madrid y TRADE)
            5. Breve listado de funcionalidades:
               - Registrar y procesar convocatorias desde una URL
                    Ejemplo: 'Registra la convocatoria https://www.cdti.es/ayudas/proyectos-de-i-d'
                    Ejemplo: 'Añade la convocatoria https://www.ader.es/ayudas/ayudas-por-areas/i-d/idi-proyectos-de-i-d-i/'
               - Consultar convocatorias almacenadas en la base de datos
                    Ejemplo: 'Muestra todas las convocatorias'
                    Ejemplo: 'Busca convocatorias de CDTI'
               - Buscar criterios específicos de convocatorias
                    Ejemplo: '¿Qué requisitos hay para la convocatoria de Proyectos de I+D de Transferencia Tecnológica?'
                    Ejemplo: '¿Qué costes tiene la convocatoria de Proyectos de I+D de CDTI?'
                    Ejemplo: '¿Qué beneficiarios tiene la Línea Directa de Expansión?'
                    Ejemplo: '¿Cuál es el presupuesto para los Cheques de ADER?'
            Formato: Crea un mensaje claro y amigable de máximo 300 palabras. Haz saltos de línea para separar 
            las secciones. No uses MD, HTML, asteriscos ni caracteres especiales."""
        },
        'registro': {
            "role": "system", 
            "content": """Registra la convocatoria proporcionada por el usuario con los siguientes pasos:
            1. Validación URL (solo dominios autorizados)
            2. Extracción documentos asociados (PDFs)
            3. Procesamiento con IA:
               - Clasificación documento
               - Extracción metadatos
               - Generación embeddings
            4. Almacenamiento en DB:
               - PostgreSQL (datos estructurados)
               - pgvector (embeddings)
            5. Respuesta al usuario:
                - Mensaje de éxito: '🤖👍 He registrado la convocatoria con éxito.' + Salto de línea
                '📌 NOMBRE DE CONVOCATORIA EN MAYÚSCULAS (Organismo)'
                '🔗 Enlace' + Salto de línea
                '📄 DOCUMENTOS (Número documentos)' 
                '🔗 Enlace'
                - Mensaje de error: '👎🤖 No he podido registrar la convocatoria con éxito' + Explicación + Soluciones
            Formato: Crea un mensaje claro y amigable. No uses MD, HTML, asteriscos ni caracteres especiales."""
        },
        'consulta': {
            "role": "system",
            "content": """Muestra la información de convocatorias según los criterios especificados por el usuario.
            1. Búsqueda en DB de tabla 'convocatorias'.
            2. Respuesta al usuario:
                - Mensaje de éxito: '🤖👍 He encontrado la/s siguiente/s convocatoria/s.' + Salto de línea +
                Tabla datos estructurados + Lista de información detallada de cada convocatoria con sangría para cada emoji
                - Mensaje de error: '👎🤖 No he podido encontrar la/s convocatoria/s' + Explicación + Soluciones
            3. Plantilla de tabla de las convocatorias:
                - Encabezados descriptivos: Organismo y Número de convocatorias.
                - Alineación izquierda.
                - Bordes con guiones/pipes (|).
                - Orden descendiente por número de convocatorias.
            4. Plantilla de lista de las convocatorias:
                '📌 NOMBRE DE CONVOCATORIA EN MAYÚSCULAS (Organismo)'
                    '🎯 Objetivo: [objetivo]'
                    '📅 Plazo: [fecha_inicio] - [fecha_fin]'
                    '👥 Beneficiarios: [beneficiarios]'
                    '🌐 Área': [area]
                    '💰 Presupuesto: [presupuesto_minimo]€ - [presupuesto_maximo]€'
                    '⏳ Duración: [duracion_minimia] - [duracion_maxima]'
                    '💸 Subvención: [intensidad_subvencion]'
                    '🏦 Préstamo: [intensidad_prestamo]'
                    '📍 Región: [region_aplicacion]'
                    '🤝 Consorcio: [tipo_consorcio]'
                    '🧾 Costes: [costes_elegibles]'
                    '🔗 Enlace: [enlace_convocatoria] con https://'
            Formato: Crea un mensaje claro y amigable. No uses MD, HTML, asteriscos ni caracteres especiales. Recuerda que
            la fecha de hoy es 2025-05."""
        },
        'buscar': {
            "role": "system",
            "content": """Eres un experto en convocatorias públicas españolas. Tu tarea es responder preguntas sobre 
            convocatorias de I+D+i siguiendo estas reglas:
            1. Búsqueda en DB de tabla 'convocatorias'.
            2. Analiza el tipo de pregunta:
            - Pregunta general (ej: "¿Qué convocatorias...?"): Lista hasta 3 convocatorias relevantes.
            - Pregunta específica (ej: "¿Cuál es...?"): Responde directamente con la información solicitada.
            - Pregunta comparativa (ej: "¿Cuál tiene mayor...?"): Compara características.
            3. Plantilla para preguntas generales:
            '📌 NOMBRE DE CONVOCATORIA EN MAYÚSCULAS (Organismo)' + Salto de línea + Sangría
                '🎯 Objetivo: [objetivo]'
                '📅 Plazo: [fecha_inicio] - [fecha_fin]'
                '💰 Presupuesto: [presupuesto_minimo]€ - [presupuesto_maximo]€'
                '🔗 Enlace: [enlace_convocatoria] con https://'
            4. Plantilla para preguntas específicas:
            '📌 NOMBRE DE CONVOCATORIA (ORGANISMO)' + Salto de línea + Sangría + Lista de puntos clave y relevantes
            '📌 NOMBRE DE CONVOCATORIA (ORGANISMO)' + Salto de línea + Sangría + Lista de puntos clave y relevantes
            5. Siempre:
            - Sé conciso (máximo 50 palabras por punto)
            - Usa emojis para cada categoría
            - Si no encuentras información, sugiere refinar la búsqueda
            Formato: Crea un mensaje claro y amigable. No uses MD, HTML, asteriscos ni caracteres especiales. Recuerda que
            la fecha de hoy es 2025-05."""
        }
    }

    @classmethod
    def get_prompt(cls, tipo: str) -> Dict:
        """Obtiene el prompt estructurado para un tipo de consulta específica."""
        return cls.SYSTEM_PROMPTS.get(tipo.lower(), {
            "role": "system",
            "content": "Responde de manera clara y concisa"
        })
    
class TipoConsulta(Enum):
    AYUDA = auto()
    REGISTRAR = auto()
    CONSULTAR = auto()
    BUSCAR = auto()
    ESPECIFICA = auto()    

@dataclass
class ConsultaUsuario:
    texto: str
    tipo: TipoConsulta
    params: Dict = None

class Orquestador:
    """Agente principal de coordinación de todas las interacciones del usuario y los módulos del sistema."""
    
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.crawler = CrawlerAgent()
        self.llm = LLMAgent()
        self.metricas = MetricasManager()
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.organismos_permitidos = {'ader.es', 'cdti.es', 'comunidad.madrid', 'andaluciatrade.es'}

    def main(self):
        """Implementa la interfaz de usuario por consola."""
        bienvenida = self._generar_bienvenida()
        print("\n", bienvenida)
        
        while True:
            try:
                # Obtener entrada del usuario
                entrada = input("\n👤 ").strip()
                if entrada.lower() in ('salir', 'exit', 'quit'):
                    print("\n👋🤖 ¡Adiós!\n")
                    break
                    
                # Procesar la consulta del usuario
                resultado = self.procesar_consulta(entrada)
                if resultado.get('success'):
                    print("\n" + resultado['response'] + "\n")
                else:
                    print("\n" + resultado.get('error', 'Error desconocido') + "\n")
                    
            except KeyboardInterrupt:
                print("\n\nSaliendo del sistema...\n")
                break
            except Exception as e:
                print(f"\nError inesperado: {str(e)}\n")

    def _generar_bienvenida(self) -> str:
        """Genera un mensaje de bienvenida para el usuario."""
        respuesta = self.llm.client.chat.completions.create(
            model=self.config.LLM_CONFIG['deployment_name'],
            messages=[
                PromptManager.get_prompt('bienvenida'),
                {"role": "user", "content": "Genera un mensaje de bienvenida"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return respuesta.choices[0].message.content

    def procesar_consulta(self, input_usuario: str) -> Dict:
        """Flujo principal de procesamiento."""
        consulta = self._clasificar_consulta(input_usuario)
        
        try:
            if consulta.tipo == TipoConsulta.AYUDA:
                return self._generar_respuesta_ia(
                    PromptManager.get_prompt('ayuda'),
                    input_usuario
                )
                
            elif consulta.tipo == TipoConsulta.REGISTRAR:
                return self._procesar_registro(consulta)
                
            elif consulta.tipo == TipoConsulta.CONSULTAR:
                return self._generar_respuesta_ia(
                    PromptManager.get_prompt('consulta'),
                    self._obtener_datos_consulta(input_usuario)
                )
                
            else:
                return self._procesar_busqueda(consulta)
                
        except Exception as e:
            return self._generar_error(f"Error procesando consulta: {str(e)}")

    def _clasificar_consulta(self, texto: str) -> ConsultaUsuario:
        """Clasifica el tipo de consulta."""
        texto_lower = texto.lower()

        # Detectar preguntas específicas
        palabras_especificas = [
            'cuál', 'cuánto', 'cómo', 'qué', 'cuándo', 'dónde', 
            'quién', 'por qué', 'cuales', 'requisito', 'plazo', 
            'intensidad', 'consorcio', 'gasto', 'financiable', 
            'elegible', 'objetivo', 'duración', 'criterio'
        ]

        if any(palabra in texto_lower for palabra in palabras_especificas):
            return ConsultaUsuario(texto=texto, tipo=TipoConsulta.ESPECIFICA)        

        # Detecta si la consulta es de registro
        if any(palabra in texto.lower() for palabra in ["registra", "añade", "agrega"]):
            url = self._extraer_url(texto)
            if url:
                return ConsultaUsuario(texto=texto, tipo=TipoConsulta.REGISTRAR, params={'url': url})
            
        # Detectar si es una pregunta de búsqueda
        if any(palabra in texto.lower() for palabra in ["buscar", "encontrar", "recomendar", "aplicar", "para un"]):
            return ConsultaUsuario(texto=texto, tipo=TipoConsulta.BUSCAR)        

        # Usar IA para clasificar la consulta
        prompt = """Clasifica la consulta del usuario:
        1. AYUDA: Si pregunta sobre funcionalidades
        2. REGISTRAR: Si pide añadir nueva convocatoria
        3. CONSULTAR: Si solicita información general
        4. BUSCAR: Si hace pregunta específica
        
        Ejemplos:
        - "¿Cómo funciona?" → AYUDA
        - "Registra esta convocatoria" → REGISTRAR
        - "Muestra ayudas para PYMES" → CONSULTAR
        - "¿Qué porcentaje cubre?" → BUSCAR
        
        Devuelve solo el tipo en MAYÚSCULAS"""
        
        respuesta = self.llm.client.chat.completions.create(
            model=self.config.LLM_CONFIG['deployment_name'],
            messages=[{"role": "user", "content": f"{prompt}\n\nUsuario: {texto}"}],
            temperature=0
        )
        
        tipo = respuesta.choices[0].message.content.strip()
        return ConsultaUsuario(
            texto=texto,
            tipo=getattr(TipoConsulta, tipo, TipoConsulta.AYUDA),
            params=self._extraer_parametros(texto, tipo)
        )

    def _procesar_registro(self, consulta: ConsultaUsuario) -> Dict:
        """Gestiona el registro de nuevas convocatorias."""
        if not consulta.params.get('url'):
            return self._generar_error("No se detectó URL válida")
            
        if not self._validar_url(consulta.params['url']):
            return self._generar_error(
                f"🤖🫸 ¡Vaya! No soporto el dominio de la URL proporcionada. "
                f"Los dominios permitidos son {', '.join(self.organismos_permitidos)}"
            )
            
        print("\n🤏🤖 ¡Genial! Estoy procesando la URL proporcionada. Esto puede tomar unos minutos...")
        resultado = self.crawler.procesar_convocatoria(consulta.params['url'])
        return self._generar_respuesta_ia(
            PromptManager.get_prompt('registro'),
            str(resultado)
        )
    
    def _generar_respuesta_ia(self, prompt: Dict, contexto: str = "") -> Dict:
        """Genera respuesta con el prompt dado."""
        try:
            respuesta = self.llm.client.chat.completions.create(
                model=self.config.LLM_CONFIG['deployment_name'],
                messages=[prompt, {"role": "user", "content": contexto}],
                temperature=0.3,
                max_tokens=500
            )
            return {
                "success": True,
                "response": respuesta.choices[0].message.content,
                "contexto": contexto
            }
        except Exception as e:
            return self._generar_error(f"Error generando respuesta: {str(e)}")

    def _obtener_datos_consulta(self, texto: str) -> str:
        """Prepara datos estructurados para consultas."""
        # Detectar si es una consulta de búsqueda
        filtros = {}
        
        # Filtrar por organismo
        organismos = {
            'ader': 'ADER', 'rioja': 'ADER',
            'cdti': 'CDTI', 'estatal': 'CDTI',
            'madrid': 'Comunidad de Madrid',
            'trade': 'TRADE', 'andaluciatrade': 'TRADE', 'andalucía': 'TRADE'
        }
        
        for clave, valor in organismos.items():
            if clave in texto.lower():
                filtros['organismo'] = valor
                break
                
        # Obtener convocatorias filtradas
        convocatorias = self.db.obtener_convocatorias(filtros)
        
        # Formatear respuesta
        if not convocatorias:
            return "No se encontraron convocatorias con los criterios especificados"
            
        resumen = f"Convocatorias encontradas: {len(convocatorias)}\n\n"
        resumen += "\n".join(
            f"- {conv['nombre'] or 'Sin nombre'} ({conv['organismo']})" 
            for conv in convocatorias[:10]  # Limitar a 10 resultados
        )
        
        if len(convocatorias) > 10:
            resumen += f"\n\n... y {len(convocatorias) - 10} más"
            
        return resumen

    def _validar_url(self, url: str) -> bool:
        """Valida que la URL pertenezca a un organismo permitido."""
        try:
            dominio = urlparse(url).netloc.lower()
            return any(org in dominio for org in self.organismos_permitidos)
        except:
            return False

    def _generar_error(self, mensaje: str) -> Dict:
        """Estandariza respuestas de error"""
        return {
            "success": False,
            "error": mensaje,
            "response": f"⚠️ {mensaje}"
        }

    def _extraer_parametros(self, texto: str, tipo: str) -> Dict:
        """Extrae parámetros clave según el tipo de consulta."""
        params = {}
        
        if tipo == "REGISTRAR":
            params['url'] = self._extraer_url(texto)
        elif tipo == "CONSULTAR":
            # Podemos extraer filtros adicionales
            pass
            
        return params

    def _extraer_url(self, texto: str) -> Optional[str]:
        """Extrae la primera URL válida del texto."""
        # Buscar patrones comunes de URLs
        palabras = texto.split()
        for palabra in palabras:
            if palabra.startswith(('http://', 'https://')):
                return palabra
            if '.' in palabra and '/' in palabra:
                return f"https://{palabra}"
        return None

    def _procesar_busqueda(self, consulta: ConsultaUsuario) -> Dict:
        """Gestiona búsquedas semánticas y por criterios específicos."""
        try:
            # Interpretar la consulta para extraer criterios
            criterios = self._interpretar_consulta(consulta.texto)
            
            # Búsqueda semántica
            embedding = self.embedder.encode(consulta.texto)
            chunks = self.db.buscar_semantica(embedding.tolist(), limite=10)
            
            contexto = f"Consulta: {consulta.texto}\n"
            
            if chunks:
                contexto += "Información relevante encontrada:\n"
                for i, chunk in enumerate(chunks[:3], 1):
                    contexto += f"{i}. {chunk['chunk_texto'][:200]}...\n"
            
            # Búsqueda por criterios si se detectaron
            if criterios:
                convocatorias = self.db.buscar_convocatorias_por_criterios(criterios)
                if convocatorias:
                    contexto += "\nConvocatorias relevantes:\n"
                    for conv in convocatorias[:3]:
                        contexto += f"- {conv.get('nombre', 'Sin nombre')} ({conv.get('organismo', '')})\n"
            
            return self._generar_respuesta_ia(
                PromptManager.get_prompt('buscar'),
                contexto
            )
                
        except Exception as e:
            return self._generar_error(f"Error en búsqueda: {str(e)}")

    def _interpretar_consulta(self, texto: str) -> Dict:
        """Interpreta la consulta del usuario para extraer criterios de búsqueda."""
        prompt = f"""Analiza la siguiente consulta y extrae criterios de búsqueda:

        Consulta: "{texto}"

        Devuelve un JSON con campos posibles:
        - organismo (ADER, CDTI, etc)
        - area (I+D, Innovación, Inversión, etc)
        - tipo_empresa (PYME, gran empresa)
        - tipo_proyecto (digitalización, investigación, etc)
        - caracteristica_especifica (plazo, intensidad_ayuda, consorcio, etc)
        - consulta_texto (texto para búsqueda semántica)

        Ejemplos:
        Input: "¿Qué convocatorias para digitalización en pymes?"
        Output: {{"tipo_empresa": "PYME", "tipo_proyecto": "digitalización"}}

        Input: "¿Cuál es la intensidad de ayuda para grandes empresas?"
        Output: {{"caracteristica_especifica": "intensidad_ayuda", "tipo_empresa": "gran empresa"}}"""

        try:
            respuesta = self.llm.client.chat.completions.create(
                model=self.config.LLM_CONFIG['deployment_name'],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            return json.loads(respuesta.choices[0].message.content)
        except:
            return {"consulta_texto": texto}