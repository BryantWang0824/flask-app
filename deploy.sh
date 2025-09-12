#!/bin/bash

# Deployment script for Flask APM Demo App on Amazon Linux 2023
# This script sets up the application for production deployment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="flask-apm-demo"
APP_USER="flask-app"
APP_DIR="/opt/$APP_NAME"
LOG_DIR="/var/log/$APP_NAME"
SERVICE_NAME="$APP_NAME.service"

echo -e "${BLUE}🚀 Starting deployment of Flask APM Demo App${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Updating system packages..."
dnf update -y

print_status "Installing required packages..."
dnf install -y python3 python3-pip git nginx firewalld systemd

print_status "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/false --home-dir $APP_DIR --create-home $APP_USER
fi

print_status "Setting up application directory..."
mkdir -p $APP_DIR
mkdir -p $LOG_DIR
chown $APP_USER:$APP_USER $APP_DIR
chown $APP_USER:$APP_USER $LOG_DIR

print_status "Installing application..."
# Copy application files (assuming we're running from the app directory)
cp -r . $APP_DIR/
chown -R $APP_USER:$APP_USER $APP_DIR

print_status "Installing Python dependencies..."
cd $APP_DIR
pip3 install -r requirements.txt

print_status "Creating systemd service file..."
cat > /etc/systemd/system/$SERVICE_NAME << EOF
[Unit]
Description=Flask APM Demo Application
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR
Environment=DD_SERVICE=$APP_NAME
Environment=DD_ENV=production
Environment=DD_VERSION=1.0.0
ExecStart=/usr/bin/ddtrace-run gunicorn -w 2 -b 0.0.0.0:8000 --access-logfile $LOG_DIR/access.log --error-logfile $LOG_DIR/error.log app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=append:$LOG_DIR/app.log
StandardError=append:$LOG_DIR/error.log

[Install]
WantedBy=multi-user.target
EOF

print_status "Creating nginx configuration..."
cat > /etc/nginx/conf.d/$APP_NAME.conf << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
    
    location /static {
        alias $APP_DIR/static;
        expires 1d;
    }
}
EOF

print_status "Configuring firewall..."
systemctl enable firewalld
systemctl start firewalld
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

print_status "Starting and enabling services..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl enable nginx
systemctl start $SERVICE_NAME
systemctl start nginx

print_status "Creating log rotation..."
cat > /etc/logrotate.d/$APP_NAME << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

print_status "Setting up health check script..."
cat > /usr/local/bin/$APP_NAME-health << EOF
#!/bin/bash
curl -f http://localhost:8000/health >/dev/null 2>&1
if [ \$? -eq 0 ]; then
    echo "OK: Application is healthy"
    exit 0
else
    echo "CRITICAL: Application health check failed"
    exit 1
fi
EOF
chmod +x /usr/local/bin/$APP_NAME-health

print_status "Checking service status..."
sleep 5
systemctl status $SERVICE_NAME --no-pager
nginx -t

echo
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo
echo "Application Details:"
echo "- Service: $SERVICE_NAME"
echo "- Status: $(systemctl is-active $SERVICE_NAME)"
echo "- Logs: $LOG_DIR/"
echo "- Health Check: /usr/local/bin/$APP_NAME-health"
echo
echo "Application URLs:"
echo "- Dashboard: http://$(curl -s ifconfig.me)/ (or http://localhost/)"
echo "- Health Check: http://$(curl -s ifconfig.me)/health"
echo "- API Stats: http://$(curl -s ifconfig.me)/api/stats"
echo "- Load Testing: http://$(curl -s ifconfig.me)/load-test"
echo
echo "Useful Commands:"
echo "- Check logs: sudo journalctl -u $SERVICE_NAME -f"
echo "- Restart service: sudo systemctl restart $SERVICE_NAME"
echo "- Check status: sudo systemctl status $SERVICE_NAME"
echo "- Health check: sudo /usr/local/bin/$APP_NAME-health"
echo
print_warning "Remember to configure your APM agent (Datadog) with proper API keys!"
print_warning "Update firewall rules if needed for your specific environment."
