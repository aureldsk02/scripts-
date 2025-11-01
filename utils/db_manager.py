#!/usr/bin/env python3
"""
Database Manager
Backup, Restore et gestion de bases de données MySQL/PostgreSQL
Usage: python3 database_manager.py <command> [options]
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json
import gzip

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

class DatabaseManager:
    def __init__(self, db_type, host, port, user, password, database=None):
        self.db_type = db_type.lower()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
    
    def banner(self):
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║      Database Manager v2.0             ║")
        print("║    MySQL | PostgreSQL | Backup         ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def backup_mysql(self, output_file, compress=True, tables=None):
        """Sauvegarde une base MySQL"""
        print(f"{Colors.BLUE}[*] Backup MySQL: {self.database}{Colors.END}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = Path(output_file or f"backup_mysql_{self.database}_{timestamp}.sql")
        
        # Commande mysqldump
        cmd = [
            'mysqldump',
            f'-h{self.host}',
            f'-P{self.port}',
            f'-u{self.user}',
            f'-p{self.password}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
        ]
        
        if tables:
            cmd.append(self.database)
            cmd.extend(tables)
        else:
            cmd.append(self.database)
        
        try:
            print(f"{Colors.YELLOW}[*] Création du backup...{Colors.END}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"{Colors.RED}[!] Erreur mysqldump: {result.stderr}{Colors.END}")
                return False
            
            # Écrire le backup
            if compress:
                backup_file = backup_file.with_suffix('.sql.gz')
                with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
                    f.write(result.stdout)
                print(f"{Colors.GREEN}[✓] Backup compressé: {backup_file}{Colors.END}")
            else:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                print(f"{Colors.GREEN}[✓] Backup créé: {backup_file}{Colors.END}")
            
            # Taille du fichier
            size = backup_file.stat().st_size
            print(f"{Colors.GREEN}[✓] Taille: {self.get_size(size)}{Colors.END}")
            
            return True
        
        except FileNotFoundError:
            print(f"{Colors.RED}[!] mysqldump non trouvé. Installez MySQL client.{Colors.END}")
            return False
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def restore_mysql(self, input_file):
        """Restaure une base MySQL"""
        print(f"{Colors.BLUE}[*] Restauration MySQL: {self.database}{Colors.END}")
        
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"{Colors.RED}[!] Fichier introuvable: {input_file}{Colors.END}")
            return False
        
        try:
            # Lire le fichier (compressé ou non)
            if input_path.suffix == '.gz':
                print(f"{Colors.YELLOW}[*] Décompression du backup...{Colors.END}")
                with gzip.open(input_path, 'rt', encoding='utf-8') as f:
                    sql_content = f.read()
            else:
                with open(input_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
            
            # Commande mysql
            cmd = [
                'mysql',
                f'-h{self.host}',
                f'-P{self.port}',
                f'-u{self.user}',
                f'-p{self.password}',
                self.database
            ]
            
            print(f"{Colors.YELLOW}[*] Restauration en cours...{Colors.END}")
            
            result = subprocess.run(cmd, input=sql_content, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"{Colors.RED}[!] Erreur: {result.stderr}{Colors.END}")
                return False
            
            print(f"{Colors.GREEN}[✓] Base de données restaurée avec succès{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def backup_postgresql(self, output_file, compress=True, tables=None):
        """Sauvegarde une base PostgreSQL"""
        print(f"{Colors.BLUE}[*] Backup PostgreSQL: {self.database}{Colors.END}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = Path(output_file or f"backup_postgres_{self.database}_{timestamp}.sql")
        
        # Commande pg_dump
        cmd = [
            'pg_dump',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            '--no-password',
            '--clean',
            '--create',
        ]
        
        if tables:
            for table in tables:
                cmd.extend(['-t', table])
        
        cmd.append(self.database)
        
        # Variables d'environnement pour le mot de passe
        env = {'PGPASSWORD': self.password}
        
        try:
            print(f"{Colors.YELLOW}[*] Création du backup...{Colors.END}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                print(f"{Colors.RED}[!] Erreur pg_dump: {result.stderr}{Colors.END}")
                return False
            
            # Écrire le backup
            if compress:
                backup_file = backup_file.with_suffix('.sql.gz')
                with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
                    f.write(result.stdout)
                print(f"{Colors.GREEN}[✓] Backup compressé: {backup_file}{Colors.END}")
            else:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                print(f"{Colors.GREEN}[✓] Backup créé: {backup_file}{Colors.END}")
            
            # Taille du fichier
            size = backup_file.stat().st_size
            print(f"{Colors.GREEN}[✓] Taille: {self.get_size(size)}{Colors.END}")
            
            return True
        
        except FileNotFoundError:
            print(f"{Colors.RED}[!] pg_dump non trouvé. Installez PostgreSQL client.{Colors.END}")
            return False
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def restore_postgresql(self, input_file):
        """Restaure une base PostgreSQL"""
        print(f"{Colors.BLUE}[*] Restauration PostgreSQL: {self.database}{Colors.END}")
        
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"{Colors.RED}[!] Fichier introuvable: {input_file}{Colors.END}")
            return False
        
        try:
            # Lire le fichier
            if input_path.suffix == '.gz':
                print(f"{Colors.YELLOW}[*] Décompression du backup...{Colors.END}")
                with gzip.open(input_path, 'rt', encoding='utf-8') as f:
                    sql_content = f.read()
            else:
                with open(input_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
            
            # Commande psql
            cmd = [
                'psql',
                f'--host={self.host}',
                f'--port={self.port}',
                f'--username={self.user}',
                '--no-password',
                self.database
            ]
            
            env = {'PGPASSWORD': self.password}
            
            print(f"{Colors.YELLOW}[*] Restauration en cours...{Colors.END}")
            
            result = subprocess.run(cmd, input=sql_content, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                print(f"{Colors.RED}[!] Erreur: {result.stderr}{Colors.END}")
                return False
            
            print(f"{Colors.GREEN}[✓] Base de données restaurée avec succès{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def list_databases_mysql(self):
        """Liste toutes les bases MySQL"""
        print(f"{Colors.BLUE}[*] Listing des bases MySQL...{Colors.END}\n")
        
        cmd = [
            'mysql',
            f'-h{self.host}',
            f'-P{self.port}',
            f'-u{self.user}',
            f'-p{self.password}',
            '-e', 'SHOW DATABASES;'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"{Colors.RED}[!] Erreur: {result.stderr}{Colors.END}")
                return False
            
            print(result.stdout)
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def list_databases_postgresql(self):
        """Liste toutes les bases PostgreSQL"""
        print(f"{Colors.BLUE}[*] Listing des bases PostgreSQL...{Colors.END}\n")
        
        cmd = [
            'psql',
            f'--host={self.host}',
            f'--port={self.port}',
            f'--username={self.user}',
            '--no-password',
            '-c', '\\l'
        ]
        
        env = {'PGPASSWORD': self.password}
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                print(f"{Colors.RED}[!] Erreur: {result.stderr}{Colors.END}")
                return False
            
            print(result.stdout)
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def list_tables(self):
        """Liste les tables d'une base"""
        print(f"{Colors.BLUE}[*] Tables de la base: {self.database}{Colors.END}\n")
        
        if self.db_type == 'mysql':
            cmd = [
                'mysql',
                f'-h{self.host}',
                f'-P{self.port}',
                f'-u{self.user}',
                f'-p{self.password}',
                self.database,
                '-e', 'SHOW TABLES;'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(result.stdout)
                    return True
            except Exception as e:
                print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
        
        elif self.db_type == 'postgresql':
            cmd = [
                'psql',
                f'--host={self.host}',
                f'--port={self.port}',
                f'--username={self.user}',
                '--no-password',
                self.database,
                '-c', '\\dt'
            ]
            
            env = {'PGPASSWORD': self.password}
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                if result.returncode == 0:
                    print(result.stdout)
                    return True
            except Exception as e:
                print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
        
        return False
    
    def export_to_csv(self, table, output_file):
        """Exporte une table en CSV"""
        print(f"{Colors.BLUE}[*] Export de {table} vers CSV...{Colors.END}")
        
        if self.db_type == 'mysql':
            query = f"SELECT * FROM {table} INTO OUTFILE '{output_file}' FIELDS TERMINATED BY ',' ENCLOSED BY '\"' LINES TERMINATED BY '\\n';"
            cmd = [
                'mysql',
                f'-h{self.host}',
                f'-P{self.port}',
                f'-u{self.user}',
                f'-p{self.password}',
                self.database,
                '-e', query
            ]
        
        elif self.db_type == 'postgresql':
            query = f"COPY {table} TO STDOUT WITH CSV HEADER;"
            cmd = [
                'psql',
                f'--host={self.host}',
                f'--port={self.port}',
                f'--username={self.user}',
                '--no-password',
                self.database,
                '-c', query
            ]
        
        try:
            if self.db_type == 'postgresql':
                env = {'PGPASSWORD': self.password}
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    with open(output_file, 'w') as f:
                        f.write(result.stdout)
                    print(f"{Colors.GREEN}[✓] Exporté: {output_file}{Colors.END}")
                    return True
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"{Colors.GREEN}[✓] Exporté: {output_file}{Colors.END}")
                    return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
        
        return False
    
    def get_size(self, bytes):
        """Convertit les bytes en format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"

def main():
    parser = argparse.ArgumentParser(
        description="Database Manager - Backup, Restore et gestion de bases de données"
    )
    
    # Arguments globaux
    parser.add_argument('-t', '--type', choices=['mysql', 'postgresql'], required=True,
                       help='Type de base de données')
    parser.add_argument('-H', '--host', default='localhost', help='Hôte (défaut: localhost)')
    parser.add_argument('-P', '--port', type=int, help='Port (défaut: 3306 MySQL, 5432 PostgreSQL)')
    parser.add_argument('-u', '--user', required=True, help='Utilisateur')
    parser.add_argument('-p', '--password', required=True, help='Mot de passe')
    parser.add_argument('-d', '--database', help='Nom de la base de données')
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Backup
    backup_parser = subparsers.add_parser('backup', help='Sauvegarder une base')
    backup_parser.add_argument('-o', '--output', help='Fichier de sortie')
    backup_parser.add_argument('--no-compress', action='store_true', help='Ne pas compresser')
    backup_parser.add_argument('--tables', nargs='+', help='Tables spécifiques à sauvegarder')
    
    # Restore
    restore_parser = subparsers.add_parser('restore', help='Restaurer une base')
    restore_parser.add_argument('-i', '--input', required=True, help='Fichier de sauvegarde')
    
    # List databases
    list_db_parser = subparsers.add_parser('list-db', help='Lister toutes les bases')
    
    # List tables
    list_tables_parser = subparsers.add_parser('list-tables', help='Lister les tables')
    
    # Export to CSV
    export_parser = subparsers.add_parser('export-csv', help='Exporter une table en CSV')
    export_parser.add_argument('table', help='Nom de la table')
    export_parser.add_argument('-o', '--output', required=True, help='Fichier CSV de sortie')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Port par défaut
    if not args.port:
        args.port = 3306 if args.type == 'mysql' else 5432
    
    # Créer le manager
    manager = DatabaseManager(
        db_type=args.type,
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    manager.banner()
    
    try:
        if args.command == 'backup':
            if not args.database:
                print(f"{Colors.RED}[!] -d/--database requis pour le backup{Colors.END}")
                sys.exit(1)
            
            compress = not args.no_compress
            if args.type == 'mysql':
                manager.backup_mysql(args.output, compress, args.tables)
            else:
                manager.backup_postgresql(args.output, compress, args.tables)
        
        elif args.command == 'restore':
            if not args.database:
                print(f"{Colors.RED}[!] -d/--database requis pour la restauration{Colors.END}")
                sys.exit(1)
            
            if args.type == 'mysql':
                manager.restore_mysql(args.input)
            else:
                manager.restore_postgresql(args.input)
        
        elif args.command == 'list-db':
            if args.type == 'mysql':
                manager.list_databases_mysql()
            else:
                manager.list_databases_postgresql()
        
        elif args.command == 'list-tables':
            if not args.database:
                print(f"{Colors.RED}[!] -d/--database requis{Colors.END}")
                sys.exit(1)
            manager.list_tables()
        
        elif args.command == 'export-csv':
            if not args.database:
                print(f"{Colors.RED}[!] -d/--database requis{Colors.END}")
                sys.exit(1)
            manager.export_to_csv(args.table, args.output)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[*] Opération interrompue{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")

if __name__ == "__main__":
    main()