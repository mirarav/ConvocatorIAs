"""
Módulo para extraer URLs de documentos PDF con manejo de reintentos y expansión de secciones ocultas.
"""

import time
from typing import List
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class PdfUrlExtractor:
    """Extrae URLs de de documentos PDF desde una página web."""

    def __init__(self, config):
        self.config = config

    def _expandir_secciones_ocultas(self, page):
        """Expande secciones colapsadas o con contenido oculto de la página."""
        selectores = [
            'button[aria-expanded="false"]',
            '.accordion-button:not(.collapsed)',
            '.show-more',
            '.expand-section',
            '[data-toggle="collapse"]'
        ]
        
        for selector in selectores:
            elements = page.query_selector_all(selector)
            for element in elements:
                try:
                    element.click()
                    page.wait_for_timeout(300)
                except Exception:
                    continue

    def extraer_pdfs(self, url: str, max_retries: int, base_wait_time: int, silent: bool) -> List[str]:
        """Extrae URLs de documentos PDF de la página especificada."""
        pdf_urls = set()
        retries = 0

        while retries < max_retries:
            try:
                with sync_playwright() as p:
                    # Lanzar navegador con opciones avanzadas
                    browser = p.chromium.launch(
                        headless=self.config.SCRAPING_CONFIG['headless'],
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--ignore-certificate-errors',
                            '--start-maximized',
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage'
                        ],
                        timeout=30000
                    )
                    context = browser.new_context(
                        user_agent=self.config.SCRAPING_CONFIG['user_agent'],
                        viewport={'width': 1920, 'height': 1080},
                        ignore_https_errors=True,
                        java_script_enabled=True,
                        bypass_csp=True
                    )

                    # Configurar tiempo de espera más largo para páginas pesadas
                    page = context.new_page()
                    page.set_default_timeout(30000)
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    page.wait_for_timeout(5000)
                    
                    # Verificar si la página contiene CAPTCHA
                    if "captcha" in page.content().lower() and not silent:
                        print(f"Advertencia: CAPTCHA detectado en {url}")
                        break

                    self._expandir_secciones_ocultas(page)
                    
                    all_links = []
                    try:
                        all_links = page.eval_on_selector_all(
                            'a[href], [role="link"][href], [data-href], [data-pdf]',
                            '''elements => elements.map(el => {
                                try {
                                    return el.href || el.getAttribute('data-href') || 
                                           el.getAttribute('data-pdf') || null;
                                } catch (e) {
                                    return null;
                                }
                            }).filter(Boolean)'''
                        )
                    except Exception as e:
                        if not silent: print(f"Error extraer enlaces: {str(e)}")
                    
                    # Filtrar y validar enlaces
                    for link in all_links:
                        if link.lower().endswith('.pdf') or 'pdf' in link.lower():
                            absolute_url = urljoin(url, link)
                            if absolute_url.startswith('http'):
                                pdf_urls.add(absolute_url)

                    # Buscar iframes y embeds que contengan PDFs
                    iframes = page.query_selector_all('iframe, embed')
                    for iframe in iframes:
                        try:
                            src = iframe.get_attribute('src')
                            if src and ('pdf' in src.lower() or src.lower().endswith('.pdf')):
                                absolute_url = urljoin(url, src)
                                if absolute_url.startswith('http'):
                                    pdf_urls.add(absolute_url)
                        except Exception: continue
                    
                    context.close()
                    browser.close()
                    return list(pdf_urls)
                    
            except PlaywrightTimeoutError:
                retries, wait_time = self._manejar_reintento(retries, max_retries, base_wait_time, silent)
                time.sleep(wait_time)
            except Exception as e:
                retries, wait_time = self._manejar_reintento(retries, max_retries, base_wait_time, silent)
                if not silent: print(f"Error Playwright: {str(e)}")
                time.sleep(wait_time)
        
        return list(pdf_urls)

    def _manejar_reintento(self, retries: int, max_retries: int, base_wait_time: int, silent: bool):
        """Calcula el tiempo de espera y actualiza el contador de reintentos."""
        retries += 1
        wait_time = base_wait_time * (2 ** retries)
        if retries < max_retries and not silent:
            print(f"Reintentando en {wait_time} segundos...")
        return retries, wait_time