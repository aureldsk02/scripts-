#!/usr/bin/env python3
"""
Advanced Web Scraper
Extraction intelligente de données depuis des sites web
Usage: python3 web_scraper.py <url> [options]
"""

import requests
from bs4 import BeautifulSoup
import argparse
import sys
import json
import csv
from urllib.parse import urljoin, urlparse
import re
import time

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

class WebScraper:
    def __init__(self, url, headers=None, timeout=10, max_pages=None):
        self.base_url = url
        self.domain = urlparse(url).netloc
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = timeout
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.visited_urls = set()
        self.scraped_data = []
    
    def banner(self):
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║        Advanced Web Scraper v2.0       ║")
        print("║      Extract Data from Websites        ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def get_page(self, url):
        """Récupère une page web"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"{Colors.RED}[ERROR]{Colors.END} {url}: {e}")
            return None
    
    def extract_links(self, soup, base_url):
        """Extrait tous les liens d'une page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Garder uniquement les liens du même domaine
            if urlparse(full_url).netloc == self.domain:
                links.append(full_url)
        
        return list(set(links))
    
    def extract_images(self, soup, base_url):
        """Extrait toutes les images d'une page"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                full_url = urljoin(base_url, src)
                images.append({
                    'url': full_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        return images
    
    def extract_text(self, soup, selectors=None):
        """Extrait le texte selon des sélecteurs CSS"""
        if selectors:
            results = {}
            for name, selector in selectors.items():
                elements = soup.select(selector)
                results[name] = [el.get_text(strip=True) for el in elements]
            return results
        else:
            # Extraire tout le texte de la page
            return soup.get_text(strip=True)
    
    def extract_tables(self, soup):
        """Extrait toutes les tables HTML"""
        tables = []
        for table in soup.find_all('table'):
            headers = []
            rows = []
            
            # Headers
            thead = table.find('thead')
            if thead:
                headers = [th.get_text(strip=True) for th in thead.find_all('th')]
            
            # Rows
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append({
                    'headers': headers,
                    'rows': rows
                })
        
        return tables
    
    def extract_metadata(self, soup):
        """Extrait les métadonnées de la page"""
        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'og_title': '',
            'og_description': '',
            'og_image': ''
        }
        
        # Title
        title = soup.find('title')
        if title:
            metadata['title'] = title.get_text(strip=True)
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name == 'description':
                metadata['description'] = content
            elif name == 'keywords':
                metadata['keywords'] = content
            elif property_attr == 'og:title':
                metadata['og_title'] = content
            elif property_attr == 'og:description':
                metadata['og_description'] = content
            elif property_attr == 'og:image':
                metadata['og_image'] = content
        
        return metadata
    
    def extract_emails(self, text):
        """Extrait les emails d'un texte"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    def extract_phones(self, text):
        """Extrait les numéros de téléphone"""
        phone_patterns = [
            r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\d{3}-\d{3}-\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))
    
    def scrape_page(self, url, selectors=None):
        """Scrape une page complète"""
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        print(f"{Colors.BLUE}[*] Scraping: {url}{Colors.END}")
        
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraire les données
        data = {
            'url': url,
            'metadata': self.extract_metadata(soup),
            'links': self.extract_links(soup, url),
            'images': self.extract_images(soup, url),
            'tables': self.extract_tables(soup)
        }
        
        # Texte personnalisé avec sélecteurs
        if selectors:
            data['custom_data'] = self.extract_text(soup, selectors)
        
        # Emails et téléphones
        page_text = soup.get_text()
        data['emails'] = self.extract_emails(page_text)
        data['phones'] = self.extract_phones(page_text)
        
        return data
    
    def crawl(self, selectors=None, depth=1):
        """Crawl le site avec profondeur spécifiée"""
        self.banner()
        
        print(f"{Colors.BLUE}[*] URL de départ: {self.base_url}{Colors.END}")
        print(f"{Colors.BLUE}[*] Profondeur: {depth}{Colors.END}")
        if self.max_pages:
            print(f"{Colors.BLUE}[*] Max pages: {self.max_pages}{Colors.END}")
        print()
        
        urls_to_visit = [(self.base_url, 0)]
        
        while urls_to_visit:
            if self.max_pages and len(self.visited_urls) >= self.max_pages:
                print(f"{Colors.YELLOW}[*] Limite de pages atteinte{Colors.END}")
                break
            
            current_url, current_depth = urls_to_visit.pop(0)
            
            if current_depth > depth:
                continue
            
            data = self.scrape_page(current_url, selectors)
            
            if data:
                self.scraped_data.append(data)
                
                print(f"{Colors.GREEN}[+] Métadonnées: {data['metadata']['title'][:50]}{Colors.END}")
                print(f"{Colors.GREEN}[+] Liens trouvés: {len(data['links'])}{Colors.END}")
                print(f"{Colors.GREEN}[+] Images: {len(data['images'])}{Colors.END}")
                print(f"{Colors.GREEN}[+] Tables: {len(data['tables'])}{Colors.END}")
                
                if data['emails']:
                    print(f"{Colors.MAGENTA}[+] Emails: {', '.join(data['emails'][:3])}{Colors.END}")
                
                # Ajouter les nouveaux liens à visiter
                if current_depth < depth:
                    for link in data['links']:
                        if link not in self.visited_urls:
                            urls_to_visit.append((link, current_depth + 1))
            
            time.sleep(0.5)  # Délai pour éviter de surcharger le serveur
        
        print(f"\n{Colors.GREEN}[✓] Scraping terminé{Colors.END}")
        print(f"{Colors.GREEN}[✓] {len(self.scraped_data)} page(s) scrapée(s){Colors.END}")
    
    def save_json(self, filename):
        """Sauvegarde les données en JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=4, ensure_ascii=False)
        print(f"{Colors.GREEN}[+] Données sauvegardées: {filename}{Colors.END}")
    
    def save_csv(self, filename):
        """Sauvegarde les données en CSV"""
        if not self.scraped_data:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Headers
            writer.writerow(['URL', 'Title', 'Description', 'Links Count', 'Images Count', 'Emails', 'Phones'])
            
            # Data
            for data in self.scraped_data:
                writer.writerow([
                    data['url'],
                    data['metadata']['title'],
                    data['metadata']['description'],
                    len(data['links']),
                    len(data['images']),
                    ', '.join(data['emails']),
                    ', '.join(data['phones'])
                ])
        
        print(f"{Colors.GREEN}[+] Données sauvegardées: {filename}{Colors.END}")
    
    def save_markdown(self, filename):
        """Sauvegarde un rapport en Markdown"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Web Scraping Report\n\n")
            f.write(f"**Base URL:** {self.base_url}\n\n")
            f.write(f"**Pages scrapées:** {len(self.scraped_data)}\n\n")
            f.write("---\n\n")
            
            for i, data in enumerate(self.scraped_data, 1):
                f.write(f"## Page {i}: {data['metadata']['title']}\n\n")
                f.write(f"**URL:** {data['url']}\n\n")
                
                if data['metadata']['description']:
                    f.write(f"**Description:** {data['metadata']['description']}\n\n")
                
                f.write(f"**Statistiques:**\n")
                f.write(f"- Liens: {len(data['links'])}\n")
                f.write(f"- Images: {len(data['images'])}\n")
                f.write(f"- Tables: {len(data['tables'])}\n")
                
                if data['emails']:
                    f.write(f"\n**Emails trouvés:**\n")
                    for email in data['emails']:
                        f.write(f"- {email}\n")
                
                if data['phones']:
                    f.write(f"\n**Téléphones trouvés:**\n")
                    for phone in data['phones']:
                        f.write(f"- {phone}\n")
                
                f.write("\n---\n\n")
        
        print(f"{Colors.GREEN}[+] Rapport sauvegardé: {filename}{Colors.END}")

def main():
    parser = argparse.ArgumentParser(
        description="Advanced Web Scraper - Extraction de données depuis des sites web"
    )
    parser.add_argument("url", help="URL du site à scraper")
    parser.add_argument("-d", "--depth", type=int, default=0,
                       help="Profondeur de crawl (défaut: 0 = page unique)")
    parser.add_argument("-m", "--max-pages", type=int,
                       help="Nombre maximum de pages à scraper")
    parser.add_argument("-s", "--selectors", help="Sélecteurs CSS personnalisés (format JSON)")
    parser.add_argument("-o", "--output", default="scraped_data",
                       help="Nom de fichier de sortie (sans extension)")
    parser.add_argument("-f", "--format", choices=['json', 'csv', 'markdown', 'all'],
                       default='json', help="Format de sortie")
    parser.add_argument("--timeout", type=int, default=10,
                       help="Timeout des requêtes en secondes")
    
    args = parser.parse_args()
    
    # Parser les sélecteurs personnalisés
    selectors = None
    if args.selectors:
        try:
            selectors = json.loads(args.selectors)
        except json.JSONDecodeError:
            print(f"{Colors.RED}[!] Format JSON invalide pour les sélecteurs{Colors.END}")
            sys.exit(1)
    
    # Créer le scraper
    scraper = WebScraper(
        url=args.url,
        timeout=args.timeout,
        max_pages=args.max_pages
    )
    
    try:
        # Lancer le scraping
        scraper.crawl(selectors=selectors, depth=args.depth)
        
        # Sauvegarder les résultats
        print()
        if args.format == 'json' or args.format == 'all':
            scraper.save_json(f"{args.output}.json")
        
        if args.format == 'csv' or args.format == 'all':
            scraper.save_csv(f"{args.output}.csv")
        
        if args.format == 'markdown' or args.format == 'all':
            scraper.save_markdown(f"{args.output}.md")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[*] Scraping interrompu{Colors.END}")
        
        # Sauvegarder ce qui a été scrapé
        if scraper.scraped_data:
            scraper.save_json(f"{args.output}_partial.json")

if __name__ == "__main__":
    main()