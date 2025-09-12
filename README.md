# Flask APM Demo Application

A comprehensive Flask web application designed to demonstrate Application Performance Monitoring (APM) capabilities. Features a modern web UI and various endpoints that simulate real-world scenarios for testing performance monitoring, error tracking, and distributed tracing.

## 🚀 Features

### Web Interface
- **Interactive Dashboard**: Modern Bootstrap-based UI for testing all endpoints
- **Load Testing Interface**: Built-in load testing with real-time metrics and charts
- **Response Monitoring**: Real-time display of API responses and performance metrics

### APM Demonstration Endpoints

| Endpoint | Purpose | APM Focus |
|----------|---------|-----------|
| `GET /api/fast` | Quick response (~10ms) | Baseline performance |
| `GET /api/slow` | Slow response (1-3s) | Latency monitoring |
| `GET /api/memory-intensive` | High memory usage | Resource monitoring |
| `GET /api/cpu-intensive` | CPU-heavy calculations | Performance monitoring |
| `GET /api/error-random` | Random HTTP errors | Error tracking |
| `GET /api/external-call` | External API calls | Distributed tracing |
| `GET /api/database-simulation` | DB operation simulation | Database monitoring |
| `GET /api/chain-calls` | Service call chaining | Service dependencies |
| `GET /api/stats` | Application statistics | Metrics endpoint |
| `GET /health` | Health check | Service health |

## 📋 Prerequisites

- Python 3.8+ (tested with Python 3.11)
- Git
- Amazon Linux 2023 server (for production deployment)
- Datadog account (for APM monitoring)

## 🏠 Local Development

### 1. Clone and Setup
```bash
git clone <your-repository-url>
cd flask-app
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip3 install -r requirements.txt
```

### 3. Run Locally
```bash
# Development mode (with auto-reload)
python3 app.py

# Production mode with Gunicorn
gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

### 4. Test the Application
Open your browser and navigate to:
- Dashboard: http://localhost:8000
- Load Testing: http://localhost:8000/load-test
- Health Check: http://localhost:8000/health
- API Stats: http://localhost:8000/api/stats

## 🐳 Docker Development

### Using Docker Compose (with Datadog Agent)
```bash
# Build and run with Datadog APM
docker-compose up --build

# Access the application
open http://localhost:8000
```

### Using Docker Only
```bash
# Build the image
docker build -t flask-apm-demo .

# Run the container
docker run -p 8000:8000 -e DD_API_KEY=your-api-key flask-apm-demo
```

## 🌐 Production Deployment on Amazon Linux 2023

### Quick Deployment (Automated)

1. **Clone the repository on your server:**
   ```bash
   git clone <your-repository-url>
   cd flask-app
   ```

2. **Install system dependencies:**
   ```bash
   sudo ./install-dependencies.sh
   ```

3. **Deploy the application:**
   ```bash
   sudo ./deploy.sh
   ```

The automated deployment will:
- ✅ Create a dedicated user for the application
- ✅ Install all dependencies
- ✅ Set up systemd service
- ✅ Configure Nginx reverse proxy
- ✅ Set up log rotation
- ✅ Configure firewall rules
- ✅ Create health check scripts

### Manual Deployment Steps

<details>
<summary>Click to expand manual deployment instructions</summary>

#### 1. System Preparation
```bash
# Update system
sudo dnf update -y

# Install required packages
sudo dnf install -y python3 python3-pip git nginx firewalld systemd

# Create application user
sudo useradd --system --shell /bin/false --home-dir /opt/flask-apm-demo --create-home flask-app
```

#### 2. Application Setup
```bash
# Clone repository
sudo git clone <your-repo-url> /opt/flask-apm-demo
sudo chown -R flask-app:flask-app /opt/flask-apm-demo

# Install Python dependencies
cd /opt/flask-apm-demo
sudo pip3 install -r requirements.txt
```

#### 3. Configure Systemd Service
```bash
sudo nano /etc/systemd/system/flask-apm-demo.service
```

Add the service configuration (see `deploy.sh` for the complete configuration).

#### 4. Configure Nginx
```bash
sudo nano /etc/nginx/conf.d/flask-apm-demo.conf
```

Add the Nginx configuration (see `deploy.sh` for the complete configuration).

#### 5. Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable flask-apm-demo nginx firewalld
sudo systemctl start flask-apm-demo nginx firewalld

# Configure firewall
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

</details>

### Post-Deployment Verification

```bash
# Check service status
sudo systemctl status flask-apm-demo

# Check application health
curl http://localhost/health

# View logs
sudo journalctl -u flask-apm-demo -f

# Run health check script
sudo /usr/local/bin/flask-apm-demo-health
```

## 📊 Datadog APM Configuration

### 1. Environment Variables
Copy `.env.example` to `.env` and update:

```bash
DD_API_KEY=your-datadog-api-key
DD_SERVICE=flask-apm-demo
DD_ENV=production
DD_VERSION=1.0.0
DD_SITE=datadoghq.com  # or your specific site (e.g., datadoghq.eu)
```

### 2. Agent Installation
```bash
# Install Datadog Agent on Amazon Linux 2023
DD_API_KEY=your-api-key DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"

# Enable APM
sudo systemctl enable datadog-agent
sudo systemctl start datadog-agent
```

### 3. APM Dashboard Setup
1. Login to Datadog
2. Navigate to APM → Services
3. Find your `flask-apm-demo` service
4. Explore traces, errors, and performance metrics

## 🧪 Testing APM Features

### Using the Web Interface
1. **Dashboard Testing**: Visit `/` and click on endpoint cards
2. **Load Testing**: Visit `/load-test` for controlled load generation
3. **Error Simulation**: Use the "Random Errors" endpoint
4. **Performance Testing**: Try CPU and Memory intensive endpoints

### Using curl Commands
```bash
# Fast endpoint
curl http://your-server/api/fast

# Slow endpoint
curl http://your-server/api/slow

# Generate errors
for i in {1..10}; do curl http://your-server/api/error-random; done

# Memory intensive
curl http://your-server/api/memory-intensive

# External API call (distributed tracing)
curl http://your-server/api/external-call
```

### Load Testing Script
```bash
# Simple load test with Apache Bench
ab -n 100 -c 10 http://your-server/api/fast

# Or use the built-in load testing interface at /load-test
```

## 📁 Project Structure

```
flask-app/
├── app.py                     # Main Flask application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose with Datadog
├── deploy.sh                  # Automated deployment script
├── install-dependencies.sh    # System dependencies installer
├── .env.example              # Environment variables template
├── README.md                 # This file
├── templates/
│   ├── base.html             # Base template
│   ├── index.html            # Dashboard
│   └── load_test.html        # Load testing interface
└── compose.yml               # Original Datadog compose file
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key-change-in-production` |
| `PORT` | Application port | `8000` |
| `DD_API_KEY` | Datadog API key | Required for APM |
| `DD_SERVICE` | Service name in Datadog | `flask-apm-demo` |
| `DD_ENV` | Environment tag | `production` |

### Service Management
```bash
# Start/stop/restart service
sudo systemctl start flask-apm-demo
sudo systemctl stop flask-apm-demo
sudo systemctl restart flask-apm-demo

# View logs
sudo journalctl -u flask-apm-demo -f

# Check service status
sudo systemctl status flask-apm-demo
```

## 📈 Monitoring & Observability

### Key Metrics to Monitor
- **Response Time**: Average, P95, P99 latencies
- **Error Rate**: HTTP 4xx/5xx responses
- **Throughput**: Requests per second
- **Resource Usage**: CPU, memory consumption
- **External Dependencies**: External API call performance

### Datadog Dashboards
Create custom dashboards monitoring:
- Service overview and health
- Error rates and types
- Response time distribution
- Resource utilization
- Custom business metrics

### Alerts Configuration
Set up alerts for:
- High error rates (>5%)
- Slow response times (>1s average)
- Service downtime
- High CPU/memory usage (>80%)

## 🐛 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u flask-apm-demo -f
   sudo systemctl status flask-apm-demo
   ```

2. **Permission errors**
   ```bash
   sudo chown -R flask-app:flask-app /opt/flask-apm-demo
   sudo chmod -R 755 /opt/flask-apm-demo
   ```

3. **Port conflicts**
   ```bash
   sudo netstat -tlnp | grep 8000
   sudo lsof -i :8000
   ```

4. **Nginx configuration**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. **Datadog APM not working**
   - Verify `DD_API_KEY` is set correctly
   - Check Datadog Agent status: `sudo systemctl status datadog-agent`
   - Verify network connectivity to Datadog

### Log Locations
- Application logs: `/var/log/flask-apm-demo/`
- Nginx logs: `/var/log/nginx/`
- System logs: `sudo journalctl -u flask-apm-demo`

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Service health script
sudo /usr/local/bin/flask-apm-demo-health

# Check all endpoints
curl http://localhost:8000/api/stats
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review application logs
3. Check Datadog APM traces for detailed error information
4. Create an issue in the repository

---

**Happy Monitoring!** 📊✨
