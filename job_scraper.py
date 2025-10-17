import requests
import json
import time
import hashlib
from datetime import datetime
import os

class JobScraper:
    
    def __init__(self):
        # WordPress credentials from environment variables
        self.wp_url = os.getenv('WP_URL', 'https://techjobs360.com')
        self.wp_user = os.getenv('WP_USERNAME')
        self.wp_password = os.getenv('WP_APP_PASSWORD')
        
        # API Keys from environment variables
        self.adzuna_app_id = '6e27536a'
        self.adzuna_api_key = '4e216b84d2a29d5a815a765fde36ad61'
        self.jsearch_api_key = os.getenv('JSEARCH_API_KEY')
        
        # Track posted jobs to avoid duplicates
        self.posted_jobs_file = 'posted_jobs.json'
        self.posted_jobs = self.load_posted_jobs()
        
        # Countries to scrape jobs from
        self.countries = ['in', 'us', 'fr', 'gb', 'de']  # India, USA, France, UK, Germany
    
    def load_posted_jobs(self):
        """Load previously posted job IDs"""
        try:
            with open(self.posted_jobs_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_posted_jobs(self):
        """Save posted job IDs"""
        with open(self.posted_jobs_file, 'w') as f:
            json.dump(self.posted_jobs[-1000:], f)  # Keep last 1000 jobs
    
    def generate_job_id(self, job_title, company, location):
        """Generate unique ID for job"""
        unique_string = f"{job_title}_{company}_{location}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def is_job_posted(self, job_id):
        """Check if job already posted"""
        return job_id in self.posted_jobs
    
    def mark_job_posted(self, job_id):
        """Mark job as posted"""
        self.posted_jobs.append(job_id)
        self.save_posted_jobs()
    
    def fetch_adzuna_jobs(self, location='in', results_per_page=10):
        """Fetch jobs from Adzuna API
        
        Location codes:
        - India: 'in'
        - USA: 'us'
        - UK: 'gb'
        - Germany: 'de'
        - France: 'fr'
        """
        url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/1"
        params = {
            'app_id': self.adzuna_app_id,
            'app_key': self.adzuna_api_key,
            'results_per_page': results_per_page,
            'what': 'software developer',
            'content-type': 'application/json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            print(f"Error fetching Adzuna jobs for {location}: {e}")
            return []
    
    def fetch_jsearch_jobs(self, query='software developer', num_pages=1):
        """Fetch jobs from JSearch API (RapidAPI)"""
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            'X-RapidAPI-Key': self.jsearch_api_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }
        params = {
            'query': query,
            'page': '1',
            'num_pages': str(num_pages),
            'date_posted': 'today'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            print(f"Error fetching JSearch jobs: {e}")
            return []
    
    def post_to_wordpress(self, job_data):
        """Post job to WordPress"""
        endpoint = f"{self.wp_url}/wp-json/wp/v2/job-listings"
        
        # Create post content
        content = f"""
        Company: {job_data.get('company', 'N/A')}
        Location: {job_data.get('location', 'N/A')}
        Description: {job_data.get('description', 'No description available')}
        """
        
        if job_data.get('redirect_url'):
            content += f"<p>Apply: <a href=\"{job_data.get('redirect_url')}\" target=\"_blank\">Click here to apply</a></p>"
        
        post_data = {
            'title': job_data.get('title', 'Job Opportunity'),
            'content': content,
            'status': 'publish',
            'categories': [1]  # Update with your category ID
        }
        
        try:
            response = requests.post(
                endpoint,
                json=post_data,
                auth=(self.wp_user, self.wp_password),
                timeout=30
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error posting to WordPress: {e}")
            return False
    
    def process_adzuna_job(self, job):
        """Process and format Adzuna job"""
        return {
            'title': job.get('title', 'N/A'),
            'company': job.get('company', {}).get('display_name', 'N/A'),
            'location': job.get('location', {}).get('display_name', 'N/A'),
            'description': job.get('description', 'No description available'),
            'redirect_url': job.get('redirect_url', '')
        }
    
    def process_jsearch_job(self, job):
        """Process and format JSearch job"""
        return {
            'title': job.get('job_title', 'N/A'),
            'company': job.get('employer_name', 'N/A'),
            'location': job.get('job_city', 'N/A') + ', ' + job.get('job_country', 'N/A'),
            'description': job.get('job_description', 'No description available'),
            'redirect_url': job.get('job_apply_link', '')
        }
    
    def run(self):
        """Main execution method"""
        print("Starting job scraper...")
        print(f"Fetching jobs from countries: {', '.join(self.countries)}")
        
        posted_count = 0
        
        # Fetch jobs from Adzuna for all countries
        for country in self.countries:
            print(f"\nFetching jobs from Adzuna for country: {country}")
            adzuna_jobs = self.fetch_adzuna_jobs(location=country)
            print(f"Fetched {len(adzuna_jobs)} jobs from Adzuna ({country})")
            
            # Process Adzuna jobs for this country
            for job in adzuna_jobs:
                processed_job = self.process_adzuna_job(job)
                job_id = self.generate_job_id(
                    processed_job['title'],
                    processed_job['company'],
                    processed_job['location']
                )
                
                if not self.is_job_posted(job_id):
                    if self.post_to_wordpress(processed_job):
                        self.mark_job_posted(job_id)
                        posted_count += 1
                        print(f"Posted: {processed_job['title']} at {processed_job['company']} - {processed_job['location']}")
                        time.sleep(2)  # Rate limiting
            
            # Add delay between country requests
            time.sleep(3)
        
        # Fetch jobs from JSearch (global)
        print(f"\nFetching jobs from JSearch...")
        jsearch_jobs = self.fetch_jsearch_jobs()
        print(f"Fetched {len(jsearch_jobs)} jobs from JSearch")
        
        # Process JSearch jobs
        for job in jsearch_jobs:
            processed_job = self.process_jsearch_job(job)
            job_id = self.generate_job_id(
                processed_job['title'],
                processed_job['company'],
                processed_job['location']
            )
            
            if not self.is_job_posted(job_id):
                if self.post_to_wordpress(processed_job):
                    self.mark_job_posted(job_id)
                    posted_count += 1
                    print(f"Posted: {processed_job['title']} at {processed_job['company']}")
                    time.sleep(2)  # Rate limiting
        
        print(f"\nTotal jobs posted: {posted_count}")

if __name__ == '__main__':
    scraper = JobScraper()
    scraper.run()
