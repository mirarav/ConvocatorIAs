"""
Módulo para extraer texto y tablas de documentos PDF.
"""

import io
import pdfplumber
from typing import List, Dict

class PdfContentExtractor:
    """Extrae texto y tablas estructuradas de documentos PDF."""
    
    def extract_text(self, pdf_stream: io.BytesIO) -> List[Dict]:
        """Extrae el contenido textual y tabular de cada página de un PDF."""
        try:
            with pdfplumber.open(pdf_stream) as pdf:
                paginas = []
                
                for pagina_num, pagina in enumerate(pdf.pages, start=1):
                    try:
                        # Extraer texto simple de la página
                        texto = pagina.extract_text() or ""
                        
                        # Extraer tablas con configuración mejorada
                        tablas = pagina.extract_tables({
                            "vertical_strategy": "lines", 
                            "horizontal_strategy": "lines",
                            "intersection_y_tolerance": 10,
                            "intersection_x_tolerance": 10,
                            "text_tolerance": 3,
                            "text_x_tolerance": 3,
                            "text_y_tolerance": 3
                        })
                    
                        # Procesar tablas y convertirlas a texto estructurado
                        texto_tablas = self._procesar_tablas(tablas, pagina_num)
                        
                        # Combinar texto y tablas
                        texto_completo = texto + "\n\n" + texto_tablas if texto_tablas else texto

                        if texto_completo.strip():
                            paginas.append({
                                'numero_pagina': pagina_num,
                                'texto': texto_completo,
                                'dimensiones': (pagina.width, pagina.height),
                                'tiene_tablas': len(tablas) > 0,
                                'num_tablas': len(tablas)
                            })
                    except Exception as e:
                        print(f"Error extrayendo texto de página {pagina_num}: {str(e)}")
                        continue

                if not paginas:
                    print("No se pudo extraer texto de ninguna página del PDF")
                    return []

                return paginas
        except pdfplumber.PDFSyntaxError as e:
            print(f"Error de sintaxis en el PDF: {str(e)}")
            return []
        except Exception as e:
            print(f"Error inesperado al procesar PDF: {str(e)}")
            return []
        
    def _procesar_tablas(self, tablas: List, pagina_num: int) -> str:
        """Convierte tablas extraídas de PDF a texto estructurado."""
        texto_tablas = ""
        
        for i, tabla in enumerate(tablas, 1):
            try:
                # Establecer encabezados como primera fila
                encabezados = tabla[0] if tabla else []
                
                # Establecer filas de datos
                filas = tabla[1:] if len(tabla) > 1 else []
                
                # Construir representación textual con marcado especial
                texto_tabla = f"\n--- TABLA {i} PÁG {pagina_num} ---\n"
                
                if encabezados:
                    # Procesar encabezados
                    texto_encabezados = " | ".join(
                        str(h).strip() if h is not None else "" 
                        for h in encabezados
                    )
                    texto_tabla += f"CABECERA: {texto_encabezados}\n"
                    texto_tabla += "-" * (sum(len(str(h)) for h in encabezados if h)) + "\n"
                
                # Procesar filas de datos
                for fila_num, fila in enumerate(filas, 1):
                    texto_fila = " | ".join(
                        str(celda).strip() if celda is not None else "" 
                        for celda in fila
                    )
                    texto_tabla += f"FILA {fila_num}: {texto_fila}\n"
                
                texto_tablas += texto_tabla + "\n"
                
            except Exception as e:
                print(f"Error procesando tabla {i}: {str(e)}")
                continue
        
        return texto_tablas