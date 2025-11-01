#!/usr/bin/env python3
"""
Port Scanner Multi-threaded
Scan rapide de ports avec détection de services
Usage: python3 port_scanner.py <target> [options]
"""

import socket
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json

# Ports communs et leurs services
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
    6379: "Redis", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt", 27017: "MongoDB"
}

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def banner():
    print(f"{Colors.BLUE}{Colors.BOLD}")
    print("╔════════════════════════════════════════╗")
    print("║       Port Scanner Multi-threaded     ║")
    print("║            by CyberSec Tools           ║")
    print("╚════════════════════════════════════════╝")
    print(f"{Colors.END}")

def scan_port(target, port, timeout=1):
    """Scan un port spécifique"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        sock.close()
        
        if result == 0:
            service = COMMON_PORTS.get(port, "Unknown")
            try:
                # Essayer de récupérer la bannière
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect((target, port))
                sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                sock.close()
                return (port, service, banner[:100] if banner else None)
            except:
                return (port, service, None)
        return None
    except socket.gaierror:
        return None
    except socket.error:
        return None

def resolve_target(target):
    """Résoudre le nom d'hôte en IP"""
    try:
        ip = socket.gethostbyname(target)
        return ip
    except socket.gaierror:
        print(f"{Colors.RED}[!] Impossible de résoudre l'hôte: {target}{Colors.END}")
        sys.exit(1)

def scan_ports(target, ports, threads=100, timeout=1, verbose=False):
    """Scan multiple ports avec threading"""
    results = []
    total_ports = len(ports)
    scanned = 0
    
    print(f"{Colors.YELLOW}[*] Scan de {total_ports} ports sur {target}...{Colors.END}\n")
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_port = {
            executor.submit(scan_port, target, port, timeout): port 
            for port in ports
        }
        
        for future in as_completed(future_to_port):
            scanned += 1
            result = future.result()
            
            if result:
                port, service, banner = result
                results.append(result)
                print(f"{Colors.GREEN}[+] Port {port:5d} OUVERT  - {service:15s}", end="")
                if banner and verbose:
                    print(f" | Banner: {banner[:50]}...")
                else:
                    print()
            
            # Progression
            if scanned % 100 == 0 or scanned == total_ports:
                progress = (scanned / total_ports) * 100
                print(f"{Colors.BLUE}[*] Progression: {progress:.1f}% ({scanned}/{total_ports}){Colors.END}", end='\r')
    
    print()  # Nouvelle ligne après la progression
    return results

def generate_report(target, results, output_file=None):
    """Générer un rapport des résultats"""
    report = {
        "target": target,
        "scan_time": datetime.now().isoformat(),
        "total_open_ports": len(results),
        "open_ports": [
            {
                "port": port,
                "service": service,
                "banner": banner
            }
            for port, service, banner in results
        ]
    }
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=4)
        print(f"{Colors.GREEN}[+] Rapport sauvegardé dans: {output_file}{Colors.END}")
    
    return report

def main():
    parser = argparse.ArgumentParser(
        description="Port Scanner Multi-threaded avec détection de services"
    )
    parser.add_argument("target", help="Cible (IP ou hostname)")
    parser.add_argument("-p", "--ports", help="Ports à scanner (ex: 80,443,8080 ou 1-1000)", 
                       default="1-1000")
    parser.add_argument("-t", "--threads", type=int, default=100, 
                       help="Nombre de threads (défaut: 100)")
    parser.add_argument("--timeout", type=float, default=1.0, 
                       help="Timeout par port en secondes (défaut: 1.0)")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Mode verbeux (afficher les bannières)")
    parser.add_argument("-o", "--output", help="Fichier de sortie JSON")
    parser.add_argument("--top", action="store_true", 
                       help="Scanner uniquement les ports les plus communs")
    
    args = parser.parse_args()
    
    banner()
    
    # Résoudre la cible
    target_ip = resolve_target(args.target)
    print(f"{Colors.BLUE}[*] Cible: {args.target} ({target_ip}){Colors.END}")
    
    # Déterminer les ports à scanner
    if args.top:
        ports = list(COMMON_PORTS.keys())
        print(f"{Colors.BLUE}[*] Mode: Top ports communs ({len(ports)} ports){Colors.END}")
    else:
        if '-' in args.ports:
            start, end = map(int, args.ports.split('-'))
            ports = range(start, end + 1)
        elif ',' in args.ports:
            ports = [int(p) for p in args.ports.split(',')]
        else:
            ports = [int(args.ports)]
    
    print(f"{Colors.BLUE}[*] Threads: {args.threads}{Colors.END}")
    print(f"{Colors.BLUE}[*] Timeout: {args.timeout}s{Colors.END}")
    
    # Démarrer le scan
    start_time = datetime.now()
    print(f"{Colors.BLUE}[*] Début du scan: {start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
    
    try:
        results = scan_ports(target_ip, ports, args.threads, args.timeout, args.verbose)
        
        # Afficher le résumé
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
        print(f"{Colors.GREEN}[✓] Scan terminé en {duration:.2f} secondes{Colors.END}")
        print(f"{Colors.GREEN}[✓] {len(results)} port(s) ouvert(s) trouvé(s){Colors.END}")
        
        if results:
            print(f"\n{Colors.BOLD}Résumé des ports ouverts:{Colors.END}")
            for port, service, _ in sorted(results):
                print(f"  {Colors.GREEN}► {port:5d}/tcp - {service}{Colors.END}")
        
        # Générer le rapport
        if args.output:
            generate_report(args.target, results, args.output)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Scan interrompu par l'utilisateur{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()