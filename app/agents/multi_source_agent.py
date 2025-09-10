"""
Multi-Source Company Analysis Agent
Scrapes data from multiple sources for comprehensive startup analysis.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
from playwright.async_api import async_playwright

from app.agents.profile_agent import CompanyProfileAgent

logger = logging.getLogger(__name__)


class MultiSourceAnalysisAgent(CompanyProfileAgent):
    """Enhanced agent that gathers data from multiple sources."""
    
    def __init__(self):
        super().__init__()
        self.data_sources = []
    
    async def run_multi_source_analysis(self, company_name: str, company_url: str) -> Dict[str, Any]:
        """
        Run comprehensive multi-source analysis.
        
        Args:
            company_name: Name of the company
            company_url: Primary company website
            
        Returns:
            Dict containing analysis from multiple sources
        """
        try:
            logger.info(f"Starting multi-source analysis for {company_name}")
            
            # Generate potential URLs for different sources
            source_urls = self._generate_source_urls(company_name, company_url)
            
            # Scrape all sources concurrently
            source_data = await self._scrape_multiple_sources(source_urls)
            
            # Combine and analyze all data
            combined_analysis = await self._analyze_combined_data(
                company_name, company_url, source_data
            )
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Multi-source analysis failed: {e}")
            return {
                "company_name": company_name,
                "company_url": company_url,
                "status": "error",
                "error": str(e)
            }
    
    def _generate_source_urls(self, company_name: str, company_url: str) -> Dict[str, str]:
        """Generate URLs for different data sources."""
        company_slug = company_name.lower().replace(' ', '-').replace('.', '')
        encoded_name = quote_plus(company_name)
        
        return {
            "main_website": company_url,
            "linkedin_company": f"https://www.linkedin.com/company/{company_slug}",
            "linkedin_search": f"https://www.linkedin.com/search/results/companies/?keywords={encoded_name}",
            "crunchbase": f"https://www.crunchbase.com/organization/{company_slug}",
            "glassdoor": f"https://www.glassdoor.com/Overview/Working-at-{company_slug}",
            "google_search": f"https://www.google.com/search?q={encoded_name}+startup+company",
            "angel_list": f"https://angel.co/company/{company_slug}",
            "pitchbook": f"https://pitchbook.com/profiles/company/{company_slug}"
        }
    
    async def _scrape_multiple_sources(self, source_urls: Dict[str, str]) -> Dict[str, Dict]:
        """Scrape data from multiple sources concurrently."""
        results = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Create multiple pages for concurrent scraping
            tasks = []
            for source_name, url in source_urls.items():
                tasks.append(self._scrape_single_source(browser, source_name, url))
            
            # Execute all scraping tasks concurrently
            scrape_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, (source_name, _) in enumerate(source_urls.items()):
                result = scrape_results[i]
                if isinstance(result, Exception):
                    results[source_name] = {"status": "error", "error": str(result)}
                else:
                    results[source_name] = result
            
            await browser.close()
        
        return results
    
    async def _scrape_single_source(self, browser, source_name: str, url: str) -> Dict:
        """Scrape data from a single source."""
        try:
            page = await browser.new_page()
            
            # Set user agent to avoid blocking
            await page.set_user_agent(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            
            logger.info(f"Scraping {source_name}: {url}")
            
            # Navigate with timeout
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Extract data based on source type
            if source_name == "main_website":
                data = await self._extract_website_data(page)
            elif source_name.startswith("linkedin"):
                data = await self._extract_linkedin_data(page)
            elif source_name == "crunchbase":
                data = await self._extract_crunchbase_data(page)
            elif source_name == "glassdoor":
                data = await self._extract_glassdoor_data(page)
            else:
                data = await self._extract_generic_data(page)
            
            await page.close()
            
            return {
                "status": "success",
                "url": url,
                "data": data
            }
            
        except Exception as e:
            logger.warning(f"Failed to scrape {source_name}: {e}")
            return {
                "status": "error", 
                "url": url,
                "error": str(e)
            }
    
    async def _extract_linkedin_data(self, page) -> Dict:
        """Extract LinkedIn-specific data."""
        try:
            # LinkedIn company data extraction
            company_info = {}
            
            # Company description
            try:
                description = await page.text_content('[data-test-id="about-us-description"]')
                company_info["description"] = description
            except:
                pass
            
            # Employee count
            try:
                employees = await page.text_content('[data-test-id="employees-count"]')
                company_info["employee_count"] = employees
            except:
                pass
            
            # Industry
            try:
                industry = await page.text_content('[data-test-id="company-industry"]')
                company_info["industry"] = industry
            except:
                pass
            
            # Headquarters
            try:
                hq = await page.text_content('[data-test-id="headquarters"]')
                company_info["headquarters"] = hq
            except:
                pass
            
            return company_info
            
        except Exception as e:
            logger.warning(f"LinkedIn extraction failed: {e}")
            return {"error": str(e)}
    
    async def _extract_crunchbase_data(self, page) -> Dict:
        """Extract Crunchbase-specific data."""
        try:
            crunchbase_info = {}
            
            # Funding information
            try:
                funding = await page.text_content('[data-test-id="funding-total"]')
                crunchbase_info["total_funding"] = funding
            except:
                pass
            
            # Founded date
            try:
                founded = await page.text_content('[data-test-id="founded-date"]')
                crunchbase_info["founded_date"] = founded
            except:
                pass
            
            # Founders
            try:
                founders = await page.query_selector_all('[data-test-id="founder-name"]')
                founder_names = [await f.text_content() for f in founders]
                crunchbase_info["founders"] = founder_names
            except:
                pass
            
            return crunchbase_info
            
        except Exception as e:
            logger.warning(f"Crunchbase extraction failed: {e}")
            return {"error": str(e)}
    
    async def _extract_glassdoor_data(self, page) -> Dict:
        """Extract Glassdoor-specific data."""
        try:
            glassdoor_info = {}
            
            # Company rating
            try:
                rating = await page.text_content('[data-test="employer-rating"]')
                glassdoor_info["rating"] = rating
            except:
                pass
            
            # Company size
            try:
                size = await page.text_content('[data-test="employer-size"]')
                glassdoor_info["company_size"] = size
            except:
                pass
            
            return glassdoor_info
            
        except Exception as e:
            logger.warning(f"Glassdoor extraction failed: {e}")
            return {"error": str(e)}
    
    async def _extract_generic_data(self, page) -> Dict:
        """Extract generic data from any page."""
        try:
            title = await page.title()
            content = await page.text_content('body')
            
            # Clean and limit content
            cleaned_content = content[:2000] if content else ""
            
            return {
                "title": title,
                "content": cleaned_content,
                "content_length": len(content) if content else 0
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _analyze_combined_data(self, company_name: str, company_url: str, source_data: Dict) -> Dict:
        """Analyze combined data from all sources using LLM."""
        try:
            # Combine all successful data
            combined_text = f"Company: {company_name}\nWebsite: {company_url}\n\n"
            
            for source_name, source_result in source_data.items():
                if source_result.get("status") == "success":
                    data = source_result.get("data", {})
                    combined_text += f"\n=== {source_name.upper()} DATA ===\n"
                    
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if value and key != "error":
                                combined_text += f"{key}: {value}\n"
                    else:
                        combined_text += str(data)[:500] + "\n"
            
            # Use LLM to analyze combined data
            enhanced_prompt = f"""
            Analyze this comprehensive startup data from multiple sources:

            {combined_text}

            Provide a detailed analysis including:
            1. Company Overview and Mission
            2. Business Model and Value Proposition  
            3. Market Position and Competition
            4. Funding and Financial Status
            5. Team and Leadership
            6. Company Culture and Employee Satisfaction
            7. Growth Potential and Risks
            8. Key Insights and Recommendations

            Focus on factual information extracted from the sources.
            """
            
            # Generate enhanced analysis
            analysis_result = await asyncio.to_thread(
                self.chain.invoke,
                {
                    "website_text": enhanced_prompt,
                    "company_url": company_url
                }
            )
            
            return {
                "company_name": company_name,
                "company_url": company_url,
                "status": "success",
                "enhanced_analysis": analysis_result,
                "source_data": source_data,
                "data_sources_used": [k for k, v in source_data.items() if v.get("status") == "success"]
            }
            
        except Exception as e:
            logger.error(f"Combined analysis failed: {e}")
            return {
                "company_name": company_name,
                "company_url": company_url,
                "status": "error",
                "error": str(e),
                "source_data": source_data
            }
