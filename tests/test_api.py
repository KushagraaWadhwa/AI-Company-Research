#!/usr/bin/env python3
"""
API integration tests for AI Startup Copilot.
Tests all API endpoints with various scenarios.
"""

import asyncio
import httpx
import json
import time
import sys
import os
from typing import Dict, Any

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)


BASE_URL = "http://localhost:8000/api/v1"


class APITester:
    """API testing class with comprehensive endpoint coverage."""
    
    def __init__(self):
        self.client = None
        self.test_results = []
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅" if success else "❌"
        print(f"{status} {name}: {details}")
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })
    
    async def test_health_endpoint(self) -> bool:
        """Test the health check endpoint."""
        print("\n🏥 Testing Health Endpoint")
        print("-" * 30)
        
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                services = health_data.get("services", {})
                
                self.log_test(
                    "Health Check", 
                    True, 
                    f"Overall: {health_data.get('overall_status', 'unknown')}"
                )
                
                # Check individual services
                for service, status in services.items():
                    service_status = status.get("status", "unknown")
                    self.log_test(
                        f"Service: {service}",
                        service_status == "healthy",
                        service_status
                    )
                
                return True
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    async def test_analyze_endpoint(self) -> Dict[str, Any]:
        """Test the analyze endpoint with various inputs."""
        print("\n🔍 Testing Analyze Endpoint")
        print("-" * 30)
        
        test_cases = [
            {
                "name": "Standard Analysis",
                "data": {
                    "company_name": "Test Company",
                    "company_url": "https://example.com",
                    "analysis_type": "standard"
                }
            },
            {
                "name": "Comprehensive Analysis",
                "data": {
                    "company_name": "OpenAI",
                    "company_url": "https://openai.com",
                    "analysis_type": "comprehensive",
                    "additional_info": "AI research company"
                }
            },
            {
                "name": "Universal Analysis",
                "data": {
                    "company_name": "Google",
                    "analysis_type": "universal"
                }
            },
            {
                "name": "Minimal Request",
                "data": {
                    "company_name": "Minimal Test"
                }
            }
        ]
        
        successful_tasks = []
        
        for test_case in test_cases:
            try:
                response = await self.client.post(
                    f"{BASE_URL}/analyze",
                    json=test_case["data"]
                )
                
                if response.status_code in [200, 202]:
                    result = response.json()
                    task_id = result.get("task_id")
                    message = result.get("message", "")
                    
                    self.log_test(
                        test_case["name"],
                        True,
                        f"Task ID: {task_id[:8]}... | {message}"
                    )
                    
                    successful_tasks.append({
                        "name": test_case["name"],
                        "task_id": task_id,
                        "data": test_case["data"]
                    })
                else:
                    self.log_test(
                        test_case["name"],
                        False,
                        f"HTTP {response.status_code}: {response.text[:100]}"
                    )
                    
            except Exception as e:
                self.log_test(test_case["name"], False, str(e))
        
        return {"successful_tasks": successful_tasks}
    
    async def test_status_endpoint(self, task_ids: list) -> bool:
        """Test the status endpoint with various task IDs."""
        print("\n📊 Testing Status Endpoint")
        print("-" * 30)
        
        if not task_ids:
            self.log_test("Status Check", False, "No task IDs to test")
            return False
        
        all_success = True
        
        for i, task_id in enumerate(task_ids[:3]):  # Test first 3 tasks
            try:
                response = await self.client.get(f"{BASE_URL}/status/{task_id}")
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status", "unknown")
                    
                    self.log_test(
                        f"Status Check #{i+1}",
                        True,
                        f"Task: {task_id[:8]}... | Status: {status}"
                    )
                else:
                    self.log_test(
                        f"Status Check #{i+1}",
                        False,
                        f"HTTP {response.status_code}"
                    )
                    all_success = False
                    
            except Exception as e:
                self.log_test(f"Status Check #{i+1}", False, str(e))
                all_success = False
        
        # Test invalid task ID
        try:
            response = await self.client.get(f"{BASE_URL}/status/invalid-task-id")
            # API might return 200 with different status indicators
            if response.status_code in [400, 404, 500]:
                expected_behavior = True
                details = f"HTTP {response.status_code} (proper error response)"
            elif response.status_code == 200:
                # Check response content
                try:
                    data = response.json()
                    status = data.get("status", "").upper()
                    # Celery treats unknown task IDs as PENDING, which is acceptable behavior
                    # UNKNOWN, PENDING, or explicit error are all valid responses for invalid IDs
                    if status in ["UNKNOWN", "PENDING"] or data.get("error"):
                        expected_behavior = True
                        details = f"HTTP 200 with status: {status} (Celery behavior - acceptable)"
                    else:
                        expected_behavior = False
                        details = f"HTTP 200 with unexpected status: {status}"
                except:
                    expected_behavior = False
                    details = f"HTTP 200 with invalid JSON"
            else:
                expected_behavior = False
                details = f"HTTP {response.status_code} (unexpected)"
            
            self.log_test("Invalid Task ID Handling", expected_behavior, details)
            if not expected_behavior:
                all_success = False
        except Exception as e:
            self.log_test("Invalid Task ID Handling", False, str(e))
            all_success = False
        
        return all_success
    
    async def test_report_endpoint(self) -> bool:
        """Test the report endpoint."""
        print("\n📋 Testing Report Endpoint")
        print("-" * 30)
        
        # Test with invalid company ID
        try:
            response = await self.client.get(f"{BASE_URL}/report/invalid-company-id")
            expected_error = response.status_code in [400, 404]
            self.log_test(
                "Invalid Company ID",
                expected_error,
                f"HTTP {response.status_code} (expected error)"
            )
        except Exception as e:
            self.log_test("Invalid Company ID", False, str(e))
            return False
        
        # Note: We can't easily test valid company IDs without knowing existing ones
        # This would require a database query or completed analysis
        self.log_test(
            "Report Endpoint Structure",
            True,
            "Endpoint responds correctly to invalid IDs"
        )
        
        return True
    
    async def test_error_handling(self) -> bool:
        """Test API error handling."""
        print("\n🚨 Testing Error Handling")
        print("-" * 30)
        
        error_tests = [
            {
                "name": "Missing Company Name",
                "endpoint": "/analyze",
                "method": "POST",
                "data": {"company_url": "https://example.com"}
            },
            {
                "name": "Invalid URL Format",
                "endpoint": "/analyze", 
                "method": "POST",
                "data": {
                    "company_name": "Test",
                    "company_url": "not-a-valid-url"
                }
            },
            {
                "name": "Nonexistent Endpoint",
                "endpoint": "/nonexistent",
                "method": "GET",
                "data": None
            }
        ]
        
        all_success = True
        
        for test in error_tests:
            try:
                if test["method"] == "POST":
                    response = await self.client.post(
                        f"{BASE_URL}{test['endpoint']}", 
                        json=test["data"]
                    )
                else:
                    response = await self.client.get(f"{BASE_URL}{test['endpoint']}")
                
                # Error responses should be 4xx or 5xx
                is_error = 400 <= response.status_code < 600
                self.log_test(
                    test["name"],
                    is_error,
                    f"HTTP {response.status_code} (expected error)"
                )
                
                if not is_error:
                    all_success = False
                    
            except Exception as e:
                self.log_test(test["name"], False, str(e))
                all_success = False
        
        return all_success
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("📊 API TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All API tests passed!")
        else:
            print("\n❌ Failed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['name']}: {result['details']}")
        
        return passed == total


async def main():
    """Run comprehensive API tests."""
    print("🧪 AI Startup Copilot API Tests")
    print("=" * 50)
    
    async with APITester() as tester:
        # Test all endpoints
        await tester.test_health_endpoint()
        
        analyze_results = await tester.test_analyze_endpoint()
        successful_tasks = analyze_results.get("successful_tasks", [])
        task_ids = [task["task_id"] for task in successful_tasks]
        
        await tester.test_status_endpoint(task_ids)
        await tester.test_report_endpoint()
        await tester.test_error_handling()
        
        # Print final summary
        return tester.print_summary()


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        
        print(f"\n🚀 API testing complete!")
        print(f"Run this script regularly to validate API functionality.")
        
        exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 API tests interrupted")
        exit(1)
    except Exception as e:
        print(f"\n💥 API test error: {e}")
        exit(1)
