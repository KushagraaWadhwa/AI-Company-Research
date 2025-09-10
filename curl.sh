curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"company_name": "OpenAI", "company_url": "https://openai.com", "analysis_type": "standard"}'


curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Stripe", "company_url": "https://stripe.com", "analysis_type": "comprehensive"}'


curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Tesla", "company_url": "https://tesla.com", "analysis_type": "universal"}'

curl http://localhost:8000/api/v1/status/"Task Id" | jq '.'

curl http://localhost:8000/api/v1/status/"5e6016b9-9a4b-49fa-928d-e9c0bb6f24da" | jq '.'