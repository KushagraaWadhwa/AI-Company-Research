#!/usr/bin/env python3
"""
Worker debug tests for AI Startup Copilot.
Tests worker connectivity, task submission, and Celery integration.
"""

import asyncio
import httpx
import json
import time
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)


BASE_URL = "http://localhost:8000/api/v1"


async def debug_worker():
    """Debug worker connectivity step by step."""
    
    async with httpx.AsyncClient() as client:
        print("🔧 WORKER DEBUG TEST")
        print("=" * 30)
        
        # Test 1: Basic health check
        print("1. Testing API health...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health = response.json()
                print("✅ API healthy")
                
                # Check Celery worker status specifically
                celery_status = health.get('services', {}).get('celery_worker', {})
                print(f"   Celery Worker: {celery_status.get('status', 'unknown')}")
            else:
                print(f"❌ API unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
        
        # Test 2: Submit simple analysis with original format
        print("\n2. Testing simple analysis submission...")
        
        simple_request = {
            "company_name": "Debug Test",
            "company_url": "https://example.com"
        }
        
        print(f"Request: {json.dumps(simple_request, indent=2)}")
        
        try:
            response = await client.post(f"{BASE_URL}/analyze", json=simple_request)
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code in [200, 202]:
                result = response.json()
                task_id = result.get('task_id')
                print(f"✅ Task created: {task_id}")
                
                # Immediately check status
                print("\n3. Checking task status immediately...")
                await asyncio.sleep(1)
                
                status_response = await client.get(f"{BASE_URL}/status/{task_id}")
                print(f"Status response: {status_response.status_code}")
                print(f"Status body: {status_response.text}")
                
                return True
            else:
                print(f"❌ Task creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return False


def test_celery_direct():
    """Test Celery task directly without API."""
    print("\n4. Testing Celery task directly...")
    
    try:
        from app.workers.tasks import run_startup_analysis
        
        print("✅ Task import successful")
        
        # Submit task directly
        task = run_startup_analysis.delay("Direct Test", "https://example.com")
        print(f"✅ Direct task submitted: {task.id}")
        
        # Check task state
        print(f"Task state: {task.state}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct task failed: {e}")
        return False


def check_redis():
    """Check Redis connectivity."""
    print("\n5. Testing Redis connectivity...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Test connection
        result = r.ping()
        print(f"✅ Redis ping: {result}")
        
        # Check queue length
        queue_length = r.llen('default')
        print(f"Tasks in default queue: {queue_length}")
        
        # Check for any task-related keys
        keys = r.keys('celery-task-meta-*')
        print(f"Task metadata keys: {len(keys)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False


if __name__ == "__main__":
    print("🔍 COMPREHENSIVE WORKER DEBUG")
    print("This will help identify why tasks aren't being processed.")
    print()
    
    try:
        # Test API
        api_success = asyncio.run(debug_worker())
        
        # Test Celery direct
        celery_success = test_celery_direct()
        
        # Test Redis
        redis_success = check_redis()
        
        print(f"\n📊 DEBUG SUMMARY")
        print("=" * 30)
        print(f"API: {'✅' if api_success else '❌'}")
        print(f"Celery Direct: {'✅' if celery_success else '❌'}")
        print(f"Redis: {'✅' if redis_success else '❌'}")
        
        if all([api_success, celery_success, redis_success]):
            print(f"\n🎯 All components working!")
            print(f"Issue might be:")
            print(f"• Worker not actually running")
            print(f"• Worker not connected to same Redis")
            print(f"• Task routing issue")
        else:
            print(f"\n❌ Found issues above")
            
    except Exception as e:
        print(f"\n💥 Debug error: {e}")
    
    print(f"\n🔧 TROUBLESHOOTING STEPS:")
    print(f"1. Check if worker terminal shows 'celery@hostname ready'")
    print(f"2. Restart worker: Ctrl+C then 'python start_worker.py'")
    print(f"3. Check Redis: redis-cli ping")
    print(f"4. Check .env file exists and has correct Redis settings")
