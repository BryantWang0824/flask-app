from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, has_request_context
import logging
import logging.handlers
import time
import random
import requests
import json
from datetime import datetime
import os
import uuid
from pathlib import Path

# Import python-json-logger
from pythonjsonlogger import jsonlogger

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Setup logging directory and file
log_dir = Path('/var/log/flask-app')
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'app.log'

# Configure JSON file logging with python-json-logger
# This formatter automatically works with Datadog's log injection
json_formatter = jsonlogger.JsonFormatter(
    fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
    datefmt='%Y-%m-%dT%H:%M:%S'
)

file_handler = logging.handlers.RotatingFileHandler(
    log_file, 
    maxBytes=50*1024*1024,  # 50MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(json_formatter)

# Configure console logging (non-JSON for readability during development)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(console_formatter)

# Setup Flask app logger
app.logger.setLevel(logging.INFO)
app.logger.handlers.clear()
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)

# Setup root logger
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(file_handler)

# Configure Datadog log injection (must be done before any logging)
try:
    from ddtrace.contrib.logging import patch as patch_logging
    
    # This enables automatic trace correlation in logs
    # dd.trace_id and dd.span_id will be automatically added
    patch_logging()
    
    app.logger.info("Datadog log correlation enabled", extra={
        'dd_logging': 'enabled', 
        'trace_injection': True,
        'formatter': 'python-json-logger'
    })
except ImportError:
    app.logger.warning("ddtrace not available - trace correlation disabled", extra={
        'dd_logging': 'disabled', 
        'trace_injection': False
    })

@app.before_request
def before_request():
    """Add request ID and log request start"""
    request.request_id = str(uuid.uuid4())
    app.logger.info("Request started", extra={
        'request_id': request.request_id,
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr
    })

# Global counter for demonstration
request_counter = 0

# Global error rate (percentage) - can be modified via API
global_error_rate = 3.0  # Default 3% error rate

def trigger_random_errors():
    """Randomly trigger various types of errors for APM demonstration"""
    global global_error_rate
    error_chance = random.random() * 100  # Convert to percentage
    
    # Use configurable error rate instead of hardcoded values
    error_threshold = global_error_rate
    
    if error_chance < error_threshold / 3:  # 1/3 of error rate for ValueError
        app.logger.error("Simulated ValueError occurred", extra={
            'error_type': 'ValueError', 
            'error_category': 'application_error',
            'error_rate_setting': global_error_rate
        })
        raise ValueError("Simulated application error for APM testing")
    elif error_chance < (error_threshold * 2) / 3:  # 2/3 of error rate for KeyError
        app.logger.error("Simulated KeyError occurred", extra={
            'error_type': 'KeyError', 
            'error_category': 'application_error',
            'error_rate_setting': global_error_rate
        })
        raise KeyError("missing_key_simulation")
    elif error_chance < error_threshold:  # Full error rate for TypeError
        app.logger.error("Simulated TypeError occurred", extra={
            'error_type': 'TypeError', 
            'error_category': 'application_error',
            'error_rate_setting': global_error_rate
        })
        raise TypeError("Simulated type error for APM monitoring")

@app.route("/")
def index():
    """Main dashboard with APM demonstration features"""
    app.logger.info("Dashboard accessed", extra={
        'endpoint': 'dashboard', 
        'action': 'view'
    })
    
    # Random chance of error
    trigger_random_errors()
    
    return render_template('index.html')

@app.route("/health")
def health():
    """Health check endpoint"""
    app.logger.info("Health check called", extra={
        'custom_fields': {'endpoint': 'health', 'action': 'check'}
    })
    
    # Occasionally simulate unhealthy state (1% chance)
    if random.random() < 0.01:
        app.logger.warning("Health check failed - simulated unhealthy state", extra={
            'custom_fields': {'health_status': 'unhealthy', 'reason': 'simulated_failure'}
        })
        return jsonify(status="unhealthy", timestamp=datetime.now().isoformat(), 
                      reason="Simulated service degradation"), 503
    
    return jsonify(status="ok", timestamp=datetime.now().isoformat())

@app.route("/api/fast")
def fast_endpoint():
    """Fast response endpoint for APM baseline"""
    global request_counter
    request_counter += 1
    app.logger.info("Fast endpoint called", extra={
        'custom_fields': {
            'endpoint': 'fast',
            'request_number': request_counter,
            'expected_response_time': '10ms'
        }
    })
    
    # Random chance of error
    trigger_random_errors()
    
    # Simulate occasional network hiccup (2% chance)
    if random.random() < 0.02:
        app.logger.warning("Fast endpoint experiencing simulated slowdown", extra={
            'custom_fields': {'performance_issue': 'network_hiccup', 'request_id': request_counter}
        })
        time.sleep(random.uniform(0.5, 1.5))  # Unexpected delay
    
    return jsonify({
        "message": "Fast response!",
        "response_time": "~10ms",
        "request_id": request_counter,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/slow")
def slow_endpoint():
    """Intentionally slow endpoint to demonstrate latency monitoring"""
    global request_counter
    request_counter += 1
    delay = random.uniform(1.0, 3.0)
    
    app.logger.info("Slow endpoint called", extra={
        'custom_fields': {
            'endpoint': 'slow',
            'request_number': request_counter,
            'expected_delay': f"{delay:.2f}s"
        }
    })
    
    # Random chance of timeout error (2% chance)
    if random.random() < 0.02:
        app.logger.error("Slow endpoint timeout simulation", extra={
            'custom_fields': {
                'error_type': 'TimeoutError',
                'request_id': request_counter,
                'attempted_delay': f"{delay:.2f}s"
            }
        })
        time.sleep(delay * 2)  # Make it even slower
        return jsonify({"error": "Request timed out during processing"}), 504
    
    # Random chance of processing error (1% chance)  
    if random.random() < 0.01:
        app.logger.error("Slow endpoint processing error", extra={
            'custom_fields': {'error_type': 'ProcessingError', 'request_id': request_counter}
        })
        raise Exception("Simulated processing error during slow operation")
    
    # Simulate slow processing
    time.sleep(delay)
    
    return jsonify({
        "message": "Slow response completed",
        "actual_delay": f"{delay:.2f}s",
        "request_id": request_counter,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/memory-intensive")
def memory_intensive():
    """Memory-intensive operation for resource monitoring"""
    global request_counter
    request_counter += 1
    
    app.logger.info("Memory intensive endpoint called", extra={
        'custom_fields': {
            'endpoint': 'memory_intensive',
            'request_number': request_counter,
            'expected_memory_usage': '~100MB'
        }
    })
    
    # Random chance of memory error (2% chance)
    if random.random() < 0.02:
        app.logger.error("Memory allocation failed simulation", extra={
            'custom_fields': {
                'error_type': 'MemoryError',
                'request_id': request_counter,
                'resource': 'memory'
            }
        })
        raise MemoryError("Simulated out of memory error for APM testing")
    
    # Random chance of allocation failure (1% chance)
    if random.random() < 0.01:
        app.logger.critical("Critical memory shortage simulation", extra={
            'custom_fields': {
                'error_type': 'OutOfMemoryError',
                'severity': 'critical',
                'request_id': request_counter
            }
        })
        return jsonify({"error": "Out of memory - unable to allocate resources"}), 507
    
    try:
        # Create large list to consume memory
        large_data = []
        for i in range(100000):
            large_data.append({
                "id": i,
                "data": f"Sample data item {i}" * 10,
                "timestamp": datetime.now().isoformat()
            })
        
        # Process the data (CPU + memory intensive)
        processed_count = len([item for item in large_data if item["id"] % 2 == 0])
        
        app.logger.info("Memory operation completed successfully", extra={
            'custom_fields': {
                'processed_items': processed_count,
                'memory_freed': True,
                'request_id': request_counter
            }
        })
        
        # Clear the large data
        large_data.clear()
        
        return jsonify({
            "message": "Memory intensive operation completed",
            "processed_items": processed_count,
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error("Unexpected error in memory intensive operation", extra={
            'custom_fields': {
                'error_message': str(e),
                'request_id': request_counter
            }
        })
        raise

@app.route("/api/cpu-intensive")
def cpu_intensive():
    """CPU-intensive operation for performance monitoring"""
    global request_counter
    request_counter += 1
    
    app.logger.info("CPU intensive endpoint called", extra={
        'custom_fields': {
            'endpoint': 'cpu_intensive',
            'request_number': request_counter,
            'operation_type': 'mathematical_calculation'
        }
    })
    
    # Random chance of computation error (1.5% chance)
    if random.random() < 0.015:
        app.logger.error("CPU computation overflow simulation", extra={
            'custom_fields': {
                'error_type': 'OverflowError',
                'computation_type': 'mathematical',
                'request_id': request_counter
            }
        })
        raise OverflowError("Simulated arithmetic overflow during CPU intensive operation")
    
    # Simulate CPU-intensive calculation
    start_time = time.time()
    result = 0
    iterations = random.randint(500000, 1500000)  # Variable workload
    
    try:
        for i in range(iterations):
            result += i ** 2
            
            # Random chance of computation getting stuck (0.5% chance)
            if random.random() < 0.005 and i > 100000:
                app.logger.warning("CPU computation slowdown detected", extra={
                    'custom_fields': {
                        'performance_issue': 'computation_slowdown',
                        'iterations_completed': i,
                        'request_id': request_counter
                    }
                })
                time.sleep(random.uniform(2, 4))  # Simulate system lag
        
        processing_time = time.time() - start_time
        
        app.logger.info("CPU operation completed successfully", extra={
            'custom_fields': {
                'processing_time': f"{processing_time:.4f}s",
                'iterations': iterations,
                'result_magnitude': len(str(result)),
                'request_id': request_counter
            }
        })
        
        return jsonify({
            "message": "CPU intensive operation completed",
            "calculation_result": result,
            "processing_time": f"{processing_time:.4f}s",
            "iterations": iterations,
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error("Unexpected error in CPU intensive operation", extra={
            'custom_fields': {
                'error_message': str(e),
                'iterations_completed': locals().get('i', 0),
                'request_id': request_counter
            }
        })
        raise

@app.route("/api/error-random")
def random_error():
    """Randomly generates different types of errors for error monitoring"""
    global request_counter
    request_counter += 1
    app.logger.info(f"Random error endpoint called - Request #{request_counter}")
    
    error_type = random.choice(['success', '400', '404', '500', 'timeout'])
    
    if error_type == 'success':
        return jsonify({
            "message": "Lucky! No error this time",
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        })
    elif error_type == '400':
        app.logger.error("Simulated 400 error")
        return jsonify({"error": "Bad Request - Simulated client error"}), 400
    elif error_type == '404':
        app.logger.error("Simulated 404 error")
        return jsonify({"error": "Not Found - Simulated not found error"}), 404
    elif error_type == '500':
        app.logger.error("Simulated 500 error")
        return jsonify({"error": "Internal Server Error - Simulated server error"}), 500
    elif error_type == 'timeout':
        app.logger.error("Simulated timeout")
        time.sleep(5)  # Simulate timeout
        return jsonify({"error": "Request timed out"}), 504

@app.route("/api/external-call")
def external_api_call():
    """Makes external API calls for distributed tracing"""
    global request_counter
    request_counter += 1
    
    api_endpoints = [
        'https://httpbin.org/json',
        'https://httpbin.org/uuid',
        'https://jsonplaceholder.typicode.com/posts/1',
        'https://api.github.com/zen'
    ]
    
    chosen_endpoint = random.choice(api_endpoints)
    
    app.logger.info("External API call started", extra={
        'custom_fields': {
            'endpoint': 'external_call',
            'request_number': request_counter,
            'target_api': chosen_endpoint,
            'call_type': 'http_get'
        }
    })
    
    # Random chance of network error before call (2% chance)
    if random.random() < 0.02:
        app.logger.error("Simulated network connectivity issue", extra={
            'custom_fields': {
                'error_type': 'ConnectionError',
                'target_api': chosen_endpoint,
                'request_id': request_counter
            }
        })
        return jsonify({
            "error": "Network connectivity issue - unable to reach external service",
            "target_api": chosen_endpoint,
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        }), 503
    
    try:
        # Random timeout value to simulate network variability
        timeout = random.choice([5, 10, 15])
        
        app.logger.debug("Making external HTTP request", extra={
            'custom_fields': {
                'target_url': chosen_endpoint,
                'timeout': timeout,
                'request_id': request_counter
            }
        })
        
        response = requests.get(chosen_endpoint, timeout=timeout)
        
        # Random chance of simulating a bad response (1% chance)
        if random.random() < 0.01:
            app.logger.warning("External API returned unexpected response", extra={
                'custom_fields': {
                    'status_code': response.status_code,
                    'response_size': len(response.content),
                    'api_issue': 'unexpected_format',
                    'request_id': request_counter
                }
            })
            return jsonify({
                "error": "External API returned malformed response",
                "status_code": response.status_code,
                "request_id": request_counter,
                "timestamp": datetime.now().isoformat()
            }), 502
        
        # Handle different response types
        try:
            if 'json' in response.headers.get('content-type', '').lower():
                external_data = response.json()
            else:
                external_data = response.text
        except ValueError:
            external_data = response.text
        
        app.logger.info("External API call completed successfully", extra={
            'custom_fields': {
                'target_api': chosen_endpoint,
                'response_status': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'response_size': len(response.content),
                'request_id': request_counter
            }
        })
        
        return jsonify({
            "message": "External API call successful",
            "target_api": chosen_endpoint,
            "response_status": response.status_code,
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            "external_response": external_data,
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        })
        
    except requests.exceptions.Timeout:
        app.logger.error("External API call timed out", extra={
            'custom_fields': {
                'error_type': 'TimeoutError',
                'target_api': chosen_endpoint,
                'timeout_duration': timeout,
                'request_id': request_counter
            }
        })
        return jsonify({
            "error": "External API call timed out",
            "target_api": chosen_endpoint,
            "timeout": f"{timeout}s",
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        }), 504
        
    except requests.exceptions.ConnectionError as e:
        app.logger.error("External API connection failed", extra={
            'custom_fields': {
                'error_type': 'ConnectionError',
                'target_api': chosen_endpoint,
                'error_message': str(e),
                'request_id': request_counter
            }
        })
        return jsonify({
            "error": "Failed to connect to external API",
            "target_api": chosen_endpoint,
            "details": str(e),
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        }), 503
        
    except requests.exceptions.RequestException as e:
        app.logger.error("External API call failed", extra={
            'custom_fields': {
                'error_type': type(e).__name__,
                'target_api': chosen_endpoint,
                'error_message': str(e),
                'request_id': request_counter
            }
        })
        return jsonify({
            "error": "External API call failed",
            "target_api": chosen_endpoint,
            "details": str(e),
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/database-simulation")
def database_simulation():
    """Simulates database operations for APM monitoring"""
    global request_counter
    request_counter += 1
    app.logger.info(f"Database simulation endpoint called - Request #{request_counter}")
    
    operations = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
    operation = random.choice(operations)
    
    # Simulate database query time
    query_time = random.uniform(0.1, 1.5)
    time.sleep(query_time)
    
    # Simulate random database errors (10% chance)
    if random.random() < 0.1:
        app.logger.error("Simulated database error")
        return jsonify({
            "error": "Database connection failed",
            "operation": operation,
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        }), 500
    
    return jsonify({
        "message": f"Database {operation} operation completed",
        "operation": operation,
        "query_time": f"{query_time:.3f}s",
        "rows_affected": random.randint(1, 100),
        "request_id": request_counter,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/chain-calls")
def chain_calls():
    """Demonstrates service call chaining for distributed tracing"""
    global request_counter
    request_counter += 1
    app.logger.info(f"Chain calls endpoint called - Request #{request_counter}")
    
    results = []
    
    # Simulate calling multiple internal services
    services = ['user-service', 'order-service', 'payment-service', 'notification-service']
    
    for service in services:
        start_time = time.time()
        
        # Simulate service call
        call_time = random.uniform(0.1, 0.5)
        time.sleep(call_time)
        
        # Simulate occasional service failures (5% chance)
        if random.random() < 0.05:
            app.logger.error(f"Simulated {service} failure")
            results.append({
                "service": service,
                "status": "error",
                "error": "Service temporarily unavailable",
                "call_time": f"{call_time:.3f}s"
            })
        else:
            results.append({
                "service": service,
                "status": "success",
                "data": f"Response from {service}",
                "call_time": f"{call_time:.3f}s"
            })
    
    total_time = sum(float(r["call_time"].replace('s', '')) for r in results)
    
    return jsonify({
        "message": "Service chain completed",
        "services_called": len(services),
        "results": results,
        "total_time": f"{total_time:.3f}s",
        "request_id": request_counter,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/stats")
def api_stats():
    """Returns basic API statistics"""
    app.logger.info("API stats requested", extra={
        'custom_fields': {
            'endpoint': 'stats',
            'total_requests': request_counter
        }
    })
    
    return jsonify({
        "total_requests": request_counter,
        "uptime": "Running",
        "timestamp": datetime.now().isoformat(),
        "logging": {
            "format": "JSON",
            "location": "/var/log/flask-app/app.log",
            "rotation": "50MB max, 5 backups"
        },
        "available_endpoints": [
            "/api/fast", "/api/slow", "/api/memory-intensive",
            "/api/cpu-intensive", "/api/error-random", "/api/external-call",
            "/api/database-simulation", "/api/chain-calls", "/api/crash-test",
            "/api/security-error", "/api/security-input"
        ],
        "error_control_endpoints": [
            "/api/set-error-rate", "/api/get-error-rate"
        ],
        "current_error_rate": f"{global_error_rate}%"
    })

@app.route("/load-test")
def load_test():
    """Simple load testing interface"""
    return render_template('load_test.html')

@app.route("/security-test")
def security_test():
    """Security input testing interface"""
    app.logger.info("Security test page accessed", extra={
        'endpoint': 'security_test',
        'action': 'page_view',
        'user_agent': request.headers.get('User-Agent', ''),
        'remote_addr': request.remote_addr
    })
    return render_template('security_test.html')

@app.route("/api/security-input", methods=['POST'])
def security_input():
    """Handle security test input and log for Datadog analysis"""
    global request_counter
    request_counter += 1
    
    # Get form data
    user_input = request.form.get('user_input', '') if request.form else request.json.get('user_input', '')
    input_type = request.form.get('input_type', 'general') if request.form else request.json.get('input_type', 'general')
    
    # Log the input for Datadog security monitoring
    app.logger.info("Security test input received", extra={
        'endpoint': 'security_input',
        'request_id': request_counter,
        'user_input': user_input[:500],  # Log first 500 chars
        'input_type': input_type,
        'input_length': len(user_input),
        'security_test': True,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'referer': request.headers.get('Referer', ''),
        'content_type': request.content_type
    })
    
    # Additional logging for different input types
    if input_type == 'sql':
        app.logger.info("SQL input test", extra={
            'test_category': 'sql_injection',
            'user_input': user_input[:200],
            'request_id': request_counter
        })
    elif input_type == 'xss':
        app.logger.info("XSS input test", extra={
            'test_category': 'cross_site_scripting',
            'user_input': user_input[:200],
            'request_id': request_counter
        })
    elif input_type == 'command':
        app.logger.info("Command injection input test", extra={
            'test_category': 'command_injection',
            'user_input': user_input[:200],
            'request_id': request_counter
        })
    elif input_type == 'path':
        app.logger.info("Path traversal input test", extra={
            'test_category': 'path_traversal',
            'user_input': user_input[:200],
            'request_id': request_counter
        })
    
    return jsonify({
        'status': 'success',
        'message': 'Input received and logged for security analysis',
        'input_type': input_type,
        'input_length': len(user_input),
        'request_id': request_counter,
        'timestamp': datetime.now().isoformat()
    })

@app.route("/api/set-error-rate", methods=['POST'])
def set_error_rate():
    """Set the global error rate for backend error simulation"""
    global global_error_rate, request_counter
    request_counter += 1
    
    try:
        data = request.get_json()
        new_error_rate = float(data.get('error_rate', 3.0))
        
        # Validate error rate is between 0 and 100
        if 0 <= new_error_rate <= 100:
            old_error_rate = global_error_rate
            global_error_rate = new_error_rate
            
            app.logger.info("Global error rate updated", extra={
                'endpoint': 'set_error_rate',
                'old_error_rate': old_error_rate,
                'new_error_rate': global_error_rate,
                'request_id': request_counter,
                'updated_by': request.remote_addr
            })
            
            return jsonify({
                'status': 'success',
                'message': f'Error rate updated from {old_error_rate}% to {global_error_rate}%',
                'old_error_rate': old_error_rate,
                'new_error_rate': global_error_rate,
                'request_id': request_counter,
                'timestamp': datetime.now().isoformat()
            })
        else:
            app.logger.warning("Invalid error rate provided", extra={
                'endpoint': 'set_error_rate',
                'invalid_error_rate': new_error_rate,
                'request_id': request_counter
            })
            return jsonify({
                'status': 'error',
                'message': 'Error rate must be between 0 and 100',
                'provided_value': new_error_rate
            }), 400
            
    except (TypeError, ValueError) as e:
        app.logger.error("Error setting error rate", extra={
            'endpoint': 'set_error_rate',
            'error': str(e),
            'request_id': request_counter
        })
        return jsonify({
            'status': 'error',
            'message': 'Invalid error rate format',
            'error': str(e)
        }), 400

@app.route("/api/get-error-rate", methods=['GET'])
def get_error_rate():
    """Get the current global error rate"""
    global global_error_rate, request_counter
    request_counter += 1
    
    app.logger.info("Error rate requested", extra={
        'endpoint': 'get_error_rate',
        'current_error_rate': global_error_rate,
        'request_id': request_counter
    })
    
    return jsonify({
        'status': 'success',
        'current_error_rate': global_error_rate,
        'request_id': request_counter,
        'timestamp': datetime.now().isoformat()
    })

@app.route("/api/crash-test")
def crash_test():
    """Endpoint that intentionally crashes for error testing"""
    global request_counter
    request_counter += 1
    
    crash_types = ['division_by_zero', 'null_reference', 'index_error', 'attribute_error', 'import_error']
    crash_type = random.choice(crash_types)
    
    app.logger.warning("Crash test endpoint called", extra={
        'custom_fields': {
            'endpoint': 'crash_test',
            'crash_type': crash_type,
            'request_id': request_counter,
            'intentional_crash': True
        }
    })
    
    if crash_type == 'division_by_zero':
        return 1 / 0
    elif crash_type == 'null_reference':
        none_obj = None
        return none_obj.some_attribute
    elif crash_type == 'index_error':
        empty_list = []
        return empty_list[10]
    elif crash_type == 'attribute_error':
        return "string".nonexistent_method()
    elif crash_type == 'import_error':
        import nonexistent_module
        return nonexistent_module.function()

@app.route("/api/security-error")
def security_error():
    """Simulates security-related errors"""
    global request_counter
    request_counter += 1
    
    error_types = ['auth_failure', 'permission_denied', 'token_expired', 'invalid_credentials']
    error_type = random.choice(error_types)
    
    app.logger.error("Security error simulated", extra={
        'custom_fields': {
            'endpoint': 'security_error',
            'security_error_type': error_type,
            'request_id': request_counter,
            'security_event': True,
            'user_agent': request.headers.get('User-Agent', ''),
            'remote_addr': request.remote_addr
        }
    })
    
    if error_type == 'auth_failure':
        return jsonify({"error": "Authentication failed", "code": "AUTH_FAILED"}), 401
    elif error_type == 'permission_denied':
        return jsonify({"error": "Access denied", "code": "PERMISSION_DENIED"}), 403
    elif error_type == 'token_expired':
        return jsonify({"error": "Access token expired", "code": "TOKEN_EXPIRED"}), 401
    elif error_type == 'invalid_credentials':
        return jsonify({"error": "Invalid credentials provided", "code": "INVALID_CREDS"}), 401

@app.after_request
def after_request(response):
    """Log response details for APM monitoring"""
    app.logger.info("Request completed", extra={
        'request_id': getattr(request, 'request_id', 'unknown'),
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'content_length': response.content_length,
        'response_time_ms': 'calculated_by_apm'  # APM tools will calculate this
    })
    return response

# Enhanced Error handlers for APM monitoring
@app.errorhandler(400)
def bad_request(error):
    app.logger.error("Bad request error", extra={
        'custom_fields': {
            'error_type': '400_BadRequest',
            'request_url': request.url,
            'request_method': request.method,
            'error_message': str(error),
            'request_id': getattr(request, 'request_id', 'unknown')
        }
    })
    return jsonify({"error": "Bad request", "message": str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    app.logger.error("Not found error", extra={
        'custom_fields': {
            'error_type': '404_NotFound',
            'requested_url': request.url,
            'request_method': request.method,
            'referrer': request.referrer,
            'request_id': getattr(request, 'request_id', 'unknown')
        }
    })
    return jsonify({"error": "Endpoint not found", "requested_path": request.path}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error("Internal server error", extra={
        'custom_fields': {
            'error_type': '500_InternalServerError',
            'error_message': str(error),
            'request_url': request.url,
            'request_method': request.method,
            'request_id': getattr(request, 'request_id', 'unknown')
        }
    })
    return jsonify({"error": "Internal server error", "message": "Something went wrong"}), 500

@app.errorhandler(ValueError)
def handle_value_error(error):
    app.logger.error("ValueError occurred", extra={
        'custom_fields': {
            'error_type': 'ValueError',
            'error_message': str(error),
            'request_path': request.path,
            'request_id': getattr(request, 'request_id', 'unknown')
        }
    })
    return jsonify({"error": "Value error", "message": str(error)}), 400

@app.errorhandler(KeyError)
def handle_key_error(error):
    app.logger.error("KeyError occurred", extra={
        'custom_fields': {
            'error_type': 'KeyError',
            'missing_key': str(error),
            'request_path': request.path,
            'request_id': getattr(request, 'request_id', 'unknown')
        }
    })
    return jsonify({"error": "Missing required key", "key": str(error)}), 400

@app.errorhandler(Exception)
def handle_generic_exception(error):
    app.logger.error("Unhandled exception occurred", extra={
        'custom_fields': {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'request_path': request.path,
            'request_method': request.method,
            'request_id': getattr(request, 'request_id', 'unknown')
        }
    }, exc_info=True)
    return jsonify({"error": "An unexpected error occurred", "type": type(error).__name__}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)