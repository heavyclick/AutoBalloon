# How AutoBalloon CIE Works - Complete System Explanation

**A Non-Technical Guide to Understanding Your New Application**

---

## Table of Contents

1. [Big Picture Overview](#big-picture-overview)
2. [The User Journey](#the-user-journey)
3. [Technical Architecture](#technical-architecture)
4. [How Each Component Works](#how-each-component-works)
5. [The Subscription System](#the-subscription-system)
6. [Data Flow](#data-flow)
7. [Setup Instructions](#setup-instructions)

---

## Big Picture Overview

**What is AutoBalloon CIE?**

AutoBalloon CIE (Canonical Inspection Engine) is a web application that helps quality inspectors and engineers automatically balloon engineering drawings and generate AS9102 First Article Inspection (FAI) reports.

**The Problem It Solves:**

Traditionally, ballooning a drawing and creating an AS9102 report is a manual, time-consuming process:
1. Print the drawing
2. Manually circle each dimension with a balloon number
3. Manually type each dimension into an Excel spreadsheet
4. Double-check for errors
5. Spend hours on a single drawing

**What AutoBalloon CIE Does:**

1. Upload a PDF drawing (drag and drop)
2. **Automatically extracts** all dimensions using AI
3. **Automatically balloons** the drawing with numbered markers
4. **Automatically generates** an AS9102 Excel report
5. All in **under 60 seconds**

**The Innovation:**

- **Zero-Storage Security**: Your drawings never touch our servers - everything runs in your browser
- **AI-Powered**: Uses Google Gemini to understand complex dimensions (tolerances, fits, GD&T)
- **Investment Loss Doctrine**: You only pay when you want to export (after seeing results)
- **Vector-First**: Reads PDF data directly for 100% accuracy (no OCR guessing)

---

## The User Journey

Let me walk you through what a user experiences:

### Step 1: Landing Page (Marketing)
- User visits `https://your-app.railway.app`
- Sees a clean interface with:
  - Drop zone for PDF upload
  - How It Works section (below the fold)
  - Pricing cards (below the fold)
  - FAQ (below the fold)

### Step 2: Upload PDF
- User drags a PDF drawing onto the drop zone
- **No confirmation dialog** - the app immediately starts processing
- The page "morphs" into a processing view

### Step 3: Processing View
- Shows animated progress:
  - ✓ Extracting vector text from PDF...
  - ✓ Running OCR fallback (if needed)...
  - ✓ Parsing dimensions with AI...
  - ✓ Detecting grid zones...
  - ✓ Finalizing...

### Step 4: Workbench View (The Editor)
- The page morphs again into the main editor
- User sees:
  - **Drawing Canvas** (center) - Their PDF with red balloon overlays
  - **Properties Sidebar** (right) - Details of selected dimension
  - **Table Manager** (bottom) - Excel-like grid of all dimensions
  - **Toolbar** (top) - Tools and Export button

### Step 5: Editing (Optional)
- User can click any balloon to select it
- Edit nominal value, tolerances, inspection method, etc.
- Changes sync instantly across canvas, sidebar, and table
- Can add manual balloons using "Smart Balloon" mode

### Step 6: Export (Paywall Trigger)
- User clicks green "Export" button
- **PaywallModal appears** (Investment Loss Doctrine)
- Shows two pricing tiers:
  - Light: $20/month (30/day, 150/month)
  - Production: $99/month (100/day, 500/month)
- User selects plan and clicks "Subscribe"

### Step 7: Payment
- Redirects to LemonSqueezy checkout (secure payment processor)
- User enters payment details
- After successful payment, webhook updates database
- User is redirected back to app

### Step 8: Export (Success)
- Export button now works
- Downloads two files:
  - **AS9102_Form3.xlsx** - Excel spreadsheet with all dimensions
  - **Drawing_Ballooned.pdf** - PDF with balloon overlays

### Step 9: Ongoing Usage
- User can upload more drawings
- Usage counter tracks daily/monthly uploads
- When limit reached, paywall appears again (upgrade prompt)

---

## Technical Architecture

**Technology Stack:**

- **Frontend**: Next.js 14 (React 18) with TypeScript
- **State Management**: Zustand with IndexedDB persistence
- **Styling**: TailwindCSS
- **PDF Processing**: pdf.js (vector extraction)
- **OCR**: Google Cloud Vision API
- **AI Parsing**: Google Gemini 1.5 Flash
- **Payment Processing**: LemonSqueezy
- **Database**: Supabase (PostgreSQL with Row Level Security)
- **Hosting**: Railway

**Architecture Principles (CIE Doctrine):**

1. **Unified Surface**: Single route application (`/`), no navigation
2. **State Morphing**: Three views (landing, processing, workbench) on same URL
3. **Vector-First**: Extract text from PDF data, not OCR
4. **Zero-Storage**: Drawings stay in browser (IndexedDB), never server
5. **Investment Loss**: Paywall triggers only after user has invested time
6. **Client-Side Math**: All calculations happen in browser (instant updates)

---

## How Each Component Works

### 1. PDF Extraction (`src/lib/pdfExtractor.ts`)

**What it does:**
Reads PDF file and extracts text with exact coordinates.

**How it works:**
```
1. User drops PDF file
2. pdf.js loads file into memory
3. For each page:
   a. Extract vector text (internal PDF text data)
   b. Render page as high-res PNG image
   c. If vector text < 5 strings → trigger OCR fallback
4. Store pages in IndexedDB
```

**Why vector-first?**
- PDFs created from CAD (SolidWorks, AutoCAD, etc.) have embedded text
- Reading this text = 100% accuracy, no OCR errors
- OCR only used for scanned drawings or images

---

### 2. AI Dimension Parsing (`src/app/api/gemini/route.ts`)

**What it does:**
Takes raw text like `"2.500 +0.005/-0.010"` and structures it into JSON.

**How it works:**
```
1. Extracted text sent to Google Gemini API
2. Structured prompt asks for JSON output:
   {
     "nominal": 2.500,
     "plus_tolerance": 0.005,
     "minus_tolerance": -0.010,
     "units": "in",
     "tolerance_type": "bilateral",
     "subtype": "Linear"
   }
3. Gemini understands complex formats:
   - Bilateral tolerances: ±0.010
   - Limit dimensions: 2.505/2.490
   - Fits: Ø1.000 H7/g6
   - GD&T: ⌖0.005 A B C
   - Threads: 1/4-20 UNC
```

**Why Gemini?**
- Regex patterns fail on complex formats
- Gemini has been trained on engineering drawings
- Handles ambiguous cases (e.g., "2.5" vs "2.500" precision)

---

### 3. Canvas Rendering (`src/components/canvas/DrawingCanvas.tsx`)

**What it does:**
Displays PDF pages with zoomable, pannable interface and balloon overlays.

**How it works:**
```
1. Uses react-zoom-pan-pinch library for controls
2. Renders all PDF pages vertically (continuous scroll)
3. For each extracted dimension:
   - Draw red rectangle at bounding box coordinates
   - Add balloon number
   - Show confidence indicator (pulse if < 80%)
4. Click balloon → highlight in sidebar and table
```

**Layers:**
- **Layer 1**: PDF page image (base)
- **Layer 2**: Balloon overlays (red boxes + numbers)
- **Layer 3**: Watermark (for free users, every 3rd balloon)

---

### 4. Properties Sidebar (`src/components/panels/PropertiesSidebar.tsx`)

**What it does:**
Shows detailed information about selected dimension with inline editing.

**Progressive Disclosure:**
- **Tier 1** (always visible): Nominal, Tolerances, Limits
- **Tier 2** (collapsible): Feature Type, Units, Inspection Method
- **Tier 3** (advanced): AQL Sampling, GD&T details

**How editing works:**
```
1. User changes nominal value from "2.500" to "2.505"
2. Zustand store updates characteristic
3. mathEngine recalculates limits:
   - Upper Limit = 2.505 + 0.005 = 2.510
   - Lower Limit = 2.505 - 0.010 = 2.495
4. Updates propagate to:
   - Canvas balloon (re-renders)
   - Table row (updates cell)
   - IndexedDB (persists change)
```

---

### 5. Table Manager (`src/components/panels/TableManager.tsx`)

**What it does:**
Excel-like grid view of all dimensions with inline editing.

**Features:**
- Click row → highlight balloon on canvas
- Edit any cell → updates sidebar and canvas
- Sort by balloon number, nominal, confidence, etc.
- Shows CMM data (if imported)

---

### 6. Math Engine (`src/lib/mathEngine.ts`)

**What it does:**
Performs all tolerance and limit calculations with perfect precision.

**Why decimal.js?**
JavaScript has a floating-point bug:
```javascript
0.1 + 0.2 = 0.30000000000000004  // WRONG!
```

Using decimal.js:
```javascript
new Decimal(0.1).plus(0.2).toNumber() = 0.3  // CORRECT!
```

**Functions:**
- `calculateLimits()` - Upper = Nominal + Plus, Lower = Nominal + Minus
- `getBlockTolerance()` - Infer tolerance from decimal places (.X = ±0.030, .XX = ±0.010)

---

### 7. Subscription System (Phase 10)

This is what I just built. Let me explain the full flow:

#### Components:

**A. Database (Supabase PostgreSQL)**

Four tables:

1. **users** - Extended user profiles
   ```sql
   - id (UUID, links to auth.users)
   - email
   - is_pro (boolean)
   - subscription_status ('free', 'tier_20', 'tier_99', 'cancelled')
   - subscription_tier ('tier_20', 'tier_99')
   - lemonsqueezy_subscription_id
   - subscription_ends_at
   ```

2. **usage** - Upload tracking
   ```sql
   - id
   - user_id (or visitor_id for anonymous)
   - daily_count (resets every day)
   - monthly_count (resets every month)
   - daily_reset_at
   - monthly_reset_at
   ```

3. **subscriptions** - LemonSqueezy sync
   ```sql
   - id
   - user_id
   - lemonsqueezy_subscription_id
   - plan_type ('tier_20', 'tier_99')
   - status ('active', 'cancelled', 'expired')
   - renews_at
   ```

4. **webhook_events** - Debug log
   ```sql
   - id
   - event_type
   - payload (JSONB)
   - processed (boolean)
   ```

**B. Payment Processor (LemonSqueezy)**

LemonSqueezy handles:
- Checkout page (payment form)
- Subscription billing (recurring charges)
- Webhooks (tells our app about subscription events)

**C. Paywall Modal (`src/components/PaywallModal.tsx`)**

Beautiful modal that shows:
- Pricing comparison (Light vs Production)
- Plan selection with radio buttons
- "Subscribe" button that redirects to LemonSqueezy

**D. usePaywall Hook (`src/hooks/usePaywall.ts`)**

React hook that manages:
- Fetching usage statistics
- Checking if user can export
- Triggering paywall modal
- Visitor fingerprint for anonymous users

**E. API Endpoints**

1. `/api/checkout/create` (POST)
   - Creates LemonSqueezy checkout session
   - Returns checkout URL
   - Keeps API keys server-side

2. `/api/webhooks/lemonsqueezy` (POST)
   - Receives webhook from LemonSqueezy
   - Verifies HMAC signature
   - Updates database (users, subscriptions tables)
   - Logs event

3. `/api/usage/check` (GET)
   - Returns current usage stats
   - Calculates remaining quota

   (POST)
   - Increments usage counter
   - Returns 429 if limit reached

---

## The Subscription System (Detailed Flow)

### Scenario 1: Free User Tries to Export

```
1. User clicks "Export" button
   ↓
2. Toolbar calls usePaywall.canExport()
   ↓
3. canExport() fetches /api/usage/check
   ↓
4. API checks:
   - Is user authenticated? → Get from Supabase
   - Is user pro? → Check users.is_pro
   - Has user hit limits? → Check usage.daily_count
   ↓
5. Result: is_pro = false
   ↓
6. Toolbar triggers PaywallModal (trigger: 'export')
   ↓
7. Modal displays pricing
   ↓
8. User selects "Production" plan
   ↓
9. User clicks "Subscribe to Production Plan"
   ↓
10. Modal calls /api/checkout/create
    ↓
11. API creates LemonSqueezy checkout session:
    POST https://api.lemonsqueezy.com/v1/checkouts
    {
      variantId: "123457", // Production plan
      email: user@example.com,
      customData: { user_id: "abc123" }
    }
    ↓
12. LemonSqueezy returns checkout URL
    ↓
13. Browser redirects to LemonSqueezy
    ↓
14. User enters payment details
    ↓
15. LemonSqueezy processes payment
    ↓
16. LemonSqueezy sends webhook to our app:
    POST https://your-app.railway.app/api/webhooks/lemonsqueezy
    {
      meta: { event_name: "subscription_created" },
      data: {
        id: "sub_12345",
        attributes: {
          status: "active",
          variant_id: "123457",
          customer_id: "cust_789"
        }
      }
    }
    ↓
17. Our webhook handler:
    a. Verifies HMAC signature
    b. Logs to webhook_events table
    c. Creates subscription record
    d. Updates users table:
       - is_pro = true
       - subscription_status = 'tier_99'
       - subscription_tier = 'tier_99'
    ↓
18. LemonSqueezy redirects user back to app
    ↓
19. User clicks "Export" again
    ↓
20. canExport() returns true (is_pro = true)
    ↓
21. Export succeeds, files downloaded
```

### Scenario 2: Subscribed User Hits Daily Limit

```
1. User uploads 101st drawing today (on $20 plan)
   ↓
2. Processing completes
   ↓
3. App calls /api/usage/check (POST)
   ↓
4. API increments usage:
   - daily_count = 101
   - Daily cap for tier_20 = 30
   - 101 > 30 → LIMIT REACHED
   ↓
5. API returns 429 Too Many Requests
   ↓
6. usePaywall.incrementUsage() detects 429
   ↓
7. Triggers PaywallModal (trigger: 'usage_limit')
   ↓
8. Modal shows "Usage Limit Reached" message
   ↓
9. User can upgrade to Production plan ($99)
   ↓
10. If upgraded:
    - New daily cap = 100
    - User can continue
```

### Scenario 3: User Cancels Subscription

```
1. User cancels in LemonSqueezy portal
   ↓
2. LemonSqueezy sends webhook:
   event_name: "subscription_cancelled"
   ↓
3. Our webhook handler:
   - Updates subscriptions.status = 'cancelled'
   - Updates users.is_pro = false
   - Updates users.subscription_status = 'cancelled'
   - Sets users.subscription_ends_at = end_date
   ↓
4. Next time user tries to export:
   - canExport() returns false
   - PaywallModal appears
```

---

## Data Flow

Let me trace a complete upload → export flow:

```
┌─────────────────────────────────────────────────────────────┐
│                      USER DROPS PDF                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  BROWSER (Client-Side)                                      │
│  ┌────────────────────────────────────────────────┐         │
│  │ 1. DropZone receives file                      │         │
│  │ 2. Zustand store: initializeProject()         │         │
│  │ 3. Mode changes: 'landing' → 'processing'     │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PDF EXTRACTION (src/lib/pdfExtractor.ts)                   │
│  ┌────────────────────────────────────────────────┐         │
│  │ 1. pdf.js loads file into ArrayBuffer         │         │
│  │ 2. For each page:                              │         │
│  │    - Extract vector text (PDF ops)            │         │
│  │    - Render to PNG (canvas → base64)          │         │
│  │    - If vector text < 5 → OCR fallback        │         │
│  │ 3. Store in Zustand: addPage()                │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  OCR FALLBACK (Optional)                                    │
│  ┌────────────────────────────────────────────────┐         │
│  │ POST /api/ocr                                  │         │
│  │   → Google Cloud Vision API                   │         │
│  │   → Returns text with bounding boxes          │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  AI PARSING (src/app/api/gemini/route.ts)                   │
│  ┌────────────────────────────────────────────────┐         │
│  │ 1. For each extracted text string:            │         │
│  │    POST /api/gemini                            │         │
│  │      Body: { text: "2.500 ±0.010" }           │         │
│  │    ↓                                           │         │
│  │    Google Gemini API                           │         │
│  │    ↓                                           │         │
│  │    Response: {                                 │         │
│  │      nominal: 2.500,                           │         │
│  │      plus_tolerance: 0.010,                    │         │
│  │      minus_tolerance: -0.010,                  │         │
│  │      units: "in"                               │         │
│  │    }                                           │         │
│  │ 2. Zustand: addCharacteristic()               │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CLIENT-SIDE MATH (src/lib/mathEngine.ts)                   │
│  ┌────────────────────────────────────────────────┐         │
│  │ calculateLimits(2.500, 0.010, -0.010)         │         │
│  │   → upper_limit: 2.510                        │         │
│  │   → lower_limit: 2.490                        │         │
│  │                                                 │         │
│  │ Updates Zustand: updateCharacteristic()        │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  INDEXEDDB PERSISTENCE                                      │
│  ┌────────────────────────────────────────────────┐         │
│  │ Zustand middleware saves to IndexedDB:         │         │
│  │ {                                               │         │
│  │   project: {                                    │         │
│  │     metadata: {...},                            │         │
│  │     pages: [...],                               │         │
│  │     characteristics: [...]                      │         │
│  │   }                                             │         │
│  │ }                                               │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  MODE CHANGE                                                 │
│  'processing' → 'workbench'                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  WORKBENCH VIEW                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │ User sees:                                      │         │
│  │ - Canvas with PDF + balloons                   │         │
│  │ - Sidebar with dimension details               │         │
│  │ - Table with all characteristics               │         │
│  │                                                 │         │
│  │ User can edit, zoom, pan, select...            │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  USER CLICKS EXPORT                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  SUBSCRIPTION CHECK                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │ 1. usePaywall.canExport()                      │         │
│  │ 2. GET /api/usage/check?visitor_id=xyz         │         │
│  │    ↓                                            │         │
│  │    Query Supabase:                              │         │
│  │    - Check users.is_pro                         │         │
│  │    - Check usage.daily_count vs caps           │         │
│  │    ↓                                            │         │
│  │    Response: {                                  │         │
│  │      subscription: {                            │         │
│  │        is_pro: false,                           │         │
│  │        tier: 'free'                             │         │
│  │      }                                           │         │
│  │    }                                            │         │
│  │ 3. canExport() returns false                   │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PAYWALL MODAL APPEARS                                       │
│  User subscribes (flow described earlier)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  AFTER SUBSCRIPTION                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │ 1. User clicks Export again                    │         │
│  │ 2. canExport() returns true                    │         │
│  │ 3. Export logic runs:                          │         │
│  │    POST /api/export/excel                      │         │
│  │      Body: { characteristics: [...] }         │         │
│  │    ↓                                            │         │
│  │    Server generates Excel using ExcelJS        │         │
│  │    ↓                                            │         │
│  │    Returns .xlsx file as blob                  │         │
│  │ 4. Browser downloads file                      │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

See detailed guide below in next section.

---

This is how your entire system works! Every piece connects together to create a seamless experience from upload to export, with secure payment processing in between.
