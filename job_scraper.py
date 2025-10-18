name: Run job scraper (every 30 min)

on:
  schedule:
    - cron: "*/30 * * * *"    # UTC, every 30 minutes
  workflow_dispatch:          # manual runs

concurrency:
  group: job-scraper
  cancel-in-progress: true

jobs:
  scrape:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install deps
        run: pip install requests

      - name: Verify WP auth
        env:
          WP_BASE_URL: https://techjobs360.com
          WP_USER: ${{ secrets.WP_USER }}
          WP_APP_PASSWORD: "${{ secrets.WP_APP_PASSWORD }}"
        run: |
          CODE=$(curl -s -o /dev/null -w "%{http_code}" \
                 -u "${WP_USER}:${WP_APP_PASSWORD}" \
                 "${WP_BASE_URL}/wp-json/wp/v2/users/me")
          [ "$CODE" = "200" ] && echo "✅ Auth OK" || (echo "❌ Auth failed ($CODE)"; exit 1)

      - name: Run job_scraper.py
        env:
          WP_BASE_URL: https://techjobs360.com
          WP_USER: ${{ secrets.WP_USER }}
          WP_APP_PASSWORD: "${{ secrets.WP_APP_PASSWORD }}"
          # JSearch
          JSEARCH_API_KEY: ${{ secrets.JSEARCH_API_KEY }}
          JSEARCH_HOST: jsearch.p.rapidapi.com
          JSEARCH_QUERY: "software developer OR data engineer"
          JSEARCH_NUM_PAGES: "2"
          # Adzuna (optional)
          ADZUNA_APP_ID: ${{ secrets.ADZUNA_APP_ID }}
          ADZUNA_APP_KEY: ${{ secrets.ADZUNA_APP_KEY }}
          COUNTRIES: "in,us,fr,gb,de"
          ADZUNA_WHAT: "software OR developer OR engineer"
          ADZUNA_MAX_DAYS_OLD: "3"
          ADZUNA_RESULTS_PER_PAGE: "20"
        run: python job_scraper.py

      - name: Print latest WP job_listings
        run: |
          echo "Latest 5 job_listings:"
          curl -s "https://techjobs360.com/wp-json/wp/v2/job-listings?per_page=5" | python - <<'PY'
import sys, json
data=json.load(sys.stdin)
if not data:
    print("No job_listings returned ([]). If you expected new posts, check previous step.")
else:
    for j in data:
        print(f"- {j.get('id')} | {j.get('title',{}).get('rendered')} | {j.get('link')}")
PY
