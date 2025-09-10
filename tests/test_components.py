#!/usr/bin/env python3
"""
Component tests for AI Startup Copilot.
Tests individual components like Playwright, Ollama, MongoDB, and agents.
"""

import asyncio
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

async def test_playwright():
    """Test Playwright web scraping."""
    print("🌐 Testing Playwright...")
    try:
        import playwright
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto('https://example.com', timeout=30000)
            title = await page.title()
            content = await page.content()
            await browser.close()
            
            print(f"✅ Playwright working - Title: {title}")
            return True
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False
    except Exception as e:
        print(f"❌ Playwright failed: {e}")
        return False

def test_ollama_llm():
    """Test Ollama LLM."""
    print("🤖 Testing Ollama LLM...")
    try:
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(
            model="llama3.2",
            base_url="http://localhost:11434",
            temperature=0.1
        )
        
        # Simple test
        response = llm.invoke("What is 2+2?")
        print(f"✅ Ollama LLM working - Response: {response.content[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Ollama LLM failed: {e}")
        return False

def test_embeddings():
    """Test Ollama embeddings."""
    print("📊 Testing Ollama Embeddings...")
    try:
        from langchain_ollama import OllamaEmbeddings
        
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        # Test embedding
        result = embeddings.embed_query("test text")
        print(f"✅ Embeddings working - Dimension: {len(result)}")
        return True
    except Exception as e:
        print(f"❌ Embeddings failed: {e}")
        return False

def test_mongodb():
    """Test MongoDB connection."""
    print("🗄️ Testing MongoDB...")
    try:
        from app.core.mongo_client import get_sync_database
        
        db = get_sync_database()
        result = db.command('ping')
        print(f"✅ MongoDB working - Ping result: {result}")
        return True
    except Exception as e:
        print(f"❌ MongoDB failed: {e}")
        return False

async def test_agent():
    """Test the complete agent workflow."""
    print("🕵️ Testing CompanyProfileAgent...")
    try:
        from app.agents.profile_agent import CompanyProfileAgent
        
        agent = CompanyProfileAgent()
        result = await agent.run("https://example.com")
        
        if result.get("status") == "success":
            print("✅ Agent working - Analysis completed")
            return True
        else:
            print(f"❌ Agent failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Agent failed: {e}")
        return False

async def main():
    """Run all component tests."""
    print("🧪 AI Startup Copilot Component Tests")
    print("=" * 50)
    
    results = []
    
    # Test individual components
    results.append(await test_playwright())
    results.append(test_ollama_llm())
    results.append(test_embeddings())
    results.append(test_mongodb())
    results.append(await test_agent())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All components working!")
    else:
        print("❌ Some components failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        sys.exit(1)
