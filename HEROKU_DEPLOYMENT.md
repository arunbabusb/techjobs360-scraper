# Heroku Deployment Guide for TechJobs360 Scraper

## 🚀 Quick Deployment Steps

### Prerequisites
- Heroku account (free tier works)
- Heroku CLI installed: https://devcenter.heroku.com/articles/heroku-cli
- Git installed

### Step 1: Create Heroku App

```bash
# Login to Heroku
heroku login

# Create a new app (replace 'your-app-name' with unique name)
heroku create your-app-name

# Or use auto-generated name
heroku create
```

### Step 2: Set Environment Variables

```bash
# Required WordPress credentials
heroku config:set WP_URL="https://your-wordpress-site.com"
heroku config:set WP_USERNAME="your-wp-username"
heroku config:set WP_APP_PASSWORD="your-wp-app-password"

# Optional: JSearch API key (if using paid source)
heroku config:set JSEARCH_API_KEY="your-rapidapi-key"

# Optional: Process specific continent
heroku config:set PROCESS_CONTINENT="asia"

# Optional: Disable auto-rotation
heroku config:set AUTO_ROTATE="false"

# Verify all variables are set
heroku config
```

### Step 3: Deploy to Heroku

```bash
# Add Heroku remote (if not done automatically)
heroku git:remote -a your-app-name

# Push code to Heroku
git push heroku main

# Or if you're on a different branch
git push heroku your-branch:main
```

### Step 4: Set Up Heroku Scheduler

The scraper needs to run periodically. Use Heroku Scheduler (free addon):

```bash
# Add Heroku Scheduler
heroku addons:create scheduler:standard

# Open scheduler dashboard
heroku addons:open scheduler
```

In the Scheduler dashboard:
1. Click "Create job"
2. Command: `python job_scraper.py`
3. Frequency: Choose based on your needs:
   - **Every hour** - More frequent updates
   - **Every 3 hours** - Balanced (recommended)
   - **Every day at...** - Less frequent
4. Click "Save"

### Step 5: Test the Deployment

```bash
# Run diagnostic tool
heroku run python diagnose.py

# Run scraper manually (one-time)
heroku run python job_scraper.py

# View logs
heroku logs --tail

# Check recent logs
heroku logs -n 200
```

## 🔧 Alternative: Heroku APScheduler (Always Running)

If you want the scraper to run continuously without Scheduler addon:

### Create `scheduler_app.py`:

```python
#!/usr/bin/env python3
"""
Heroku APScheduler runner for TechJobs360 Scraper
Keeps the app running and schedules jobs at specific times
"""

from apscheduler.schedulers.blocking import BlockingScheduler
import job_scraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")

scheduler = BlockingScheduler()

# Run scraper 4 times daily (same as GitHub Actions)
@scheduler.scheduled_job('cron', hour='0,6,12,18', minute=30)
def scheduled_scrape():
    logger.info("Starting scheduled scrape...")
    try:
        job_scraper.main()
        logger.info("Scrape completed successfully")
    except Exception as e:
        logger.error(f"Scrape failed: {e}")

if __name__ == "__main__":
    logger.info("Scheduler started - will run at 00:30, 06:30, 12:30, 18:30 UTC")
    scheduler.start()
```

### Update `requirements.txt`:

```bash
# Add to requirements.txt
APScheduler==3.10.4
```

### Update `Procfile`:

```
worker: python scheduler_app.py
```

### Deploy:

```bash
git add .
git commit -m "Add APScheduler for continuous running"
git push heroku main

# Scale up the worker dyno
heroku ps:scale worker=1
```

## 📊 Monitoring on Heroku

### View Real-time Logs

```bash
# Stream logs continuously
heroku logs --tail

# Filter logs by source
heroku logs --source app --tail

# Show last 500 lines
heroku logs -n 500
```

### Check Dyno Status

```bash
# View running dynos
heroku ps

# Restart all dynos
heroku restart

# Restart specific dyno
heroku restart worker.1
```

### Resource Usage

```bash
# Check addon usage
heroku addons

# View metrics (requires addons)
heroku logs --tail | grep "INFO"
```

## 💰 Cost Considerations

### Free Tier (Heroku Eco Dynos - $5/month)
- 1000 dyno hours/month
- Scheduler addon: FREE
- Perfect for:
  - Running scraper 4x daily
  - Small to medium job volumes
  - Testing and development

### Paid Options (if needed)
- **Basic dyno** ($7/month): More reliable, doesn't sleep
- **APScheduler** (recommended): Always running, precise scheduling

## 🐛 Troubleshooting Heroku Deployment

### Issue: "Application Error"

```bash
# Check logs for errors
heroku logs --tail

# Ensure buildpack is set
heroku buildpacks:set heroku/python
```

### Issue: "No web process running"

```bash
# For worker dyno (scraper doesn't need web)
heroku ps:scale web=0 worker=1
```

### Issue: "Cannot connect to WordPress"

```bash
# Verify config vars
heroku config

# Test WordPress connection
heroku run python diagnose.py
```

### Issue: "Module not found"

```bash
# Rebuild with clear cache
heroku builds:cache:purge
git commit --allow-empty -m "Rebuild"
git push heroku main
```

### Issue: "Out of memory"

```bash
# Upgrade dyno type
heroku ps:type worker=standard-1x
```

## 🔄 Updating Your Heroku App

```bash
# Make changes to code
git add .
git commit -m "Update scraper code"

# Push to Heroku
git push heroku main

# Restart to apply changes
heroku restart
```

## 📝 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| WP_URL | ✅ Yes | WordPress site URL | https://techjobs360.com |
| WP_USERNAME | ✅ Yes | WordPress username | admin |
| WP_APP_PASSWORD | ✅ Yes | Application password | xxxx xxxx xxxx xxxx |
| JSEARCH_API_KEY | ⚠️ Optional | RapidAPI key | your-api-key |
| PROCESS_CONTINENT | ⚠️ Optional | Limit to one continent | asia, europe, etc. |
| AUTO_ROTATE | ⚠️ Optional | Enable rotation | true/false |

## 🎯 Recommended Setup

For most users, we recommend:

1. **Heroku Scheduler** (free addon) - Simple, reliable
2. **Run 4x daily** - Balances freshness with rate limits
3. **Monitor logs weekly** - Catch issues early
4. **Enable auto-rotate** - Distribute load across continents

```bash
# Complete setup in 3 commands:
heroku create your-techjobs-scraper
heroku config:set WP_URL="..." WP_USERNAME="..." WP_APP_PASSWORD="..."
heroku addons:create scheduler:standard
```

Then configure the scheduler to run `python job_scraper.py` every 3 hours.

## 📞 Support

If you encounter issues:
1. Run: `heroku run python diagnose.py`
2. Check: `heroku logs --tail`
3. Verify: `heroku config`
4. Review: GitHub Issues at repository

---

**Happy Scraping! 🎉**
