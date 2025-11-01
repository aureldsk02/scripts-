#!/bin/bash

# Script d'installation d'outils de cybersécurité pour Linux
# Détecte automatiquement la distribution et installe les outils de pentesting et sécurité

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo_header() {
    echo -e "${CYAN}[*]${NC} $1"
}

# Vérifier si le script est exécuté en tant que root
if [[ $EUID -ne 0 ]]; then
   echo_error "Ce script doit être exécuté avec les privilèges root (sudo)"
   exit 1
fi

# Détecter la distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        echo_error "Impossible de détecter la distribution"
        exit 1
    fi
    
    echo_info "Distribution détectée: $DISTRO $VERSION"
}

# Fonction pour installer les dépendances de base
install_base_dependencies() {
    echo_header "Installation des dépendances de base..."
    
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt update
            apt install -y curl wget git build-essential python3 python3-pip python3-venv pipx \
                libssl-dev libffi-dev python3-dev tor proxychains4 unzip golang-go
            # Configurer pipx
            pipx ensurepath 2>/dev/null || true
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y curl wget git gcc python3 python3-pip \
                openssl-devel libffi-devel python3-devel tor proxychains-ng unzip golang
            ;;
        arch|manjaro|endeavouros)
            pacman -Syu --noconfirm
            pacman -S --noconfirm curl wget git base-devel python python-pip \
                openssl tor proxychains-ng unzip go
            ;;
    esac
    
    echo_info "Dépendances de base installées"
}

# Installation des outils de reconnaissance
install_recon_tools() {
    echo_header "Installation des outils de reconnaissance..."
    
    # Nmap
    echo_info "Installation de Nmap..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y nmap
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y nmap
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm nmap
            ;;
    esac
    
    # Masscan
    echo_info "Installation de Masscan..."
    if ! command -v masscan &> /dev/null; then
        git clone https://github.com/robertdavidgraham/masscan /tmp/masscan
        cd /tmp/masscan
        make
        make install
        cd -
        rm -rf /tmp/masscan
    fi
    
    # Amass
    echo_info "Installation de Amass..."
    if ! command -v amass &> /dev/null; then
        case $DISTRO in
            ubuntu|debian|linuxmint|pop|kali)
                apt install -y amass 2>/dev/null || snap install amass 2>/dev/null || {
                    echo_warn "Impossible d'installer Amass automatiquement"
                    echo_warn "Installation manuelle: snap install amass"
                }
                ;;
            fedora|rhel|centos|rocky|almalinux)
                dnf install -y amass 2>/dev/null || {
                    echo_warn "Impossible d'installer Amass automatiquement"
                    echo_warn "Installation manuelle: https://github.com/owasp-amass/amass"
                }
                ;;
            arch|manjaro|endeavouros)
                pacman -S --noconfirm amass 2>/dev/null || {
                    echo_warn "Impossible d'installer Amass automatiquement"
                    echo_warn "Installation manuelle: yay -S amass"
                }
                ;;
        esac
    else
        echo_warn "Amass est déjà installé"
    fi
    
    # Subfinder
    echo_info "Installation de Subfinder..."
    if ! command -v subfinder &> /dev/null; then
        # Essayer avec Go d'abord
        if command -v go &> /dev/null; then
            go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
            # Copier dans /usr/local/bin si installé dans ~/go/bin
            if [ -f "$HOME/go/bin/subfinder" ]; then
                cp "$HOME/go/bin/subfinder" /usr/local/bin/ 2>/dev/null || true
            fi
        else
            echo_warn "Go n'est pas installé. Subfinder nécessite Go."
            echo_warn "Installation manuelle: apt install golang-go puis go install subfinder"
        fi
    else
        echo_warn "Subfinder est déjà installé"
    fi
    
    # DNSenum
    echo_info "Installation de DNSenum..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y dnsenum
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y dnsenum
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm dnsenum
            ;;
    esac
    
    echo_info "Outils de reconnaissance installés"
}

# Installation des outils de scan de vulnérabilités
install_vuln_scanners() {
    echo_header "Installation des scanners de vulnérabilités..."
    
    # Nikto
    echo_info "Installation de Nikto..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y nikto
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y nikto
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm nikto
            ;;
    esac
    
    # Nuclei
    echo_info "Installation de Nuclei..."
    if ! command -v nuclei &> /dev/null; then
        # Essayer avec Go d'abord
        if command -v go &> /dev/null; then
            go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
            # Copier dans /usr/local/bin si installé dans ~/go/bin
            if [ -f "$HOME/go/bin/nuclei" ]; then
                cp "$HOME/go/bin/nuclei" /usr/local/bin/ 2>/dev/null || true
            fi
        else
            echo_warn "Go n'est pas installé. Nuclei nécessite Go."
            echo_warn "Installation manuelle: apt install golang-go puis go install nuclei"
        fi
    else
        echo_warn "Nuclei est déjà installé"
    fi
    
    # Wapiti
    echo_info "Installation de Wapiti..."
    # Essayer d'abord avec pipx (recommandé pour Ubuntu 24.04+)
    if command -v pipx &> /dev/null; then
        pipx install wapiti3 2>/dev/null || echo_warn "Échec de l'installation de Wapiti via pipx"
    else
        # Installer pipx si pas présent
        case $DISTRO in
            ubuntu|debian|linuxmint|pop|kali)
                apt install -y pipx
                pipx install wapiti3 2>/dev/null || pip3 install wapiti3 --break-system-packages
                ;;
            *)
                pip3 install wapiti3 --break-system-packages 2>/dev/null || pip3 install wapiti3
                ;;
        esac
    fi
    
    echo_info "Scanners de vulnérabilités installés"
}

# Installation des outils web
install_web_tools() {
    echo_header "Installation des outils web..."
    
    # Gobuster
    echo_info "Installation de Gobuster..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y gobuster
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y gobuster
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm gobuster
            ;;
    esac
    
    # Ffuf
    echo_info "Installation de Ffuf..."
    if ! command -v ffuf &> /dev/null; then
        # Essayer avec Go d'abord
        if command -v go &> /dev/null; then
            go install github.com/ffuf/ffuf/v2@latest
            # Copier dans /usr/local/bin si installé dans ~/go/bin
            if [ -f "$HOME/go/bin/ffuf" ]; then
                cp "$HOME/go/bin/ffuf" /usr/local/bin/ 2>/dev/null || true
            fi
        else
            echo_warn "Go n'est pas installé. Ffuf nécessite Go."
            echo_warn "Installation manuelle: apt install golang-go puis go install ffuf"
        fi
    else
        echo_warn "Ffuf est déjà installé"
    fi
    
    # SQLMap
    echo_info "Installation de SQLMap..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y sqlmap
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y sqlmap
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm sqlmap
            ;;
    esac
    
    # Burp Suite Community (nécessite Java)
    echo_info "Installation de Java pour Burp Suite..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y default-jdk
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y java-latest-openjdk
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm jdk-openjdk
            ;;
    esac
    
    echo_info "Outils web installés"
}

# Installation des outils d'exploitation
install_exploit_tools() {
    echo_header "Installation des outils d'exploitation..."
    
    # Metasploit Framework
    echo_info "Installation de Metasploit Framework..."
    if ! command -v msfconsole &> /dev/null; then
        curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > /tmp/msfinstall
        chmod 755 /tmp/msfinstall
        /tmp/msfinstall
        rm /tmp/msfinstall
    else
        echo_warn "Metasploit est déjà installé"
    fi
    
    # Hydra
    echo_info "Installation de Hydra..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y hydra
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y hydra
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm hydra
            ;;
    esac
    
    # John the Ripper
    echo_info "Installation de John the Ripper..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y john
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y john
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm john
            ;;
    esac
    
    # Hashcat
    echo_info "Installation de Hashcat..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y hashcat
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y hashcat
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm hashcat
            ;;
    esac
    
    echo_info "Outils d'exploitation installés"
}

# Installation des outils réseau
install_network_tools() {
    echo_header "Installation des outils réseau..."
    
    # Wireshark
    echo_info "Installation de Wireshark..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            DEBIAN_FRONTEND=noninteractive apt install -y wireshark
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y wireshark
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm wireshark-qt
            ;;
    esac
    
    # TCPDump
    echo_info "Installation de TCPDump..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y tcpdump
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y tcpdump
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm tcpdump
            ;;
    esac
    
    # Aircrack-ng
    echo_info "Installation de Aircrack-ng..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y aircrack-ng
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y aircrack-ng
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm aircrack-ng
            ;;
    esac
    
    # Netcat
    echo_info "Installation de Netcat..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|kali)
            apt install -y netcat-openbsd
            ;;
        fedora|rhel|centos|rocky|almalinux)
            dnf install -y nc
            ;;
        arch|manjaro|endeavouros)
            pacman -S --noconfirm openbsd-netcat
            ;;
    esac
    
    echo_info "Outils réseau installés"
}

# Installation des outils de post-exploitation
install_post_exploit_tools() {
    echo_header "Installation des outils de post-exploitation..."
    
    # LinPEAS
    echo_info "Téléchargement de LinPEAS..."
    mkdir -p /opt/privilege-escalation
    wget https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh -O /opt/privilege-escalation/linpeas.sh
    chmod +x /opt/privilege-escalation/linpeas.sh
    
    # Linux Exploit Suggester
    echo_info "Téléchargement de Linux Exploit Suggester..."
    wget https://raw.githubusercontent.com/mzet-/linux-exploit-suggester/master/linux-exploit-suggester.sh -O /opt/privilege-escalation/les.sh
    chmod +x /opt/privilege-escalation/les.sh
    
    # Mimipenguin
    echo_info "Installation de Mimipenguin..."
    git clone https://github.com/huntergregal/mimipenguin.git /opt/mimipenguin
    chmod +x /opt/mimipenguin/mimipenguin.sh
    
    echo_info "Outils de post-exploitation installés dans /opt/"
}

# Installation des wordlists
install_wordlists() {
    echo_header "Installation des wordlists..."
    
    mkdir -p /usr/share/wordlists
    
    # SecLists
    echo_info "Clonage de SecLists..."
    if [ ! -d "/usr/share/wordlists/SecLists" ]; then
        git clone https://github.com/danielmiessler/SecLists.git /usr/share/wordlists/SecLists
    else
        echo_warn "SecLists déjà présent"
    fi
    
    # RockYou
    echo_info "Téléchargement de RockYou..."
    if [ ! -f "/usr/share/wordlists/rockyou.txt" ]; then
        case $DISTRO in
            ubuntu|debian|linuxmint|pop|kali)
                apt install -y wordlists 2>/dev/null || {
                    wget https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt -O /usr/share/wordlists/rockyou.txt
                }
                ;;
            *)
                wget https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt -O /usr/share/wordlists/rockyou.txt
                ;;
        esac
    else
        echo_warn "RockYou déjà présent"
    fi
    
    echo_info "Wordlists installées dans /usr/share/wordlists/"
}

# Créer un résumé des outils installés
create_summary() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Installation des outils de cybersécurité       ║${NC}"
    echo -e "${BLUE}║                    TERMINÉE ✓                          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}📋 Outils installés :${NC}"
    echo ""
    echo -e "${GREEN}🔍 Reconnaissance :${NC}"
    echo "   • Nmap, Masscan, Amass, Subfinder, DNSenum"
    echo ""
    echo -e "${GREEN}🎯 Scan de vulnérabilités :${NC}"
    echo "   • Nikto, Nuclei, Wapiti"
    echo ""
    echo -e "${GREEN}🌐 Outils Web :${NC}"
    echo "   • Gobuster, Ffuf, SQLMap, Burp Suite (Java)"
    echo ""
    echo -e "${GREEN}💥 Exploitation :${NC}"
    echo "   • Metasploit, Hydra, John the Ripper, Hashcat"
    echo ""
    echo -e "${GREEN}🌍 Réseau :${NC}"
    echo "   • Wireshark, TCPDump, Aircrack-ng, Netcat"
    echo ""
    echo -e "${GREEN}📁 Post-exploitation :${NC}"
    echo "   • LinPEAS (/opt/privilege-escalation/)"
    echo "   • Linux Exploit Suggester (/opt/privilege-escalation/)"
    echo "   • Mimipenguin (/opt/mimipenguin/)"
    echo ""
    echo -e "${GREEN}📚 Wordlists :${NC}"
    echo "   • SecLists (/usr/share/wordlists/SecLists/)"
    echo "   • RockYou (/usr/share/wordlists/rockyou.txt)"
    echo ""
    echo -e "${YELLOW}⚠️  Notes importantes :${NC}"
    echo "   • Certains outils nécessitent des privilèges root"
    echo "   • Utilisez ces outils uniquement dans un cadre légal"
    echo "   • Configurez Tor pour l'anonymat (proxychains4 installé)"
    echo "   • Mettez à jour régulièrement : nuclei -update-templates"
    echo ""
    echo -e "${CYAN}🚀 Pour commencer :${NC}"
    echo "   • nmap -sV <target>        : Scan de services"
    echo "   • nuclei -u <url>          : Scan de vulnérabilités"
    echo "   • gobuster dir -u <url>    : Énumération de répertoires"
    echo "   • msfconsole               : Lancer Metasploit"
    echo ""
}

# Menu interactif
show_menu() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║    Installation d'outils de cybersécurité Linux       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Choisissez une option d'installation :"
    echo ""
    echo "  1) Installation complète (tous les outils)"
    echo "  2) Outils de reconnaissance uniquement"
    echo "  3) Scanners de vulnérabilités uniquement"
    echo "  4) Outils web uniquement"
    echo "  5) Outils d'exploitation uniquement"
    echo "  6) Outils réseau uniquement"
    echo "  7) Outils de post-exploitation uniquement"
    echo "  8) Wordlists uniquement"
    echo "  9) Quitter"
    echo ""
    read -p "Votre choix [1-9]: " choice
    
    case $choice in
        1)
            detect_distro
            install_base_dependencies
            install_recon_tools
            install_vuln_scanners
            install_web_tools
            install_exploit_tools
            install_network_tools
            install_post_exploit_tools
            install_wordlists
            create_summary
            ;;
        2)
            detect_distro
            install_base_dependencies
            install_recon_tools
            echo_info "Installation des outils de reconnaissance terminée"
            ;;
        3)
            detect_distro
            install_base_dependencies
            install_vuln_scanners
            echo_info "Installation des scanners de vulnérabilités terminée"
            ;;
        4)
            detect_distro
            install_base_dependencies
            install_web_tools
            echo_info "Installation des outils web terminée"
            ;;
        5)
            detect_distro
            install_base_dependencies
            install_exploit_tools
            echo_info "Installation des outils d'exploitation terminée"
            ;;
        6)
            detect_distro
            install_base_dependencies
            install_network_tools
            echo_info "Installation des outils réseau terminée"
            ;;
        7)
            detect_distro
            install_post_exploit_tools
            echo_info "Installation des outils de post-exploitation terminée"
            ;;
        8)
            install_wordlists
            echo_info "Installation des wordlists terminée"
            ;;
        9)
            echo_info "Installation annulée"
            exit 0
            ;;
        *)
            echo_error "Option invalide"
            exit 1
            ;;
    esac
}

# Point d'entrée
main() {
    clear
    show_menu
}

main
