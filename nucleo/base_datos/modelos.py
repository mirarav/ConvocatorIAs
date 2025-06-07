"""
Módulo para gestionar la base de datos PostgreSQL con extensión pgvector.
"""

import psycopg2
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Union

from nucleo.configuracion.configuracion import Config

@dataclass
class QueryResult:
    """Estandariza los resultados de consultas a la base de datos."""
    success: bool
    data: Union[List[Dict], Dict, None]
    message: str
    affected_rows: int = 0

    def __len__(self) -> int:
        """Devuelve la cantidad de elementos en los datos."""
        if self.data is None:
            return 0
        if isinstance(self.data, dict):
            return 1
        return len(self.data)

    def __bool__(self) -> bool:
        """Evalúa si la consulta fue exitosa."""
        return self.success

    def __iter__(self):
        """Permite iterar sobre los datos."""
        if isinstance(self.data, list):
            return iter(self.data)
        if isinstance(self.data, dict):
            return iter([self.data])
        return iter([])

class Database:
    """Agente principal de gestión de las operaciones con la base de datos."""

    def __init__(self):
        """Inicializa la conexión a la base de datos."""
        self.config = Config()
    
    def _get_connection(self):
        """Establece la conexión a la base de datos."""
        return psycopg2.connect(
            host=self.config.DB_CONFIG['host'],
            port=self.config.DB_CONFIG['port'],
            dbname=self.config.DB_CONFIG['dbname'],
            user=self.config.DB_CONFIG['user'],
            password=self.config.DB_CONFIG['password'],
            connect_timeout=5  # Timeout de conexión de 5 segundos
        )

    def verificar_crear_tablas(self) -> bool:
        """Verifica y crea las tablas si no existen."""
        try:
            # Verificar si la tabla convocatorias existe
            result = self._execute_query(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'convocatorias')",
                fetch=True
            )
            if not result.success:
                return False
            # Si la tabla no existe, crear todas las tablas
            if not result.data or not result.data.get('exists', False):
                return self._crear_tablas()
            return True
        except Exception as e:
            return False

    def _crear_tablas(self) -> bool:
        """Ejecuta el script SQL para crear las tablas."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    with open('nucleo/base_datos/esquema.sql', 'r') as f:
                        cur.execute(f.read())
                    conn.commit()
                    return True
        except Exception:
            return False

    def _execute_query(self, query: str, params: Tuple = None, fetch: bool = False, many: bool = False) -> QueryResult:
        """Ejecuta una consulta SQL genérica con manejo de errores."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params or ())
                    
                    result = None
                    if fetch:
                        if many:
                            columnas = [desc[0] for desc in cur.description]
                            result = [dict(zip(columnas, fila)) for fila in cur.fetchall()]
                        else:
                            columnas = [desc[0] for desc in cur.description]
                            row = cur.fetchone()
                            result = dict(zip(columnas, row)) if row else None
                    
                    conn.commit()
                    return QueryResult(
                        success=True,
                        data=result,
                        message="Operación exitosa",
                        affected_rows=cur.rowcount
                    )
        except psycopg2.Error as e:
            return QueryResult(
                success=False,
                data=None,
                message=str(e),
                affected_rows=0
            )

    # --- Métodos para convocatorias ---

    def insertar_convocatoria(self, campos: Dict) -> Tuple[bool, str, Optional[int]]:
        """Inserta una nueva convocatoria en la base de datos."""
        result = self._execute_query(
            """INSERT INTO convocatorias (organismo, enlace_convocatoria) 
               VALUES (%(organismo)s, %(enlace_convocatoria)s) RETURNING id""",
            campos,
            fetch=True
        )
        
        if result.success and result.data:
            return True, result.message, result.data['id']
        return False, result.message, None

    def obtener_convocatoria_por_url(self, url: str) -> Optional[Dict]:
        """Obtiene una convocatoria por su URL."""
        result = self._execute_query(
            "SELECT * FROM convocatorias WHERE enlace_convocatoria = %s",
            (url,),
            fetch=True
        )
        return result.data if result.success else None
    
    def obtener_convocatorias(self, filtros: Dict = None) -> List[Dict]:
        """Obtiene convocatorias con filtros opcionales."""
        query = "SELECT * FROM convocatorias"
        params = []
        
        if filtros:
            conditions = []
            for key, value in filtros.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id"
        result = self._execute_query(
            query,
            tuple(params),
            fetch=True,
            many=True
        )
        return result.data if result.success else []    

    # --- Métodos para documentos ---

    def insertar_documento(self, datos: Dict) -> Tuple[bool, str, Optional[int]]:
        """Inserta un nuevo documento o devuelve el existente si ya está registrado."""
        campos_requeridos = ['tipo_mime', 'hash_sha256', 'enlace_documento']
        for campo in campos_requeridos:
            if campo not in datos:
                return False, f"Falta campo requerido: {campo}", None
        # Proporcionar valores por defecto para campos opcionales
        datos.setdefault('titulo', '')
        datos.setdefault('tipo_documento', None)
        datos.setdefault('numero_paginas', 0)
        datos.setdefault('tamano_bytes', 0)
        datos.setdefault('ultima_modificacion', None)
        # Verificar si ya existe
        existente = self.documento_existe_por_hash(datos['hash_sha256'])
        if existente:
            return True, "Documento ya existente", existente['id']
        result = self._execute_query(
            """INSERT INTO documentos 
               (titulo, tipo_mime, tipo_documento, numero_paginas,
                tamano_bytes, hash_sha256, enlace_documento, ultima_modificacion) 
               VALUES (%(titulo)s, %(tipo_mime)s, %(tipo_documento)s, %(numero_paginas)s,
                      %(tamano_bytes)s, %(hash_sha256)s, %(enlace_documento)s, %(ultima_modificacion)s)
               RETURNING id""",
            datos,
            fetch=True
        )
        if result.success and result.data:
            return True, result.message, result.data['id']
        return False, result.message, None

    def documento_existe_por_hash(self, hash_sha256: str) -> Optional[Dict]:
        """Verifica si un documento existe por su hash SHA256."""
        result = self._execute_query(
            "SELECT * FROM documentos WHERE hash_sha256 = %s",
            (hash_sha256,),
            fetch=True
        )
        return result.data if result.success else None

    # --- Métodos para relaciones ---

    def asociar_documento_convocatoria(self, convocatoria_id: int, documento_id: int) -> bool:
        """Crea una relación entre una convocatoria y un documento."""
        result = self._execute_query(
            """INSERT INTO convocatorias_documentos
               (convocatoria_id, documento_id) VALUES (%s, %s)
               ON CONFLICT DO NOTHING""",
            (convocatoria_id, documento_id)
        )
        return result.success
    
    def obtener_documentos_por_convocatoria(self, convocatoria_id: int) -> List[Dict]:
        """Obtiene documentos asociados a una convocatoria."""
        result = self._execute_query(
            """SELECT d.* FROM documentos d
               JOIN convocatorias_documentos cd ON d.id = cd.documento_id
               WHERE cd.convocatoria_id = %s
               ORDER BY d.id""",
            (convocatoria_id,),
            fetch=True,
            many=True
        )
        return result.data if result.success else []
    
    def obtener_convocatorias_por_documento(self, documento_id: int) -> List[Dict]:
        """Obtiene todas las convocatorias asociadas a un documento."""
        result = self._execute_query(
            """SELECT c.* FROM convocatorias c
                JOIN convocatorias_documentos cd ON c.id = cd.convocatoria_id
                WHERE cd.documento_id = %s
                ORDER BY c.id""",
            (documento_id,),
            fetch=True,
            many=True
        )
        return result.data if result.success else []
    
    # --- Métodos para chunks ---

    def insertar_chunk_documento(self, documento_id: int, chunk_texto: str, chunk_vector: List[float], 
                                 titulo_seccion: str = None, numero_pagina: int = None) -> bool:
        """Inserta un chunk de documento con su embedding vectorial."""
        result = self._execute_query(
            """INSERT INTO documentos_chunks
               (documento_id, chunk_texto, chunk_vector, titulo_seccion, numero_pagina)
               VALUES (%s, %s, %s, %s, %s)""",
            (documento_id, chunk_texto, chunk_vector, titulo_seccion, numero_pagina)
        )
        return result.success
    
    def obtener_chunks_por_documento(self, documento_id: int, limite: int = None) -> QueryResult:
        """Obtiene chunks de un documento específico."""
        query = """
            SELECT * FROM documentos_chunks
            WHERE documento_id = %s
            ORDER BY numero_pagina, id
        """
        params = [documento_id]
        if limite:
            query += " LIMIT %s"
            params.append(limite)
            
        return self._execute_query(query, tuple(params), fetch=True, many=True)

    def obtener_chunks_con_tablas(self, documento_id: int, limite: int = 5) -> List[Dict]:
        """Obtiene chunks que contienen tablas de un documento específico."""
        result = self._execute_query(
            """SELECT * FROM documentos_chunks 
            WHERE documento_id = %s AND titulo_seccion LIKE 'TABLA%%'
            ORDER BY numero_pagina LIMIT %s""",
            (documento_id, limite),
            fetch=True,
            many=True
        )
        return result.data if result.success else []

    # --- Métodos para actualización ---

    def actualizar_campo_convocatoria(self, convocatoria_id: int, campo: str, valor: str) -> bool:
        """Actualiza un campo específico de una convocatoria."""
        campos_validos = [
            'nombre', 'linea', 'fecha_inicio', 'fecha_fin', 'objetivo', 'beneficiarios', 'anio', 
            'area', 'presupuesto_minimo', 'presupuesto_maximo', 'duracion_minima', 'duracion_maxima',
            'intensidad_subvencion', 'intensidad_prestamo', 'tipo_financiacion', 'forma_plazo_cobro', 
            'minimis', 'region_aplicacion', 'tipo_consorcio', 'costes_elegibles', 'enlace_ficha_tecnica',
            'enlace_orden_bases'
        ]
        if campo not in campos_validos:
            return False
        result = self._execute_query(
            f"UPDATE convocatorias SET {campo} = %s WHERE id = %s",
            (valor, convocatoria_id)
        )
        return result.success

    def actualizar_campo_documento(self, documento_id: int, campo: str, valor: str) -> bool:
        """Actualiza un campo específico de un documento."""
        campos_validos = ['titulo', 'tipo_documento', 'numero_paginas', 'es_comun']
        if campo not in campos_validos:
            return False
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE documentos SET {campo} = %s WHERE id = %s",
                        (valor, documento_id)
                    )
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            print(f"Error actualizando campo {campo} del documento {documento_id}: {str(e)}")
            return False
        
    def actualizar_enlace_ficha_tecnica_convocatoria(self, convocatoria_id: int, enlace: str) -> bool:
        """Actualiza el enlace a la ficha técnica de una convocatoria."""
        try:
            # Obtener el valor actual
            conv = self.obtener_convocatorias_por_ids([convocatoria_id])
            if not conv:
                return False
            actual = conv[0].get('enlace_ficha_tecnica', '')
            # Añadir el nuevo enlace
            if actual and enlace not in actual:
                nuevo_valor = f"{actual}\n{enlace}"
            else:
                nuevo_valor = enlace
            return self._execute_query(
                "UPDATE convocatorias SET enlace_ficha_tecnica = %s WHERE id = %s",
                (nuevo_valor, convocatoria_id)
            ).success
        except Exception as e:
            print(f"Error actualizando ficha técnica: {str(e)}")
            return False

    def actualizar_enlace_orden_bases_convocatoria(self, convocatoria_id: int, enlace: str) -> bool:
        """Actualiza el enlace a la orden de bases de una convocatoria."""
        try:
            # Obtener el valor actual
            conv = self.obtener_convocatorias_por_ids([convocatoria_id])
            if not conv:
                return False
            actual = conv[0].get('enlace_orden_bases', '')
            # Añadir el nuevo enlace
            if actual and enlace not in actual:
                nuevo_valor = f"{actual}\n{enlace}"
            else:
                nuevo_valor = enlace
            return self._execute_query(
                "UPDATE convocatorias SET enlace_orden_bases = %s WHERE id = %s",
                (nuevo_valor, convocatoria_id)
            ).success
        except Exception as e:
            print(f"Error actualizando orden de bases: {str(e)}")
            return False        

    # --- Métodos para consulta ---

    def documento_existe_por_id(self, documento_id: int) -> Optional[Dict]:
        """Obtiene un documento por ID."""
        result = self._execute_query(
            "SELECT * FROM documentos WHERE id = %s",
            (documento_id,),
            fetch=True
        )
        return result.data if result.success else None

    def documento_tiene_chunks(self, documento_id: int) -> bool:
        """Verifica si un documento tiene chunks asociados."""
        result = self._execute_query(
            "SELECT COUNT(*) FROM documentos_chunks WHERE documento_id = %s",
            (documento_id,),
            fetch=True
        )
        return result.data['count'] > 0 if result.success else False

    def obtener_documentos_por_ids(self, ids: List[int]) -> List[Dict]:
        """Obtiene documentos por una lista de IDs."""
        result = self._execute_query(
            "SELECT * FROM documentos WHERE id = ANY(%s) ORDER BY id",
            (ids,),
            fetch=True,
            many=True
        )
        return result.data if result.success else []

    def obtener_convocatorias_por_ids(self, ids: List[int]) -> List[Dict]:
        """Obtiene convocatorias por una lista de IDs."""
        result = self._execute_query(
            "SELECT * FROM convocatorias WHERE id = ANY(%s) ORDER BY id",
            (ids,),
            fetch=True,
            many=True
        )
        return result.data if result.success else []

    # --- Métodos para búsquedas ---

    def buscar_chunks_por_similitud(self, documento_id: int, vector_consulta: List[float], limite: int = 3) -> List[Dict]:
        """Busca chunks similares usando embeddings vectoriales."""
        result = self._execute_query(
            """SELECT id, chunk_texto, numero_pagina,
               1 - (chunk_vector <=> %s::vector) as similitud
               FROM documentos_chunks
               WHERE documento_id = %s
               ORDER BY similitud DESC
               LIMIT %s""",
            (vector_consulta, documento_id, limite),
            fetch=True,
            many=True
        )
        return result.data if result.success else []
    
    def buscar_semantica(self, vector_consulta: List[float], limite: int = 5) -> List[Dict]:
        """Realiza búsqueda semántica en los chunks de documentos usando embeddings."""
        try:
            result = self._execute_query(
                """SELECT dc.id, 
                    dc.chunk_texto, 
                    dc.numero_pagina,
                    dc.documento_id,
                    d.titulo as documento_titulo, 
                    d.enlace_documento,
                    1 - (dc.chunk_vector <=> %s::vector) as similitud
                FROM documentos_chunks dc
                JOIN documentos d ON dc.documento_id = d.id
                WHERE 1 - (dc.chunk_vector <=> %s::vector) > 0.25
                ORDER BY similitud DESC
                LIMIT %s""",
                (vector_consulta, vector_consulta, limite),
                fetch=True,
                many=True
            )
            return result.data if result.success else []
        except Exception as e:
            print(f"Error en búsqueda semántica: {str(e)}")
            return []

    def buscar_convocatorias_por_criterios(self, criterios: Dict) -> List[Dict]:
        """Busca convocatorias que coincidan con criterios específicos."""
        try:
            query = "SELECT * FROM convocatorias WHERE "
            conditions = []
            params = []
            
            # Mapeo de campos de criterios a columnas de la base de datos
            mapeo_campos = {
                'organismo': 'organismo',
                'area': 'area',
                'tipo_empresa': 'beneficiarios',
                'tipo_proyecto': 'linea',
                'caracteristica_especifica': None  # Búsqueda semántica
            }
            
            for clave, valor in criterios.items():
                columna = mapeo_campos.get(clave)
                
                if columna:
                    conditions.append(f"LOWER({columna}) LIKE LOWER(%s)")
                    params.append(f"%{valor}%")
                elif clave == 'consulta_texto':
                    # Búsqueda semántica ya realizada
                    continue
            
            if not conditions:
                return []
                
            query += " AND ".join(conditions) + " LIMIT 5"
            result = self._execute_query(query, tuple(params), fetch=True, many=True)
            return result.data if result.success else []
        except Exception as e:
            print(f"Error buscando convocatorias: {str(e)}")
            return []