# Complete Setup Guide - AutoBalloon CIE

**Step-by-Step Instructions to Get Your App Running**

---

## Quick Start (Local Development)

If you just want to see the app running on your computer:

```bash
# 1. Navigate to the project
cd /Users/Tk/Downloads/autoballoon-cie

# 2. Install dependencies (using pnpm)
pnpm install

# 3. Copy environment variables template
cp .env.example .env.local

# 4. Add your API keys to .env.local (see below)

# 5. Start development server
pnpm dev

# 6. Open browser
# Visit: http://localhost:3000
```

---

## Environment Variables Setup

You need to create a `.env.local` file with the following API keys.

### 1. Google Cloud Setup (15 minutes)

**What you need:** Vision API (for OCR) and Gemini API (for AI parsing)

**Steps:**

1. Go to https://console.cloud.google.com
2. Create a new project: `autoballoon-cie`
3. Enable APIs:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Cloud Vision API" → Enable
   - Search for "Gemini API" (or "AI Platform") → Enable

4. Create API Keys:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the key (this is your `NEXT_PUBLIC_GOOGLE_VISION_API_KEY`)
   - Create another key for Gemini (or use the same one)
   - **Optional but recommended:** Restrict keys to specific APIs

5. Add to `.env.local`:
   ```env
   NEXT_PUBLIC_GOOGLE_VISION_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX
   NEXT_PUBLIC_GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX
   GOOGLE_CLOUD_PROJECT_ID=autoballoon-cie
   ```

### 2. Supabase Setup (20 minutes)

**What you need:** Database for users, subscriptions, and usage tracking

**Steps:**

1. Go to https://supabase.com
2. Create account (or sign in)
3. Click "New Project"
   - Organization: Create new (or select existing)
   - Name: `autoballoon-cie`
   - Database Password: Choose a strong password (save it!)
   - Region: Choose closest to you
   - Click "Create new project"
   - Wait ~2 minutes for provisioning

4. Run Database Migration:
   - In Supabase dashboard, go to "SQL Editor"
   - Click "New Query"
   - Copy entire contents of `/Users/Tk/Downloads/autoballoon-cie/supabase/migrations/001_initial_schema.sql`
   - Paste into query editor
   - Click "Run"
   - You should see "Success. No rows returned"
   - Verify tables created: Go to "Table Editor" → Should see `users`, `usage`, `subscriptions`, `webhook_events`

5. Configure Authentication:
   - Go to "Authentication" → "Providers"
   - Enable "Email" provider
   - (Optional) Disable email confirmation for faster testing
   - Go to "URL Configuration"
   - Add Site URL: `http://localhost:3000`
   - Add Redirect URLs: `http://localhost:3000`

6. Get API Keys:
   - Go to "Settings" → "API"
   - Copy these three values:
     - Project URL
     - `anon` `public` key
     - `service_role` key (⚠️ Keep secret!)

7. Add to `.env.local`:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

### 3. LemonSqueezy Setup (30 minutes)

**What you need:** Payment processor for subscriptions

**Steps:**

1. Go to https://lemonsqueezy.com
2. Create account
3. Create a store:
   - Go to "Settings" → "Stores"
   - Click "Create Store"
   - Store Name: `AutoBalloon`
   - Store URL: `autoballoon` (becomes autoballoon.lemonsqueezy.com)
   - Fill in required info
   - Complete store setup

4. Note your Store ID:
   - Go to "Settings" → "General"
   - You'll see "Store ID: 12345" (copy this number)

5. Create Products:

   **Product 1: Light Plan**
   - Go to "Products" → "Create Product"
   - Name: `AutoBalloon Light`
   - Description: `30 uploads per day, 150 per month`
   - Click "Create Product"
   - Add Variant:
     - Name: `Monthly`
     - Price: `$20.00`
     - Billing: `Recurring` → `Monthly`
     - Click "Save"
   - Note the Variant ID (in URL or variant details)

   **Product 2: Production Plan**
   - Repeat above with:
     - Name: `AutoBalloon Production`
     - Description: `100 uploads per day, 500 per month`
     - Price: `$99.00`
     - Note the Variant ID

6. Create API Key:
   - Go to "Settings" → "API"
   - Click "Create API Key"
   - Name: `AutoBalloon Production`
   - Copy the key (starts with `LS-...`)

7. Configure Webhook (IMPORTANT - do this after deploying):
   - Go to "Settings" → "Webhooks"
   - Click "Add Endpoint"
   - URL: `https://your-app.railway.app/api/webhooks/lemonsqueezy` (update after deploy)
   - Signing Secret: Click "Generate"
   - Events to subscribe:
     - ✓ `subscription_created`
     - ✓ `subscription_updated`
     - ✓ `subscription_cancelled`
     - ✓ `subscription_expired`
     - ✓ `subscription_payment_success`
   - Click "Save"
   - Copy the Signing Secret

8. Add to `.env.local`:
   ```env
   LEMONSQUEEZY_API_KEY=LS-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   LEMONSQUEEZY_STORE_ID=12345
   LEMONSQUEEZY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   NEXT_PUBLIC_LEMONSQUEEZY_STORE_URL=https://autoballoon.lemonsqueezy.com
   LEMONSQUEEZY_TIER_20_VARIANT_ID=123456
   LEMONSQUEEZY_TIER_99_VARIANT_ID=123457
   ```

### 4. App Configuration

Add these to `.env.local`:

```env
# App Config
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development

# Pricing Tiers (caps)
TIER_20_DAILY_CAP=30
TIER_20_MONTHLY_CAP=150
TIER_99_DAILY_CAP=100
TIER_99_MONTHLY_CAP=500
```

---

## Complete `.env.local` File

Your final `.env.local` should look like this:

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Google APIs
NEXT_PUBLIC_GOOGLE_VISION_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX
NEXT_PUBLIC_GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX
GOOGLE_CLOUD_PROJECT_ID=autoballoon-cie

# LemonSqueezy (Payment Processor)
LEMONSQUEEZY_API_KEY=LS-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LEMONSQUEEZY_STORE_ID=12345
LEMONSQUEEZY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_LEMONSQUEEZY_STORE_URL=https://autoballoon.lemonsqueezy.com

# Product/Variant IDs
LEMONSQUEEZY_TIER_20_VARIANT_ID=123456
LEMONSQUEEZY_TIER_99_VARIANT_ID=123457

# App Config
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development

# Pricing Tiers
TIER_20_DAILY_CAP=30
TIER_20_MONTHLY_CAP=150
TIER_99_DAILY_CAP=100
TIER_99_MONTHLY_CAP=500
```

---

## Testing Locally

### 1. Start the App

```bash
pnpm dev
```

Open http://localhost:3000

### 2. Test Upload Flow

1. Find a sample PDF (any engineering drawing)
2. Drag and drop onto the upload zone
3. Watch processing animation
4. See workbench with balloons

### 3. Test Paywall

1. Click the green "Export" button
2. PaywallModal should appear
3. Select a plan
4. Click "Subscribe to [Plan Name]"
5. You should be redirected to LemonSqueezy checkout

**Note:** In development, you can use LemonSqueezy's test mode.

### 4. Test Webhook (Local)

To test webhooks locally, you need to expose your local server:

**Option 1: ngrok**
```bash
# Install ngrok
brew install ngrok

# Expose port 3000
ngrok http 3000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update LemonSqueezy webhook URL to:
# https://abc123.ngrok.io/api/webhooks/lemonsqueezy
```

**Option 2: Skip webhook testing locally**
- Deploy to Railway first
- Test webhooks in production

---

## Deployment to Railway

See `RAILWAY_DEPLOYMENT.md` for complete guide.

**Quick steps:**

1. Push code to GitHub (see GitHub section below)
2. Go to https://railway.app
3. Click "Deploy from GitHub repo"
4. Select your repository
5. Add all environment variables (from `.env.local`)
6. Wait for build to complete
7. Copy Railway app URL
8. Update LemonSqueezy webhook URL
9. Update Supabase redirect URLs
10. Test full flow

---

## Troubleshooting

### "Supabase client error"

**Problem:** Missing or incorrect Supabase keys

**Solution:**
1. Check `.env.local` has correct `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
2. Restart dev server: `pnpm dev`

### "Google API key not configured"

**Problem:** Missing Google API keys

**Solution:**
1. Check `.env.local` has `NEXT_PUBLIC_GOOGLE_VISION_API_KEY` and `NEXT_PUBLIC_GEMINI_API_KEY`
2. Verify keys are enabled in Google Cloud Console
3. Restart dev server

### "LemonSqueezy not configured"

**Problem:** Missing LemonSqueezy keys

**Solution:**
1. Check `.env.local` has all `LEMONSQUEEZY_*` variables
2. Verify API key is correct (starts with `LS-`)
3. Restart dev server

### "Webhook signature invalid"

**Problem:** Incorrect webhook secret

**Solution:**
1. Go to LemonSqueezy → Settings → Webhooks
2. Copy the correct signing secret
3. Update `LEMONSQUEEZY_WEBHOOK_SECRET` in `.env.local` (or Railway)
4. Restart server

### "IndexedDB quota exceeded"

**Problem:** Too much data stored in browser

**Solution:**
1. Open browser DevTools
2. Application → Storage → IndexedDB
3. Delete `AutoBalloon-CIE` database
4. Refresh page

### Build errors

**Problem:** Missing dependencies

**Solution:**
```bash
rm -rf node_modules
rm pnpm-lock.yaml
pnpm install
```

---

## Development Workflow

### Making Changes

1. Edit files in `src/`
2. Changes auto-reload (Fast Refresh)
3. Check browser console for errors

### Adding New Features

1. Create new component in `src/components/`
2. Import and use in existing components
3. Update Zustand store if needed (`src/store/useAppStore.ts`)

### Testing Subscription Flow

1. Create test subscription in LemonSqueezy
2. Use test credit card: `4242 4242 4242 4242`
3. Any future date, any CVC
4. Check Supabase tables updated

---

## Project Structure

```
autoballoon-cie/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── api/                # API routes
│   │   │   ├── checkout/       # Checkout creation
│   │   │   ├── export/         # Excel export
│   │   │   ├── gemini/         # AI parsing
│   │   │   ├── ocr/            # OCR fallback
│   │   │   ├── usage/          # Usage tracking
│   │   │   └── webhooks/       # LemonSqueezy webhooks
│   │   ├── globals.css         # Global styles
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Main page (Unified Surface)
│   ├── components/             # React components
│   │   ├── canvas/             # Drawing canvas
│   │   ├── marketing/          # Marketing content
│   │   ├── panels/             # Sidebar and table
│   │   ├── DropZone.tsx        # File upload
│   │   ├── PaywallModal.tsx    # Subscription modal
│   │   ├── Toolbar.tsx         # Top toolbar
│   │   └── ...
│   ├── hooks/                  # Custom React hooks
│   │   └── usePaywall.ts       # Subscription logic
│   ├── lib/                    # Libraries and utilities
│   │   ├── lemonsqueezy.ts     # Payment integration
│   │   ├── mathEngine.ts       # Precision calculations
│   │   ├── pdfExtractor.ts     # PDF processing
│   │   └── supabase.ts         # Database client
│   └── store/                  # State management
│       └── useAppStore.ts      # Zustand store
├── supabase/                   # Database
│   └── migrations/             # SQL migrations
├── public/                     # Static assets
├── .env.local                  # Local environment vars (YOU CREATE THIS)
├── .env.example                # Environment template
├── package.json                # Dependencies
├── railway.toml                # Railway config
└── README.md                   # Project overview
```

---

## Next Steps

1. ✅ Complete `.env.local` setup
2. ✅ Test locally with `pnpm dev`
3. ✅ Push to GitHub
4. ✅ Deploy to Railway
5. ✅ Test production webhooks
6. 🚀 Launch!

---

## Support Resources

- **Supabase Docs:** https://supabase.com/docs
- **LemonSqueezy Docs:** https://docs.lemonsqueezy.com
- **Railway Docs:** https://docs.railway.app
- **Next.js Docs:** https://nextjs.org/docs

---

**You're all set!** If you run into issues, check the troubleshooting section or the detailed `RAILWAY_DEPLOYMENT.md` guide.
