#!/usr/bin/env python3
"""
PDF Tools Suite
Manipulation complète de fichiers PDF
Usage: python3 pdf_tools.py <command> [options]
"""

import argparse
import sys
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from PIL import Image
import io

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

class PDFTools:
    def __init__(self):
        pass
    
    def banner(self):
        print(f"{Colors.MAGENTA}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║          PDF Tools Suite v2.0          ║")
        print("║    Merge | Split | Compress | Convert  ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def merge_pdfs(self, pdf_files, output_file):
        """Fusionne plusieurs PDFs en un seul"""
        print(f"{Colors.BLUE}[*] Fusion de {len(pdf_files)} fichiers PDF...{Colors.END}")
        
        try:
            merger = PdfMerger()
            
            for pdf_file in pdf_files:
                print(f"{Colors.CYAN}  → Ajout de {pdf_file}{Colors.END}")
                merger.append(pdf_file)
            
            merger.write(output_file)
            merger.close()
            
            print(f"{Colors.GREEN}[✓] PDF fusionné: {output_file}{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la fusion: {e}{Colors.END}")
            return False
    
    def split_pdf(self, input_file, output_dir, pages_per_file=1):
        """Divise un PDF en plusieurs fichiers"""
        print(f"{Colors.BLUE}[*] Division du PDF: {input_file}{Colors.END}")
        
        try:
            reader = PdfReader(input_file)
            total_pages = len(reader.pages)
            
            print(f"{Colors.BLUE}[*] Total de pages: {total_pages}{Colors.END}")
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            input_name = Path(input_file).stem
            
            for i in range(0, total_pages, pages_per_file):
                writer = PdfWriter()
                
                # Ajouter les pages
                for page_num in range(i, min(i + pages_per_file, total_pages)):
                    writer.add_page(reader.pages[page_num])
                
                # Sauvegarder
                output_filename = output_path / f"{input_name}_part_{i+1}-{min(i+pages_per_file, total_pages)}.pdf"
                with open(output_filename, 'wb') as output_pdf:
                    writer.write(output_pdf)
                
                print(f"{Colors.GREEN}[+] Créé: {output_filename}{Colors.END}")
            
            print(f"{Colors.GREEN}[✓] PDF divisé en {(total_pages + pages_per_file - 1) // pages_per_file} fichiers{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la division: {e}{Colors.END}")
            return False
    
    def extract_pages(self, input_file, output_file, pages):
        """Extrait des pages spécifiques"""
        print(f"{Colors.BLUE}[*] Extraction des pages: {pages}{Colors.END}")
        
        try:
            reader = PdfReader(input_file)
            writer = PdfWriter()
            
            # Parser les pages (ex: "1,3,5-8")
            page_numbers = self.parse_page_range(pages, len(reader.pages))
            
            for page_num in page_numbers:
                writer.add_page(reader.pages[page_num - 1])
            
            with open(output_file, 'wb') as output_pdf:
                writer.write(output_pdf)
            
            print(f"{Colors.GREEN}[✓] Pages extraites: {output_file}{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de l'extraction: {e}{Colors.END}")
            return False
    
    def rotate_pdf(self, input_file, output_file, angle, pages=None):
        """Fait pivoter les pages d'un PDF"""
        print(f"{Colors.BLUE}[*] Rotation de {angle}° du PDF{Colors.END}")
        
        try:
            reader = PdfReader(input_file)
            writer = PdfWriter()
            
            total_pages = len(reader.pages)
            
            if pages:
                page_numbers = self.parse_page_range(pages, total_pages)
            else:
                page_numbers = range(1, total_pages + 1)
            
            for i in range(total_pages):
                page = reader.pages[i]
                if (i + 1) in page_numbers:
                    page.rotate(angle)
                writer.add_page(page)
            
            with open(output_file, 'wb') as output_pdf:
                writer.write(output_pdf)
            
            print(f"{Colors.GREEN}[✓] PDF pivoté: {output_file}{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la rotation: {e}{Colors.END}")
            return False
    
    def add_watermark(self, input_file, output_file, watermark_text, position='center'):
        """Ajoute un filigrane à un PDF"""
        print(f"{Colors.BLUE}[*] Ajout du filigrane: {watermark_text}{Colors.END}")
        
        try:
            reader = PdfReader(input_file)
            writer = PdfWriter()
            
            # Créer le filigrane
            watermark_pdf = self.create_watermark(watermark_text, reader.pages[0], position)
            watermark_reader = PdfReader(watermark_pdf)
            watermark_page = watermark_reader.pages[0]
            
            # Ajouter le filigrane à chaque page
            for page in reader.pages:
                page.merge_page(watermark_page)
                writer.add_page(page)
            
            with open(output_file, 'wb') as output_pdf:
                writer.write(output_pdf)
            
            print(f"{Colors.GREEN}[✓] Filigrane ajouté: {output_file}{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de l'ajout du filigrane: {e}{Colors.END}")
            return False
    
    def create_watermark(self, text, page, position='center'):
        """Crée un PDF de filigrane"""
        packet = io.BytesIO()
        
        # Obtenir les dimensions de la page
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        
        c = canvas.Canvas(packet, pagesize=(width, height))
        c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
        c.setFont("Helvetica", 50)
        
        # Positionner le texte
        if position == 'center':
            x, y = width / 2, height / 2
        elif position == 'top':
            x, y = width / 2, height - 50
        elif position == 'bottom':
            x, y = width / 2, 50
        else:
            x, y = width / 2, height / 2
        
        c.saveState()
        c.translate(x, y)
        c.rotate(45)
        c.drawCentredString(0, 0, text)
        c.restoreState()
        
        c.save()
        packet.seek(0)
        
        return packet
    
    def compress_pdf(self, input_file, output_file):
        """Compresse un PDF (réduit la qualité des images)"""
        print(f"{Colors.BLUE}[*] Compression du PDF...{Colors.END}")
        
        try:
            reader = PdfReader(input_file)
            writer = PdfWriter()
            
            for page in reader.pages:
                page.compress_content_streams()
                writer.add_page(page)
            
            with open(output_file, 'wb') as output_pdf:
                writer.write(output_pdf)
            
            # Calculer la réduction de taille
            original_size = Path(input_file).stat().st_size
            compressed_size = Path(output_file).stat().st_size
            reduction = ((original_size - compressed_size) / original_size) * 100
            
            print(f"{Colors.GREEN}[✓] PDF compressé: {output_file}{Colors.END}")
            print(f"{Colors.GREEN}[✓] Réduction: {reduction:.1f}%{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la compression: {e}{Colors.END}")
            return False
    
    def images_to_pdf(self, image_files, output_file, page_size='A4'):
        """Convertit des images en PDF"""
        print(f"{Colors.BLUE}[*] Conversion de {len(image_files)} images en PDF...{Colors.END}")
        
        try:
            # Choisir la taille de page
            if page_size.upper() == 'A4':
                pagesize = A4
            else:
                pagesize = letter
            
            c = canvas.Canvas(output_file, pagesize=pagesize)
            page_width, page_height = pagesize
            
            for img_file in image_files:
                print(f"{Colors.CYAN}  → Ajout de {img_file}{Colors.END}")
                
                # Ouvrir l'image
                img = Image.open(img_file)
                img_width, img_height = img.size
                
                # Calculer le ratio pour adapter l'image
                ratio = min(page_width / img_width, page_height / img_height)
                new_width = img_width * ratio
                new_height = img_height * ratio
                
                # Centrer l'image
                x = (page_width - new_width) / 2
                y = (page_height - new_height) / 2
                
                # Dessiner l'image
                c.drawImage(img_file, x, y, width=new_width, height=new_height)
                c.showPage()
            
            c.save()
            
            print(f"{Colors.GREEN}[✓] PDF créé: {output_file}{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la conversion: {e}{Colors.END}")
            return False
    
    def pdf_to_images(self, input_file, output_dir, format='PNG'):
        """Convertit un PDF en images (nécessite pdf2image)"""
        print(f"{Colors.BLUE}[*] Conversion du PDF en images {format}...{Colors.END}")
        
        try:
            from pdf2image import convert_from_path
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            images = convert_from_path(input_file)
            
            input_name = Path(input_file).stem
            
            for i, image in enumerate(images, 1):
                output_filename = output_path / f"{input_name}_page_{i}.{format.lower()}"
                image.save(output_filename, format)
                print(f"{Colors.GREEN}[+] Créé: {output_filename}{Colors.END}")
            
            print(f"{Colors.GREEN}[✓] {len(images)} image(s) créée(s){Colors.END}")
            return True
        
        except ImportError:
            print(f"{Colors.RED}[!] pdf2image non installé. Installez avec: pip install pdf2image{Colors.END}")
            return False
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la conversion: {e}{Colors.END}")
            return False
    
    def get_info(self, input_file):
        """Affiche les informations d'un PDF"""
        print(f"{Colors.BLUE}[*] Informations du PDF: {input_file}{Colors.END}\n")
        
        try:
            reader = PdfReader(input_file)
            
            print(f"{Colors.CYAN}Nombre de pages:{Colors.END} {len(reader.pages)}")
            
            if reader.metadata:
                print(f"\n{Colors.CYAN}Métadonnées:{Colors.END}")
                for key, value in reader.metadata.items():
                    print(f"  {key}: {value}")
            
            # Taille du fichier
            file_size = Path(input_file).stat().st_size
            print(f"\n{Colors.CYAN}Taille:{Colors.END} {self.get_size(file_size)}")
            
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def parse_page_range(self, page_range, total_pages):
        """Parse une chaîne de pages (ex: "1,3,5-8")"""
        pages = set()
        
        for part in page_range.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.update(range(start, min(end + 1, total_pages + 1)))
            else:
                pages.add(int(part))
        
        return sorted(pages)
    
    def get_size(self, bytes):
        """Convertit les bytes en format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"

def main():
    tools = PDFTools()
    tools.banner()
    
    parser = argparse.ArgumentParser(
        description="PDF Tools Suite - Manipulation complète de fichiers PDF"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Merge
    merge_parser = subparsers.add_parser('merge', help='Fusionner plusieurs PDFs')
    merge_parser.add_argument('files', nargs='+', help='Fichiers PDF à fusionner')
    merge_parser.add_argument('-o', '--output', required=True, help='Fichier de sortie')
    
    # Split
    split_parser = subparsers.add_parser('split', help='Diviser un PDF')
    split_parser.add_argument('input', help='Fichier PDF à diviser')
    split_parser.add_argument('-o', '--output-dir', required=True, help='Répertoire de sortie')
    split_parser.add_argument('-p', '--pages-per-file', type=int, default=1, 
                             help='Pages par fichier (défaut: 1)')
    
    # Extract
    extract_parser = subparsers.add_parser('extract', help='Extraire des pages')
    extract_parser.add_argument('input', help='Fichier PDF source')
    extract_parser.add_argument('-p', '--pages', required=True, help='Pages à extraire (ex: 1,3,5-8)')
    extract_parser.add_argument('-o', '--output', required=True, help='Fichier de sortie')
    
    # Rotate
    rotate_parser = subparsers.add_parser('rotate', help='Faire pivoter les pages')
    rotate_parser.add_argument('input', help='Fichier PDF à pivoter')
    rotate_parser.add_argument('-a', '--angle', type=int, required=True, 
                              choices=[90, 180, 270], help='Angle de rotation')
    rotate_parser.add_argument('-p', '--pages', help='Pages à pivoter (toutes par défaut)')
    rotate_parser.add_argument('-o', '--output', required=True, help='Fichier de sortie')
    
    # Watermark
    watermark_parser = subparsers.add_parser('watermark', help='Ajouter un filigrane')
    watermark_parser.add_argument('input', help='Fichier PDF')
    watermark_parser.add_argument('-t', '--text', required=True, help='Texte du filigrane')
    watermark_parser.add_argument('-pos', '--position', choices=['center', 'top', 'bottom'],
                                 default='center', help='Position du filigrane')
    watermark_parser.add_argument('-o', '--output', required=True, help='Fichier de sortie')
    
    # Compress
    compress_parser = subparsers.add_parser('compress', help='Compresser un PDF')
    compress_parser.add_argument('input', help='Fichier PDF à compresser')
    compress_parser.add_argument('-o', '--output', required=True, help='Fichier de sortie')
    
    # Images to PDF
    img2pdf_parser = subparsers.add_parser('img2pdf', help='Convertir images en PDF')
    img2pdf_parser.add_argument('images', nargs='+', help='Fichiers images')
    img2pdf_parser.add_argument('-o', '--output', required=True, help='Fichier PDF de sortie')
    img2pdf_parser.add_argument('-s', '--size', choices=['A4', 'Letter'], default='A4',
                               help='Taille de page')
    
    # PDF to Images
    pdf2img_parser = subparsers.add_parser('pdf2img', help='Convertir PDF en images')
    pdf2img_parser.add_argument('input', help='Fichier PDF')
    pdf2img_parser.add_argument('-o', '--output-dir', required=True, help='Répertoire de sortie')
    pdf2img_parser.add_argument('-f', '--format', choices=['PNG', 'JPG'], default='PNG',
                               help='Format d\'image')
    
    # Info
    info_parser = subparsers.add_parser('info', help='Afficher les informations d\'un PDF')
    info_parser.add_argument('input', help='Fichier PDF')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Exécuter la commande
    try:
        if args.command == 'merge':
            tools.merge_pdfs(args.files, args.output)
        
        elif args.command == 'split':
            tools.split_pdf(args.input, args.output_dir, args.pages_per_file)
        
        elif args.command == 'extract':
            tools.extract_pages(args.input, args.output, args.pages)
        
        elif args.command == 'rotate':
            tools.rotate_pdf(args.input, args.output, args.angle, args.pages)
        
        elif args.command == 'watermark':
            tools.add_watermark(args.input, args.output, args.text, args.position)
        
        elif args.command == 'compress':
            tools.compress_pdf(args.input, args.output)
        
        elif args.command == 'img2pdf':
            tools.images_to_pdf(args.images, args.output, args.size)
        
        elif args.command == 'pdf2img':
            tools.pdf_to_images(args.input, args.output_dir, args.format)
        
        elif args.command == 'info':
            tools.get_info(args.input)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[*] Opération interrompue{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")

if __name__ == "__main__":
    main()