#!/bin/bash

# ============================================================================
# Creativity Rating App - Setup Script
# ============================================================================
# Automatically sets up the development environment for the app.
# Run this script after cloning the repository to a new machine.
#
# Usage: ./setup.sh
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Minimum required Python version
REQUIRED_PYTHON_MAJOR=3
REQUIRED_PYTHON_MINOR=8

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Main Setup
# ============================================================================

print_header "Creativity Rating App Setup"
echo ""

# Check OS
print_info "Detecting operating system..."
OS=$(uname -s)
if [[ "$OS" == "Linux" ]]; then
    print_success "Detected: Linux"
    PACKAGE_MANAGER="apt"
elif [[ "$OS" == "Darwin" ]]; then
    print_success "Detected: macOS"
    PACKAGE_MANAGER="brew"
else
    print_error "Unsupported operating system: $OS"
    exit 1
fi
echo ""

# Check Python version
print_info "Checking Python installation..."
if check_command python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -ge $REQUIRED_PYTHON_MAJOR ] && [ "$PYTHON_MINOR" -ge $REQUIRED_PYTHON_MINOR ]; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python $REQUIRED_PYTHON_MAJOR.$REQUIRED_PYTHON_MINOR+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found"
    print_info "Please install Python 3.8 or higher first"
    exit 1
fi
echo ""

# Check FFmpeg
print_info "Checking FFmpeg installation..."
if check_command ffmpeg; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    print_success "FFmpeg $FFMPEG_VERSION found"
    FFMPEG_INSTALLED=true
else
    print_warning "FFmpeg not found (required for video playback)"
    FFMPEG_INSTALLED=false
fi
echo ""

# Offer to install FFmpeg if not found
if [ "$FFMPEG_INSTALLED" = false ]; then
    echo -e "${YELLOW}FFmpeg is required for video playback.${NC}"
    read -p "Would you like to install FFmpeg now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OS" == "Linux" ]]; then
            print_info "Installing FFmpeg via apt..."
            sudo apt-get update && sudo apt-get install -y ffmpeg
        elif [[ "$OS" == "Darwin" ]]; then
            print_info "Installing FFmpeg via Homebrew..."
            brew install ffmpeg
        fi

        if check_command ffmpeg; then
            print_success "FFmpeg installed successfully"
        else
            print_error "FFmpeg installation failed"
            exit 1
        fi
    else
        print_warning "Skipping FFmpeg installation. Video playback may not work."
    fi
    echo ""
fi

# Check for virtual environment
print_info "Checking for existing virtual environment..."
if [ -d "venv" ] || [ -d ".venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Would you like to recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing virtual environment..."
        rm -rf venv .venv
        CREATE_VENV=true
    else
        CREATE_VENV=false
    fi
else
    CREATE_VENV=true
fi
echo ""

# Create virtual environment
if [ "$CREATE_VENV" = true ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        print_success "Virtual environment created"
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
    echo ""
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
if [ $? -eq 0 ]; then
    print_success "Virtual environment activated"
else
    print_error "Failed to activate virtual environment"
    exit 1
fi
echo ""

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "pip upgraded"
else
    print_warning "Failed to upgrade pip (continuing anyway)"
fi
echo ""

# Install Python dependencies
print_info "Installing Python dependencies from requirements.txt..."
print_info "This may take a few minutes..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi
echo ""

# Create necessary directories
print_info "Creating application directories..."
mkdir -p user_data user_ratings backup/user_data backup/user_ratings output
print_success "Directories created"
echo ""

# Check configuration files
print_info "Checking configuration files..."
CONFIG_COMPLETE=true

if [ ! -f "config.yaml" ]; then
    print_warning "config.yaml not found"
    CONFIG_COMPLETE=false
fi

if [ ! -f "questionnaire_fields.yaml" ]; then
    print_warning "questionnaire_fields.yaml not found"
    CONFIG_COMPLETE=false
fi

if [ ! -f "rating_scales.yaml" ]; then
    print_warning "rating_scales.yaml not found"
    CONFIG_COMPLETE=false
fi

if [ "$CONFIG_COMPLETE" = true ]; then
    print_success "All configuration files present"
else
    print_warning "Some configuration files are missing"
    print_info "The app may not work until you configure these files"
fi
echo ""

# Test syntax
print_info "Testing Python syntax..."
python3 -m py_compile CreativityRatingApp.py
if [ $? -eq 0 ]; then
    print_success "Python syntax check passed"
else
    print_error "Python syntax errors found"
    exit 1
fi
echo ""

# Summary
print_header "Setup Complete!"
echo ""
print_success "Virtual environment created and activated"
print_success "All dependencies installed"
print_success "Application directories created"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Configure your paths in config.yaml"
echo "2. Customize questionnaire_fields.yaml and rating_scales.yaml if needed"
echo "3. Run the app with: ${GREEN}python3 CreativityRatingApp.py${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} To activate the virtual environment in the future, run:"
echo -e "  ${GREEN}source venv/bin/activate${NC}"
echo ""
