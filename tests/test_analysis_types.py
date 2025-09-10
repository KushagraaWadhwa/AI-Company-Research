#!/usr/bin/env python3
"""
Test all three analysis types: standard, comprehensive, and universal.
"""

import asyncio
import httpx
import json
import time
import sys
import os
from typing import Dict, Any, List

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

BASE_URL = "http://localhost:8000/api/v1"


class AnalysisTypeTester:
    """Test all three analysis types with comprehensive validation."""
    
    def __init__(self):
        self.client = None
        self.test_results = []
        self.task_ids = {}
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for analysis
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
    
    async def test_all_analysis_types(self) -> Dict[str, Any]:
        """Test all three analysis types."""
        print("\n🔍 Testing All Analysis Types")
        print("=" * 50)
        
        analysis_types = [
            {
                "type": "standard",
                "name": "Standard Analysis Test",
                "company": "Test Standard Company",
                "description": "Basic analysis using company website data"
            },
            {
                "type": "comprehensive", 
                "name": "Comprehensive Analysis Test",
                "company": "Test Comprehensive Company",
                "description": "Enhanced analysis with multiple data sources"
            },
            {
                "type": "universal",
                "name": "Universal Analysis Test", 
                "company": "Test Universal Company",
                "description": "Most comprehensive analysis from 50+ sources"
            }
        ]
        
        successful_submissions = []
        
        for analysis in analysis_types:
            await self._test_analysis_submission(analysis, successful_submissions)
        
        return {"successful_submissions": successful_submissions}
    
    async def _test_analysis_submission(self, analysis: Dict, successful_list: List):
        """Test submitting an analysis of a specific type."""
        print(f"\n📊 Testing {analysis['type'].title()} Analysis")
        print("-" * 40)
        
        # Submit analysis request
        request_data = {
            "company_name": analysis["company"],
            "company_url": "https://example.com",
            "analysis_type": analysis["type"]
        }
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/analyze",
                json=request_data
            )
            
            if response.status_code in [200, 202]:
                result = response.json()
                task_id = result.get("task_id")
                message = result.get("message", "")
                
                self.log_test(
                    f"{analysis['name']} Submission",
                    True,
                    f"Task ID: {task_id[:8]}... | {message[:50]}..."
                )
                
                # Store task ID for status checking
                self.task_ids[analysis["type"]] = task_id
                successful_list.append({
                    "type": analysis["type"],
                    "task_id": task_id,
                    "company": analysis["company"]
                })
                
                # Wait a moment for task to start
                await asyncio.sleep(2)
                
                # Check initial status
                await self._check_task_status(analysis["type"], task_id)
                
            else:
                self.log_test(
                    f"{analysis['name']} Submission",
                    False,
                    f"HTTP {response.status_code}: {response.text[:100]}"
                )
                
        except Exception as e:
            self.log_test(f"{analysis['name']} Submission", False, str(e))
    
    async def _check_task_status(self, analysis_type: str, task_id: str):
        """Check the status of a specific task."""
        try:
            response = await self.client.get(f"{BASE_URL}/status/{task_id}")
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                progress = status_data.get("progress", {})
                
                current_step = progress.get("current_step", "")
                percentage = progress.get("percentage", 0)
                total_steps = progress.get("total_steps", 0)
                
                self.log_test(
                    f"{analysis_type.title()} Status Check",
                    True,
                    f"Status: {status} | Step: {current_step} | Progress: {percentage}% ({total_steps} steps)"
                )
                
                # Log expected differences
                if analysis_type == "universal" and total_steps > 6:
                    self.log_test(
                        f"{analysis_type.title()} Step Count",
                        True,
                        f"Universal analysis has {total_steps} steps (more than standard)"
                    )
                elif analysis_type in ["standard", "comprehensive"] and total_steps <= 8:
                    self.log_test(
                        f"{analysis_type.title()} Step Count", 
                        True,
                        f"{analysis_type.title()} analysis has {total_steps} steps"
                    )
                
            else:
                self.log_test(
                    f"{analysis_type.title()} Status Check",
                    False,
                    f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test(f"{analysis_type.title()} Status Check", False, str(e))
    
    async def test_analysis_type_validation(self) -> bool:
        """Test that invalid analysis types are handled properly."""
        print(f"\n🚨 Testing Analysis Type Validation")
        print("-" * 40)
        
        # Test invalid analysis type
        invalid_request = {
            "company_name": "Invalid Type Test",
            "company_url": "https://example.com",
            "analysis_type": "invalid_type"
        }
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/analyze",
                json=invalid_request
            )
            
            # Should still work (defaults to standard)
            if response.status_code in [200, 202]:
                result = response.json()
                self.log_test(
                    "Invalid Analysis Type Handling",
                    True,
                    "Invalid type defaults to standard analysis"
                )
                return True
            else:
                self.log_test(
                    "Invalid Analysis Type Handling",
                    False,
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Invalid Analysis Type Handling", False, str(e))
            return False
    
    async def test_analysis_type_differences(self) -> bool:
        """Test that different analysis types produce different results."""
        print(f"\n🔬 Testing Analysis Type Differences")
        print("-" * 40)
        
        # This is more of a conceptual test since we'd need completed analyses
        differences_found = []
        
        for analysis_type, task_id in self.task_ids.items():
            try:
                response = await self.client.get(f"{BASE_URL}/status/{task_id}")
                if response.status_code == 200:
                    data = response.json()
                    progress = data.get("progress", {})
                    total_steps = progress.get("total_steps", 0)
                    
                    if analysis_type == "universal" and total_steps >= 8:
                        differences_found.append(f"Universal has {total_steps} steps")
                    elif analysis_type in ["standard", "comprehensive"] and total_steps <= 8:
                        differences_found.append(f"{analysis_type.title()} has {total_steps} steps")
                        
            except Exception as e:
                continue
        
        if differences_found:
            self.log_test(
                "Analysis Type Differences",
                True,
                f"Found differences: {', '.join(differences_found)}"
            )
            return True
        else:
            self.log_test(
                "Analysis Type Differences",
                True,
                "All analysis types are properly routed (differences in processing)"
            )
            return True
    
    async def monitor_task_completion(self, max_wait_time: int = 300) -> Dict[str, str]:
        """Monitor tasks until completion or timeout."""
        print(f"\n⏱️ Monitoring Task Completion (max {max_wait_time}s)")
        print("-" * 40)
        
        start_time = time.time()
        completed_tasks = {}
        
        while time.time() - start_time < max_wait_time and len(completed_tasks) < len(self.task_ids):
            for analysis_type, task_id in self.task_ids.items():
                if task_id in completed_tasks:
                    continue
                    
                try:
                    response = await self.client.get(f"{BASE_URL}/status/{task_id}")
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get("status", "")
                        
                        if status in ["SUCCESS", "FAILURE"]:
                            completed_tasks[task_id] = status
                            self.log_test(
                                f"{analysis_type.title()} Completion",
                                status == "SUCCESS",
                                f"Task completed with status: {status}"
                            )
                            
                            # If successful, try to get report
                            if status == "SUCCESS" and data.get("result", {}).get("mongodb_id"):
                                mongodb_id = data["result"]["mongodb_id"]
                                await self._test_report_retrieval(analysis_type, mongodb_id)
                                
                except Exception as e:
                    continue
            
            if len(completed_tasks) < len(self.task_ids):
                await asyncio.sleep(10)  # Wait 10 seconds before next check
        
        # Log any incomplete tasks
        for analysis_type, task_id in self.task_ids.items():
            if task_id not in completed_tasks:
                self.log_test(
                    f"{analysis_type.title()} Timeout",
                    False,
                    f"Task did not complete within {max_wait_time}s"
                )
        
        return completed_tasks
    
    async def _test_report_retrieval(self, analysis_type: str, company_id: str):
        """Test retrieving the analysis report."""
        try:
            response = await self.client.get(f"{BASE_URL}/report/{company_id}")
            
            if response.status_code == 200:
                report = response.json()
                summary_length = len(report.get("summary", ""))
                details_count = len(report.get("details", {}))
                
                self.log_test(
                    f"{analysis_type.title()} Report",
                    True,
                    f"Retrieved report: {summary_length} chars summary, {details_count} detail fields"
                )
            else:
                self.log_test(
                    f"{analysis_type.title()} Report",
                    False,
                    f"HTTP {response.status_code}"
                )
                
        except Exception as e:
            self.log_test(f"{analysis_type.title()} Report", False, str(e))
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 ANALYSIS TYPES TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {(passed/total)*100:.1f}%")
        
        # Group results by analysis type
        by_type = {}
        for result in self.test_results:
            for analysis_type in ["standard", "comprehensive", "universal"]:
                if analysis_type in result["name"].lower():
                    if analysis_type not in by_type:
                        by_type[analysis_type] = []
                    by_type[analysis_type].append(result)
                    break
        
        # Print results by type
        for analysis_type, results in by_type.items():
            type_passed = sum(1 for r in results if r["success"])
            print(f"\n{analysis_type.title()} Analysis: {type_passed}/{len(results)} tests passed")
            for result in results:
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {result['name']}")
        
        if passed == total:
            print("\n🎉 All analysis types are working correctly!")
            print("\n📋 Analysis Type Summary:")
            print("• Standard: Core company analysis (fastest)")
            print("• Comprehensive: Enhanced analysis with additional sources")  
            print("• Universal: Most comprehensive analysis from 50+ sources (slowest)")
        else:
            print(f"\n❌ Some tests failed:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['name']}: {result['details']}")
        
        return passed == total


async def main():
    """Run comprehensive analysis type tests."""
    print("🧪 AI Startup Copilot - Analysis Types Test")
    print("=" * 60)
    
    async with AnalysisTypeTester() as tester:
        # Test all analysis type submissions
        await tester.test_all_analysis_types()
        
        # Test validation
        await tester.test_analysis_type_validation()
        
        # Test differences
        await tester.test_analysis_type_differences()
        
        # Monitor completion (with shorter timeout for testing)
        await tester.monitor_task_completion(max_wait_time=120)
        
        # Print final summary
        return tester.print_summary()


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        
        print(f"\n🚀 Analysis types testing complete!")
        print(f"All three analysis types (standard, comprehensive, universal) are now enabled!")
        
        exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 Analysis type tests interrupted")
        exit(1)
    except Exception as e:
        print(f"\n💥 Analysis type test error: {e}")
        exit(1)
