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
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for result in data.get('results', []):
                jobs.append({
                    'title': result.get('title', 'No Title'),
                    'company': result.get('company', {}).get('display_name', 'Unknown Company'),
                    'location': result.get('location', {}).get('display_name', location),
                    'description': result.get('description', ''),
                    'url': result.get('redirect_url', ''),
                    'created': result.get('created', ''),
                    'source': 'Adzuna'
                })
            
            return jobs
        except Exception as e:
            print(f"Error fetching Adzuna jobs: {e}")
            return []
    
    def fetch_jsearch_jobs(self, query='technology', num_pages=1):
        """Fetch jobs from JSearch API (RapidAPI)"""
        url = "https://jsearch.p.rapidapi.com/search"
        
        headers = {
            'X-RapidAPI-Key': self.jsearch_api_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }
        
        all_jobs = []
        
        for page in range(1, num_pages + 1):
            params = {
                'query': f'{query} jobs in India',
                'page': str(page),
                'num_pages': '1'
            }
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                for result in data.get('data', []):
                    all_jobs.append({
                        'title': result.get('job_title', 'No Title'),
                        'company': result.get('employer_name', 'Unknown Company'),
                        'location': result.get('job_city', 'India'),
                        'description': result.get('job_description', ''),
                        'url': result.get('job_apply_link', result.get('job_google_link', '')),
                        'created': result.get('job_posted_at_datetime_utc', ''),
                        'source': 'JSearch'
                    })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching JSearch jobs (page {page}): {e}")
                break
        
        return all_jobs
    
    def get_or_create_tag_id(self, tag_name):
        """Get tag ID by name, create if doesn't exist"""
        # First, try to get existing tag
        tags_url = f"{self.wp_url}/wp-json/wp/v2/tags"
        params = {'search': tag_name}
        
        try:
            response = requests.get(
                tags_url,
                params=params,
                auth=(self.wp_user, self.wp_password),
                timeout=10
            )
            response.raise_for_status()
            tags = response.json()
            
            # Check if tag exists (case-insensitive match)
            for tag in tags:
                if tag['name'].lower() == tag_name.lower():
                    return tag['id']
            
            # Tag doesn't exist, create it
            create_response = requests.post(
                tags_url,
                json={'name': tag_name},
                auth=(self.wp_user, self.wp_password),
                timeout=10
            )
            create_response.raise_for_status()
            return create_response.json()['id']
            
        except Exception as e:
            print(f"Error getting/creating tag '{tag_name}': {e}")
            return None
    
    def post_to_wordpress(self, job):
        """Post job to WordPress"""
        # Generate unique job ID
        job_id = self.generate_job_id(job['title'], job['company'], job['location'])
        
        # Check if already posted
        if self.is_job_posted(job_id):
            print(f"Skipping duplicate: {job['title']} at {job['company']}")
            return False
        
        # Prepare post data
        post_url = f"{self.wp_url}/wp-json/wp/v2/posts"
        
        # Convert tag names to tag IDs
        tag_names = [job['location'], job['company'], 'tech-jobs']
        tag_ids = []
        for tag_name in tag_names:
            tag_id = self.get_or_create_tag_id(tag_name)
            if tag_id:
                tag_ids.append(tag_id)
        
        post_data = {
            'title': job['title'],
            'content': f"""
            <h2>Job Details</h2>
            <p><strong>Company:</strong> {job['company']}</p>
            <p><strong>Location:</strong> {job['location']}</p>
            <p><strong>Source:</strong> {job['source']}</p>
            
            <h3>Description</h3>
            {job['description']}
            
            <p><a href="{job['url']}" target="_blank">Apply Now</a></p>
            """,
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
