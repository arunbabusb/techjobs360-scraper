# Reed API Integration - Enhancement Summary

## ✅ Changes Made

### 1. **Increased Reed API Limit**
- **Before:** 20 jobs per query
- **After:** 50 jobs per query
- **Location:** `config.yaml` line 46

### 2. **Added 13 More UK Cities**
- **Before:** 5 cities (London, Manchester, Birmingham, Leeds, Edinburgh)
- **After:** 18 cities
- **New cities added:**
  1. Bristol - frontend developer
  2. Cambridge - data scientist
  3. Oxford - machine learning engineer
  4. Glasgow - full stack developer
  5. Liverpool - python developer
  6. Newcastle - react developer
  7. Brighton - mobile developer
  8. Nottingham - QA engineer
  9. Reading - software engineer
  10. Southampton - backend developer
  11. Cardiff - cloud architect
  12. Belfast - nodejs developer

### 3. **Expected Impact**
- **Before:** 5 cities × 20 jobs = **100 jobs max** from Reed API per Europe run
- **After:** 18 cities × 50 jobs = **900 jobs max** from Reed API per Europe run
- **Increase:** 9x more potential jobs from Reed! 🚀

---

## 🧪 Local Testing Instructions

### Step 1: Set Your Reed API Key

```bash
export REED_API_KEY='your-reed-api-key-here'
```

**To get your Reed API key:**
1. Sign up at https://www.reed.co.uk/developers
2. Create an account and verify email
3. Get your API key from the dashboard

### Step 2: Run the Test Script

```bash
bash test_local.sh
```

Or run the Python test directly:

```bash
python3 test_reed.py
```

### Step 3: Expected Output

```
==============================================================
Reed API Integration Test
==============================================================
✅ REED_API_KEY is set: 12345678...9012

Test 1: Querying 'software engineer' in 'London' (limit: 5)
------------------------------------------------------------
✅ SUCCESS: Found 5 jobs from Reed API

Sample job:
  Title: Senior Software Engineer
  Company: Tech Company Ltd
  Location: London
  URL: https://www.reed.co.uk/jobs/...
  Job ID: 12345678

Test 2: Querying 'python developer' in 'Manchester' (limit: 3)
------------------------------------------------------------
✅ SUCCESS: Found 3 jobs from Reed API
...
```

---

## 🚀 Deploy to GitHub Actions

The changes are ready to commit. Once pushed, the GitHub Actions workflow will automatically:

1. Use your REED_API_KEY from GitHub Secrets
2. Query all 18 UK cities on Europe rotation days
3. Fetch up to 50 jobs per city
4. Deduplicate and post to WordPress

### Commit & Push

```bash
git add config.yaml
git commit -m "Enhance Reed API: Add 13 UK cities + increase limit to 50"
git push -u origin claude/fix-scraper-deployment-015N7ncFVrgUzjrrewesx6Hv
```

---

## 📊 Reed API Rate Limits

**Reed API Free Tier:**
- **Rate Limit:** Not publicly documented, but be polite
- **Current Configuration:** 18 queries per Europe rotation
- **Pause Between Sources:** 2 seconds (configured in config.yaml)
- **Recommendation:** Monitor for 429 (Too Many Requests) errors in GitHub Actions logs

**If you hit rate limits:**
1. Reduce `pause_seconds` in config.yaml from 2 to 3-5 seconds
2. Reduce number of UK cities
3. Reduce `limit` from 50 to 30

---

## 🗺️ UK Tech Hubs Covered

| City | Population | Tech Scene | Query |
|------|-----------|------------|-------|
| London | 9M | 🔥🔥🔥🔥🔥 Massive | backend engineer |
| Manchester | 2.7M | 🔥🔥🔥🔥 Large | software engineer |
| Birmingham | 2.6M | 🔥🔥🔥 Growing | java developer |
| Leeds | 793K | 🔥🔥🔥 Strong | devops engineer |
| Edinburgh | 540K | 🔥🔥🔥🔥 FinTech hub | cloud engineer |
| Bristol | 463K | 🔥🔥🔥 Tech/Creative | frontend developer |
| Cambridge | 145K | 🔥🔥🔥🔥 AI/Research | data scientist |
| Oxford | 162K | 🔥🔥🔥 Academia/AI | ML engineer |
| Glasgow | 635K | 🔥🔥 Growing | full stack developer |
| Liverpool | 498K | 🔥🔥 Emerging | python developer |
| Newcastle | 302K | 🔥🔥 Emerging | react developer |
| Brighton | 290K | 🔥🔥🔥 Digital/Creative | mobile developer |
| Nottingham | 332K | 🔥🔥 Gaming/Tech | QA engineer |
| Reading | 163K | 🔥🔥 Tech corridor | software engineer |
| Southampton | 254K | 🔥 Maritime/Tech | backend developer |
| Cardiff | 364K | 🔥🔥 Growing | cloud architect |
| Belfast | 345K | 🔥🔥 Cybersecurity | nodejs developer |

---

## 🔍 Monitoring

After deployment, check GitHub Actions logs for:

```
✅ Good signs:
- "Querying reed for 'backend engineer' / 'London'"
- "Reed returned 50 jobs"
- "Posted job to WP: <job-title>"

⚠️ Watch for:
- "Reed returned 403" (API key issue)
- "Reed returned 429" (rate limit)
- "No REED_API_KEY set" (environment issue)
```

---

## 📝 Files Modified

1. `config.yaml` - Added 13 UK cities, increased limit to 50
2. `test_reed.py` - New test script for Reed API
3. `test_local.sh` - New bash wrapper for local testing

---

**Last Updated:** 2025-11-29
**Status:** ✅ Ready for deployment
