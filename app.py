from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import logging
import time
import random
import requests
import json
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure Flask logger to use stdout
logging.basicConfig(level=logging.INFO)

# Global counter for demonstration
request_counter = 0

@app.route("/")
def index():
    """Main dashboard with APM demonstration features"""
    app.logger.info("Dashboard accessed")
    return render_template('index.html')

@app.route("/health")
def health():
    """Health check endpoint"""
    app.logger.info("Health check called")
    return jsonify(status="ok", timestamp=datetime.now().isoformat())

@app.route("/api/fast")
def fast_endpoint():
    """Fast response endpoint for APM baseline"""
    global request_counter
    request_counter += 1
    app.logger.info(f"Fast endpoint called - Request #{request_counter}")
    
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
    app.logger.info(f"Slow endpoint called - Request #{request_counter}")
    
    # Simulate slow processing
    delay = random.uniform(1.0, 3.0)
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
    app.logger.info(f"Memory intensive endpoint called - Request #{request_counter}")
    
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
    
    # Clear the large data
    large_data.clear()
    
    return jsonify({
        "message": "Memory intensive operation completed",
        "processed_items": processed_count,
        "request_id": request_counter,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/cpu-intensive")
def cpu_intensive():
    """CPU-intensive operation for performance monitoring"""
    global request_counter
    request_counter += 1
    app.logger.info(f"CPU intensive endpoint called - Request #{request_counter}")
    
    # Simulate CPU-intensive calculation
    start_time = time.time()
    result = 0
    for i in range(1000000):
        result += i ** 2
    
    processing_time = time.time() - start_time
    
    return jsonify({
        "message": "CPU intensive operation completed",
        "calculation_result": result,
        "processing_time": f"{processing_time:.4f}s",
        "request_id": request_counter,
        "timestamp": datetime.now().isoformat()
    })

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
    app.logger.info(f"External API call endpoint called - Request #{request_counter}")
    
    try:
        # Make a call to a public API
        response = requests.get('https://httpbin.org/json', timeout=10)
        external_data = response.json()
        
        return jsonify({
            "message": "External API call successful",
            "external_response": external_data,
            "request_id": request_counter,
            "timestamp": datetime.now().isoformat()
        })
    except requests.exceptions.RequestException as e:
        app.logger.error(f"External API call failed: {str(e)}")
        return jsonify({
            "error": "External API call failed",
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
    return jsonify({
        "total_requests": request_counter,
        "uptime": "Running",
        "timestamp": datetime.now().isoformat(),
        "available_endpoints": [
            "/api/fast", "/api/slow", "/api/memory-intensive",
            "/api/cpu-intensive", "/api/error-random", "/api/external-call",
            "/api/database-simulation", "/api/chain-calls"
        ]
    })

@app.route("/load-test")
def load_test():
    """Simple load testing interface"""
    return render_template('load_test.html')

# Error handlers for APM monitoring
@app.errorhandler(404)
def not_found(error):
    app.logger.error(f"404 error: {request.url}")
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)