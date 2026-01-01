# Railway Deployment Guide

**AutoBalloon CIE v3.0 - Production Deployment on Railway**

This guide covers deploying the AutoBalloon CIE application to Railway with Supabase PostgreSQL and LemonSqueezy payment processing.

---

## Prerequisites

1. **Railway Account**: https://railway.app
2. **Supabase Project**: https://supabase.com
3. **LemonSqueezy Account**: https://lemonsqueezy.com
4. **Google Cloud Project**: For Vision API and Gemini API

---

## Step 1: Supabase Setup

### 1.1 Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Set project name: `autoballoon-cie-prod`
4. Choose region (closest to your Railway region)
5. Set database password (save it securely)

### 1.2 Run Database Migration

1. In Supabase dashboard, go to SQL Editor
2. Create new query
3. Copy entire contents of `supabase/migrations/001_initial_schema.sql`
4. Run the migration
5. Verify tables created: `users`, `usage`, `subscriptions`, `webhook_events`

### 1.3 Configure Authentication

1. Go to Authentication → Settings
2. Enable Email provider
3. Configure Site URL: `https://your-app.railway.app`
4. Add redirect URLs:
   - `https://your-app.railway.app`
   - `http://localhost:3000` (for local testing)
5. Disable email confirmations (optional, for faster onboarding)

### 1.4 Get API Keys

1. Go to Settings → API
2. Copy the following:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY` (keep secret!)

---

## Step 2: LemonSqueezy Setup

### 2.1 Create Store

1. Go to https://app.lemonsqueezy.com
2. Create a new store (if you don't have one)
3. Note your Store ID (Settings → General)

### 2.2 Create Products

**Product 1: Light Plan**
- Name: AutoBalloon Light
- Price: $20/month (recurring)
- Description: 30 uploads/day, 150/month
- Create variant, note the Variant ID

**Product 2: Production Plan**
- Name: AutoBalloon Production
- Price: $99/month (recurring)
- Description: 100 uploads/day, 500/month
- Create variant, note the Variant ID

### 2.3 Create API Key

1. Go to Settings → API
2. Create new API key
3. Copy `LEMONSQUEEZY_API_KEY`

### 2.4 Configure Webhook

1. Go to Settings → Webhooks
2. Click "Add endpoint"
3. URL: `https://your-app.railway.app/api/webhooks/lemonsqueezy`
4. Events to subscribe:
   - `subscription_created`
   - `subscription_updated`
   - `subscription_cancelled`
   - `subscription_expired`
   - `subscription_payment_success`
5. Copy the Signing Secret → `LEMONSQUEEZY_WEBHOOK_SECRET`

---

## Step 3: Google Cloud Setup

### 3.1 Enable APIs

1. Go to https://console.cloud.google.com
2. Create new project: `autoballoon-cie`
3. Enable the following APIs:
   - Cloud Vision API
   - Gemini API (AI Platform)

### 3.2 Create API Keys

1. Go to APIs & Services → Credentials
2. Create API Key for Vision API
3. Create API Key for Gemini API
4. Restrict keys to specific APIs (recommended)

---

## Step 4: Railway Deployment

### 4.1 Connect Repository

1. Go to https://railway.app/new
2. Select "Deploy from GitHub repo"
3. Authorize Railway to access your repository
4. Select `autoballoon-cie` repository

### 4.2 Configure Environment Variables

In Railway dashboard, go to Variables tab and add:

**Supabase**
```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...
```

**Google APIs**
```
NEXT_PUBLIC_GOOGLE_VISION_API_KEY=AIzaSyxxx...
NEXT_PUBLIC_GEMINI_API_KEY=AIzaSyxxx...
GOOGLE_CLOUD_PROJECT_ID=autoballoon-cie
```

**LemonSqueezy**
```
LEMONSQUEEZY_API_KEY=your_api_key_here
LEMONSQUEEZY_STORE_ID=12345
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret
NEXT_PUBLIC_LEMONSQUEEZY_STORE_URL=https://yourstore.lemonsqueezy.com
LEMONSQUEEZY_TIER_20_VARIANT_ID=123456
LEMONSQUEEZY_TIER_99_VARIANT_ID=123457
```

**App Configuration**
```
NEXT_PUBLIC_APP_URL=https://your-app.railway.app
NODE_ENV=production
```

**Pricing Tiers**
```
TIER_20_DAILY_CAP=30
TIER_20_MONTHLY_CAP=150
TIER_99_DAILY_CAP=100
TIER_99_MONTHLY_CAP=500
```

### 4.3 Deploy

1. Railway will automatically build and deploy
2. Monitor build logs for errors
3. Once deployed, copy the Railway app URL
4. Update LemonSqueezy webhook URL with Railway domain
5. Update Supabase Site URL and Redirect URLs

---

## Step 5: Post-Deployment Configuration

### 5.1 Test LemonSqueezy Webhook

1. In LemonSqueezy dashboard, go to Webhooks
2. Click "Send test webhook"
3. Check Railway logs for webhook processing
4. Verify `webhook_events` table in Supabase has entry

### 5.2 Test Upload Flow

1. Visit your Railway app URL
2. Upload a test PDF
3. Verify processing completes
4. Check `usage` table in Supabase for new record

### 5.3 Test Paywall

1. Click Export without subscription
2. Verify PaywallModal appears
3. Click subscribe
4. Verify redirect to LemonSqueezy checkout

### 5.4 Test Subscription

1. Complete a test subscription (use test mode if available)
2. Verify webhook processed successfully
3. Check `users` and `subscriptions` tables updated
4. Try export again - should succeed

---

## Step 6: Scheduled Tasks (Usage Reset)

### Option A: Supabase Cron (If Available)

If your Supabase plan supports pg_cron:

```sql
-- Daily reset (runs at midnight UTC)
SELECT cron.schedule(
  'reset-daily-usage',
  '0 0 * * *',
  $$ SELECT reset_daily_usage(); $$
);

-- Monthly reset (runs on 1st of month)
SELECT cron.schedule(
  'reset-monthly-usage',
  '0 0 1 * *',
  $$ SELECT reset_monthly_usage(); $$
);
```

### Option B: External Cron (cron-job.org)

If pg_cron not available:

1. Create API endpoint: `/api/cron/reset-usage`
2. Add logic to call `reset_daily_usage()` and `reset_monthly_usage()`
3. Set up cron job at https://cron-job.org to hit endpoint daily

---

## Step 7: Monitoring & Logging

### 7.1 Railway Logs

- Monitor deployment logs in Railway dashboard
- Set up log alerts for errors

### 7.2 Supabase Logs

- Check database logs for query errors
- Monitor `webhook_events` table for processing failures

### 7.3 Error Tracking (Optional)

Add Sentry for production error tracking:

```bash
pnpm add @sentry/nextjs
```

Configure in `sentry.client.config.ts` and `sentry.server.config.ts`

---

## Step 8: Custom Domain (Optional)

### 8.1 Add Domain to Railway

1. Railway dashboard → Settings → Domains
2. Click "Add Domain"
3. Enter your domain: `app.autoballoon.com`

### 8.2 Configure DNS

Add CNAME record at your DNS provider:

```
Type: CNAME
Name: app
Value: your-app.railway.app
```

### 8.3 Update Environment Variables

Update the following with custom domain:

```
NEXT_PUBLIC_APP_URL=https://app.autoballoon.com
```

Update Supabase and LemonSqueezy URLs accordingly.

---

## Troubleshooting

### Build Fails

**Error: "pnpm not found"**
- Railway should auto-detect pnpm from `package.json`
- If not, add to `railway.toml`: `builder = "NIXPACKS"`

**Error: "Out of memory"**
- Increase Railway instance size in Settings

### Webhook Not Working

**Error: "Invalid signature"**
- Verify `LEMONSQUEEZY_WEBHOOK_SECRET` is correct
- Check webhook payload in Railway logs
- Ensure endpoint URL is correct

**Error: "User not found"**
- Verify customer email matches Supabase user
- Check `auth.users` table

### Database Connection Issues

**Error: "Connection refused"**
- Verify `SUPABASE_SERVICE_ROLE_KEY` is correct
- Check Supabase project is active
- Verify RLS policies allow service role access

### Export Not Working

**Error: "Usage limit reached"**
- Check `usage` table in Supabase
- Verify subscription status in `users` table
- Check if daily/monthly reset functions running

---

## Security Checklist

- [ ] All API keys stored as Railway environment variables
- [ ] `SUPABASE_SERVICE_ROLE_KEY` never exposed to client
- [ ] LemonSqueezy webhook signature verification enabled
- [ ] Supabase RLS policies enabled on all tables
- [ ] HTTPS enforced (Railway default)
- [ ] CORS configured (Next.js handles this)
- [ ] Rate limiting considered (optional, via Railway)

---

## Cost Estimation

**Monthly Costs (Approximate)**

- Railway Hobby Plan: $5/month (or free trial)
- Supabase Free Tier: $0 (up to 500MB database, 2GB bandwidth)
- LemonSqueezy: 5% + 50¢ per transaction
- Google Cloud Vision API: $1.50 per 1,000 images (generous free tier)
- Google Gemini API: Pay-as-you-go (very cheap for text parsing)

**Expected Costs at 100 Users:**
- Railway: $5-$20/month
- Supabase: Free (unless high usage)
- LemonSqueezy: ~5% of revenue
- Google APIs: $5-$10/month

---

## Rollback Plan

If deployment fails:

1. Railway keeps previous deployment running
2. Click "Rollback" in Railway dashboard
3. Or redeploy from specific Git commit

---

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure all environment variables
3. ✅ Test full user flow (upload → process → export → subscribe)
4. ✅ Set up usage reset cron jobs
5. ✅ Monitor logs for 24 hours
6. 🚀 Launch to production!

---

**Deployment Checklist**

- [ ] Supabase project created and migrated
- [ ] LemonSqueezy products and webhook configured
- [ ] Google Cloud APIs enabled
- [ ] Railway environment variables set
- [ ] App deployed and accessible
- [ ] Webhook tested and working
- [ ] Upload flow tested
- [ ] Paywall tested
- [ ] Subscription flow tested
- [ ] Usage reset scheduled
- [ ] Monitoring configured
- [ ] Custom domain configured (optional)

---

**Support:**
- Railway Docs: https://docs.railway.app
- Supabase Docs: https://supabase.com/docs
- LemonSqueezy Docs: https://docs.lemonsqueezy.com

---

*Last Updated: 2024-12-19*
*Version: CIE v3.0*
