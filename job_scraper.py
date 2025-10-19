import requests
import os
def fetch_jobs():
    api_key = os.getenv("JSEARCH_API_KEY")
    url = "https://api.yourjobsource.com/jobs"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        jobs = response.json()
        print(jobs)
    else:
        print(f"Failed to fetch jobs, status={response.status_code}")
if __name__ == "__main__":
    fetch_jobs()
