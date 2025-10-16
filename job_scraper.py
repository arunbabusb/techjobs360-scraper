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
        self.adzuna_app_id = os.getenv('ADZUNA_APP_ID')
        self.adzuna_api_key = os.getenv('ADZUNA_API_KEY')
        self.jsearch_api_key = os.getenv('JSEARCH_API_KEY')
        
        # Track posted jobs to avoid duplicates
        self.posted_jobs_file = 'posted_jobs.json'
        self.posted_jobs = self.load_posted_jobs()
    
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
    
    def generate_job_id(self, job):
        """Generate unique ID for job to prevent duplicates"""
        unique_string = f"{job['title']}{job['company']}{job['location']}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def fetch_adzuna_jobs(self, country='in', query='software engineer', location=''):
        """Fetch jobs from Adzuna API - FREE tier 1000 calls/month"""
        if not self.adzuna_app_id or not self.adzuna_api_key:
            print("⚠️ Adzuna API credentials not set")
            return []
        
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            'app_id': self.adzuna_app_id,
            'app_key': self.adzuna_api_key,
            'results_per_page': 20,
            'what': query,
            'where': location,
            'sort_by': 'date'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data.get('results', []):
                jobs.append({
                    'title': job.get('title', 'No Title'),
                    'company': job.get('company', {}).get('display_name', 'Unknown Company'),
                    'location': job.get('location', {}).get('display_name', location),
                    'description': job.get('description', ''),
                    'url': job.get('redirect_url', ''),
                    'salary': job.get('salary_max', ''),
                    'posted_date': job.get('created', ''),
                    'source': 'Adzuna'
                })
            
            print(f"✅ Fetched {len(jobs)} jobs from Adzuna ({country})")
            return jobs
        
        except Exception as e:
            print(f"❌ Error fetching Adzuna jobs: {e}")
            return []
    
    def fetch_remotive_jobs(self):
        """Fetch remote jobs from Remotive API - 100% FREE"""
        url = "https://remotive.com/api/remote-jobs"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data.get('jobs', [])[:20]:  # Get latest 20
                # Filter for tech/engineering jobs
                if 'software' in job.get('category', '').lower() or \
                   'dev' in job.get('category', '').lower() or \
                   'engineer' in job.get('title', '').lower():
                    
                    jobs.append({
                        'title': job.get('title', 'No Title'),
                        'company': job.get('company_name', 'Unknown Company'),
                        'location': 'Remote',
                        'description': job.get('description', ''),
                        'url': job.get('url', ''),
                        'salary': job.get('salary', ''),
                        'posted_date': job.get('publication_date', ''),
                        'source': 'Remotive'
                    })
            
            print(f"✅ Fetched {len(jobs)} remote jobs from Remotive")
            return jobs
        
        except Exception as e:
            print(f"❌ Error fetching Remotive jobs: {e}")
            return []
    
    def fetch_arbeitnow_jobs(self):
        """Fetch jobs from Arbeitnow API - 100% FREE"""
        url = "https://www.arbeitnow.com/api/job-board-api"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data.get('data', [])[:20]:
                jobs.append({
                    'title': job.get('title', 'No Title'),
                    'company': job.get('company_name', 'Unknown Company'),
                    'location': job.get('location', 'Remote'),
                    'description': job.get('description', ''),
                    'url': job.get('url', ''),
                    'salary': '',
                    'posted_date': job.get('created_at', ''),
                    'source': 'Arbeitnow'
                })
            
            print(f"✅ Fetched {len(jobs)} jobs from Arbeitnow")
            return jobs
        
        except Exception as e:
            print(f"❌ Error fetching Arbeitnow jobs: {e}")
            return []
    
    def post_to_wordpress(self, job):
        """Post job to WordPress via REST API"""
        if not self.wp_user or not self.wp_password:
            print("⚠️ WordPress credentials not set")
            return False
        
        # Check if already posted
        job_id = self.generate_job_id(job)
        if job_id in self.posted_jobs:
            print(f"⏭️ Skipping duplicate: {job['title']} at {job['company']}")
            return False
        
        # Prepare post content
        content = f"""
        <div class="job-listing">
            <h2>{job['title']}</h2>
            <p><strong>Company:</strong> {job['company']}</p>
            <p><strong>Location:</strong> {job['location']}</p>
            {f"<p><strong>Salary:</strong> {job['salary']}</p>" if job['salary'] else ''}
            <div class="job-description">
                {job['description'][:500]}...
            </div>
            <p><a href="{job['url']}" target="_blank" class="apply-button">Apply Now</a></p>
            <p class="job-meta">Source: {job['source']} | Posted: {job['posted_date']}</p>
        </div>
        """
        
        # Create WordPress post
        post_data = {
            'title': f"{job['title']} - {job['company']}",
            'content': content,
            'status': 'publish',
            'categories': [1],  # Adjust category ID as needed
            'tags': [job['location'], job['company'], 'tech-jobs'],
            'meta': {
                'job_location': job['location'],
                'job_company': job['company'],
                'job_url': job['url'],
                'job_source': job['source']
            }
        }
        
        try:
            response = requests.post(
                f"{self.wp_url}/wp-json/wp/v2/posts",
                json=post_data,
                auth=(self.wp_user, self.wp_password),
                timeout=10
            )
            
            if response.status_code == 201:
                self.posted_jobs.append(job_id)
                print(f"✅ Posted: {job['title']} at {job['company']}")
                return True
            else:
                print(f"❌ Failed to post: {response.status_code} - {response.text[:200]}")
                return False
        
        except Exception as e:
            print(f"❌ Error posting to WordPress: {e}")
            return False
    
    def run(self):
        """Main execution function"""
        print(f"\n🚀 Starting job scraping at {datetime.now()}")
        print("=" * 60)
        
        all_jobs = []
        
        # Fetch from multiple sources
        print("\n📥 Fetching jobs from APIs...")
        
        # India jobs
        all_jobs.extend(self.fetch_adzuna_jobs(country='in', query='software engineer', location='Bangalore'))
        all_jobs.extend(self.fetch_adzuna_jobs(country='in', query='data engineer', location='Hyderabad'))
        
        # USA jobs
        all_jobs.extend(self.fetch_adzuna_jobs(country='us', query='software engineer', location='San Francisco'))
        all_jobs.extend(self.fetch_adzuna_jobs(country='us', query='python developer', location='Austin'))
        
        # Remote jobs (free APIs)
        all_jobs.extend(self.fetch_remotive_jobs())
        all_jobs.extend(self.fetch_arbeitnow_jobs())
        
        print(f"\n📊 Total jobs fetched: {len(all_jobs)}")
        
        # Post to WordPress
        print("\n📤 Posting jobs to WordPress...")
        posted_count = 0
        
        for job in all_jobs:
            if self.post_to_wordpress(job):
                posted_count += 1
                time.sleep(2)  # Rate limiting - be nice to WordPress
        
        # Save posted jobs list
        self.save_posted_jobs()
        
        print("\n" + "=" * 60)
        print(f"✨ Completed! Posted {posted_count} new jobs")
        print(f"⏰ Next run in 30 minutes")
        print("=" * 60)

if __name__ == "__main__":
    scraper = JobScraper()
    scraper.run()
