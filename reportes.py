"""
Interfaz para generar y mostrar reportes de métricas del sistema.
"""

from servicios.monitoreo.generador_reportes import ReportGenerator

def mostrar_reporte_general(dias: int = 1):
    """Muestra un reporte general de rendimiento."""
    generador = ReportGenerator()
    reporte = generador.generar_reporte_rendimiento(dias)
    
    print("\n📈 REPORTE DE RENDIMIENTO DEL SISTEMA")
    
    # Resumen ejecutivo
    resumen = reporte['resumen']
    print("\n🔍 RESUMEN EJECUTIVO")
    print(f"- Convocatorias procesadas: {resumen['convocatorias_procesadas']}")
    print(f"- Documentos procesados: {resumen['documentos_procesados']}")
    print(f"- Chunks generados: {resumen['chunks_generados']}")
    print(f"- Llamadas al LLM: {resumen['llamadas_llm']}")
    print(f"- Tasa de éxito promedio: {resumen['tasa_exito_promedio']:.2f}%")
    print(f"- Tiempo respuesta LLM promedio: {resumen['tiempo_respuesta_llm_promedio']:.2f} segundos")
    
    # Detalle por área
    print("\n📊 MÉTRICAS DETALLADAS")
    
    # Extracción
    if 'extraccion' in reporte and reporte['extraccion']['total_registros'] > 0:
        print("1. Extracción:")
        print(f"   - Cobertura organismos: {reporte['extraccion']['promedios'].get('cobertura_organismos', 0):.2f}%")
        print(f"   - Tiempo promedio por convocatoria: {reporte['extraccion']['promedios'].get('tiempo_promedio', 0):.2f} segundos")
    
    # Procesamiento
    if 'procesamiento' in reporte and reporte['procesamiento']['total_registros'] > 0:
        print("\n2. Procesamiento:")
        print(f"   - Tasa texto principal: {reporte['procesamiento']['promedios'].get('tasa_texto_principal', 0):.2f}%")
        print(f"   - Tamaño promedio chunks: {reporte['procesamiento']['promedios'].get('tamano_promedio_chunks', 0):.2f} caracteres")
    
    # LLM
    if 'llm' in reporte and reporte['llm']['total_registros'] > 0:
        print("\n3. LLM:")
        print(f"   - Tiempo respuesta texto corto: {reporte['llm']['promedios'].get('tiempo_respuesta_texto_corto', 0):.4f} segundos")
        print(f"   - Tiempo respuesta tablas: {reporte['llm']['promedios'].get('tiempo_respuesta_tablas', 0):.4f} segundos")
    
    # Búsqueda (solo si hay datos)
    if 'busqueda' in reporte and reporte['busqueda']['total_registros'] > 0:
        print("\n4. Búsqueda:")
        print(f"   - Tiempo respuesta búsqueda vectorial: {reporte['busqueda']['promedios'].get('tiempo_respuesta_vectorial', 0):.4f} segundos")

def main():
    """Función principal para la interfaz de reportes."""
    print("\n📊 Sistema de Reportes de Métricas")
    
    while True:
        try:
            dias_input = input("\nIngrese número de días a analizar (1-7, default 1): ").strip()
            dias = int(dias_input) if dias_input.isdigit() and 1 <= int(dias_input) <= 7 else 1
            
            mostrar_reporte_general(dias)
            
            continuar = input("\n¿Desea generar otro reporte? (s/n): ").strip().lower()
            if continuar != 's':
                print("\nSaliendo del sistema de reportes...\n")
                break
                
        except KeyboardInterrupt:
            print("\n\nSaliendo del sistema de reportes...\n")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Por favor, intente nuevamente.\n")

if __name__ == '__main__':
    main()