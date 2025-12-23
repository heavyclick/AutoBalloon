# AutoBalloon Deployment Guide
## Complete Step-by-Step for Beginners

This guide assumes you have ZERO coding experience. Follow each step exactly.

---

## Table of Contents
1. [What You Need Before Starting](#1-what-you-need-before-starting)
2. [Set Up Supabase (Database)](#2-set-up-supabase-database)
3. [Set Up Resend (Email)](#3-set-up-resend-email)
4. [Set Up Paystack (Payments)](#4-set-up-paystack-payments)
5. [Set Up Railway (Hosting)](#5-set-up-railway-hosting)
6. [Connect Your Domain](#6-connect-your-domain)
7. [Test Everything](#7-test-everything)
8. [Go Live Checklist](#8-go-live-checklist)

---

## 1. What You Need Before Starting

### Accounts to Create (all free to start):
- [ ] **Supabase account** - https://supabase.com (free tier: 500MB database)
- [ ] **Resend account** - https://resend.com (free tier: 3,000 emails/month)
- [ ] **Paystack account** - https://paystack.com (you already applied)
- [ ] **Railway account** - https://railway.app (free tier: $5/month credits)
- [ ] **GitHub account** - https://github.com (free)

### Things You Already Have:
- [ ] Domain: autoballoon.space
- [ ] Google Cloud API Key (for Vision OCR)
- [ ] Gemini API Key

### Time Required:
- First-time setup: 2-3 hours
- Future deployments: 5 minutes

---

## 2. Set Up Supabase (Database)

Supabase is where all your user data, subscriptions, and history will be stored.

### Step 2.1: Create Account
1. Go to https://supabase.com
2. Click **"Start your project"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if required

### Step 2.2: Create New Project
1. Click **"New Project"**
2. Fill in:
   - **Name:** `autoballoon`
   - **Database Password:** Generate a strong password and SAVE IT SOMEWHERE SAFE
   - **Region:** Choose closest to your users (e.g., "East US" or "Frankfurt")
3. Click **"Create new project"**
4. Wait 2-3 minutes for setup to complete

### Step 2.3: Get Your API Keys
1. In your project dashboard, click **"Settings"** (gear icon) in left sidebar
2. Click **"API"** under Configuration
3. You'll see a page with your keys. Copy these EXACTLY:

```
┌─────────────────────────────────────────────────────────────┐
│  Project URL                                                 │
│  ──────────────────────────────────────────────────────────  │
│  https://xyzabc123.supabase.co          [Copy button]        │
│                                                              │
│  This is your SUPABASE_URL                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Project API keys                                            │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  anon (public)                                               │
│  eyJhbGciOiJIUzI1NiIsInR5cCI6...        [Copy button]        │
│                                                              │
│  This is your SUPABASE_ANON_KEY                              │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  service_role (secret)                     [Reveal button]   │
│  eyJhbGciOiJIUzI1NiIsInR5cCI6...        [Copy button]        │
│                                                              │
│  This is your SUPABASE_SERVICE_KEY                           │
│  ⚠️ NEVER share this publicly!                               │
└─────────────────────────────────────────────────────────────┘
```

4. Save these three values in a secure note:
   - `SUPABASE_URL` = The Project URL
   - `SUPABASE_ANON_KEY` = The anon public key
   - `SUPABASE_SERVICE_KEY` = The service_role secret key (click "Reveal" first)

### Step 2.4: Create Database Tables
1. In left sidebar, click **"SQL Editor"**
2. Click **"New query"**
3. Copy the ENTIRE contents of `supabase/migrations/001_initial_schema.sql` from your project
4. Paste it into the SQL editor
5. Click **"Run"** (or press Ctrl+Enter)
6. You should see "Success. No rows returned" - this is correct!

### Step 2.5: Verify Tables Were Created
1. In left sidebar, click **"Table Editor"**
2. You should see these tables:
   - users
   - usage
   - history
   - magic_links
   - subscriptions
   - payment_events

✅ **Supabase is now set up!**

---

## 3. Set Up Resend (Email)

Resend sends the magic login links to your users.

### Step 3.1: Create Account
1. Go to https://resend.com
2. Click **"Get Started"**
3. Sign up with GitHub or email

### Step 3.2: Verify Your Domain
1. In dashboard, click **"Domains"** in left sidebar
2. Click **"Add Domain"**
3. Enter: `autoballoon.space`
4. Click **"Add"**

You'll see DNS records to add. Go to your domain registrar (where you bought autoballoon.space):

```
┌──────────────────────────────────────────────────────────────┐
│  Add these DNS records to your domain:                        │
│                                                               │
│  Type: TXT                                                    │
│  Name: resend._domainkey                                      │
│  Value: (a long string they provide)                          │
│  TTL: 3600                                                    │
│                                                               │
│  Type: TXT                                                    │
│  Name: @                                                      │
│  Value: v=spf1 include:... (they provide this)               │
└──────────────────────────────────────────────────────────────┘
```

5. After adding DNS records, click **"Verify"** in Resend
6. Wait 5-30 minutes for DNS to propagate
7. Status will change from "Pending" to "Verified" ✓

### Step 3.3: Get Your API Key
1. Click **"API Keys"** in left sidebar
2. Click **"Create API Key"**
3. Name: `autoballoon-production`
4. Permission: **Full access**
5. Click **"Create"**
6. COPY THE KEY IMMEDIATELY (you can't see it again!)

Save this as your `RESEND_API_KEY`

✅ **Resend is now set up!**

---

## 4. Set Up Paystack (Payments)

### Step 4.1: Complete Your Account Setup
Since you've already applied, once approved:
1. Log in to https://dashboard.paystack.com
2. Complete any verification steps they require

### Step 4.2: Get Your API Keys
1. Click **"Settings"** (gear icon) in left sidebar
2. Click **"API Keys & Webhooks"**
3. You'll see:

```
┌─────────────────────────────────────────────────────────────┐
│  Test Keys (for development)                                 │
│  ──────────────────────────────────────────────────────────  │
│  Public Key: pk_test_xxxxxxxxxxxxxxxx                        │
│  Secret Key: sk_test_xxxxxxxxxxxxxxxx        [Show]          │
│                                                              │
│  Live Keys (for real payments)                               │
│  ──────────────────────────────────────────────────────────  │
│  Public Key: pk_live_xxxxxxxxxxxxxxxx                        │
│  Secret Key: sk_live_xxxxxxxxxxxxxxxx        [Show]          │
└─────────────────────────────────────────────────────────────┘
```

4. Save BOTH test and live keys:
   - `PAYSTACK_PUBLIC_KEY` = Public Key (starts with pk_)
   - `PAYSTACK_SECRET_KEY` = Secret Key (starts with sk_)

### Step 4.3: Create Subscription Plan
1. Click **"Products"** in left sidebar
2. Click **"Plans"**
3. Click **"Create Plan"**
4. Fill in:
   - **Name:** AutoBalloon Pro
   - **Amount:** ₦158,400 (or $99 USD equivalent)
   - **Interval:** Monthly
   - **Description:** Unlimited blueprint processing, AS9102 exports, permanent history
5. Click **"Create Plan"**
6. Copy the **Plan Code** (looks like `PLN_xxxxxxxx`)

Save this as `PAYSTACK_PLAN_CODE`

### Step 4.4: Set Up Webhook (Do This AFTER Railway Setup)
We'll come back to this in Step 5.7

✅ **Paystack keys saved!**

---

## 5. Set Up Railway (Hosting)

Railway is the easiest way to deploy your app. It's like magic - push code, it runs.

### Step 5.1: Create Account
1. Go to https://railway.app
2. Click **"Login"**
3. Sign up with **GitHub** (important - makes deployment easier)

### Step 5.2: Upload Code to GitHub
First, we need to put your code on GitHub:

1. Go to https://github.com
2. Sign in or create account
3. Click the **"+"** icon (top right) → **"New repository"**
4. Fill in:
   - **Repository name:** `autoballoon`
   - **Description:** AutoBalloon - Blueprint dimension detection
   - Select **"Private"** (keeps your code private)
   - DON'T check "Add README" (you already have one)
5. Click **"Create repository"**

Now you'll see instructions. Here's the easiest way:

**Option A: Using GitHub Desktop (Easiest for Beginners)**
1. Download GitHub Desktop: https://desktop.github.com
2. Install and sign in with your GitHub account
3. Click **"Add"** → **"Add Existing Repository"**
4. Browse to your `autoballoon` folder
5. It will say "This directory doesn't appear to be a Git repository"
6. Click **"create a repository"**
7. Fill in name: `autoballoon`
8. Click **"Create Repository"**
9. Click **"Publish repository"**
10. Uncheck "Keep this code private" if you want it private
11. Click **"Publish Repository"**

**Option B: Using Command Line**
If you have Git installed, open terminal/command prompt in your autoballoon folder:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/autoballoon.git
git push -u origin main
```

### Step 5.3: Create Railway Project
1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Click **"Deploy from GitHub repo"**
4. Select your `autoballoon` repository
5. Railway will detect you have multiple services

### Step 5.4: Deploy Backend
1. In Railway dashboard, click **"New"** → **"GitHub Repo"**
2. Select your repo
3. Click **"Add service"**
4. Set the **Root Directory** to: `backend`
5. Railway auto-detects Python

Now add environment variables:
1. Click on the backend service
2. Click **"Variables"** tab
3. Click **"New Variable"** for each:

```
ENVIRONMENT = production
GOOGLE_CLOUD_API_KEY = (your Google Cloud key)
GEMINI_API_KEY = (your Gemini key)
SUPABASE_URL = (from Step 2.3)
SUPABASE_ANON_KEY = (from Step 2.3)
SUPABASE_SERVICE_KEY = (from Step 2.3)
PAYSTACK_PUBLIC_KEY = (from Step 4.2 - use LIVE key for production)
PAYSTACK_SECRET_KEY = (from Step 4.2 - use LIVE key for production)
PAYSTACK_PLAN_CODE = (from Step 4.3)
RESEND_API_KEY = (from Step 3.3)
JWT_SECRET = (generate at https://randomkeygen.com - use 256-bit key)
APP_URL = https://autoballoon.space
```

4. Click **"Deploy"**

### Step 5.5: Get Backend URL
1. After deployment (green checkmark), click **"Settings"**
2. Under **"Domains"**, click **"Generate Domain"**
3. You'll get something like: `autoballoon-backend-production.up.railway.app`
4. Save this URL - this is your API URL

### Step 5.6: Deploy Frontend
1. Click **"New"** → **"GitHub Repo"**
2. Select your repo again
3. Set **Root Directory** to: `frontend`
4. Add environment variables:

```
VITE_API_URL = https://autoballoon-backend-production.up.railway.app/api
VITE_APP_URL = https://autoballoon.space
```

5. Click **"Deploy"**

### Step 5.7: Set Up Paystack Webhook (Now That We Have URL)
1. Go back to Paystack dashboard
2. Go to **"Settings"** → **"API Keys & Webhooks"**
3. Scroll to **"Webhook URL"**
4. Enter: `https://autoballoon-backend-production.up.railway.app/api/payments/webhook`
5. Click **"Save"**

For webhook secret:
1. In same Paystack page, look for "Webhook Secret" or generate one
2. Copy it
3. Go back to Railway → Backend service → Variables
4. Add: `PAYSTACK_WEBHOOK_SECRET = (the secret you copied)`
5. Redeploy backend

✅ **Railway deployment complete!**

---

## 6. Connect Your Domain

### Step 6.1: Set Up Custom Domain for Frontend
1. In Railway, click on your frontend service
2. Click **"Settings"**
3. Under **"Domains"**, click **"Custom Domain"**
4. Enter: `autoballoon.space`
5. Railway will show you DNS records to add

### Step 6.2: Add DNS Records
Go to your domain registrar (where you bought the domain) and add:

```
Type: CNAME
Name: @ (or leave blank, depends on registrar)
Value: (Railway provides this, like "abc123.up.railway.app")
TTL: 3600

Type: CNAME  
Name: www
Value: (same as above)
TTL: 3600
```

### Step 6.3: Set Up API Subdomain (Optional but Recommended)
For cleaner URLs, set up `api.autoballoon.space`:

1. In Railway, click on backend service
2. Settings → Domains → Custom Domain
3. Enter: `api.autoballoon.space`
4. Add CNAME record at your registrar:

```
Type: CNAME
Name: api
Value: (Railway provides this)
TTL: 3600
```

5. Update your frontend environment variable:
   `VITE_API_URL = https://api.autoballoon.space/api`

### Step 6.4: Wait for DNS & SSL
- DNS propagation: 5 minutes to 48 hours (usually under 1 hour)
- SSL certificate: Railway auto-generates this (5-10 minutes)

You can check status at: https://dnschecker.org

✅ **Domain connected!**

---

## 7. Test Everything

### Step 7.1: Test the Website
1. Go to https://autoballoon.space
2. The landing page should load
3. Scroll down - all sections should display

### Step 7.2: Test File Processing (Free Tier)
1. Drag a PDF blueprint onto the upload area
2. Wait for processing
3. You should see:
   - Detected dimensions with balloons
   - Export buttons
4. Try 3 free uploads (the limit)
5. On 4th upload, paywall should appear

### Step 7.3: Test Authentication
1. Click "Log in" in navbar
2. Enter your email
3. Click "Send login link"
4. Check your email
5. Click the link
6. You should be logged in

### Step 7.4: Test Payment Flow
1. Trigger paywall (use 4th upload)
2. Enter email and click "Upgrade"
3. Complete Paystack payment
4. You should be redirected to /success page
5. Check email for welcome message
6. Verify Pro badge appears

### Step 7.5: Test Export
1. As Pro user, upload a blueprint
2. Click "AS9102 Excel" button
3. Excel file should download
4. Open it - should have your dimensions

### Troubleshooting Common Issues

**Site not loading:**
- Check Railway deployment status (should be green)
- Wait for DNS propagation
- Try incognito/private browser

**API errors:**
- Check Railway logs (click service → Logs tab)
- Verify all environment variables are set
- Check Supabase connection

**Emails not arriving:**
- Check Resend domain is verified
- Check spam folder
- Verify RESEND_API_KEY is correct

**Payment not working:**
- Verify using correct Paystack keys (test vs live)
- Check webhook URL is correct
- View Paystack logs in their dashboard

✅ **Testing complete!**

---

## 8. Go Live Checklist

Before announcing to customers:

### Technical
- [ ] Site loads on autoballoon.space
- [ ] SSL certificate is active (https, green padlock)
- [ ] File upload and processing works
- [ ] Export generates valid Excel file
- [ ] Login/logout works
- [ ] Payment flow completes successfully
- [ ] Webhook creates Pro account
- [ ] Pro users get unlimited access

### Business
- [ ] Paystack account fully verified
- [ ] Using LIVE keys (not test)
- [ ] Subscription plan is $99/month
- [ ] Welcome email looks good
- [ ] Support email works (support@autoballoon.space)

### Legal (Create These Pages)
- [ ] Privacy Policy page
- [ ] Terms of Service page
- [ ] Refund policy defined

### Monitoring
- [ ] Set up Railway alerts (they'll email if site goes down)
- [ ] Bookmark Supabase dashboard for user management
- [ ] Bookmark Paystack dashboard for revenue tracking

---

## Quick Reference: All Your Keys

Create a secure document with all these values:

```
=== SUPABASE ===
SUPABASE_URL = https://xxxxx.supabase.co
SUPABASE_ANON_KEY = eyJhbGc...
SUPABASE_SERVICE_KEY = eyJhbGc...

=== RESEND ===
RESEND_API_KEY = re_xxxxx

=== PAYSTACK ===
PAYSTACK_PUBLIC_KEY = pk_live_xxxxx
PAYSTACK_SECRET_KEY = sk_live_xxxxx
PAYSTACK_PLAN_CODE = PLN_xxxxx
PAYSTACK_WEBHOOK_SECRET = xxxxx

=== GOOGLE ===
GOOGLE_CLOUD_API_KEY = xxxxx
GEMINI_API_KEY = xxxxx

=== APP ===
JWT_SECRET = (256-bit random string)
APP_URL = https://autoballoon.space
```

⚠️ **NEVER share these keys publicly!**

---

## Need Help?

**Railway Issues:** https://docs.railway.app
**Supabase Issues:** https://supabase.com/docs
**Paystack Issues:** https://paystack.com/docs

Or reply to this conversation and I can help troubleshoot!

---

## What's Next After Launch?

1. **Monitor:** Check Railway/Supabase daily for first week
2. **Support:** Set up help@autoballoon.space email
3. **Marketing:** Share on LinkedIn, aerospace forums
4. **Iterate:** Add features based on customer feedback

Good luck! 🚀
