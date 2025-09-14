#!/usr/bin/env python3
"""
Test script to verify APM features in the Flask application
Tests JSON logging and intentional errors
"""

import requests
import time
import json
from pathlib import Path
import sys

def test_endpoints():
    """Test various endpoints to generate logs and errors"""
    base_url = "http://localhost:8000"
    endpoints = [
        "/api/fast",
        "/api/slow", 
        "/api/memory-intensive",
        "/api/cpu-intensive",
        "/api/error-random",
        "/api/external-call",
        "/api/database-simulation",
        "/api/chain-calls",
        "/api/crash-test",
        "/api/security-error",
        "/health",
        "/api/stats"
    ]
    
    print("Testing Flask APM Demo Application Endpoints...")
    print("-" * 50)
    
    results = []
    
    for endpoint in endpoints:
        print(f"Testing {endpoint}...")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            status = "✅ SUCCESS" if response.status_code < 400 else "⚠️ ERROR"
            results.append({
                "endpoint": endpoint,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "success": response.status_code < 400
            })
            print(f"  {status} - Status: {response.status_code}, Time: {response.elapsed.total_seconds():.3f}s")
        except requests.exceptions.RequestException as e:
            results.append({
                "endpoint": endpoint,
                "error": str(e),
                "success": False
            })
            print(f"  ❌ FAILED - {str(e)}")
        
        time.sleep(0.5)  # Small delay between requests
    
    return results

def check_json_logs():
    """Check if JSON logs are being generated"""
    log_file = Path("/var/log/flask-app/app.log")
    
    print("\nChecking JSON Log File...")
    print("-" * 30)
    
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"✅ Log file exists with {len(lines)} entries")
                    
                    # Check if last few lines are valid JSON
                    valid_json_count = 0
                    for line in lines[-5:]:  # Check last 5 lines
                        try:
                            json.loads(line.strip())
                            valid_json_count += 1
                        except json.JSONDecodeError:
                            pass
                    
                    if valid_json_count > 0:
                        print(f"✅ Found {valid_json_count} valid JSON log entries in last 5 lines")
                        
                        # Show sample log entry
                        for line in reversed(lines):
                            try:
                                log_entry = json.loads(line.strip())
                                print("\nSample JSON Log Entry:")
                                print(json.dumps(log_entry, indent=2))
                                break
                            except json.JSONDecodeError:
                                continue
                    else:
                        print("⚠️ No valid JSON entries found in recent logs")
                else:
                    print("⚠️ Log file is empty")
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
    else:
        print("⚠️ Log file not found. Make sure the application has write permissions to /var/log/flask-app/")
        print("   You may need to run: sudo mkdir -p /var/log/flask-app && sudo chown $USER /var/log/flask-app")

def generate_test_load():
    """Generate some load to create more logs and errors"""
    print("\nGenerating Test Load...")
    print("-" * 25)
    
    base_url = "http://localhost:8000"
    test_endpoints = [
        "/api/fast",
        "/api/error-random",  # This will generate random errors
        "/api/crash-test",    # This will generate crashes
    ]
    
    for i in range(10):
        endpoint = test_endpoints[i % len(test_endpoints)]
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            status_symbol = "✅" if response.status_code < 400 else "❌"
            print(f"  {status_symbol} Request {i+1}: {endpoint} -> {response.status_code}")
        except Exception as e:
            print(f"  ❌ Request {i+1}: {endpoint} -> Exception: {type(e).__name__}")
        
        time.sleep(0.2)

def main():
    print("🚀 Flask APM Demo Test Suite")
    print("=" * 50)
    
    # Test if application is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Application is running")
        else:
            print(f"⚠️ Application returned status {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ Application is not running on localhost:8000")
        print("   Please start the application first with: python3 app.py")
        sys.exit(1)
    
    # Run tests
    results = test_endpoints()
    generate_test_load()
    check_json_logs()
    
    # Summary
    print("\nTest Summary:")
    print("=" * 20)
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    print(f"Successful tests: {successful_tests}/{total_tests}")
    print(f"Error tests (expected): {total_tests - successful_tests}/{total_tests}")
    
    print("\n✅ APM Feature Testing Complete!")
    print("\nNext Steps:")
    print("1. Check your APM dashboard for traces and errors")
    print("2. Review JSON logs in /var/log/flask-app/app.log")
    print("3. Monitor metrics and alerts in your APM tool")

if __name__ == "__main__":
    main()
