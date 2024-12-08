import requests
from fake_useragent import UserAgent
import random
import sqlite3
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time





# ----- Sector 1: Configuración Básica y Conexiones -----
class Configuración:
    def __init__(self, proxy_list=None, db_path="crawler_data.db"):
        self.proxy_list = proxy_list or []
        self.user_agent = UserAgent()
        self.db_path = db_path

    def rotate_proxy(self):
        """Selecciona un proxy aleatorio de la lista."""
        if self.proxy_list:
            return random.choice(self.proxy_list)
        return None

    def obtener_headers(self):
        """Genera encabezados con User-Agent aleatorio."""
        headers = {'User-Agent': self.user_agent.random}
        return headers

# ----- Sector 2: Extracción de URLs y Gestión de Recursos -----
class ExtracciónURLs:
    def __init__(self, config: Configuración):
        self.config = config
        self.visited_urls = set()

    def parse(self, base_url):
        """Solicita y analiza la página web para extraer enlaces."""
        proxy = self.config.rotate_proxy()
        headers = self.config.obtener_headers()

        try:
            response = requests.get(base_url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=10)
            response.raise_for_status()  # Verifica que la solicitud fue exitosa

            if 'text/html' not in response.headers.get('Content-Type', ''):
                print(f"Contenido no es HTML: {base_url}")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            self.extraer_links(base_url, soup)

        except requests.exceptions.RequestException as e:
            print(f"Error en la solicitud {base_url}: {e}")

    def extraer_links(self, base_url, soup):
        """Extrae URLs de la página web y las almacena si no han sido visitadas previamente."""
        for anchor_tag in soup.find_all('a', href=True):
            href = anchor_tag['href']
            full_url = urljoin(base_url, href)

            if full_url not in self.visited_urls:
                self.visited_urls.add(full_url)
                print(f"Nueva URL encontrada: {full_url}")

# ----- Sector 3: Análisis Dinámico (JavaScript y Selenium) -----
class AnalisisDinamico:
    def __init__(self):
        self.driver = None

    def iniciar_selenium(self):
        """Configura y abre Selenium WebDriver."""
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

    def analizar_con_selenium(self, url):
        """Obtiene la fuente HTML de una página cargada dinámicamente con Selenium."""
        self.driver.get(url)
        time.sleep(3)  # Espera para que se cargue el contenido dinámico
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup

    def cerrar_selenium(self):
        """Cierra el navegador Selenium."""
        if self.driver:
            self.driver.quit()

# ----- Sector 4: Almacenamiento y Persistencia de Datos (Base de Datos) -----
class Almacenamiento:
    def __init__(self, db_path="crawler_data.db"):
        self.db_path = db_path
        self._setup_database()

    def _setup_database(self):
        """Configura la base de datos SQLite para almacenar resultados."""
        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    status TEXT
                )
                """)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    asset_type TEXT,
                    asset_url TEXT
                )
                """)
                conn.commit()

    def almacenar_url(self, url, status="pending"):
        """Almacena URLs en la base de datos."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO urls (url, status) VALUES (?, ?)
            """, (url, status))
            conn.commit()

    def almacenar_asset(self, url, asset_type, asset_url):
        """Almacena activos como imágenes o scripts."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO assets (url, asset_type, asset_url) VALUES (?, ?, ?)
            """, (url, asset_type, asset_url))
            conn.commit()

# ----- Crawler Completo (Integración de todos los sectores) -----
class CrawlerCompleto:
    def __init__(self, proxy_list=None):
        self.config = Configuración(proxy_list)
        self.extraccion_urls = ExtracciónURLs(self.config)
        self.analisis_dinamico = AnalisisDinamico()
        self.almacenamiento = Almacenamiento()

    def ejecutar(self, start_url):
        """Inicia el proceso de crawling."""
        print(f"Iniciando el análisis de: {start_url}")
        self.extraccion_urls.parse(start_url)
        
        for url in self.extraccion_urls.visited_urls:
            self.almacenamiento.almacenar_url(url)

        # Si Selenium es necesario (para páginas con JS dinámico):
        self.analisis_dinamico.iniciar_selenium()
        for url in self.extraccion_urls.visited_urls:
            soup = self.analisis_dinamico.analizar_con_selenium(url)
            self.analizar_con_selenium(url)  # Procesa el contenido dinámico
            print(f"Contenido dinámico de {url}: {soup.title.string}")
        
        self.analisis_dinamico.cerrar_selenium()

if __name__ == "__main__":
    # Simula una lista de proxies
    proxies = ["http://proxy1", "http://proxy2"]
    
    # Iniciar el crawler
    crawler = CrawlerCompleto(proxy_list=proxies)
    start_url = "http://example.com"  # URL de inicio
    crawler.ejecutar(start_url)
