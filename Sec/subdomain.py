#!/usr/bin/env python3
"""
Subdomain Enumerator
Énumération de sous-domaines avec vérification DNS
Usage: python3 subdomain_enum.py <domain> [options]
"""

import dns.resolver
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import socket
import json

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Liste de sous-domaines communs
COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "webdisk",
    "ns2", "cpanel", "whm", "autodiscover", "autoconfig", "m", "imap", "test",
    "ns", "blog", "pop3", "dev", "www2", "admin", "forum", "news", "vpn", "ns3",
    "mail2", "new", "mysql", "old", "lists", "support", "mobile", "mx", "static",
    "docs", "beta", "shop", "sql", "secure", "demo", "cp", "calendar", "wiki",
    "web", "media", "email", "images", "img", "www1", "intranet", "portal", "video",
    "sip", "dns2", "api", "cdn", "stats", "dns1", "ns4", "www3", "dns", "search",
    "staging", "server", "mx1", "chat", "wap", "my", "svn", "mail1", "sites",
    "proxy", "ads", "host", "crm", "cms", "backup", "mx2", "lyncdiscover", "info",
    "apps", "download", "remote", "db", "forums", "store", "relay", "files",
    "newsletter", "app", "live", "owa", "en", "start", "sms", "office", "exchange",
    "ipv4", "help", "home", "library", "ftp2", "ntp", "monitor", "login", "service",
    "correo", "www4", "moodle", "it", "gateway", "gw", "i", "stat", "stage",
    "ldap", "tv", "ssl", "web1", "web2", "ns5", "upload", "nagios", "smtp2",
    "online", "ad", "survey", "data", "radio", "extranet", "test2", "mssql", "dns3",
    "jobs", "services", "panel", "irc", "hosting", "cloud", "de", "gmail", "s",
    "bbs", "cs", "ww", "mrtg", "git", "image", "members", "poczta", "s1", "meet",
    "preview", "fr", "cloudflare-resolve-to", "dev2", "photo", "jabber", "legacy",
    "go", "es", "ssh", "redmine", "partner", "vps", "server1", "sv", "ns6", "webmail2"
]

def banner():
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔════════════════════════════════════════╗")
    print("║       Subdomain Enumerator v1.0        ║")
    print("║         DNS + HTTP Verification        ║")
    print("╚════════════════════════════════════════╝")
    print(f"{Colors.END}")

def check_subdomain(subdomain, domain, verify_http=False, timeout=3):
    """Vérifie si un sous-domaine existe"""
    full_domain = f"{subdomain}.{domain}"
    result = {
        "subdomain": full_domain,
        "exists": False,
        "ip": None,
        "http_status": None,
        "https_status": None
    }
    
    try:
        # Résolution DNS
        answers = dns.resolver.resolve(full_domain, 'A')
        ips = [str(rdata) for rdata in answers]
        result["exists"] = True
        result["ip"] = ips[0] if ips else None
        
        # Vérification HTTP/HTTPS si demandé
        if verify_http and result["ip"]:
            try:
                # Test HTTP
                resp = requests.get(f"http://{full_domain}", timeout=timeout, allow_redirects=False)
                result["http_status"] = resp.status_code
            except:
                pass
            
            try:
                # Test HTTPS
                resp = requests.get(f"https://{full_domain}", timeout=timeout, allow_redirects=False, verify=False)
                result["https_status"] = resp.status_code
            except:
                pass
        
        return result
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return None
    except Exception:
        return None

def enumerate_subdomains(domain, subdomains, threads=50, verify_http=False, timeout=3):
    """Énumère les sous-domaines"""
    results = []
    total = len(subdomains)
    checked = 0
    
    print(f"{Colors.YELLOW}[*] Énumération de {total} sous-domaines...{Colors.END}\n")
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_sub = {
            executor.submit(check_subdomain, sub, domain, verify_http, timeout): sub 
            for sub in subdomains
        }
        
        for future in as_completed(future_to_sub):
            checked += 1
            result = future.result()
            
            if result and result["exists"]:
                results.append(result)
                
                # Affichage
                print(f"{Colors.GREEN}[+] {result['subdomain']:40s} ", end="")
                print(f"{Colors.CYAN}→ {result['ip']:15s}", end="")
                
                if verify_http:
                    if result["http_status"]:
                        print(f" | HTTP: {result['http_status']}", end="")
                    if result["https_status"]:
                        print(f" | HTTPS: {result['https_status']}", end="")
                
                print(f"{Colors.END}")
            
            # Progression
            if checked % 10 == 0 or checked == total:
                progress = (checked / total) * 100
                print(f"{Colors.BLUE}[*] Progression: {progress:.1f}% ({checked}/{total}){Colors.END}", end='\r')
    
    print()
    return results

def check_zone_transfer(domain):
    """Tente un transfert de zone DNS"""
    print(f"{Colors.YELLOW}[*] Tentative de transfert de zone...{Colors.END}")
    
    try:
        # Récupérer les serveurs NS
        ns_records = dns.resolver.resolve(domain, 'NS')
        nameservers = [str(ns) for ns in ns_records]
        
        print(f"{Colors.BLUE}[*] Serveurs NS trouvés: {', '.join(nameservers)}{Colors.END}")
        
        for ns in nameservers:
            try:
                # Tenter le transfert de zone
                zone = dns.zone.from_xfr(dns.query.xfr(ns, domain))
                print(f"{Colors.GREEN}[+] Transfert de zone réussi depuis {ns}!{Colors.END}")
                
                subdomains = []
                for name, node in zone.nodes.items():
                    subdomain = str(name)
                    if subdomain != "@":
                        subdomains.append(f"{subdomain}.{domain}")
                
                return subdomains
            except Exception:
                continue
        
        print(f"{Colors.RED}[-] Transfert de zone échoué (normal){Colors.END}")
        return []
    except Exception as e:
        print(f"{Colors.RED}[-] Erreur lors du transfert de zone: {e}{Colors.END}")
        return []

def get_dns_records(domain):
    """Récupère différents types d'enregistrements DNS"""
    print(f"\n{Colors.YELLOW}[*] Récupération des enregistrements DNS...{Colors.END}")
    
    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
    records = {}
    
    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            records[record_type] = [str(rdata) for rdata in answers]
            print(f"{Colors.GREEN}[+] {record_type:6s}: {', '.join(records[record_type][:3])}{Colors.END}")
        except:
            pass
    
    return records

def save_results(domain, results, dns_records, output_file):
    """Sauvegarde les résultats en JSON"""
    data = {
        "domain": domain,
        "total_subdomains": len(results),
        "subdomains": results,
        "dns_records": dns_records
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"{Colors.GREEN}[+] Résultats sauvegardés: {output_file}{Colors.END}")

def main():
    parser = argparse.ArgumentParser(
        description="Subdomain Enumerator avec vérification DNS et HTTP"
    )
    parser.add_argument("domain", help="Domaine cible (ex: example.com)")
    parser.add_argument("-w", "--wordlist", help="Wordlist personnalisée de sous-domaines")
    parser.add_argument("-t", "--threads", type=int, default=50,
                       help="Nombre de threads (défaut: 50)")
    parser.add_argument("--verify-http", action="store_true",
                       help="Vérifier HTTP/HTTPS sur les sous-domaines trouvés")
    parser.add_argument("--timeout", type=int, default=3,
                       help="Timeout pour les requêtes HTTP (défaut: 3s)")
    parser.add_argument("--zone-transfer", action="store_true",
                       help="Tenter un transfert de zone DNS")
    parser.add_argument("--dns-records", action="store_true",
                       help="Afficher les enregistrements DNS du domaine")
    parser.add_argument("-o", "--output", help="Fichier de sortie JSON")
    
    args = parser.parse_args()
    
    banner()
    
    print(f"{Colors.BLUE}[*] Domaine cible: {args.domain}{Colors.END}")
    print(f"{Colors.BLUE}[*] Threads: {args.threads}{Colors.END}\n")
    
    # Enregistrements DNS
    dns_records = {}
    if args.dns_records:
        dns_records = get_dns_records(args.domain)
    
    # Transfert de zone
    zone_subdomains = []
    if args.zone_transfer:
        zone_subdomains = check_zone_transfer(args.domain)
        if zone_subdomains:
            print(f"{Colors.GREEN}[+] {len(zone_subdomains)} sous-domaines trouvés via transfert de zone{Colors.END}")
    
    # Préparer la liste de sous-domaines
    if args.wordlist:
        try:
            with open(args.wordlist, 'r') as f:
                subdomains = [line.strip() for line in f if line.strip()]
            print(f"{Colors.BLUE}[*] Wordlist chargée: {len(subdomains)} sous-domaines{Colors.END}")
        except FileNotFoundError:
            print(f"{Colors.RED}[!] Wordlist introuvable: {args.wordlist}{Colors.END}")
            sys.exit(1)
    else:
        subdomains = COMMON_SUBDOMAINS
        print(f"{Colors.BLUE}[*] Utilisation de la wordlist par défaut: {len(subdomains)} sous-domaines{Colors.END}")
    
    # Ajouter les sous-domaines du transfert de zone
    if zone_subdomains:
        subdomains.extend([zs.split('.')[0] for zs in zone_subdomains])
        subdomains = list(set(subdomains))  # Dédupliquer
    
    # Énumération
    try:
        results = enumerate_subdomains(
            args.domain, 
            subdomains, 
            args.threads, 
            args.verify_http,
            args.timeout
        )
        
        # Résumé
        print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
        print(f"{Colors.GREEN}[✓] Énumération terminée{Colors.END}")
        print(f"{Colors.GREEN}[✓] {len(results)} sous-domaine(s) trouvé(s){Colors.END}")
        
        if results:
            print(f"\n{Colors.BOLD}Sous-domaines trouvés:{Colors.END}")
            for r in sorted(results, key=lambda x: x['subdomain']):
                print(f"  {Colors.CYAN}► {r['subdomain']:<40s} → {r['ip']}{Colors.END}")
        
        # Sauvegarder les résultats
        if args.output:
            save_results(args.domain, results, dns_records, args.output)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Énumération interrompue{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    # Désactiver les warnings SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main()