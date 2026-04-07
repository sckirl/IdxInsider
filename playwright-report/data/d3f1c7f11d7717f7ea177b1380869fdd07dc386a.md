# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: scraper-accuracy.spec.ts >> Scraper Integration: Database matches TEST_CASES.json
- Location: tests/scraper-accuracy.spec.ts:8:5

# Error details

```
Error: apiRequestContext.get: connect ECONNREFUSED ::1:8000
Call log:
  - → GET http://localhost:8000/insider/latest
    - user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.15 Safari/537.36
    - accept: */*
    - accept-encoding: gzip,deflate,br

```