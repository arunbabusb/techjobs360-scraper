#!/usr/bin/env python3
import os
import sys
import logging
from job_scraper import (
    load_config, load_dedup, prune_dedup,
    query_jsearch, query_remotive, query_remoteok, 
    query_arbeitnow, query_jobicy, query_himalayas,
    query_adzuna, query_reed, parse_weworkremotely,
    parse_indeed, parse_linkedin, pick_continent_by_weekday
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("deployment_check")

def check_deployment():
    """Check the deployment status and configuration"""
    
    print("=" * 60)
    print("TECHJOBS360 SCRAPER DEPLOYMENT CHECK")
    print("=" * 60)
    
    # 1. Check environment variables
    print("\n1. ENVIRONMENT VARIABLES:")
    env_vars = ['WP_URL', 'WP_USERNAME', 'WP_APP_PASSWORD', 'JSEARCH_API_KEY', 
                'ADZUNA_APP_ID', 'ADZUNA_APP_KEY', 'REED_API_KEY']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ✓ {var}: {'*' * 10} (set)")
        else:
            print(f"   ✗ {var}: NOT SET")
    
    # 2. Check config
    print("\n2. CONFIGURATION:")
    try:
        config = load_config()
        print(f"   ✓ config.yaml loaded successfully")
        print(f"   - Continents: {len(config.get('continents', []))}")
        enabled_sources = [s['type'] for s in config['sources'] if s.get('enabled')]
        print(f"   - Enabled sources: {len(enabled_sources)}")
        print(f"     {', '.join(enabled_sources)}")
        print(f"   - Auto-rotate: {config['global'].get('auto_rotate', False)}")
    except Exception as e:
        print(f"   ✗ Error loading config: {e}")
        return
    
    # 3. Check dedup file
    print("\n3. DEDUPLICATION:")
    try:
        dedup_list = load_dedup()
        print(f"   ✓ posted_jobs.json loaded")
        print(f"   - Total entries: {len(dedup_list)}")
    except Exception as e:
        print(f"   ✗ Error loading dedup: {e}")
    
    # 4. Test continent rotation
    print("\n4. CONTINENT ROTATION:")
    try:
        if config['global'].get('auto_rotate'):
            continent = pick_continent_by_weekday(config['continents'])
            print(f"   ✓ Auto-rotate enabled")
            print(f"   - Today's continent: {continent['name']} ({continent['id']})")
        else:
            print(f"   - Auto-rotate disabled")
    except Exception as e:
        print(f"   ✗ Error checking rotation: {e}")
    
    # 5. Test job sources (quick test)
    print("\n5. JOB SOURCES TEST:")
    test_query = "python developer"
    
    sources_to_test = [
        ('Remotive', lambda: query_remotive(test_query, limit=5)),
        ('RemoteOK', lambda: query_remoteok(test_query, limit=5)),
        ('WeWorkRemotely', lambda: parse_weworkremotely(test_query, limit=5)),
    ]
    
    for name, func in sources_to_test:
        try:
            jobs = func()
            print(f"   ✓ {name}: {len(jobs)} jobs")
        except Exception as e:
            print(f"   ✗ {name}: Error - {str(e)[:50]}")
    
    # 6. Summary
    print("\n" + "=" * 60)
    print("DEPLOYMENT STATUS:")
    
    wp_configured = all([os.environ.get(v) for v in ['WP_URL', 'WP_USERNAME', 'WP_APP_PASSWORD']])
    if wp_configured:
        print("   ✓ WordPress configured - Jobs will be posted")
    else:
        print("   ⚠ WordPress NOT configured - Jobs will NOT be posted")
        print("     (Set WP_URL, WP_USERNAME, WP_APP_PASSWORD in GitHub Secrets)")
    
    print("=" * 60)

if __name__ == '__main__':
    check_deployment()
