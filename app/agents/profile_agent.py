"""
CompanyProfileAgent: Web scraping and AI analysis for startup profiles.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain.schema.runnable import RunnableSequence

from app.core.config import settings

logger = logging.getLogger(__name__)


class CompanyProfileOutputParser(BaseOutputParser):
    """Custom output parser for company profile analysis."""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse the LLM output into structured data."""
        try:
            # Clean up the text
            text = text.strip()
            
            # Initialize result structure
            result = {
                "summary": text,
                "mission": "",
                "value_proposition": "",
                "business_model": "",
                "key_insights": []
            }
            
            # Try to extract structured information if the LLM formatted it
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Look for section headers
                lower_line = line.lower()
                if 'mission' in lower_line and ':' in line:
                    current_section = 'mission'
                    result['mission'] = line.split(':', 1)[1].strip()
                elif 'value proposition' in lower_line and ':' in line:
                    current_section = 'value_proposition'
                    result['value_proposition'] = line.split(':', 1)[1].strip()
                elif 'business model' in lower_line and ':' in line:
                    current_section = 'business_model'
                    result['business_model'] = line.split(':', 1)[1].strip()
                elif line.startswith('- ') or line.startswith('• '):
                    # Bullet points as key insights
                    result['key_insights'].append(line[2:].strip())
                elif current_section and not any(keyword in lower_line for keyword in ['mission', 'value', 'business']):
                    # Continue previous section
                    if current_section in result and result[current_section]:
                        result[current_section] += ' ' + line
                    else:
                        result[current_section] = line
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM output: {e}")
            return {
                "summary": text,
                "mission": "",
                "value_proposition": "",
                "business_model": "",
                "key_insights": []
            }


class CompanyProfileAgent:
    """
    Agent for analyzing company websites using web scraping and LLM analysis.
    """
    
    def __init__(self):
        """Initialize the CompanyProfileAgent."""
        self.llm = None
        self.chain = None
        self.output_parser = CompanyProfileOutputParser()
        self._setup_llm_chain()
    
    def _setup_llm_chain(self):
        """Set up the LangChain LLM and processing chain."""
        try:
            # Initialize Ollama chat model
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.1,  # Low temperature for consistent analysis
                num_predict=2048,  # Maximum tokens to generate
                top_p=0.9,
                repeat_penalty=1.1
            )
            
            # Create prompt template for business analysis
            prompt_template = PromptTemplate(
                input_variables=["website_text", "company_url"],
                template="""
You are an expert business analyst. Analyze the following website content and provide a comprehensive startup analysis.

Website URL: {company_url}
Website Content:
{website_text}

Please provide a structured analysis including:

Mission: What is the company's core mission and purpose?
Value Proposition: What unique value does this company provide to its customers?
Business Model: How does this company make money? What is their primary business model?

Then provide a comprehensive summary that includes:
- Company overview and what they do
- Target market and customers
- Key products or services
- Technology stack or approach (if mentioned)
- Competitive advantages
- Market opportunity
- Any notable achievements, funding, or partnerships

Be concise but thorough. Focus on factual information extracted from the website content.
If certain information is not available, indicate that clearly.

Analysis:
""".strip()
            )
            
            # Create the processing chain
            self.chain = prompt_template | self.llm | self.output_parser
            
            logger.info("✅ LLM chain initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM chain: {e}")
            raise
    
    async def _scrape_website(self, url: str) -> Dict[str, Any]:
        """
        Scrape website content using Playwright.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dict containing scraped content and metadata
        """
        browser = None
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=settings.PLAYWRIGHT_HEADLESS
                )
                
                # Create page with mobile user agent to get cleaner content
                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15"
                )
                
                # Set timeout
                page.set_default_timeout(settings.PLAYWRIGHT_TIMEOUT)
                
                # Navigate to the URL
                logger.info(f"Navigating to {url}")
                response = await page.goto(url, wait_until="networkidle")
                
                if not response or response.status >= 400:
                    raise Exception(f"Failed to load page: HTTP {response.status if response else 'No response'}")
                
                # Wait for content to load
                await page.wait_for_load_state("domcontentloaded")
                
                # Get page title
                title = await page.title()
                
                # Get the main content from body, excluding scripts and styles
                body_content = await page.evaluate("""
                    () => {
                        // Remove script and style elements
                        const scripts = document.querySelectorAll('script, style, noscript');
                        scripts.forEach(el => el.remove());
                        
                        // Get body text content
                        const body = document.querySelector('body');
                        return body ? body.innerText : '';
                    }
                """)
                
                # Get meta description
                meta_description = await page.evaluate("""
                    () => {
                        const meta = document.querySelector('meta[name="description"]');
                        return meta ? meta.content : '';
                    }
                """)
                
                # Clean up the text content
                cleaned_content = self._clean_text_content(body_content)
                
                logger.info(f"Successfully scraped {len(cleaned_content)} characters from {url}")
                
                return {
                    "url": url,
                    "title": title,
                    "meta_description": meta_description,
                    "content": cleaned_content,
                    "content_length": len(cleaned_content),
                    "status": "success"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to scrape {url}: {e}")
            return {
                "url": url,
                "title": "",
                "meta_description": "",
                "content": "",
                "content_length": 0,
                "status": "error",
                "error": str(e)
            }
        finally:
            if browser:
                await browser.close()
    
    def _clean_text_content(self, content: str) -> str:
        """
        Clean and preprocess the scraped text content.
        
        Args:
            content: Raw text content from the website
            
        Returns:
            Cleaned text content
        """
        if not content:
            return ""
        
        # Use BeautifulSoup to further clean HTML entities
        soup = BeautifulSoup(content, 'html.parser')
        cleaned = soup.get_text()
        
        # Split into lines and clean each line
        lines = []
        for line in cleaned.split('\n'):
            line = line.strip()
            if line and len(line) > 3:  # Skip very short lines
                lines.append(line)
        
        # Join lines and limit length for LLM processing
        result = '\n'.join(lines)
        
        # Limit to approximately 8000 characters to stay within LLM context limits
        if len(result) > 8000:
            result = result[:8000] + "..."
            logger.info(f"Content truncated to 8000 characters for LLM processing")
        
        return result
    
    async def run(self, url: str) -> Dict[str, Any]:
        """
        Run the complete company profile analysis.
        
        Args:
            url: Company website URL to analyze
            
        Returns:
            Dict containing the analysis results
        """
        try:
            logger.info(f"Starting company profile analysis for {url}")
            
            # Step 1: Scrape the website
            scrape_result = await self._scrape_website(url)
            
            if scrape_result["status"] == "error":
                return {
                    "company_url": url,
                    "status": "error",
                    "error": f"Failed to scrape website: {scrape_result.get('error', 'Unknown error')}",
                    "scrape_result": scrape_result
                }
            
            # Step 2: Check if we have enough content
            if not scrape_result["content"] or len(scrape_result["content"]) < 100:
                return {
                    "company_url": url,
                    "status": "error",
                    "error": "Insufficient content found on the website",
                    "scrape_result": scrape_result
                }
            
            # Step 3: Analyze with LLM
            logger.info(f"Analyzing content with LLM ({len(scrape_result['content'])} characters)")
            
            try:
                analysis_result = await asyncio.to_thread(
                    self.chain.invoke,
                    {
                        "website_text": scrape_result["content"],
                        "company_url": url
                    }
                )
                
                # Combine results
                final_result = {
                    "company_url": url,
                    "status": "success",
                    "website_title": scrape_result["title"],
                    "meta_description": scrape_result["meta_description"],
                    "content_length": scrape_result["content_length"],
                    "analysis": analysis_result,
                    "raw_content": scrape_result["content"][:1000] + "..." if len(scrape_result["content"]) > 1000 else scrape_result["content"]
                }
                
                logger.info(f"✅ Successfully completed analysis for {url}")
                return final_result
                
            except Exception as e:
                logger.error(f"❌ LLM analysis failed for {url}: {e}")
                return {
                    "company_url": url,
                    "status": "error",
                    "error": f"LLM analysis failed: {str(e)}",
                    "scrape_result": scrape_result
                }
        
        except Exception as e:
            logger.error(f"❌ Company profile analysis failed for {url}: {e}")
            return {
                "company_url": url,
                "status": "error",
                "error": f"Analysis failed: {str(e)}"
            }
