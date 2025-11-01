#!/usr/bin/env python3
"""
Hash Cracker Multi-algorithmes
Support MD5, SHA1, SHA256, SHA512
Usage: python3 hash_cracker.py <hash> [options]
"""

import hashlib
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
import string
import time

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def banner():
    print(f"{Colors.BLUE}{Colors.BOLD}")
    print("╔════════════════════════════════════════╗")
    print("║      Hash Cracker Multi-algorithmes   ║")
    print("║         MD5 | SHA1 | SHA256 | SHA512   ║")
    print("╚════════════════════════════════════════╝")
    print(f"{Colors.END}")

def detect_hash_type(hash_string):
    """Détecte le type de hash basé sur la longueur"""
    length = len(hash_string)
    
    hash_types = {
        32: "MD5",
        40: "SHA1",
        64: "SHA256",
        128: "SHA512"
    }
    
    return hash_types.get(length, "Unknown")

def hash_word(word, algorithm):
    """Hash un mot avec l'algorithme spécifié"""
    if algorithm == "MD5":
        return hashlib.md5(word.encode()).hexdigest()
    elif algorithm == "SHA1":
        return hashlib.sha1(word.encode()).hexdigest()
    elif algorithm == "SHA256":
        return hashlib.sha256(word.encode()).hexdigest()
    elif algorithm == "SHA512":
        return hashlib.sha512(word.encode()).hexdigest()
    return None

def dictionary_attack(target_hash, algorithm, wordlist_path, threads=10):
    """Attaque par dictionnaire"""
    print(f"{Colors.YELLOW}[*] Lancement de l'attaque par dictionnaire...{Colors.END}")
    print(f"{Colors.BLUE}[*] Wordlist: {wordlist_path}{Colors.END}")
    
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            words = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Colors.RED}[!] Fichier wordlist introuvable: {wordlist_path}{Colors.END}")
        return None
    
    total = len(words)
    print(f"{Colors.BLUE}[*] Nombre de mots: {total}{Colors.END}\n")
    
    tested = 0
    start_time = time.time()
    
    def check_word(word):
        return word if hash_word(word, algorithm) == target_hash else None
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(check_word, word): word for word in words}
        
        for future in as_completed(futures):
            tested += 1
            result = future.result()
            
            if result:
                elapsed = time.time() - start_time
                print(f"\n{Colors.GREEN}{Colors.BOLD}[✓] HASH CRAQUÉ !{Colors.END}")
                print(f"{Colors.GREEN}[✓] Mot de passe: {result}{Colors.END}")
                print(f"{Colors.GREEN}[✓] Temps: {elapsed:.2f}s{Colors.END}")
                print(f"{Colors.GREEN}[✓] Tentatives: {tested}/{total}{Colors.END}")
                return result
            
            if tested % 1000 == 0:
                elapsed = time.time() - start_time
                rate = tested / elapsed if elapsed > 0 else 0
                print(f"{Colors.BLUE}[*] Testé: {tested}/{total} - Vitesse: {rate:.0f} hash/s{Colors.END}", end='\r')
    
    print(f"\n{Colors.RED}[!] Mot de passe non trouvé dans le dictionnaire{Colors.END}")
    return None

def brute_force_attack(target_hash, algorithm, min_len=1, max_len=4, charset=None, threads=10):
    """Attaque par force brute"""
    if charset is None:
        charset = string.ascii_lowercase + string.digits
    
    print(f"{Colors.YELLOW}[*] Lancement de l'attaque par force brute...{Colors.END}")
    print(f"{Colors.BLUE}[*] Longueur: {min_len}-{max_len}{Colors.END}")
    print(f"{Colors.BLUE}[*] Charset: {charset[:20]}...{Colors.END}\n")
    
    start_time = time.time()
    tested = 0
    
    def check_combination(combination):
        word = ''.join(combination)
        return word if hash_word(word, algorithm) == target_hash else None
    
    for length in range(min_len, max_len + 1):
        print(f"{Colors.YELLOW}[*] Test des combinaisons de longueur {length}...{Colors.END}")
        
        combinations = itertools.product(charset, repeat=length)
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(check_combination, combo): combo for combo in combinations}
            
            for future in as_completed(futures):
                tested += 1
                result = future.result()
                
                if result:
                    elapsed = time.time() - start_time
                    print(f"\n{Colors.GREEN}{Colors.BOLD}[✓] HASH CRAQUÉ !{Colors.END}")
                    print(f"{Colors.GREEN}[✓] Mot de passe: {result}{Colors.END}")
                    print(f"{Colors.GREEN}[✓] Temps: {elapsed:.2f}s{Colors.END}")
                    print(f"{Colors.GREEN}[✓] Tentatives: {tested}{Colors.END}")
                    return result
                
                if tested % 10000 == 0:
                    elapsed = time.time() - start_time
                    rate = tested / elapsed if elapsed > 0 else 0
                    print(f"{Colors.BLUE}[*] Testé: {tested} - Vitesse: {rate:.0f} hash/s{Colors.END}", end='\r')
    
    print(f"\n{Colors.RED}[!] Mot de passe non trouvé{Colors.END}")
    return None

def verify_hash(word, target_hash, algorithm):
    """Vérifier si un mot correspond au hash"""
    calculated = hash_word(word, algorithm)
    
    print(f"{Colors.BLUE}[*] Mot: {word}{Colors.END}")
    print(f"{Colors.BLUE}[*] Hash calculé: {calculated}{Colors.END}")
    print(f"{Colors.BLUE}[*] Hash cible:   {target_hash}{Colors.END}")
    
    if calculated == target_hash:
        print(f"{Colors.GREEN}{Colors.BOLD}[✓] CORRESPONDANCE !{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}[✗] Pas de correspondance{Colors.END}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Hash Cracker Multi-algorithmes (MD5, SHA1, SHA256, SHA512)"
    )
    parser.add_argument("hash", help="Hash à craquer")
    parser.add_argument("-w", "--wordlist", help="Chemin vers le wordlist pour l'attaque par dictionnaire")
    parser.add_argument("-b", "--brute", action="store_true", 
                       help="Activer l'attaque par force brute")
    parser.add_argument("--min-len", type=int, default=1, 
                       help="Longueur minimale pour la force brute (défaut: 1)")
    parser.add_argument("--max-len", type=int, default=4, 
                       help="Longueur maximale pour la force brute (défaut: 4)")
    parser.add_argument("-c", "--charset", 
                       help="Charset personnalisé pour la force brute")
    parser.add_argument("-t", "--threads", type=int, default=10, 
                       help="Nombre de threads (défaut: 10)")
    parser.add_argument("-a", "--algorithm", 
                       choices=["MD5", "SHA1", "SHA256", "SHA512"],
                       help="Forcer l'algorithme (auto-détecté par défaut)")
    parser.add_argument("-v", "--verify", 
                       help="Vérifier un mot contre le hash")
    
    args = parser.parse_args()
    
    banner()
    
    # Détection ou utilisation de l'algorithme spécifié
    if args.algorithm:
        algorithm = args.algorithm
        print(f"{Colors.BLUE}[*] Algorithme spécifié: {algorithm}{Colors.END}")
    else:
        algorithm = detect_hash_type(args.hash)
        print(f"{Colors.BLUE}[*] Algorithme détecté: {algorithm}{Colors.END}")
    
    if algorithm == "Unknown":
        print(f"{Colors.RED}[!] Type de hash non reconnu{Colors.END}")
        sys.exit(1)
    
    print(f"{Colors.BLUE}[*] Hash cible: {args.hash}{Colors.END}")
    print(f"{Colors.BLUE}[*] Threads: {args.threads}{Colors.END}\n")
    
    # Mode vérification
    if args.verify:
        verify_hash(args.verify, args.hash, algorithm)
        return
    
    # Attaque par dictionnaire
    if args.wordlist:
        result = dictionary_attack(args.hash, algorithm, args.wordlist, args.threads)
        if result:
            return
    
    # Attaque par force brute
    if args.brute:
        charset = args.charset if args.charset else None
        result = brute_force_attack(
            args.hash, algorithm, 
            args.min_len, args.max_len, 
            charset, args.threads
        )
        if result:
            return
    
    # Si aucune méthode spécifiée
    if not args.wordlist and not args.brute:
        print(f"{Colors.YELLOW}[!] Spécifiez au moins -w (wordlist) ou -b (brute force){Colors.END}")
        print(f"{Colors.YELLOW}[!] Utilisez -h pour l'aide{Colors.END}")

if __name__ == "__main__":
    main()