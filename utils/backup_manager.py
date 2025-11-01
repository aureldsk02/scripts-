#!/usr/bin/env python3
"""
Backup Manager & Sync Tool
Sauvegarde et synchronisation de fichiers/dossiers
Usage: python3 backup_manager.py <source> <destination> [options]
"""

import os
import shutil
import argparse
import sys
from pathlib import Path
from datetime import datetime
import json
import hashlib
import tarfile
import zipfile

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

class BackupManager:
    def __init__(self, source, destination, compress=None, incremental=False, 
                 exclude_patterns=None, max_backups=None):
        self.source = Path(source)
        self.destination = Path(destination)
        self.compress = compress
        self.incremental = incremental
        self.exclude_patterns = exclude_patterns or []
        self.max_backups = max_backups
        self.stats = {
            'files_copied': 0,
            'files_updated': 0,
            'files_deleted': 0,
            'files_skipped': 0,
            'total_size': 0,
            'errors': 0
        }
        self.manifest_file = self.destination / '.backup_manifest.json'
        self.manifest = self.load_manifest()
    
    def banner(self):
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║      Backup Manager & Sync Tool        ║")
        print("║     Smart Backup with Compression      ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def load_manifest(self):
        """Charge le manifeste des sauvegardes précédentes"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_manifest(self):
        """Sauvegarde le manifeste"""
        try:
            with open(self.manifest_file, 'w') as f:
                json.dump(self.manifest, f, indent=4)
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.END} Impossible de sauvegarder le manifeste: {e}")
    
    def get_file_hash(self, file_path):
        """Calcule le hash MD5 d'un fichier"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None
    
    def should_exclude(self, path):
        """Vérifie si un fichier doit être exclu"""
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return True
        return False
    
    def get_size(self, bytes):
        """Convertit les bytes en format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def copy_file(self, source_path, dest_path):
        """Copie un fichier avec vérification"""
        try:
            # Créer les répertoires parent si nécessaire
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copier le fichier
            shutil.copy2(source_path, dest_path)
            
            # Calculer le hash
            file_hash = self.get_file_hash(dest_path)
            
            # Mettre à jour le manifeste
            rel_path = str(source_path.relative_to(self.source))
            self.manifest[rel_path] = {
                'hash': file_hash,
                'mtime': source_path.stat().st_mtime,
                'size': source_path.stat().st_size
            }
            
            size = source_path.stat().st_size
            self.stats['total_size'] += size
            
            return True
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.END} {source_path.name}: {e}")
            self.stats['errors'] += 1
            return False
    
    def backup_directory(self):
        """Sauvegarde un répertoire"""
        print(f"{Colors.YELLOW}[*] Analyse des fichiers...{Colors.END}\n")
        
        # Récupérer tous les fichiers source
        source_files = []
        for root, dirs, files in os.walk(self.source):
            # Exclure les dossiers cachés
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                source_path = Path(root) / file
                
                if self.should_exclude(source_path):
                    continue
                
                source_files.append(source_path)
        
        total_files = len(source_files)
        print(f"{Colors.GREEN}[+] {total_files} fichier(s) à traiter{Colors.END}\n")
        
        # Traiter chaque fichier
        for i, source_path in enumerate(source_files, 1):
            rel_path = source_path.relative_to(self.source)
            dest_path = self.destination / rel_path
            
            # Vérifier si le fichier doit être copié
            should_copy = False
            status = ""
            
            if not dest_path.exists():
                should_copy = True
                status = "NEW"
                self.stats['files_copied'] += 1
            elif self.incremental:
                # Mode incrémental: vérifier si le fichier a changé
                rel_path_str = str(rel_path)
                if rel_path_str in self.manifest:
                    old_mtime = self.manifest[rel_path_str].get('mtime', 0)
                    new_mtime = source_path.stat().st_mtime
                    
                    if new_mtime > old_mtime:
                        should_copy = True
                        status = "UPDATED"
                        self.stats['files_updated'] += 1
                    else:
                        status = "SKIPPED"
                        self.stats['files_skipped'] += 1
                else:
                    should_copy = True
                    status = "NEW"
                    self.stats['files_copied'] += 1
            else:
                should_copy = True
                status = "OVERWRITE"
                self.stats['files_updated'] += 1
            
            # Copier si nécessaire
            if should_copy:
                if self.copy_file(source_path, dest_path):
                    color = Colors.GREEN if status == "NEW" else Colors.YELLOW
                    print(f"{color}[{status}]{Colors.END} ({i}/{total_files}) {rel_path}")
            else:
                print(f"{Colors.BLUE}[{status}]{Colors.END} ({i}/{total_files}) {rel_path}")
        
        # Sauvegarder le manifeste
        if self.incremental:
            self.save_manifest()
    
    def compress_backup(self, format='zip'):
        """Compresse la sauvegarde"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'zip':
            archive_name = f"backup_{timestamp}.zip"
            archive_path = self.destination.parent / archive_name
            
            print(f"\n{Colors.YELLOW}[*] Compression en ZIP...{Colors.END}")
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.destination):
                    for file in files:
                        if file == '.backup_manifest.json':
                            continue
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.destination)
                        zipf.write(file_path, arcname)
            
            print(f"{Colors.GREEN}[+] Archive créée: {archive_name}{Colors.END}")
            print(f"{Colors.GREEN}[+] Taille: {self.get_size(archive_path.stat().st_size)}{Colors.END}")
        
        elif format == 'tar.gz':
            archive_name = f"backup_{timestamp}.tar.gz"
            archive_path = self.destination.parent / archive_name
            
            print(f"\n{Colors.YELLOW}[*] Compression en TAR.GZ...{Colors.END}")
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(self.destination, arcname=self.destination.name)
            
            print(f"{Colors.GREEN}[+] Archive créée: {archive_name}{Colors.END}")
            print(f"{Colors.GREEN}[+] Taille: {self.get_size(archive_path.stat().st_size)}{Colors.END}")
        
        return archive_path
    
    def cleanup_old_backups(self):
        """Supprime les anciennes sauvegardes"""
        if not self.max_backups:
            return
        
        print(f"\n{Colors.YELLOW}[*] Nettoyage des anciennes sauvegardes...{Colors.END}")
        
        # Trouver toutes les archives
        pattern = "backup_*.zip" if self.compress == 'zip' else "backup_*.tar.gz"
        backups = sorted(self.destination.parent.glob(pattern))
        
        # Supprimer les anciennes
        if len(backups) > self.max_backups:
            to_delete = backups[:-self.max_backups]
            for backup in to_delete:
                try:
                    backup.unlink()
                    print(f"{Colors.GREEN}[DELETED]{Colors.END} {backup.name}")
                except Exception as e:
                    print(f"{Colors.RED}[ERROR]{Colors.END} {backup.name}: {e}")
            
            print(f"{Colors.GREEN}[+] {len(to_delete)} ancienne(s) sauvegarde(s) supprimée(s){Colors.END}")
    
    def sync_directories(self):
        """Synchronise deux répertoires (bidirectionnel)"""
        print(f"{Colors.YELLOW}[*] Synchronisation bidirectionnelle...{Colors.END}\n")
        
        # Copier source → destination
        print(f"{Colors.CYAN}Source → Destination:{Colors.END}")
        for root, dirs, files in os.walk(self.source):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                
                source_path = Path(root) / file
                rel_path = source_path.relative_to(self.source)
                dest_path = self.destination / rel_path
                
                if not dest_path.exists() or source_path.stat().st_mtime > dest_path.stat().st_mtime:
                    if self.copy_file(source_path, dest_path):
                        print(f"{Colors.GREEN}[SYNCED]{Colors.END} {rel_path}")
        
        # Copier destination → source
        print(f"\n{Colors.CYAN}Destination → Source:{Colors.END}")
        for root, dirs, files in os.walk(self.destination):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.') or file == '.backup_manifest.json':
                    continue
                
                dest_path = Path(root) / file
                rel_path = dest_path.relative_to(self.destination)
                source_path = self.source / rel_path
                
                if not source_path.exists() or dest_path.stat().st_mtime > source_path.stat().st_mtime:
                    try:
                        source_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(dest_path, source_path)
                        print(f"{Colors.GREEN}[SYNCED]{Colors.END} {rel_path}")
                    except Exception as e:
                        print(f"{Colors.RED}[ERROR]{Colors.END} {rel_path}: {e}")
    
    def display_stats(self):
        """Affiche les statistiques"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*50}{Colors.END}")
        print(f"{Colors.BOLD}STATISTIQUES DE SAUVEGARDE{Colors.END}")
        print(f"{Colors.CYAN}{'='*50}{Colors.END}\n")
        
        print(f"{Colors.GREEN}Nouveaux fichiers:{Colors.END}    {self.stats['files_copied']}")
        print(f"{Colors.YELLOW}Fichiers mis à jour:{Colors.END}  {self.stats['files_updated']}")
        print(f"{Colors.BLUE}Fichiers ignorés:{Colors.END}     {self.stats['files_skipped']}")
        print(f"{Colors.MAGENTA}Fichiers supprimés:{Colors.END}   {self.stats['files_deleted']}")
        print(f"{Colors.RED}Erreurs:{Colors.END}              {self.stats['errors']}")
        print(f"{Colors.CYAN}Taille totale:{Colors.END}        {self.get_size(self.stats['total_size'])}")
    
    def run(self, sync=False):
        """Exécute la sauvegarde"""
        self.banner()
        
        print(f"{Colors.BLUE}[*] Source:      {self.source}{Colors.END}")
        print(f"{Colors.BLUE}[*] Destination: {self.destination}{Colors.END}")
        
        if self.incremental:
            print(f"{Colors.BLUE}[*] Mode:        Incrémental{Colors.END}")
        
        if self.compress:
            print(f"{Colors.BLUE}[*] Compression: {self.compress.upper()}{Colors.END}")
        
        if self.exclude_patterns:
            print(f"{Colors.BLUE}[*] Exclusions:  {', '.join(self.exclude_patterns)}{Colors.END}")
        
        print()
        
        try:
            # Créer le répertoire de destination
            if not sync:
                self.destination.mkdir(parents=True, exist_ok=True)
            
            # Synchronisation ou sauvegarde
            if sync:
                self.sync_directories()
            else:
                self.backup_directory()
            
            # Compression si demandée
            if self.compress and not sync:
                archive_path = self.compress_backup(self.compress)
                
                # Nettoyer les anciennes sauvegardes
                if self.max_backups:
                    self.cleanup_old_backups()
            
            # Afficher les stats
            self.display_stats()
            
            print(f"\n{Colors.GREEN}{Colors.BOLD}[✓] Sauvegarde terminée avec succès!{Colors.END}")
        
        except Exception as e:
            print(f"\n{Colors.RED}[!] Erreur: {e}{Colors.END}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Backup Manager - Sauvegarde et synchronisation de fichiers"
    )
    parser.add_argument("source", help="Répertoire source")
    parser.add_argument("destination", help="Répertoire de destination")
    parser.add_argument("-i", "--incremental", action="store_true",
                       help="Sauvegarde incrémentale (copie uniquement les fichiers modifiés)")
    parser.add_argument("-c", "--compress", choices=['zip', 'tar.gz'],
                       help="Compresser la sauvegarde")
    parser.add_argument("-e", "--exclude", nargs='+',
                       help="Patterns à exclure (ex: *.tmp __pycache__)")
    parser.add_argument("-m", "--max-backups", type=int,
                       help="Nombre maximum de sauvegardes à conserver")
    parser.add_argument("-s", "--sync", action="store_true",
                       help="Synchronisation bidirectionnelle")
    
    args = parser.parse_args()
    
    # Vérifier que la source existe
    if not os.path.exists(args.source):
        print(f"{Colors.RED}[!] Erreur: Le répertoire source '{args.source}' n'existe pas{Colors.END}")
        sys.exit(1)
    
    manager = BackupManager(
        source=args.source,
        destination=args.destination,
        compress=args.compress,
        incremental=args.incremental,
        exclude_patterns=args.exclude,
        max_backups=args.max_backups
    )
    
    try:
        manager.run(sync=args.sync)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[*] Sauvegarde interrompue{Colors.END}")
        manager.display_stats()

if __name__ == "__main__":
    main()