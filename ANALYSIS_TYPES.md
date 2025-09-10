# 🔍 Analysis Types Guide

The AI Startup Copilot supports three distinct analysis types, each offering different levels of depth and data coverage.

## 📊 Analysis Types Overview

| Type | Agent | Data Sources | Processing Time | Use Case |
|------|-------|--------------|-----------------|----------|
| **Standard** | `CompanyProfileAgent` | Primary website | ~30-60s | Quick company overview |
| **Comprehensive** | `MultiSourceAnalysisAgent` | Multiple web sources | ~2-5 mins | Detailed analysis |
| **Universal** | `UniversalDataAgent` | 50+ data sources | ~5-15 mins | Complete intelligence |

## 🚀 Standard Analysis

**Agent**: `CompanyProfileAgent`  
**Processing Steps**: 6  
**Ideal for**: Quick company overviews, basic due diligence

### Data Sources
- Company website (primary)
- Website metadata and structure
- Basic web scraping of key pages

### What You Get
- Company mission and value proposition
- Basic business model analysis
- Key insights from website content
- Website technical analysis
- Core company information

### Example Use Cases
- Initial company research
- Quick competitive analysis
- Basic investment screening
- Simple company profiling

### API Request
```json
{
  "company_name": "OpenAI",
  "company_url": "https://openai.com",
  "analysis_type": "standard"
}
```

## 📈 Comprehensive Analysis

**Agent**: `MultiSourceAnalysisAgent`  
**Processing Steps**: 6-8  
**Ideal for**: Thorough research, investment analysis

### Data Sources
- Company website (primary)
- News articles and press releases
- Social media presence
- Industry publications
- Additional web sources
- Enhanced content analysis

### What You Get
- Everything from Standard analysis
- Market positioning analysis
- Recent news and developments
- Social media insights
- Industry context and trends
- Competitive landscape overview

### Example Use Cases
- Investment due diligence
- Market research
- Competitive intelligence
- Partnership evaluation
- Detailed company assessment

### API Request
```json
{
  "company_name": "Stripe",
  "company_url": "https://stripe.com",
  "analysis_type": "comprehensive",
  "additional_info": "fintech payment processing"
}
```

## 🌐 Universal Analysis

**Agent**: `UniversalDataAgent`  
**Processing Steps**: 8-10  
**Ideal for**: Complete intelligence, strategic analysis

### Data Sources (50+ Sources)

#### Financial & Investment
- Crunchbase
- PitchBook
- AngelList
- SEC filings
- Funding databases

#### Professional & Social
- LinkedIn (company & employees)
- Twitter/X presence
- Facebook business pages
- Instagram business accounts
- YouTube channels

#### News & Media
- Google News
- Industry publications
- Press release services
- Blog mentions
- Podcast appearances

#### Technical & Development
- GitHub repositories
- Stack Overflow mentions
- Technical documentation
- Developer communities
- Open source contributions

#### Market & Industry
- Industry reports
- Market research
- Competitor analysis
- Patent databases
- Regulatory filings

#### Review & Reputation
- Glassdoor reviews
- Trustpilot ratings
- Better Business Bureau
- Customer testimonials
- Case studies

### What You Get
- Everything from Comprehensive analysis
- Complete funding history
- Team and leadership analysis
- Technology stack assessment
- Market position and competition
- Financial health indicators
- Growth trajectory analysis
- Risk assessment
- Strategic recommendations
- Comprehensive SWOT analysis

### Example Use Cases
- Strategic investment decisions
- M&A due diligence
- Complete market intelligence
- Risk assessment
- Strategic partnership evaluation
- Comprehensive competitive analysis

### API Request
```json
{
  "company_name": "Tesla",
  "company_url": "https://tesla.com",
  "analysis_type": "universal",
  "additional_info": "Electric vehicle and clean energy company"
}
```

## ⚡ Performance Comparison

### Processing Time
- **Standard**: 30-60 seconds
- **Comprehensive**: 2-5 minutes  
- **Universal**: 5-15 minutes

### Data Volume
- **Standard**: ~1-5 web pages
- **Comprehensive**: ~10-20 sources
- **Universal**: ~50-100+ sources

### Analysis Depth
- **Standard**: Basic company profile
- **Comprehensive**: Enhanced with market context
- **Universal**: Complete business intelligence

## 🎯 Choosing the Right Analysis Type

### Use Standard When:
- You need quick results
- Basic company information is sufficient
- You're doing initial screening
- Time is a constraint
- You're analyzing many companies quickly

### Use Comprehensive When:
- You need detailed analysis
- Market context is important
- You're evaluating partnerships
- You need competitive insights
- You have 2-5 minutes to wait

### Use Universal When:
- You need complete intelligence
- Making significant investments
- Conducting M&A due diligence
- Performing strategic analysis
- Time is less important than thoroughness

## 📋 Output Differences

### Standard Output Structure
```json
{
  "summary": "Executive summary",
  "mission": "Company mission",
  "value_proposition": "Value proposition",
  "business_model": "Business model",
  "key_insights": ["insight1", "insight2"],
  "website_analysis": {...}
}
```

### Comprehensive Output Structure
```json
{
  // All Standard fields plus:
  "market_analysis": "Market positioning",
  "news_insights": [...],
  "social_presence": {...},
  "industry_context": "Industry analysis",
  "competitive_landscape": [...]
}
```

### Universal Output Structure
```json
{
  // All Comprehensive fields plus:
  "funding_history": [...],
  "team_analysis": {...},
  "technology_stack": [...],
  "financial_health": {...},
  "growth_metrics": {...},
  "risk_assessment": {...},
  "strategic_recommendations": [...],
  "swot_analysis": {...}
}
```

## 🔧 Technical Implementation

### Agent Architecture
```python
# Standard Analysis
CompanyProfileAgent()
├── Web scraping (Playwright)
├── Content analysis (BeautifulSoup)
└── AI analysis (Ollama LLM)

# Comprehensive Analysis  
MultiSourceAnalysisAgent(CompanyProfileAgent)
├── Inherits standard capabilities
├── Multi-source data collection
├── Enhanced content aggregation
└── Cross-source analysis

# Universal Analysis
UniversalDataAgent(CompanyProfileAgent)
├── Inherits standard capabilities
├── 50+ data source integration
├── Concurrent data collection
├── Advanced data correlation
└── Comprehensive intelligence synthesis
```

### Processing Pipeline
1. **Input Validation**: Validate company name and URL
2. **Agent Selection**: Choose agent based on analysis_type
3. **Data Collection**: Gather data from appropriate sources
4. **Content Processing**: Clean and structure raw data
5. **AI Analysis**: Generate insights using LLM
6. **Vector Embedding**: Create searchable embeddings
7. **Storage**: Save results to MongoDB
8. **Response**: Return analysis results

## 🚨 Rate Limits & Considerations

### Standard Analysis
- No significant rate limits
- Fast and reliable
- Minimal external API usage

### Comprehensive Analysis
- Moderate external API usage
- Some rate limiting possible
- Generally reliable

### Universal Analysis
- Heavy external API usage
- Rate limiting likely
- May encounter source unavailability
- Longest processing time
- Highest resource usage

## 📈 Future Enhancements

### Planned Features
- **Real-time Analysis**: Live data updates
- **Custom Sources**: User-defined data sources
- **Industry-Specific**: Specialized analysis for different sectors
- **Historical Tracking**: Track changes over time
- **Comparison Mode**: Side-by-side company comparisons

### API Improvements
- **Streaming Results**: Real-time progress updates
- **Partial Results**: Get results as they're processed
- **Caching**: Intelligent result caching
- **Batch Processing**: Analyze multiple companies

## 🔍 Monitoring & Debugging

### Task Monitoring
```bash
# Check task status
curl http://localhost:8000/api/v1/status/{task_id}

# Monitor progress
watch -n 5 "curl -s http://localhost:8000/api/v1/status/{task_id} | jq '.progress'"
```

### Log Analysis
- Standard: Look for `CompanyProfileAgent` logs
- Comprehensive: Look for `MultiSourceAnalysisAgent` logs  
- Universal: Look for `UniversalDataAgent` logs

### Common Issues
- **Timeouts**: Universal analysis may timeout on slow networks
- **Rate Limits**: Universal analysis may hit API limits
- **Source Unavailability**: Some sources may be temporarily unavailable
- **Data Quality**: More sources = more potential data quality issues

## 🎯 Best Practices

### For Developers
- Use Standard for batch processing
- Use Comprehensive for user-facing analysis
- Use Universal for high-value decisions
- Implement proper error handling
- Monitor rate limits

### For Users
- Start with Standard to understand the company
- Use Comprehensive for important decisions
- Use Universal for critical analysis
- Be patient with Universal analysis
- Check task status regularly

---

*This guide covers all three analysis types available in the AI Startup Copilot. Each type is designed for different use cases and offers varying levels of depth and insight.*
