#!/usr/bin/env python3
"""
Network Packet Sniffer
Capture et analyse de paquets réseau
Usage: sudo python3 network_sniffer.py [options]
"""

import socket
import struct
import argparse
import sys
from datetime import datetime
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

class PacketSniffer:
    def __init__(self, interface=None, filter_proto=None, output_file=None):
        self.interface = interface
        self.filter_proto = filter_proto
        self.output_file = output_file
        self.packet_count = 0
        self.packets = []
        
    def banner(self):
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("╔════════════════════════════════════════╗")
        print("║      Network Packet Sniffer v1.0       ║")
        print("║        Capture & Analyze Traffic       ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.END}")
    
    def create_socket(self):
        """Crée un socket raw pour capturer les paquets"""
        try:
            # Socket raw pour capturer tous les paquets IP
            if sys.platform == 'win32':
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                sock.bind((socket.gethostname(), 0))
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            else:
                sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
                if self.interface:
                    sock.bind((self.interface, 0))
            
            return sock
        except PermissionError:
            print(f"{Colors.RED}[!] Erreur: Permissions root requises{Colors.END}")
            print(f"{Colors.YELLOW}[*] Utilisez: sudo python3 {sys.argv[0]}{Colors.END}")
            sys.exit(1)
        except Exception as e:
            print(f"{Colors.RED}[!] Erreur lors de la création du socket: {e}{Colors.END}")
            sys.exit(1)
    
    def parse_ethernet_frame(self, data):
        """Parse un frame Ethernet"""
        dest_mac, src_mac, proto = struct.unpack('! 6s 6s H', data[:14])
        return {
            'dest_mac': self.format_mac(dest_mac),
            'src_mac': self.format_mac(src_mac),
            'proto': socket.htons(proto)
        }
    
    def format_mac(self, mac_bytes):
        """Formate une adresse MAC"""
        return ':'.join(map('{:02x}'.format, mac_bytes))
    
    def parse_ipv4_packet(self, data):
        """Parse un paquet IPv4"""
        version_header_length = data[0]
        version = version_header_length >> 4
        header_length = (version_header_length & 15) * 4
        ttl, proto, src, dest = struct.unpack('! 8x B B 2x 4s 4s', data[:20])
        
        return {
            'version': version,
            'header_length': header_length,
            'ttl': ttl,
            'protocol': proto,
            'src_ip': self.format_ipv4(src),
            'dest_ip': self.format_ipv4(dest)
        }
    
    def format_ipv4(self, ip_bytes):
        """Formate une adresse IPv4"""
        return '.'.join(map(str, ip_bytes))
    
    def parse_icmp_packet(self, data):
        """Parse un paquet ICMP"""
        icmp_type, code, checksum = struct.unpack('! B B H', data[:4])
        return {
            'type': icmp_type,
            'code': code,
            'checksum': checksum
        }
    
    def parse_tcp_segment(self, data):
        """Parse un segment TCP"""
        src_port, dest_port, sequence, acknowledgment, offset_reserved_flags = struct.unpack('! H H L L H', data[:14])
        offset = (offset_reserved_flags >> 12) * 4
        flag_urg = (offset_reserved_flags & 32) >> 5
        flag_ack = (offset_reserved_flags & 16) >> 4
        flag_psh = (offset_reserved_flags & 8) >> 3
        flag_rst = (offset_reserved_flags & 4) >> 2
        flag_syn = (offset_reserved_flags & 2) >> 1
        flag_fin = offset_reserved_flags & 1
        
        return {
            'src_port': src_port,
            'dest_port': dest_port,
            'sequence': sequence,
            'acknowledgment': acknowledgment,
            'flags': {
                'URG': flag_urg,
                'ACK': flag_ack,
                'PSH': flag_psh,
                'RST': flag_rst,
                'SYN': flag_syn,
                'FIN': flag_fin
            }
        }
    
    def parse_udp_segment(self, data):
        """Parse un segment UDP"""
        src_port, dest_port, length = struct.unpack('! H H 2x H', data[:8])
        return {
            'src_port': src_port,
            'dest_port': dest_port,
            'length': length
        }
    
    def get_protocol_name(self, protocol_num):
        """Retourne le nom du protocole"""
        protocols = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP'
        }
        return protocols.get(protocol_num, f'Other({protocol_num})')
    
    def format_flags(self, flags):
        """Formate les flags TCP"""
        flag_str = []
        if flags['SYN']:
            flag_str.append('SYN')
        if flags['ACK']:
            flag_str.append('ACK')
        if flags['FIN']:
            flag_str.append('FIN')
        if flags['RST']:
            flag_str.append('RST')
        if flags['PSH']:
            flag_str.append('PSH')
        if flags['URG']:
            flag_str.append('URG')
        return ','.join(flag_str)
    
    def display_packet(self, packet_info):
        """Affiche les informations du paquet"""
        self.packet_count += 1
        
        # En-tête du paquet
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}Paquet #{self.packet_count} - {packet_info['timestamp']}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        # Informations Ethernet (Linux uniquement)
        if 'ethernet' in packet_info:
            eth = packet_info['ethernet']
            print(f"{Colors.YELLOW}[Ethernet]{Colors.END}")
            print(f"  MAC Source:      {eth['src_mac']}")
            print(f"  MAC Destination: {eth['dest_mac']}")
            print(f"  Protocol:        {eth['proto']}")
        
        # Informations IP
        if 'ipv4' in packet_info:
            ip = packet_info['ipv4']
            proto_name = self.get_protocol_name(ip['protocol'])
            print(f"\n{Colors.BLUE}[IPv4 - {proto_name}]{Colors.END}")
            print(f"  Source:      {ip['src_ip']}")
            print(f"  Destination: {ip['dest_ip']}")
            print(f"  TTL:         {ip['ttl']}")
        
        # Informations TCP
        if 'tcp' in packet_info:
            tcp = packet_info['tcp']
            flags = self.format_flags(tcp['flags'])
            print(f"\n{Colors.GREEN}[TCP]{Colors.END}")
            print(f"  Port Source:      {tcp['src_port']}")
            print(f"  Port Destination: {tcp['dest_port']}")
            print(f"  Flags:           {flags}")
            print(f"  Sequence:        {tcp['sequence']}")
            print(f"  Acknowledgment:  {tcp['acknowledgment']}")
        
        # Informations UDP
        if 'udp' in packet_info:
            udp = packet_info['udp']
            print(f"\n{Colors.GREEN}[UDP]{Colors.END}")
            print(f"  Port Source:      {udp['src_port']}")
            print(f"  Port Destination: {udp['dest_port']}")
            print(f"  Longueur:        {udp['length']}")
        
        # Informations ICMP
        if 'icmp' in packet_info:
            icmp = packet_info['icmp']
            print(f"\n{Colors.MAGENTA}[ICMP]{Colors.END}")
            print(f"  Type:     {icmp['type']}")
            print(f"  Code:     {icmp['code']}")
            print(f"  Checksum: {icmp['checksum']}")
        
        # Données (premiers octets)
        if 'data' in packet_info and packet_info['data']:
            print(f"\n{Colors.YELLOW}[Données (premiers 64 octets)]{Colors.END}")
            data_preview = packet_info['data'][:64]
            print(f"  {' '.join(f'{b:02x}' for b in data_preview)}")
    
    def save_packets(self):
        """Sauvegarde les paquets capturés"""
        if self.output_file and self.packets:
            with open(self.output_file, 'w') as f:
                json.dump(self.packets, f, indent=4)
            print(f"\n{Colors.GREEN}[+] {len(self.packets)} paquets sauvegardés dans: {self.output_file}{Colors.END}")
    
    def start_sniffing(self, count=None):
        """Démarre la capture de paquets"""
        self.banner()
        
        print(f"{Colors.BLUE}[*] Démarrage de la capture...{Colors.END}")
        if self.interface:
            print(f"{Colors.BLUE}[*] Interface: {self.interface}{Colors.END}")
        if self.filter_proto:
            print(f"{Colors.BLUE}[*] Filtre: {self.filter_proto}{Colors.END}")
        print(f"{Colors.YELLOW}[*] Appuyez sur Ctrl+C pour arrêter{Colors.END}\n")
        
        sock = self.create_socket()
        
        try:
            while True:
                if count and self.packet_count >= count:
                    break
                
                raw_data, addr = sock.recvfrom(65535)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                packet_info = {'timestamp': timestamp}
                
                # Parse selon la plateforme
                if sys.platform != 'win32':
                    # Linux: parse Ethernet frame
                    eth = self.parse_ethernet_frame(raw_data)
                    packet_info['ethernet'] = eth
                    
                    # IPv4
                    if eth['proto'] == 8:
                        ipv4 = self.parse_ipv4_packet(raw_data[14:])
                        packet_info['ipv4'] = ipv4
                        data_start = 14 + ipv4['header_length']
                        
                        # Filtrage par protocole
                        proto_name = self.get_protocol_name(ipv4['protocol'])
                        if self.filter_proto and self.filter_proto.upper() != proto_name:
                            continue
                        
                        # TCP
                        if ipv4['protocol'] == 6:
                            tcp = self.parse_tcp_segment(raw_data[data_start:])
                            packet_info['tcp'] = tcp
                            packet_info['data'] = raw_data[data_start + 20:]
                        
                        # UDP
                        elif ipv4['protocol'] == 17:
                            udp = self.parse_udp_segment(raw_data[data_start:])
                            packet_info['udp'] = udp
                            packet_info['data'] = raw_data[data_start + 8:]
                        
                        # ICMP
                        elif ipv4['protocol'] == 1:
                            icmp = self.parse_icmp_packet(raw_data[data_start:])
                            packet_info['icmp'] = icmp
                            packet_info['data'] = raw_data[data_start + 4:]
                else:
                    # Windows: parse directement IPv4
                    ipv4 = self.parse_ipv4_packet(raw_data)
                    packet_info['ipv4'] = ipv4
                    
                    proto_name = self.get_protocol_name(ipv4['protocol'])
                    if self.filter_proto and self.filter_proto.upper() != proto_name:
                        continue
                    
                    data_start = ipv4['header_length']
                    
                    if ipv4['protocol'] == 6:
                        tcp = self.parse_tcp_segment(raw_data[data_start:])
                        packet_info['tcp'] = tcp
                    elif ipv4['protocol'] == 17:
                        udp = self.parse_udp_segment(raw_data[data_start:])
                        packet_info['udp'] = udp
                    elif ipv4['protocol'] == 1:
                        icmp = self.parse_icmp_packet(raw_data[data_start:])
                        packet_info['icmp'] = icmp
                
                self.display_packet(packet_info)
                self.packets.append(packet_info)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}[*] Capture interrompue{Colors.END}")
            print(f"{Colors.GREEN}[+] {self.packet_count} paquets capturés{Colors.END}")
            self.save_packets()
        except Exception as e:
            print(f"\n{Colors.RED}[!] Erreur: {e}{Colors.END}")
        finally:
            sock.close()

def main():
    parser = argparse.ArgumentParser(
        description="Network Packet Sniffer - Capture et analyse de paquets réseau"
    )
    parser.add_argument("-i", "--interface", help="Interface réseau (ex: eth0, wlan0)")
    parser.add_argument("-f", "--filter", choices=['TCP', 'UDP', 'ICMP'],
                       help="Filtrer par protocole")
    parser.add_argument("-c", "--count", type=int,
                       help="Nombre de paquets à capturer")
    parser.add_argument("-o", "--output", help="Fichier de sortie JSON")
    
    args = parser.parse_args()
    
    sniffer = PacketSniffer(
        interface=args.interface,
        filter_proto=args.filter,
        output_file=args.output
    )
    
    sniffer.start_sniffing(count=args.count)

if __name__ == "__main__":
    main()