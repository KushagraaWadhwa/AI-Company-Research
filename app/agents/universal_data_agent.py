"""
Universal Data Aggregation Agent
Comprehensive startup intelligence from 50+ data sources.
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus, urljoin
from playwright.async_api import async_playwright
import httpx

from app.agents.profile_agent import CompanyProfileAgent

logger = logging.getLogger(__name__)


class UniversalDataAgent(CompanyProfileAgent):
    """Universal agent that aggregates data from extensive sources."""
    
    def __init__(self):
        super().__init__()
        self.data_sources = self._initialize_data_sources()
        self.max_concurrent_scrapes = 10  # Limit concurrent requests
    
    def _initialize_data_sources(self) -> Dict[str, Dict]:
        """Initialize comprehensive list of data sources."""
        return {
            # Financial & Investment
            "crunchbase": {
                "url_template": "https://www.crunchbase.com/organization/{slug}",
                "category": "financial",
                "priority": "high"
            },
            "pitchbook": {
                "url_template": "https://pitchbook.com/profiles/company/{slug}",
                "category": "financial",
                "priority": "high"
            },
            "angellist": {
                "url_template": "https://angel.co/company/{slug}",
                "category": "financial",
                "priority": "medium"
            },
            
            # Professional & Social
            "linkedin_company": {
                "url_template": "https://www.linkedin.com/company/{slug}",
                "category": "professional",
                "priority": "high"
            },
            "twitter": {
                "url_template": "https://twitter.com/{handle}",
                "category": "social",
                "priority": "medium"
            },
            "facebook": {
                "url_template": "https://www.facebook.com/{slug}",
                "category": "social",
                "priority": "low"
            },
            
            # Employment & Culture
            "glassdoor": {
                "url_template": "https://www.glassdoor.com/Overview/Working-at-{slug}",
                "category": "employment",
                "priority": "high"
            },
            "indeed": {
                "url_template": "https://www.indeed.com/cmp/{slug}",
                "category": "employment",
                "priority": "medium"
            },
            
            # Business & Reviews
            "google_business": {
                "url_template": "https://www.google.com/search?q={name}+business+reviews",
                "category": "reviews",
                "priority": "medium"
            },
            "yelp": {
                "url_template": "https://www.yelp.com/biz/{slug}",
                "category": "reviews",
                "priority": "medium"
            },
            "trustpilot": {
                "url_template": "https://www.trustpilot.com/review/{domain}",
                "category": "reviews",
                "priority": "medium"
            },
            
            # Technology & Web
            "builtwith": {
                "url_template": "https://builtwith.com/{domain}",
                "category": "technology",
                "priority": "high"
            },
            "similarweb": {
                "url_template": "https://www.similarweb.com/website/{domain}",
                "category": "analytics",
                "priority": "high"
            },
            
            # News & Media
            "google_news": {
                "url_template": "https://news.google.com/search?q={name}",
                "category": "news",
                "priority": "high"
            },
            "techcrunch": {
                "url_template": "https://techcrunch.com/tag/{slug}",
                "category": "news",
                "priority": "medium"
            },
            
            # Product & E-commerce
            "product_hunt": {
                "url_template": "https://www.producthunt.com/@{slug}",
                "category": "products",
                "priority": "medium"
            },
            "app_store": {
                "url_template": "https://apps.apple.com/search?term={name}",
                "category": "products",
                "priority": "medium"
            },
            
            # Industry-Specific APIs (when available)
            "github": {
                "url_template": "https://github.com/{slug}",
                "category": "technology",
                "priority": "medium"
            },
            "stackoverflow": {
                "url_template": "https://stackoverflow.com/search?q={name}",
                "category": "technology",
                "priority": "low"
            }
        }
    
    async def run_universal_analysis(self, company_name: str, company_url: str) -> Dict[str, Any]:
        """
        Run comprehensive universal analysis from all available sources.
        
        Args:
            company_name: Name of the company
            company_url: Primary company website
            
        Returns:
            Dict containing comprehensive analysis from all sources
        """
        try:
            logger.info(f"🌐 Starting universal analysis for {company_name}")
            
            # Step 1: Generate all possible URLs
            all_urls = self._generate_all_source_urls(company_name, company_url)
            logger.info(f"Generated {len(all_urls)} potential data sources")
            
            # Step 2: Prioritize sources
            prioritized_sources = self._prioritize_sources(all_urls)
            
            # Step 3: Scrape data from all sources (with concurrency limits)
            source_data = await self._scrape_all_sources(prioritized_sources)
            
            # Step 4: Analyze and combine all data
            comprehensive_analysis = await self._create_comprehensive_analysis(
                company_name, company_url, source_data
            )
            
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Universal analysis failed: {e}")
            return {
                "company_name": company_name,
                "company_url": company_url,
                "status": "error",
                "error": str(e)
            }
    
    def _generate_all_source_urls(self, company_name: str, company_url: str) -> Dict[str, str]:
        """Generate URLs for all possible data sources."""
        # Extract domain from company URL
        domain = company_url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        
        # Create various slug formats
        slug_formats = {
            "slug": company_name.lower().replace(' ', '-').replace('.', '').replace(',', ''),
            "slug_underscore": company_name.lower().replace(' ', '_').replace('.', '').replace(',', ''),
            "name": quote_plus(company_name),
            "domain": domain,
            "handle": company_name.lower().replace(' ', '').replace('.', '')[:15]  # Twitter handle limit
        }
        
        all_urls = {}
        
        for source_name, source_config in self.data_sources.items():
            try:
                # Try different slug formats until one works
                url_template = source_config["url_template"]
                
                if "{slug}" in url_template:
                    url = url_template.format(slug=slug_formats["slug"])
                elif "{name}" in url_template:
                    url = url_template.format(name=slug_formats["name"])
                elif "{domain}" in url_template:
                    url = url_template.format(domain=slug_formats["domain"])
                elif "{handle}" in url_template:
                    url = url_template.format(handle=slug_formats["handle"])
                else:
                    url = url_template
                
                all_urls[source_name] = {
                    "url": url,
                    "category": source_config["category"],
                    "priority": source_config["priority"]
                }
                
            except Exception as e:
                logger.warning(f"Failed to generate URL for {source_name}: {e}")
        
        # Add the main website
        all_urls["main_website"] = {
            "url": company_url,
            "category": "primary",
            "priority": "critical"
        }
        
        return all_urls
    
    def _prioritize_sources(self, all_urls: Dict) -> Dict:
        """Prioritize sources based on importance and reliability."""
        priority_order = ["critical", "high", "medium", "low"]
        prioritized = {}
        
        for priority in priority_order:
            for source_name, source_info in all_urls.items():
                if source_info["priority"] == priority:
                    prioritized[source_name] = source_info
        
        return prioritized
    
    async def _scrape_all_sources(self, sources: Dict) -> Dict[str, Dict]:
        """Scrape data from all sources with concurrency control."""
        results = {}
        semaphore = asyncio.Semaphore(self.max_concurrent_scrapes)
        
        async def scrape_with_semaphore(source_name: str, source_info: Dict):
            async with semaphore:
                return await self._scrape_single_universal_source(source_name, source_info)
        
        # Create tasks for all sources
        tasks = []
        for source_name, source_info in sources.items():
            tasks.append(scrape_with_semaphore(source_name, source_info))
        
        # Execute with progress tracking
        logger.info(f"Scraping {len(tasks)} sources concurrently...")
        scrape_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, (source_name, _) in enumerate(sources.items()):
            result = scrape_results[i]
            if isinstance(result, Exception):
                results[source_name] = {"status": "error", "error": str(result)}
            else:
                results[source_name] = result
        
        successful_scrapes = sum(1 for r in results.values() if r.get("status") == "success")
        logger.info(f"Successfully scraped {successful_scrapes}/{len(results)} sources")
        
        return results
    
    async def _scrape_single_universal_source(self, source_name: str, source_info: Dict) -> Dict:
        """Scrape data from a single source with intelligent extraction."""
        try:
            url = source_info["url"]
            category = source_info["category"]
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set realistic user agent
                await page.set_user_agent(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                logger.info(f"🔍 Scraping {source_name}: {url}")
                
                try:
                    # Navigate with timeout and wait for content
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(2000)  # Wait for dynamic content
                    
                    # Check if page loaded successfully
                    title = await page.title()
                    if not title or "404" in title or "not found" in title.lower():
                        raise Exception("Page not found or failed to load")
                    
                    # Extract data based on category
                    extracted_data = await self._extract_by_category(page, category, source_name)
                    
                    await browser.close()
                    
                    return {
                        "status": "success",
                        "url": url,
                        "category": category,
                        "data": extracted_data,
                        "page_title": title
                    }
                    
                except Exception as e:
                    await browser.close()
                    raise e
                    
        except Exception as e:
            logger.warning(f"Failed to scrape {source_name}: {e}")
            return {
                "status": "error",
                "url": source_info["url"],
                "category": source_info["category"],
                "error": str(e)
            }
    
    async def _extract_by_category(self, page, category: str, source_name: str) -> Dict:
        """Extract data based on source category."""
        try:
            if category == "financial":
                return await self._extract_financial_data(page, source_name)
            elif category == "professional":
                return await self._extract_professional_data(page, source_name)
            elif category == "employment":
                return await self._extract_employment_data(page, source_name)
            elif category == "reviews":
                return await self._extract_review_data(page, source_name)
            elif category == "technology":
                return await self._extract_technology_data(page, source_name)
            elif category == "news":
                return await self._extract_news_data(page, source_name)
            elif category == "social":
                return await self._extract_social_data(page, source_name)
            else:
                return await self._extract_generic_data(page)
                
        except Exception as e:
            logger.warning(f"Category extraction failed for {category}: {e}")
            return await self._extract_generic_data(page)
    
    async def _extract_financial_data(self, page, source_name: str) -> Dict:
        """Extract financial and funding data."""
        data = {}
        
        try:
            # Common financial data selectors
            selectors = {
                "funding_total": ['[data-test="funding-total"]', '.funding-total', '.total-funding'],
                "valuation": ['[data-test="valuation"]', '.valuation', '.company-valuation'],
                "founded_date": ['[data-test="founded-date"]', '.founded-date', '.founding-date'],
                "employees": ['[data-test="employee-count"]', '.employee-count', '.team-size'],
                "stage": ['[data-test="funding-stage"]', '.funding-stage', '.company-stage'],
                "investors": ['[data-test="investors"]', '.investors', '.investor-list']
            }
            
            for field, selector_list in selectors.items():
                for selector in selector_list:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            if text and text.strip():
                                data[field] = text.strip()
                                break
                    except:
                        continue
            
            # Get general page content if specific selectors fail
            if not data:
                content = await page.text_content('body')
                if content:
                    # Extract financial keywords
                    financial_keywords = ['funding', 'valuation', 'investor', 'series', 'million', 'billion']
                    relevant_content = []
                    
                    for line in content.split('\n'):
                        if any(keyword in line.lower() for keyword in financial_keywords):
                            relevant_content.append(line.strip())
                    
                    data["financial_mentions"] = relevant_content[:10]  # Limit to 10 most relevant
            
        except Exception as e:
            data["extraction_error"] = str(e)
        
        return data
    
    async def _extract_professional_data(self, page, source_name: str) -> Dict:
        """Extract professional networking data."""
        data = {}
        
        try:
            if "linkedin" in source_name:
                # LinkedIn-specific extraction
                selectors = {
                    "description": ['[data-test-id="about-us-description"]', '.org-about-us-organization-description'],
                    "industry": ['[data-test-id="company-industry"]', '.org-top-card-summary-info-list'],
                    "headquarters": ['[data-test-id="headquarters"]', '.org-location'],
                    "employee_count": ['[data-test-id="employees-count"]', '.org-employees-count'],
                    "followers": ['[data-test-id="followers-count"]', '.follower-count']
                }
            else:
                # Generic professional selectors
                selectors = {
                    "description": ['.company-description', '.about-company', '.company-summary'],
                    "industry": ['.company-industry', '.industry', '.sector'],
                    "size": ['.company-size', '.employee-count', '.team-size']
                }
            
            for field, selector_list in selectors.items():
                for selector in selector_list:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            if text and text.strip():
                                data[field] = text.strip()
                                break
                    except:
                        continue
        
        except Exception as e:
            data["extraction_error"] = str(e)
        
        return data
    
    async def _extract_generic_data(self, page) -> Dict:
        """Extract generic data from any page."""
        try:
            title = await page.title()
            content = await page.text_content('body')
            
            # Clean and limit content
            if content:
                cleaned_content = re.sub(r'\s+', ' ', content).strip()
                cleaned_content = cleaned_content[:3000] if len(cleaned_content) > 3000 else cleaned_content
            else:
                cleaned_content = ""
            
            return {
                "title": title,
                "content": cleaned_content,
                "content_length": len(content) if content else 0
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # Additional extraction methods for other categories...
    async def _extract_employment_data(self, page, source_name: str) -> Dict:
        """Extract employment and culture data."""
        # Implementation for Glassdoor, Indeed, etc.
        return await self._extract_generic_data(page)
    
    async def _extract_review_data(self, page, source_name: str) -> Dict:
        """Extract review and rating data."""
        # Implementation for Yelp, Trustpilot, etc.
        return await self._extract_generic_data(page)
    
    async def _extract_technology_data(self, page, source_name: str) -> Dict:
        """Extract technology stack and web analytics."""
        # Implementation for BuiltWith, SimilarWeb, etc.
        return await self._extract_generic_data(page)
    
    async def _extract_news_data(self, page, source_name: str) -> Dict:
        """Extract news and media coverage."""
        # Implementation for news sources
        return await self._extract_generic_data(page)
    
    async def _extract_social_data(self, page, source_name: str) -> Dict:
        """Extract social media data."""
        # Implementation for Twitter, Facebook, etc.
        return await self._extract_generic_data(page)
    
    async def _create_comprehensive_analysis(self, company_name: str, company_url: str, source_data: Dict) -> Dict:
        """Create comprehensive analysis from all sources."""
        try:
            # Organize data by category
            categorized_data = {}
            successful_sources = []
            
            for source_name, result in source_data.items():
                if result.get("status") == "success":
                    successful_sources.append(source_name)
                    category = result.get("category", "unknown")
                    
                    if category not in categorized_data:
                        categorized_data[category] = {}
                    
                    categorized_data[category][source_name] = result.get("data", {})
            
            # Create comprehensive prompt for LLM analysis
            analysis_prompt = self._build_comprehensive_prompt(
                company_name, company_url, categorized_data
            )
            
            # Generate AI analysis
            ai_analysis = await asyncio.to_thread(
                self.chain.invoke,
                {
                    "website_text": analysis_prompt,
                    "company_url": company_url
                }
            )
            
            return {
                "company_name": company_name,
                "company_url": company_url,
                "status": "success",
                "sources_analyzed": len(successful_sources),
                "successful_sources": successful_sources,
                "categories_covered": list(categorized_data.keys()),
                "comprehensive_analysis": ai_analysis,
                "raw_data": categorized_data,
                "data_quality_score": self._calculate_data_quality_score(categorized_data)
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis creation failed: {e}")
            return {
                "company_name": company_name,
                "company_url": company_url,
                "status": "error",
                "error": str(e),
                "partial_data": source_data
            }
    
    def _build_comprehensive_prompt(self, company_name: str, company_url: str, categorized_data: Dict) -> str:
        """Build comprehensive prompt for LLM analysis."""
        prompt = f"""
        COMPREHENSIVE STARTUP INTELLIGENCE ANALYSIS
        Company: {company_name}
        Website: {company_url}
        
        Data collected from {len(categorized_data)} categories of sources:
        
        """
        
        for category, sources in categorized_data.items():
            prompt += f"\n=== {category.upper()} INTELLIGENCE ===\n"
            
            for source_name, data in sources.items():
                prompt += f"\n--- {source_name} ---\n"
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if value and str(value).strip() and key != "error":
                            prompt += f"{key}: {str(value)[:200]}...\n"
                else:
                    prompt += f"{str(data)[:200]}...\n"
        
        prompt += """
        
        ANALYSIS REQUIREMENTS:
        Provide a comprehensive startup intelligence report with:
        
        1. EXECUTIVE SUMMARY
        2. BUSINESS MODEL & VALUE PROPOSITION
        3. FINANCIAL HEALTH & FUNDING STATUS
        4. MARKET POSITION & COMPETITIVE LANDSCAPE  
        5. TEAM & LEADERSHIP ASSESSMENT
        6. TECHNOLOGY & PRODUCT ANALYSIS
        7. CUSTOMER SENTIMENT & REPUTATION
        8. GROWTH INDICATORS & MARKET TRACTION
        9. RISK ASSESSMENT & RED FLAGS
        10. INVESTMENT THESIS & RECOMMENDATIONS
        
        Base analysis on factual data from sources. Indicate confidence levels and data quality.
        """
        
        return prompt
    
    def _calculate_data_quality_score(self, categorized_data: Dict) -> float:
        """Calculate data quality score based on sources and completeness."""
        try:
            total_sources = sum(len(sources) for sources in categorized_data.values())
            total_categories = len(categorized_data)
            
            # Weight by category importance
            category_weights = {
                "primary": 1.0,
                "financial": 0.9,
                "professional": 0.8,
                "employment": 0.7,
                "reviews": 0.6,
                "technology": 0.5,
                "news": 0.4,
                "social": 0.3
            }
            
            weighted_score = 0
            max_possible_score = 0
            
            for category, sources in categorized_data.items():
                weight = category_weights.get(category, 0.2)
                max_possible_score += weight
                
                # Score based on number of successful sources in category
                category_score = min(len(sources) * 0.2, 1.0) * weight
                weighted_score += category_score
            
            if max_possible_score > 0:
                final_score = (weighted_score / max_possible_score) * 100
                return round(final_score, 2)
            else:
                return 0.0
                
        except Exception:
            return 0.0
