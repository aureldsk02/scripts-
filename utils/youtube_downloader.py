#!/usr/bin/env python3
"""
YouTube Downloader
Télécharge des vidéos et audios depuis YouTube
Usage: python3 youtube_downloader.py <url> [options]
"""

import argparse
import sys
from pathlib import Path
import yt_dlp
import json

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

class YouTubeDownloader:
    def __init__(self, url, output_dir='downloads'):
        self.url = url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def banner(self):
        print(f"{Colors.RED}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║       YouTube Downloader v2.0          ║")
        print("║    Download Videos & Audio from YT     ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def progress_hook(self, d):
        """Hook pour afficher la progression"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"{Colors.CYAN}[↓]{Colors.END} Téléchargement: {percent} | Vitesse: {speed} | ETA: {eta}", end='\r')
        elif d['status'] == 'finished':
            print(f"\n{Colors.GREEN}[✓] Téléchargement terminé{Colors.END}")
    
    def get_video_info(self):
        """Récupère les informations d'une vidéo"""
        print(f"{Colors.BLUE}[*] Récupération des informations...{Colors.END}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                return info
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return None
    
    def display_info(self, info):
        """Affiche les informations d'une vidéo"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}Informations de la vidéo:{Colors.END}")
        print(f"{Colors.GREEN}Titre:{Colors.END} {info.get('title', 'N/A')}")
        print(f"{Colors.GREEN}Chaîne:{Colors.END} {info.get('uploader', 'N/A')}")
        print(f"{Colors.GREEN}Durée:{Colors.END} {info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}")
        print(f"{Colors.GREEN}Vues:{Colors.END} {info.get('view_count', 0):,}")
        print(f"{Colors.GREEN}Date:{Colors.END} {info.get('upload_date', 'N/A')}")
        
        if 'description' in info:
            description = info['description'][:200]
            print(f"{Colors.GREEN}Description:{Colors.END} {description}...")
    
    def list_formats(self):
        """Liste tous les formats disponibles"""
        info = self.get_video_info()
        if not info:
            return
        
        self.display_info(info)
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}Formats disponibles:{Colors.END}\n")
        print(f"{'ID':<8} {'Extension':<10} {'Résolution':<15} {'Format':<40}")
        print("─" * 80)
        
        for fmt in info.get('formats', []):
            format_id = fmt.get('format_id', 'N/A')
            ext = fmt.get('ext', 'N/A')
            resolution = fmt.get('resolution', 'audio only' if 'audio' in fmt.get('format_note', '').lower() else 'N/A')
            format_note = fmt.get('format_note', 'N/A')
            
            print(f"{format_id:<8} {ext:<10} {resolution:<15} {format_note:<40}")
    
    def download_video(self, quality='best', format_id=None):
        """Télécharge une vidéo"""
        self.banner()
        
        print(f"{Colors.BLUE}[*] URL: {self.url}{Colors.END}")
        print(f"{Colors.BLUE}[*] Répertoire: {self.output_dir}{Colors.END}")
        
        # Options de téléchargement
        ydl_opts = {
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
        }
        
        if format_id:
            ydl_opts['format'] = format_id
        elif quality == 'best':
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        elif quality == 'worst':
            ydl_opts['format'] = 'worstvideo+worstaudio/worst'
        else:
            # Qualité spécifique (720p, 1080p, etc.)
            ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            print(f"{Colors.GREEN}{Colors.BOLD}[✓] Téléchargement réussi!{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors du téléchargement: {e}{Colors.END}")
            return False
    
    def download_audio(self, format='mp3', quality='best'):
        """Télécharge uniquement l'audio"""
        self.banner()
        
        print(f"{Colors.BLUE}[*] Mode: Audio uniquement{Colors.END}")
        print(f"{Colors.BLUE}[*] Format: {format.upper()}{Colors.END}")
        print(f"{Colors.BLUE}[*] URL: {self.url}{Colors.END}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': quality,
            }],
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            print(f"{Colors.GREEN}{Colors.BOLD}[✓] Audio téléchargé avec succès!{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def download_playlist(self, quality='best', audio_only=False):
        """Télécharge une playlist complète"""
        self.banner()
        
        print(f"{Colors.BLUE}[*] Mode: Playlist{Colors.END}")
        print(f"{Colors.BLUE}[*] URL: {self.url}{Colors.END}")
        
        ydl_opts = {
            'outtmpl': str(self.output_dir / '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
        }
        
        if audio_only:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            if quality == 'best':
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            else:
                ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
                if 'entries' in info:
                    print(f"{Colors.GREEN}[+] Playlist détectée: {info.get('title', 'N/A')}{Colors.END}")
                    print(f"{Colors.GREEN}[+] Nombre de vidéos: {len(info['entries'])}{Colors.END}\n")
                
                ydl.download([self.url])
            
            print(f"{Colors.GREEN}{Colors.BOLD}[✓] Playlist téléchargée!{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def download_subtitles(self, lang='en'):
        """Télécharge les sous-titres"""
        print(f"{Colors.BLUE}[*] Téléchargement des sous-titres ({lang})...{Colors.END}")
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [lang],
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            print(f"{Colors.GREEN}[✓] Sous-titres téléchargés{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False
    
    def download_thumbnail(self):
        """Télécharge la miniature"""
        print(f"{Colors.BLUE}[*] Téléchargement de la miniature...{Colors.END}")
        
        ydl_opts = {
            'skip_download': True,
            'writethumbnail': True,
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            print(f"{Colors.GREEN}[✓] Miniature téléchargée{Colors.END}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="YouTube Downloader - Télécharge vidéos et audios depuis YouTube"
    )
    
    parser.add_argument('url', help='URL YouTube (vidéo ou playlist)')
    parser.add_argument('-o', '--output', default='downloads',
                       help='Répertoire de sortie (défaut: downloads)')
    parser.add_argument('-q', '--quality', 
                       choices=['best', 'worst', '1080', '720', '480', '360'],
                       default='best', help='Qualité vidéo')
    parser.add_argument('-a', '--audio-only', action='store_true',
                       help='Télécharger uniquement l\'audio (MP3)')
    parser.add_argument('-f', '--format', default='mp3',
                       help='Format audio (défaut: mp3)')
    parser.add_argument('-p', '--playlist', action='store_true',
                       help='Télécharger la playlist complète')
    parser.add_argument('-l', '--list-formats', action='store_true',
                       help='Lister tous les formats disponibles')
    parser.add_argument('--format-id', help='ID de format spécifique')
    parser.add_argument('-s', '--subtitles', help='Télécharger les sous-titres (langue: en, fr, etc.)')
    parser.add_argument('-t', '--thumbnail', action='store_true',
                       help='Télécharger la miniature')
    parser.add_argument('-i', '--info', action='store_true',
                       help='Afficher les informations uniquement')
    
    args = parser.parse_args()
    
    downloader = YouTubeDownloader(args.url, args.output)
    
    try:
        # Lister les formats
        if args.list_formats:
            downloader.list_formats()
            return
        
        # Afficher les infos
        if args.info:
            downloader.banner()
            info = downloader.get_video_info()
            if info:
                downloader.display_info(info)
            return
        
        # Télécharger les sous-titres
        if args.subtitles:
            downloader.download_subtitles(args.subtitles)
            return
        
        # Télécharger la miniature
        if args.thumbnail:
            downloader.download_thumbnail()
            return
        
        # Télécharger la playlist
        if args.playlist:
            downloader.download_playlist(args.quality, args.audio_only)
            return
        
        # Télécharger l'audio uniquement
        if args.audio_only:
            downloader.download_audio(args.format, '192')
            return
        
        # Télécharger la vidéo
        downloader.download_video(args.quality, args.format_id)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[*] Téléchargement interrompu{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}[!] Erreur: {e}{Colors.END}")

if __name__ == "__main__":
    main()