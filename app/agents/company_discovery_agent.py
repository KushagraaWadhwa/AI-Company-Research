"""
Company Discovery Agent
Finds company information and website URLs from just the company name.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse
from playwright.async_api import async_playwright
import httpx

logger = logging.getLogger(__name__)


class CompanyDiscoveryAgent:
    """Agent that discovers company information from just the company name."""
    
    def __init__(self):
        self.search_engines = [
            "google",
            "bing", 
            "duckduckgo"
        ]
        self.business_directories = [
            "crunchbase",
            "linkedin",
            "bloomberg",
            "reuters"
        ]
    
    async def discover_company(self, company_name: str, additional_info: Optional[str] = None) -> Dict:
        """
        Discover company information from just the name.
        
        Args:
            company_name: Name of the company to search for
            additional_info: Optional additional context (industry, location, etc.)
            
        Returns:
            Dict containing discovered company information
        """
        try:
            logger.info(f"🔍 Discovering company information for: {company_name}")
            
            # Step 1: Search for company across multiple sources
            search_results = await self._multi_source_search(company_name, additional_info)
            
            # Step 2: Extract and validate potential websites
            candidate_websites = await self._extract_candidate_websites(search_results)
            
            # Step 3: Validate and rank websites
            validated_websites = await self._validate_websites(candidate_websites, company_name)
            
            # Step 4: Extract comprehensive company information
            company_info = await self._extract_company_info(validated_websites, search_results, company_name)
            
            return {
                "status": "success",
                "company_name": company_name,
                "discovered_info": company_info,
                "confidence_score": self._calculate_confidence_score(company_info),
                "search_sources": len(search_results),
                "candidate_websites": len(candidate_websites),
                "validated_websites": len(validated_websites)
            }
            
        except Exception as e:
            logger.error(f"Company discovery failed for {company_name}: {e}")
            return {
                "status": "error",
                "company_name": company_name,
                "error": str(e)
            }
    
    async def _multi_source_search(self, company_name: str, additional_info: Optional[str]) -> Dict[str, Dict]:
        """Search for company across multiple sources."""
        search_results = {}
        
        # Prepare search queries
        base_query = company_name
        enhanced_query = f"{company_name} company startup"
        if additional_info:
            enhanced_query += f" {additional_info}"
        
        # Search tasks
        search_tasks = [
            self._google_search(base_query, enhanced_query),
            self._linkedin_search(company_name),
            self._crunchbase_search(company_name),
            self._business_directory_search(company_name),
            self._news_search(company_name)
        ]
        
        # Execute searches concurrently
        search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        source_names = ["google", "linkedin", "crunchbase", "business_directories", "news"]
        for i, result in enumerate(search_results_list):
            if not isinstance(result, Exception):
                search_results[source_names[i]] = result
            else:
                search_results[source_names[i]] = {"status": "error", "error": str(result)}
        
        return search_results
    
    async def _google_search(self, base_query: str, enhanced_query: str) -> Dict:
        """Search Google for company information."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set user agent
                await page.set_user_agent(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                
                # Search Google
                google_url = f"https://www.google.com/search?q={quote_plus(enhanced_query)}"
                await page.goto(google_url, timeout=15000)
                
                # Extract search results
                results = []
                
                # Get search result links and snippets
                search_items = await page.query_selector_all('div.g')
                
                for item in search_items[:10]:  # Top 10 results
                    try:
                        # Extract title
                        title_elem = await item.query_selector('h3')
                        title = await title_elem.text_content() if title_elem else ""
                        
                        # Extract URL
                        link_elem = await item.query_selector('a')
                        url = await link_elem.get_attribute('href') if link_elem else ""
                        
                        # Extract snippet
                        snippet_elem = await item.query_selector('.VwiC3b, .s3v9rd')
                        snippet = await snippet_elem.text_content() if snippet_elem else ""
                        
                        if url and title:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error extracting search result: {e}")
                        continue
                
                await browser.close()
                
                return {
                    "status": "success",
                    "results": results,
                    "total_results": len(results)
                }
                
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _linkedin_search(self, company_name: str) -> Dict:
        """Search LinkedIn for company."""
        try:
            # Try direct LinkedIn company URL
            company_slug = company_name.lower().replace(' ', '-').replace('.', '')
            linkedin_url = f"https://www.linkedin.com/company/{company_slug}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(linkedin_url, timeout=15000)
                
                # Check if page exists (not 404)
                title = await page.title()
                if "404" not in title and "not found" not in title.lower():
                    # Extract basic company info
                    company_info = await self._extract_linkedin_basic_info(page)
                    await browser.close()
                    
                    return {
                        "status": "success",
                        "url": linkedin_url,
                        "info": company_info
                    }
                else:
                    await browser.close()
                    return {"status": "not_found"}
                    
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _crunchbase_search(self, company_name: str) -> Dict:
        """Search Crunchbase for company."""
        try:
            company_slug = company_name.lower().replace(' ', '-').replace('.', '')
            crunchbase_url = f"https://www.crunchbase.com/organization/{company_slug}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(crunchbase_url, timeout=15000)
                
                title = await page.title()
                if "404" not in title and company_name.lower() in title.lower():
                    # Extract basic info
                    info = await self._extract_crunchbase_basic_info(page)
                    await browser.close()
                    
                    return {
                        "status": "success",
                        "url": crunchbase_url,
                        "info": info
                    }
                else:
                    await browser.close()
                    return {"status": "not_found"}
                    
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _business_directory_search(self, company_name: str) -> Dict:
        """Search business directories."""
        # Implementation for other business directories
        return {"status": "not_implemented"}
    
    async def _news_search(self, company_name: str) -> Dict:
        """Search news sources for company mentions."""
        try:
            news_query = f"{company_name} company news"
            google_news_url = f"https://news.google.com/search?q={quote_plus(news_query)}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(google_news_url, timeout=15000)
                
                # Extract news results
                news_items = await page.query_selector_all('article')
                news_results = []
                
                for item in news_items[:5]:  # Top 5 news items
                    try:
                        title_elem = await item.query_selector('h3, h4')
                        title = await title_elem.text_content() if title_elem else ""
                        
                        link_elem = await item.query_selector('a')
                        url = await link_elem.get_attribute('href') if link_elem else ""
                        
                        if title and url:
                            news_results.append({
                                "title": title,
                                "url": url
                            })
                            
                    except Exception:
                        continue
                
                await browser.close()
                
                return {
                    "status": "success",
                    "results": news_results
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _extract_candidate_websites(self, search_results: Dict) -> List[Dict]:
        """Extract potential company websites from search results."""
        candidates = []
        seen_domains = set()
        
        for source, results in search_results.items():
            if results.get("status") == "success":
                if source == "google" and "results" in results:
                    for result in results["results"]:
                        url = result.get("url", "")
                        if url and self._is_potential_company_website(url):
                            domain = self._extract_domain(url)
                            if domain and domain not in seen_domains:
                                candidates.append({
                                    "url": url,
                                    "domain": domain,
                                    "title": result.get("title", ""),
                                    "snippet": result.get("snippet", ""),
                                    "source": source,
                                    "confidence": self._calculate_url_confidence(url, result)
                                })
                                seen_domains.add(domain)
                
                elif source in ["linkedin", "crunchbase"] and results.get("url"):
                    # Extract website from LinkedIn/Crunchbase if found
                    if "info" in results:
                        website = results["info"].get("website")
                        if website:
                            domain = self._extract_domain(website)
                            if domain and domain not in seen_domains:
                                candidates.append({
                                    "url": website,
                                    "domain": domain,
                                    "title": f"From {source}",
                                    "snippet": f"Website found on {source}",
                                    "source": source,
                                    "confidence": 0.9  # High confidence from business directories
                                })
                                seen_domains.add(domain)
        
        # Sort by confidence score
        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        
        return candidates
    
    def _is_potential_company_website(self, url: str) -> bool:
        """Check if URL is likely a company website."""
        if not url:
            return False
        
        # Skip social media, directories, and other non-company sites
        skip_domains = [
            'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'crunchbase.com', 'angel.co', 'glassdoor.com', 'indeed.com',
            'wikipedia.org', 'youtube.com', 'google.com', 'bing.com',
            'bloomberg.com', 'reuters.com', 'techcrunch.com', 'forbes.com'
        ]
        
        for skip_domain in skip_domains:
            if skip_domain in url.lower():
                return False
        
        # Check for common company website patterns
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Skip if it's clearly not a main company website
        if any(subdomain in domain for subdomain in ['blog.', 'news.', 'support.', 'help.', 'docs.']):
            return False
        
        return True
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract clean domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return None
    
    def _calculate_url_confidence(self, url: str, result: Dict) -> float:
        """Calculate confidence score for a potential company website."""
        confidence = 0.5  # Base confidence
        
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        # Increase confidence for official-looking titles
        if any(word in title for word in ["official", "home", "website"]):
            confidence += 0.2
        
        # Increase confidence for business-related snippets
        business_keywords = ["company", "business", "startup", "founded", "services", "products"]
        if any(keyword in snippet for keyword in business_keywords):
            confidence += 0.1
        
        # Decrease confidence for blog posts, news articles
        if any(word in title for word in ["blog", "news", "article", "post"]):
            confidence -= 0.2
        
        # Increase confidence for .com domains
        if url.endswith('.com'):
            confidence += 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    async def _validate_websites(self, candidates: List[Dict], company_name: str) -> List[Dict]:
        """Validate candidate websites by visiting them."""
        validated = []
        
        for candidate in candidates[:5]:  # Validate top 5 candidates
            try:
                validation_result = await self._validate_single_website(candidate, company_name)
                if validation_result["is_valid"]:
                    candidate.update(validation_result)
                    validated.append(candidate)
                    
            except Exception as e:
                logger.warning(f"Failed to validate {candidate['url']}: {e}")
                continue
        
        return validated
    
    async def _validate_single_website(self, candidate: Dict, company_name: str) -> Dict:
        """Validate a single website candidate."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                url = candidate["url"]
                await page.goto(url, timeout=10000)
                
                # Get page content
                title = await page.title()
                content = await page.text_content('body')
                
                await browser.close()
                
                # Check if company name appears on the page
                company_mentions = 0
                if content:
                    content_lower = content.lower()
                    company_lower = company_name.lower()
                    
                    # Count mentions of company name
                    company_mentions = content_lower.count(company_lower)
                    
                    # Check for company-like content
                    company_indicators = [
                        "about us", "our mission", "contact us", "our team",
                        "services", "products", "solutions", "founded"
                    ]
                    
                    indicator_count = sum(1 for indicator in company_indicators if indicator in content_lower)
                
                # Calculate validation score
                validation_score = 0.0
                
                if company_mentions > 0:
                    validation_score += min(company_mentions * 0.1, 0.5)
                
                if company_name.lower() in title.lower():
                    validation_score += 0.3
                
                if indicator_count >= 3:
                    validation_score += 0.2
                
                is_valid = validation_score >= 0.3
                
                return {
                    "is_valid": is_valid,
                    "validation_score": validation_score,
                    "company_mentions": company_mentions,
                    "page_title": title,
                    "content_preview": content[:500] if content else ""
                }
                
        except Exception as e:
            return {
                "is_valid": False,
                "validation_error": str(e)
            }
    
    async def _extract_company_info(self, validated_websites: List[Dict], search_results: Dict, company_name: str) -> Dict:
        """Extract comprehensive company information from all sources."""
        company_info = {
            "company_name": company_name,
            "primary_website": None,
            "alternative_websites": [],
            "social_profiles": {},
            "business_profiles": {},
            "basic_info": {}
        }
        
        # Set primary website (highest confidence validated website)
        if validated_websites:
            primary = validated_websites[0]
            company_info["primary_website"] = primary["url"]
            
            if len(validated_websites) > 1:
                company_info["alternative_websites"] = [
                    site["url"] for site in validated_websites[1:]
                ]
        
        # Extract LinkedIn info
        if search_results.get("linkedin", {}).get("status") == "success":
            linkedin_info = search_results["linkedin"]
            company_info["social_profiles"]["linkedin"] = linkedin_info["url"]
            if "info" in linkedin_info:
                company_info["basic_info"].update(linkedin_info["info"])
        
        # Extract Crunchbase info
        if search_results.get("crunchbase", {}).get("status") == "success":
            crunchbase_info = search_results["crunchbase"]
            company_info["business_profiles"]["crunchbase"] = crunchbase_info["url"]
            if "info" in crunchbase_info:
                company_info["basic_info"].update(crunchbase_info["info"])
        
        return company_info
    
    def _calculate_confidence_score(self, company_info: Dict) -> float:
        """Calculate overall confidence score for discovered information."""
        score = 0.0
        
        if company_info.get("primary_website"):
            score += 0.4
        
        if company_info.get("social_profiles"):
            score += 0.2
        
        if company_info.get("business_profiles"):
            score += 0.2
        
        if company_info.get("basic_info"):
            score += 0.2
        
        return round(score, 2)
    
    async def _extract_linkedin_basic_info(self, page) -> Dict:
        """Extract basic info from LinkedIn page."""
        info = {}
        try:
            # Try to extract website
            website_elem = await page.query_selector('a[href*="http"]:has-text("Website")')
            if website_elem:
                website = await website_elem.get_attribute('href')
                info["website"] = website
            
            # Try to extract description
            desc_elem = await page.query_selector('.org-about-us-organization-description__text')
            if desc_elem:
                description = await desc_elem.text_content()
                info["description"] = description[:500]
        except:
            pass
        
        return info
    
    async def _extract_crunchbase_basic_info(self, page) -> Dict:
        """Extract basic info from Crunchbase page."""
        info = {}
        try:
            # Try to extract website
            website_elem = await page.query_selector('a[data-test="company-website"]')
            if website_elem:
                website = await website_elem.get_attribute('href')
                info["website"] = website
        except:
            pass
        
        return info
