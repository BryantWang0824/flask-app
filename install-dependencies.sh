#!/bin/bash

# Install dependencies for Flask APM Demo App on Amazon Linux 2023
# Run this script as root before deploying the application

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Installing system dependencies for Amazon Linux 2023...${NC}"

# Update system
dnf update -y

# Install Python and development tools
dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    gcc \
    git \
    curl \
    wget \
    nginx \
    firewalld \
    systemd \
    logrotate \
    htop \
    tree

# Install pip packages globally
pip3 install --upgrade pip setuptools wheel

echo -e "${GREEN}System dependencies installed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Clone your repository: git clone <your-repo-url>"
echo "2. Navigate to the app directory: cd <app-directory>"
echo "3. Run the deployment script: sudo ./deploy.sh"
