#!/bin/bash

# Script d'installation universel pour Linux, macOS et Windows (Git Bash/WSL)
# Détecte automatiquement l'OS et installe les dépendances appropriées

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Détecter l'OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS=Linux;;
        Darwin*)    OS=macOS;;
        CYGWIN*|MINGW*|MSYS*)    OS=Windows;;
        *)          OS=Unknown;;
    esac
    
    echo_info "Système d'exploitation détecté: $OS"
    
    if [ "$OS" = "Unknown" ]; then
        echo_error "Système d'exploitation non supporté"
        exit 1
    fi
}

# Détecter la distribution Linux
detect_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        echo_error "Impossible de détecter la distribution Linux"
        exit 1
    fi
    
    echo_info "Distribution Linux détectée: $DISTRO $VERSION"
}

# Vérifier si une commande existe
command_exists() {
    command -v "$1" &> /dev/null
}

# Installation Python et pip (universel)
install_python() {
    echo_step "Vérification de Python..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo_info "Python $PYTHON_VERSION est déjà installé"
    else
        echo_warn "Python 3 n'est pas installé"
        
        case $OS in
            Linux)
                install_python_linux
                ;;
            macOS)
                install_python_macos
                ;;
            Windows)
                echo_error "Veuillez installer Python depuis https://www.python.org/downloads/"
                exit 1
                ;;
        esac
    fi
    
    # Vérifier pip
    if command_exists pip3; then
        echo_info "pip est déjà installé"
    else
        echo_warn "Installation de pip..."
        python3 -m ensurepip --upgrade 2>/dev/null || {
            case $OS in
                Linux)
                    install_pip_linux
                    ;;
                macOS)
                    python3 -m ensurepip --upgrade
                    ;;
            esac
        }
    fi
}

# Installation Python sur Linux
install_python_linux() {
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            sudo apt update
            sudo apt install -y python3 python3-pip
            ;;
        fedora|rhel|centos|rocky|almalinux)
            sudo dnf install -y python3 python3-pip
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -S --noconfirm python python-pip
            ;;
        *)
            echo_error "Distribution Linux non supportée pour l'installation automatique"
            exit 1
            ;;
    esac
}

# Installation pip sur Linux
install_pip_linux() {
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            sudo apt install -y python3-pip
            ;;
        fedora|rhel|centos|rocky|almalinux)
            sudo dnf install -y python3-pip
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -S --noconfirm python-pip
            ;;
    esac
}

# Installation Python sur macOS
install_python_macos() {
    if command_exists brew; then
        echo_info "Installation de Python via Homebrew..."
        brew install python3
    else
        echo_error "Homebrew n'est pas installé. Installez-le depuis https://brew.sh/"
        echo_error "Ou installez Python depuis https://www.python.org/downloads/"
        exit 1
    fi
}

# Installation Git (universel)
install_git() {
    echo_step "Vérification de Git..."
    
    if command_exists git; then
        GIT_VERSION=$(git --version | awk '{print $3}')
        echo_info "Git $GIT_VERSION est déjà installé"
        return
    fi
    
    echo_warn "Installation de Git..."
    
    case $OS in
        Linux)
            case $DISTRO in
                ubuntu|debian|linuxmint|pop)
                    sudo apt install -y git
                    ;;
                fedora|rhel|centos|rocky|almalinux)
                    sudo dnf install -y git
                    ;;
                arch|manjaro|endeavouros)
                    sudo pacman -S --noconfirm git
                    ;;
            esac
            ;;
        macOS)
            if command_exists brew; then
                brew install git
            else
                echo_warn "Git sera installé via Xcode Command Line Tools"
                xcode-select --install
            fi
            ;;
        Windows)
            echo_error "Veuillez installer Git depuis https://git-scm.com/download/win"
            exit 1
            ;;
    esac
    
    echo_info "Git installé avec succès"
}

# Installation Docker (universel)
install_docker() {
    echo_step "Vérification de Docker..."
    
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
        echo_info "Docker $DOCKER_VERSION est déjà installé"
        return
    fi
    
    echo_warn "Installation de Docker..."
    
    case $OS in
        Linux)
            # Installation via script officiel Docker
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            rm get-docker.sh
            
            # Démarrer et activer Docker
            sudo systemctl enable docker
            sudo systemctl start docker
            
            echo_info "Docker installé avec succès"
            echo_warn "Pour utiliser Docker sans sudo: sudo usermod -aG docker \$USER"
            echo_warn "Puis déconnectez-vous et reconnectez-vous"
            ;;
        macOS)
            echo_warn "Veuillez installer Docker Desktop depuis https://www.docker.com/products/docker-desktop"
            echo_info "Ou utilisez Homebrew: brew install --cask docker"
            ;;
        Windows)
            echo_warn "Veuillez installer Docker Desktop depuis https://www.docker.com/products/docker-desktop"
            ;;
    esac
}

# Installation VS Code (universel)
install_vscode() {
    echo_step "Vérification de VS Code..."
    
    if command_exists code; then
        echo_info "VS Code est déjà installé"
        return
    fi
    
    echo_warn "Installation de VS Code..."
    
    case $OS in
        Linux)
            case $DISTRO in
                ubuntu|debian|linuxmint|pop)
                    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
                    sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
                    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list
                    rm packages.microsoft.gpg
                    sudo apt update
                    sudo apt install -y code
                    ;;
                fedora|rhel|centos|rocky|almalinux)
                    sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
                    sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'
                    sudo dnf install -y code
                    ;;
                arch|manjaro|endeavouros)
                    sudo pacman -S --noconfirm code
                    ;;
            esac
            ;;
        macOS)
            if command_exists brew; then
                brew install --cask visual-studio-code
            else
                echo_warn "Veuillez installer VS Code depuis https://code.visualstudio.com/"
            fi
            ;;
        Windows)
            echo_warn "Veuillez installer VS Code depuis https://code.visualstudio.com/"
            ;;
    esac
}

# Installation Node.js et npm (universel)
install_nodejs() {
    echo_step "Vérification de Node.js..."
    
    if command_exists node; then
        NODE_VERSION=$(node --version)
        echo_info "Node.js $NODE_VERSION est déjà installé"
        return
    fi
    
    echo_warn "Installation de Node.js..."
    
    case $OS in
        Linux)
            case $DISTRO in
                ubuntu|debian|linuxmint|pop)
                    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
                    sudo apt install -y nodejs
                    ;;
                fedora|rhel|centos|rocky|almalinux)
                    curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
                    sudo dnf install -y nodejs
                    ;;
                arch|manjaro|endeavouros)
                    sudo pacman -S --noconfirm nodejs npm
                    ;;
            esac
            ;;
        macOS)
            if command_exists brew; then
                brew install node
            else
                echo_warn "Veuillez installer Node.js depuis https://nodejs.org/"
            fi
            ;;
        Windows)
            echo_warn "Veuillez installer Node.js depuis https://nodejs.org/"
            ;;
    esac
}

# Installation des dépendances Python du projet
install_python_dependencies() {
    echo_step "Installation des dépendances Python..."
    
    if [ -f "requirements.txt" ]; then
        echo_info "Installation depuis requirements.txt..."
        pip3 install -r requirements.txt
        echo_info "Dépendances Python installées avec succès"
    else
        echo_warn "Fichier requirements.txt non trouvé"
        echo_info "Installation des dépendances de base..."
        pip3 install requests
    fi
}

# Installation des utilitaires de base
install_basic_utilities() {
    echo_step "Installation des utilitaires de base..."
    
    case $OS in
        Linux)
            case $DISTRO in
                ubuntu|debian|linuxmint|pop)
                    sudo apt install -y curl wget vim htop tree net-tools unzip build-essential
                    ;;
                fedora|rhel|centos|rocky|almalinux)
                    sudo dnf install -y curl wget vim htop tree net-tools unzip gcc make
                    ;;
                arch|manjaro|endeavouros)
                    sudo pacman -S --noconfirm curl wget vim htop tree net-tools unzip base-devel
                    ;;
            esac
            ;;
        macOS)
            if command_exists brew; then
                brew install curl wget vim htop tree
            fi
            ;;
        Windows)
            echo_info "Utilitaires de base disponibles via Git Bash"
            ;;
    esac
}

# Menu interactif
show_menu() {
    echo ""
    echo "========================================="
    echo "  Installation Universelle - Utilitaires"
    echo "========================================="
    echo ""
    echo "Que souhaitez-vous installer ?"
    echo ""
    echo "  1) Tout installer (recommandé)"
    echo "  2) Python et pip uniquement"
    echo "  3) Git uniquement"
    echo "  4) Docker uniquement"
    echo "  5) VS Code uniquement"
    echo "  6) Node.js uniquement"
    echo "  7) Dépendances Python du projet"
    echo "  8) Utilitaires de base"
    echo "  9) Installation personnalisée"
    echo "  0) Quitter"
    echo ""
    read -p "Votre choix [1-9]: " choice
    
    case $choice in
        1)
            install_all
            ;;
        2)
            install_python
            ;;
        3)
            install_git
            ;;
        4)
            install_docker
            ;;
        5)
            install_vscode
            ;;
        6)
            install_nodejs
            ;;
        7)
            install_python_dependencies
            ;;
        8)
            install_basic_utilities
            ;;
        9)
            custom_install
            ;;
        0)
            echo_info "Installation annulée"
            exit 0
            ;;
        *)
            echo_error "Choix invalide"
            show_menu
            ;;
    esac
}

# Installation complète
install_all() {
    echo_info "=== Installation complète ==="
    install_python
    install_git
    install_docker
    install_vscode
    install_nodejs
    install_basic_utilities
    install_python_dependencies
}

# Installation personnalisée
custom_install() {
    echo ""
    echo "Installation personnalisée:"
    echo ""
    
    read -p "Installer Python et pip ? (o/n): " install_py
    read -p "Installer Git ? (o/n): " install_g
    read -p "Installer Docker ? (o/n): " install_d
    read -p "Installer VS Code ? (o/n): " install_vs
    read -p "Installer Node.js ? (o/n): " install_node
    read -p "Installer les utilitaires de base ? (o/n): " install_utils
    read -p "Installer les dépendances Python du projet ? (o/n): " install_deps
    
    [ "$install_py" = "o" ] && install_python
    [ "$install_g" = "o" ] && install_git
    [ "$install_d" = "o" ] && install_docker
    [ "$install_vs" = "o" ] && install_vscode
    [ "$install_node" = "o" ] && install_nodejs
    [ "$install_utils" = "o" ] && install_basic_utilities
    [ "$install_deps" = "o" ] && install_python_dependencies
}

# Fonction principale
main() {
    echo_info "=== Script d'installation universel ==="
    echo ""
    
    detect_os
    
    if [ "$OS" = "Linux" ]; then
        detect_linux_distro
    fi
    
    # Vérifier les permissions pour Linux
    if [ "$OS" = "Linux" ] && [ "$EUID" -eq 0 ]; then
        echo_warn "Ce script est exécuté en tant que root"
        echo_warn "Certaines installations peuvent nécessiter des permissions utilisateur"
    fi
    
    show_menu
    
    echo ""
    echo_info "=== Installation terminée ==="
    
    if [ "$OS" = "Linux" ]; then
        echo_info "Conseil: Redémarrez votre session pour appliquer tous les changements"
    fi
}

# Exécution
main
