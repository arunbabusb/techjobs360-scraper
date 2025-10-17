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
    
    def fetch_adzuna_jobs(self, location='india', results_per_page=10):
        """Fetch jobs from Adzuna API"""
        url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/1"
        params = {
            'app_id': self.adzuna_app_id,
            'app_key': self.adzuna_api_key,
            'results_per_page': results_per_page,
            'what': 'technology OR software OR IT',
            'content-type': 'application/json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data.get('results', []):
                jobs.append({
                    'title': job.get('title', 'Untitled'),
                    'company': job.get('company', {}).get('display_name', 'Unknown'),
                    'location': job.get('location', {}).get('display_name', 'Unknown'),
                    'description': job.get('description', ''),
                    'url': job.get('redirect_url', ''),
                    'source': 'Adzuna'
                })
            
            return jobs
            
        except Exception as e:
            print(f"Error fetching Adzuna jobs: {e}")
            return []
    
    def fetch_jsearch_jobs(self, query='technology', location='India', num_pages=1):
        """Fetch jobs from JSearch API"""
        if not self.jsearch_api_key:
            print("JSearch API key not found. Skipping JSearch.")
            return []
        
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            'X-RapidAPI-Key': self.jsearch_api_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }
        
        jobs = []
        for page in range(1, num_pages + 1):
            params = {
                'query': f"{query} in {location}",
                'page': str(page),
                'num_pages': '1'
            }
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for job in data.get('data', []):
                    jobs.append({
                        'title': job.get('job_title', 'Untitled'),
                        'company': job.get('employer_name', 'Unknown'),
                        'location': job.get('job_city', 'Unknown'),
                        'description': job.get('job_description', ''),
                        'url': job.get('job_apply_link', ''),
                        'source': 'JSearch'
                    })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching JSearch jobs (page {page}): {e}")
        
        return jobs
    
    def get_or_create_tag(self, tag_name):
        """Get existing tag ID or create new tag"""
        tags_url = f"{self.wp_url}/wp-json/wp/v2/tags"
        
        # Search for existing tag
        try:
            response = requests.get(
                tags_url,
                params={'search': tag_name},
                auth=(self.wp_user, self.wp_password),
                timeout=10
            )
            tags = response.json()
            if tags and len(tags) > 0:
                return tags[0]['id']
        except:
            pass
        
        # Create new tag if not found
        try:
            response = requests.post(
                tags_url,
                json={'name': tag_name},
                auth=(self.wp_user, self.wp_password),
                timeout=10
            )
            if response.status_code == 201:
                return response.json()['id']
        except:
            pass
        
        return None
    
    def post_to_wordpress(self, job):
        """Post job to WordPress using WP Job Manager endpoint"""
        # Generate unique job ID
        job_id = self.generate_job_id(job['title'], job['company'], job['location'])
        
        # Check if already posted
        if self.is_job_posted(job_id):
            print(f"Skipping duplicate: {job['title']}")
            return False
        
        # Get or create tags
        tag_ids = []
        tags = [job['source'], 'Technology', job['location'].split(',')[0]]
        for tag in tags:
            tag_id = self.get_or_create_tag(tag)
            if tag_id:
                tag_ids.append(tag_id)
        
        # Prepare API endpoint for WP Job Manager
        post_url = f"{self.wp_url}/wp-json/wp/v2/job-listings"
        
        # Prepare post data for WP Job Manager
        post_data = {
            'title': job['title'],
            'content': job['description'],
            'company_name': job['company'],
            'job_location': job['location'],
            'application': job['url'],
            'status': 'publish',
            'tags': tag_ids,
            'categories': [1]  # Default category
        }
        
        try:
            response = requests.post(
                post_url,
                json=post_data,
                auth=(self.wp_user, self.wp_password),
                timeout=30
            )
            response.raise_for_status()
            
            print(f"Posted: {job['title']} at {job['company']}")
            self.mark_job_posted(job_id)
            return True
            
        except Exception as e:
            print(f"Error posting job: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return False
    
    def run(self):
        """Main execution method"""
        print("Starting job scraper...")
        
        # Fetch jobs from both sources
        print("\nFetching jobs from Adzuna...")
        adzuna_jobs = self.fetch_adzuna_jobs()
        print(f"Found {len(adzuna_jobs)} jobs from Adzuna")
        
        print("\nFetching jobs from JSearch...")
        jsearch_jobs = self.fetch_jsearch_jobs()
        print(f"Found {len(jsearch_jobs)} jobs from JSearch")
        
        # Combine all jobs
        all_jobs = adzuna_jobs + jsearch_jobs
        print(f"\nTotal jobs found: {len(all_jobs)}")
        
        # Post to WordPress
        print("\nPosting to WordPress...")
        posted_count = 0
        for job in all_jobs:
            if self.post_to_wordpress(job):
                posted_count += 1
                time.sleep(2)  # Rate limiting
        
        print(f"\nCompleted! Posted {posted_count} new jobs.")

if __name__ == "__main__":
    scraper = JobScraper()
    scraper.run()
