import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fake_useragent import UserAgent
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from requests.exceptions import RequestException
from multiprocessing import Pool
import logging
import sqlite3
import os

class SophisticatedCrawler:
    def __init__(self, proxy_list=None, db_path="crawler_data.db"):
        self.visited_urls = set()
        self.proxy_list = proxy_list or []
        self.user_agent = UserAgent()
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

    def _store_url(self, url, status="pending"):
        """Almacena URLs en la base de datos."""
        with sqlite3.connect(self.h) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO urls (url, status) VALUES (?, ?)
            """, (url, status))
            conn.commit()

    def _store_asset(self, url, asset_type, asset_url):
        """Almacena activos como imágenes o scripts."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO assets (url, asset_type, asset_url) VALUES (?, ?, ?)
            """, (url, asset_type, asset_url))
            conn.commit()

    def rotate_proxy(self):
        """Selecciona un proxy aleatorio de la lista."""
        if self.proxy_list:
            return random.choice(self.proxy_list)
        return None

    def parse(self, base_url, use_selenium=False):
        """Analiza las URLs y extrae activos."""
        proxy = self.rotate_proxy()
        headers = {'User-Agent': self.user_agent.random}

        try:
            if use_selenium:
                self._parse_with_selenium(base_url)
            else:
                response = requests.get(base_url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=10)
                response.raise_for_status()
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    print(f"Contenido no es HTML: {base_url}")
                    return
                soup = BeautifulSoup(response.text, 'html.parser')
                self._extract_links(base_url, soup)
                self._extract_assets(base_url, soup)

        except RequestException as e:
            logging.error(f"Error en la solicitud {base_url}: {e}")

    def _parse_with_selenium(self, url):
        """Usa Selenium para analizar páginas dinámicas con JavaScript."""
        options = Options()
        options.headless = True
        options.add_argument(f"user-agent={self.user_agent.random}")
        service = Service('/path/to/chromedriver')  # Actualiza con la ruta a tu chromedriver

        with webdriver.Chrome(service=service, options=options) as driver:
            driver.get(url)
            time.sleep(random.uniform(2, 5))  # Espera aleatoria
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            self._extract_links(url, soup)
            self._extract_assets(url, soup)

    def _extract_links(self, base_url, soup):
        """Extrae y almacena enlaces válidos."""
        for anchor_tag in soup.find_all('a', href=True):
            href = anchor_tag['href']
            full_url = urljoin(base_url, href)
            if full_url not in self.visited_urls:
                self.visited_urls.add(full_url)
                self._store_url(full_url)
                print(f"Nueva URL: {full_url}")

    def _extract_assets(self, base_url, soup):
        """Extrae activos como scripts e imágenes."""
        for script in soup.find_all('script', src=True):
            script_url = urljoin(base_url, script['src'])
            self._store_asset(base_url, 'script', script_url)
            print(f"Script encontrado: {script_url}")

        for img in soup.find_all('img', src=True):
            img_url = urljoin(base_url, img['src'])
            self._store_asset(base_url, 'image', img_url)
            print(f"Imagen encontrada: {img_url}")

    def start_crawl(self, start_url, use_selenium=False, max_workers=4):
        """Inicia el proceso de crawling en paralelo."""
        with Pool(max_workers) as pool:
            pool.map(lambda url: self.parse(url, use_selenium), [start_url])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Proxies y configuración inicial
    proxies = ["http://proxy1:port", "http://proxy2:port"]
    crawler = SophisticatedCrawler(proxy_list=proxies)

    print("Bienvenido al Crawler Avanzado")
    input_url = input("Ingresa una URL para analizar: ").strip()

    if not input_url.startswith(('http://', 'https://')):
        print("La URL debe comenzar con http:// o https://")
    else:
        crawler.start_crawl(input_url, use_selenium=True)
