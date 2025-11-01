#!/usr/bin/env python3
"""
Smart File Organizer
Organise automatiquement les fichiers par type, date, ou nom
Usage: python3 file_organizer.py <directory> [options]
"""

import os
import shutil
import argparse
import sys
from pathlib import Path
from datetime import datetime
import mimetypes
import hashlib

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Catégories de fichiers par extension
FILE_CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.raw'],
    'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpeg'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.tex'],
    'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
    'Presentations': ['.ppt', '.pptx', '.odp', '.key'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
    'Code': ['.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.php', '.rb', '.go', '.rs', '.ts'],
    'Executables': ['.exe', '.msi', '.apk', '.app', '.deb', '.rpm'],
    'Databases': ['.db', '.sqlite', '.sql', '.mdb'],
    'Ebooks': ['.epub', '.mobi', '.azw', '.azw3'],
    'Fonts': ['.ttf', '.otf', '.woff', '.woff2'],
    'Design': ['.psd', '.ai', '.sketch', '.fig', '.xd'],
    'CAD': ['.dwg', '.dxf', '.step', '.stl']
}

class FileOrganizer:
    def __init__(self, directory, organize_by='type', dry_run=False, recursive=False):
        self.directory = Path(directory)
        self.organize_by = organize_by
        self.dry_run = dry_run
        self.recursive = recursive
        self.stats = {
            'processed': 0,
            'moved': 0,
            'skipped': 0,
            'duplicates': 0,
            'errors': 0
        }
        self.file_hashes = {}
    
    def banner(self):
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║        Smart File Organizer v2.0       ║")
        print("║     Auto-organize files by category    ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def get_file_category(self, file_path):
        """Détermine la catégorie d'un fichier"""
        extension = file_path.suffix.lower()
        
        for category, extensions in FILE_CATEGORIES.items():
            if extension in extensions:
                return category
        
        return 'Others'
    
    def get_file_hash(self, file_path):
        """Calcule le hash MD5 d'un fichier"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None
    
    def is_duplicate(self, file_path):
        """Vérifie si le fichier est un duplicata"""
        file_hash = self.get_file_hash(file_path)
        if file_hash is None:
            return False
        
        if file_hash in self.file_hashes:
            return True
        
        self.file_hashes[file_hash] = file_path
        return False
    
    def organize_by_type(self, file_path):
        """Organise les fichiers par type/catégorie"""
        category = self.get_file_category(file_path)
        dest_dir = self.directory / category
        return dest_dir
    
    def organize_by_date(self, file_path):
        """Organise les fichiers par date de modification"""
        timestamp = file_path.stat().st_mtime
        date = datetime.fromtimestamp(timestamp)
        
        year = str(date.year)
        month = date.strftime('%m-%B')
        
        dest_dir = self.directory / year / month
        return dest_dir
    
    def organize_by_extension(self, file_path):
        """Organise les fichiers par extension"""
        extension = file_path.suffix.lower()
        if not extension:
            extension = 'no_extension'
        else:
            extension = extension[1:]  # Enlever le point
        
        dest_dir = self.directory / extension.upper()
        return dest_dir
    
    def organize_by_name(self, file_path):
        """Organise les fichiers par première lettre du nom"""
        first_char = file_path.stem[0].upper()
        
        if first_char.isdigit():
            dest_dir = self.directory / '0-9'
        elif first_char.isalpha():
            dest_dir = self.directory / first_char
        else:
            dest_dir = self.directory / 'Special'
        
        return dest_dir
    
    def move_file(self, source, destination_dir):
        """Déplace un fichier vers le répertoire de destination"""
        try:
            # Créer le répertoire de destination
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            # Chemin de destination complet
            destination = destination_dir / source.name
            
            # Gérer les fichiers avec le même nom
            counter = 1
            original_destination = destination
            while destination.exists():
                stem = original_destination.stem
                suffix = original_destination.suffix
                destination = destination_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            if self.dry_run:
                print(f"{Colors.YELLOW}[DRY RUN]{Colors.END} {source} → {destination}")
            else:
                shutil.move(str(source), str(destination))
                print(f"{Colors.GREEN}[MOVED]{Colors.END} {source.name} → {destination_dir.name}/")
            
            self.stats['moved'] += 1
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.END} {source.name}: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_files(self):
        """Récupère la liste des fichiers à organiser"""
        if self.recursive:
            files = [f for f in self.directory.rglob('*') if f.is_file()]
        else:
            files = [f for f in self.directory.iterdir() if f.is_file()]
        
        return files
    
    def organize(self, check_duplicates=False):
        """Organise les fichiers"""
        self.banner()
        
        print(f"{Colors.BLUE}[*] Répertoire: {self.directory}{Colors.END}")
        print(f"{Colors.BLUE}[*] Organisation par: {self.organize_by}{Colors.END}")
        print(f"{Colors.BLUE}[*] Mode récursif: {'Oui' if self.recursive else 'Non'}{Colors.END}")
        
        if self.dry_run:
            print(f"{Colors.YELLOW}[*] Mode DRY RUN (aucun fichier ne sera déplacé){Colors.END}")
        
        if check_duplicates:
            print(f"{Colors.BLUE}[*] Détection de duplicatas activée{Colors.END}")
        
        print()
        
        # Récupérer tous les fichiers
        files = self.get_files()
        total_files = len(files)
        
        print(f"{Colors.GREEN}[+] {total_files} fichier(s) trouvé(s){Colors.END}\n")
        
        if total_files == 0:
            return
        
        # Organiser les fichiers
        for file_path in files:
            self.stats['processed'] += 1
            
            # Vérifier les duplicatas
            if check_duplicates and self.is_duplicate(file_path):
                print(f"{Colors.MAGENTA}[DUPLICATE]{Colors.END} {file_path.name}")
                self.stats['duplicates'] += 1
                self.stats['skipped'] += 1
                continue
            
            # Déterminer le répertoire de destination
            if self.organize_by == 'type':
                dest_dir = self.organize_by_type(file_path)
            elif self.organize_by == 'date':
                dest_dir = self.organize_by_date(file_path)
            elif self.organize_by == 'extension':
                dest_dir = self.organize_by_extension(file_path)
            elif self.organize_by == 'name':
                dest_dir = self.organize_by_name(file_path)
            else:
                print(f"{Colors.RED}[ERROR]{Colors.END} Mode d'organisation inconnu")
                continue
            
            # Ne pas déplacer si déjà dans le bon répertoire
            if file_path.parent == dest_dir:
                self.stats['skipped'] += 1
                continue
            
            # Déplacer le fichier
            self.move_file(file_path, dest_dir)
        
        # Afficher les statistiques
        self.display_stats()
    
    def display_stats(self):
        """Affiche les statistiques"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*50}{Colors.END}")
        print(f"{Colors.BOLD}STATISTIQUES{Colors.END}")
        print(f"{Colors.CYAN}{'='*50}{Colors.END}\n")
        
        print(f"{Colors.GREEN}Fichiers traités:{Colors.END}    {self.stats['processed']}")
        print(f"{Colors.GREEN}Fichiers déplacés:{Colors.END}   {self.stats['moved']}")
        print(f"{Colors.YELLOW}Fichiers ignorés:{Colors.END}    {self.stats['skipped']}")
        print(f"{Colors.MAGENTA}Duplicatas trouvés:{Colors.END}  {self.stats['duplicates']}")
        print(f"{Colors.RED}Erreurs:{Colors.END}             {self.stats['errors']}")
    
    def clean_empty_dirs(self):
        """Supprime les répertoires vides"""
        print(f"\n{Colors.YELLOW}[*] Nettoyage des répertoires vides...{Colors.END}")
        
        removed = 0
        for dirpath, dirnames, filenames in os.walk(self.directory, topdown=False):
            if not dirnames and not filenames and Path(dirpath) != self.directory:
                try:
                    if self.dry_run:
                        print(f"{Colors.YELLOW}[DRY RUN]{Colors.END} Supprimer: {dirpath}")
                    else:
                        os.rmdir(dirpath)
                        print(f"{Colors.GREEN}[REMOVED]{Colors.END} {dirpath}")
                    removed += 1
                except Exception as e:
                    print(f"{Colors.RED}[ERROR]{Colors.END} {dirpath}: {e}")
        
        if removed > 0:
            print(f"{Colors.GREEN}[+] {removed} répertoire(s) vide(s) supprimé(s){Colors.END}")
        else:
            print(f"{Colors.BLUE}[*] Aucun répertoire vide trouvé{Colors.END}")
    
    def undo_organization(self):
        """Annule l'organisation (remet tous les fichiers à la racine)"""
        print(f"\n{Colors.YELLOW}[*] Annulation de l'organisation...{Colors.END}")
        
        files = [f for f in self.directory.rglob('*') if f.is_file() and f.parent != self.directory]
        
        for file_path in files:
            try:
                destination = self.directory / file_path.name
                
                # Gérer les conflits de noms
                counter = 1
                original_destination = destination
                while destination.exists():
                    stem = original_destination.stem
                    suffix = original_destination.suffix
                    destination = self.directory / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                if self.dry_run:
                    print(f"{Colors.YELLOW}[DRY RUN]{Colors.END} {file_path} → {destination}")
                else:
                    shutil.move(str(file_path), str(destination))
                    print(f"{Colors.GREEN}[MOVED]{Colors.END} {file_path.name} → racine")
            
            except Exception as e:
                print(f"{Colors.RED}[ERROR]{Colors.END} {file_path.name}: {e}")
        
        print(f"{Colors.GREEN}[+] Organisation annulée{Colors.END}")

def main():
    parser = argparse.ArgumentParser(
        description="Smart File Organizer - Organise automatiquement vos fichiers"
    )
    parser.add_argument("directory", help="Répertoire à organiser")
    parser.add_argument("-m", "--mode", choices=['type', 'date', 'extension', 'name'],
                       default='type', help="Mode d'organisation (défaut: type)")
    parser.add_argument("-r", "--recursive", action="store_true",
                       help="Organiser récursivement tous les sous-dossiers")
    parser.add_argument("-d", "--dry-run", action="store_true",
                       help="Simuler sans déplacer les fichiers")
    parser.add_argument("--check-duplicates", action="store_true",
                       help="Détecter et ignorer les fichiers en double")
    parser.add_argument("--clean", action="store_true",
                       help="Supprimer les répertoires vides après organisation")
    parser.add_argument("--undo", action="store_true",
                       help="Annuler l'organisation (remettre tous les fichiers à la racine)")
    
    args = parser.parse_args()
    
    # Vérifier que le répertoire existe
    if not os.path.isdir(args.directory):
        print(f"{Colors.RED}[!] Erreur: Le répertoire '{args.directory}' n'existe pas{Colors.END}")
        sys.exit(1)
    
    organizer = FileOrganizer(
        directory=args.directory,
        organize_by=args.mode,
        dry_run=args.dry_run,
        recursive=args.recursive
    )
    
    try:
        if args.undo:
            organizer.undo_organization()
        else:
            organizer.organize(check_duplicates=args.check_duplicates)
        
        if args.clean and not args.dry_run:
            organizer.clean_empty_dirs()
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[*] Organisation interrompue{Colors.END}")
        organizer.display_stats()

if __name__ == "__main__":
    main()