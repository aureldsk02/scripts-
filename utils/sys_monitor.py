#!/usr/bin/env python3
"""
System Monitor & Resource Tracker
Surveillance en temps réel des ressources système
Usage: python3 system_monitor.py [options]
"""

import psutil
import time
import argparse
import sys
from datetime import datetime
import json
import os

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

class SystemMonitor:
    def __init__(self, interval=1, log_file=None, alert_cpu=80, alert_mem=80, alert_disk=90):
        self.interval = interval
        self.log_file = log_file
        self.alert_cpu = alert_cpu
        self.alert_mem = alert_mem
        self.alert_disk = alert_disk
        self.logs = []
    
    def banner(self):
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║     System Monitor & Resource Tracker  ║")
        print("║         Real-time System Stats         ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def clear_screen(self):
        """Nettoie l'écran"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def get_size(self, bytes):
        """Convertit les bytes en format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def get_cpu_info(self):
        """Récupère les informations CPU"""
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        per_cpu = psutil.cpu_percent(interval=0.5, percpu=True)
        
        return {
            'percent': cpu_percent,
            'count': cpu_count,
            'count_logical': cpu_count_logical,
            'frequency_current': cpu_freq.current if cpu_freq else 0,
            'frequency_max': cpu_freq.max if cpu_freq else 0,
            'per_cpu': per_cpu
        }
    
    def get_memory_info(self):
        """Récupère les informations mémoire"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percent': mem.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent
        }
    
    def get_disk_info(self):
        """Récupère les informations disque"""
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except PermissionError:
                continue
        
        disk_io = psutil.disk_io_counters()
        
        return {
            'partitions': partitions,
            'read_bytes': disk_io.read_bytes if disk_io else 0,
            'write_bytes': disk_io.write_bytes if disk_io else 0
        }
    
    def get_network_info(self):
        """Récupère les informations réseau"""
        net_io = psutil.net_io_counters()
        
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    
    def get_top_processes(self, limit=10):
        """Récupère les processus les plus gourmands"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Trier par CPU
        processes_cpu = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:limit]
        # Trier par mémoire
        processes_mem = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:limit]
        
        return {
            'by_cpu': processes_cpu,
            'by_memory': processes_mem
        }
    
    def get_system_info(self):
        """Récupère les informations système générales"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S'),
            'uptime': str(uptime).split('.')[0],
            'platform': sys.platform,
            'users': len(psutil.users())
        }
    
    def check_alerts(self, cpu_percent, mem_percent, disk_percent):
        """Vérifie et affiche les alertes"""
        alerts = []
        
        if cpu_percent > self.alert_cpu:
            alerts.append(f"{Colors.RED}[ALERTE!] CPU: {cpu_percent}% (seuil: {self.alert_cpu}%){Colors.END}")
        
        if mem_percent > self.alert_mem:
            alerts.append(f"{Colors.RED}[ALERTE!] Mémoire: {mem_percent}% (seuil: {self.alert_mem}%){Colors.END}")
        
        if disk_percent > self.alert_disk:
            alerts.append(f"{Colors.RED}[ALERTE!] Disque: {disk_percent}% (seuil: {self.alert_disk}%){Colors.END}")
        
        return alerts
    
    def display_stats(self, stats, top_procs):
        """Affiche les statistiques système"""
        self.clear_screen()
        self.banner()
        
        # Informations système
        print(f"{Colors.BOLD}{Colors.BLUE}═══════════════════ SYSTÈME ═══════════════════{Colors.END}")
        print(f"Démarrage: {stats['system']['boot_time']}")
        print(f"Uptime:    {stats['system']['uptime']}")
        print(f"Utilisateurs: {stats['system']['users']}")
        
        # CPU
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════════════ CPU ═══════════════════{Colors.END}")
        cpu = stats['cpu']
        cpu_color = Colors.GREEN if cpu['percent'] < 50 else Colors.YELLOW if cpu['percent'] < 80 else Colors.RED
        print(f"Utilisation: {cpu_color}{cpu['percent']:.1f}%{Colors.END}")
        print(f"Cœurs:       {cpu['count']} physiques / {cpu['count_logical']} logiques")
        print(f"Fréquence:   {cpu['frequency_current']:.0f} MHz / {cpu['frequency_max']:.0f} MHz")
        
        # Afficher les CPU individuels
        print(f"\n{Colors.CYAN}CPU par cœur:{Colors.END}")
        for i, percent in enumerate(cpu['per_cpu']):
            bar_length = int(percent / 2)
            bar = '█' * bar_length + '░' * (50 - bar_length)
            color = Colors.GREEN if percent < 50 else Colors.YELLOW if percent < 80 else Colors.RED
            print(f"  CPU {i:2d}: {color}{bar}{Colors.END} {percent:5.1f}%")
        
        # Mémoire
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════════════ MÉMOIRE ═══════════════════{Colors.END}")
        mem = stats['memory']
        mem_color = Colors.GREEN if mem['percent'] < 50 else Colors.YELLOW if mem['percent'] < 80 else Colors.RED
        print(f"Utilisation: {mem_color}{mem['percent']:.1f}%{Colors.END}")
        print(f"Total:       {self.get_size(mem['total'])}")
        print(f"Utilisée:    {self.get_size(mem['used'])}")
        print(f"Disponible:  {self.get_size(mem['available'])}")
        
        mem_bar_length = int(mem['percent'] / 2)
        mem_bar = '█' * mem_bar_length + '░' * (50 - mem_bar_length)
        print(f"  {mem_color}{mem_bar}{Colors.END}")
        
        if mem['swap_total'] > 0:
            print(f"\n{Colors.CYAN}SWAP:{Colors.END}")
            print(f"Total:       {self.get_size(mem['swap_total'])}")
            print(f"Utilisée:    {self.get_size(mem['swap_used'])} ({mem['swap_percent']:.1f}%)")
        
        # Disque
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════════════ DISQUE ═══════════════════{Colors.END}")
        for partition in stats['disk']['partitions']:
            disk_color = Colors.GREEN if partition['percent'] < 70 else Colors.YELLOW if partition['percent'] < 90 else Colors.RED
            print(f"\n{Colors.BOLD}{partition['mountpoint']}{Colors.END} ({partition['device']})")
            print(f"Total:       {self.get_size(partition['total'])}")
            print(f"Utilisé:     {self.get_size(partition['used'])} ({disk_color}{partition['percent']:.1f}%{Colors.END})")
            print(f"Libre:       {self.get_size(partition['free'])}")
            
            disk_bar_length = int(partition['percent'] / 2)
            disk_bar = '█' * disk_bar_length + '░' * (50 - disk_bar_length)
            print(f"  {disk_color}{disk_bar}{Colors.END}")
        
        # Réseau
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════════════ RÉSEAU ═══════════════════{Colors.END}")
        net = stats['network']
        print(f"Envoyé:      {self.get_size(net['bytes_sent'])} ({net['packets_sent']} paquets)")
        print(f"Reçu:        {self.get_size(net['bytes_recv'])} ({net['packets_recv']} paquets)")
        
        # Top processus
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════════════ TOP PROCESSUS (CPU) ═══════════════════{Colors.END}")
        print(f"{'PID':>7} {'Nom':<30} {'CPU %':>8} {'Mém %':>8} {'Statut':<10}")
        print("─" * 70)
        for proc in top_procs['by_cpu'][:5]:
            cpu_color = Colors.GREEN if (proc['cpu_percent'] or 0) < 50 else Colors.YELLOW if (proc['cpu_percent'] or 0) < 80 else Colors.RED
            print(f"{proc['pid']:>7} {proc['name'][:30]:<30} {cpu_color}{proc['cpu_percent'] or 0:>7.1f}%{Colors.END} {proc['memory_percent'] or 0:>7.1f}% {proc['status']:<10}")
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════════════ TOP PROCESSUS (MÉMOIRE) ═══════════════════{Colors.END}")
        print(f"{'PID':>7} {'Nom':<30} {'CPU %':>8} {'Mém %':>8} {'Statut':<10}")
        print("─" * 70)
        for proc in top_procs['by_memory'][:5]:
            mem_color = Colors.GREEN if (proc['memory_percent'] or 0) < 10 else Colors.YELLOW if (proc['memory_percent'] or 0) < 30 else Colors.RED
            print(f"{proc['pid']:>7} {proc['name'][:30]:<30} {proc['cpu_percent'] or 0:>7.1f}% {mem_color}{proc['memory_percent'] or 0:>7.1f}%{Colors.END} {proc['status']:<10}")
        
        # Alertes
        alerts = self.check_alerts(cpu['percent'], mem['percent'], 
                                   max([p['percent'] for p in stats['disk']['partitions']]))
        if alerts:
            print(f"\n{Colors.BOLD}{Colors.RED}═══════════════════ ALERTES ═══════════════════{Colors.END}")
            for alert in alerts:
                print(alert)
        
        print(f"\n{Colors.YELLOW}[*] Actualisation: {self.interval}s | Ctrl+C pour quitter{Colors.END}")
    
    def log_stats(self, stats):
        """Enregistre les stats dans un fichier"""
        if self.log_file:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': stats['cpu']['percent'],
                'memory_percent': stats['memory']['percent'],
                'disk_percent': max([p['percent'] for p in stats['disk']['partitions']]),
                'network_sent': stats['network']['bytes_sent'],
                'network_recv': stats['network']['bytes_recv']
            }
            
            self.logs.append(log_entry)
            
            # Sauvegarder toutes les 10 entrées
            if len(self.logs) >= 10:
                with open(self.log_file, 'a') as f:
                    for log in self.logs:
                        f.write(json.dumps(log) + '\n')
                self.logs = []
    
    def start(self):
        """Démarre le monitoring"""
        self.banner()
        print(f"{Colors.GREEN}[+] Monitoring démarré...{Colors.END}")
        
        if self.log_file:
            print(f"{Colors.GREEN}[+] Logs: {self.log_file}{Colors.END}")
        
        time.sleep(2)
        
        try:
            while True:
                stats = {
                    'system': self.get_system_info(),
                    'cpu': self.get_cpu_info(),
                    'memory': self.get_memory_info(),
                    'disk': self.get_disk_info(),
                    'network': self.get_network_info()
                }
                
                top_procs = self.get_top_processes()
                
                self.display_stats(stats, top_procs)
                self.log_stats(stats)
                
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}[*] Monitoring arrêté{Colors.END}")
            
            # Sauvegarder les logs restants
            if self.log_file and self.logs:
                with open(self.log_file, 'a') as f:
                    for log in self.logs:
                        f.write(json.dumps(log) + '\n')
                print(f"{Colors.GREEN}[+] Logs sauvegardés{Colors.END}")

def main():
    parser = argparse.ArgumentParser(
        description="System Monitor - Surveillance en temps réel des ressources système"
    )
    parser.add_argument("-i", "--interval", type=int, default=1,
                       help="Intervalle de rafraîchissement en secondes (défaut: 1)")
    parser.add_argument("-l", "--log", help="Fichier de log pour enregistrer les stats")
    parser.add_argument("--alert-cpu", type=int, default=80,
                       help="Seuil d'alerte CPU en %% (défaut: 80)")
    parser.add_argument("--alert-mem", type=int, default=80,
                       help="Seuil d'alerte mémoire en %% (défaut: 80)")
    parser.add_argument("--alert-disk", type=int, default=90,
                       help="Seuil d'alerte disque en %% (défaut: 90)")
    
    args = parser.parse_args()
    
    monitor = SystemMonitor(
        interval=args.interval,
        log_file=args.log,
        alert_cpu=args.alert_cpu,
        alert_mem=args.alert_mem,
        alert_disk=args.alert_disk
    )
    
    monitor.start()

if __name__ == "__main__":
    main()