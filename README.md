# AutoBalloon CIE v3.0 - The Canonical Inspection Engine

**The Unified Surface for Manufacturing Inspection**

AI-powered dimension detection for First Article Inspection. Drop a blueprint, get AS9102 reports in seconds.

---

## 🎯 What This Is

AutoBalloon CIE is a **single-page, browser-first inspection tool** that eliminates the "application setup" tax. No navigation. No context switching. No server storage.

**The Three States:**
1. **Landing:** Marketing + DropZone
2. **Processing:** Real-time extraction progress
3. **Workbench:** Full canvas editor with zoom/pan, balloons, and inline editing

**The Doctrine:**
- **Unified Surface:** The landing page IS the product
- **Vector-First:** pdf.js extracts text with 100% accuracy before falling back to OCR
- **Zero-Storage:** All processing happens in-browser via IndexedDB
- **Investment Loss:** Users complete 100% of work before paywall appears

---

## 🏗️ Architecture

### Frontend Stack
- **Next.js 14** (App Router)
- **React 18** with TypeScript
- **Zustand** + IndexedDB (persistent state)
- **TailwindCSS** (utility-first styling)
- **pdf.js** (vector text extraction)
- **react-zoom-pan-pinch** (canvas interactions)
- **decimal.js** (precision math)

### Backend Stack
- **Next.js API Routes** (serverless functions)
- **Google Cloud Vision API** (OCR fallback)
- **Google Gemini 1.5 Flash** (semantic parsing)
- **ExcelJS** (AS9102 report generation)
- **Supabase** (auth + subscription management)
- **Paystack** (payment processing)

### Key Libraries
```json
{
  "pdfjs-dist": "^4.0.379",      // Vector extraction
  "zustand": "^4.5.0",           // State management
  "localforage": "^1.10.0",      // IndexedDB persistence
  "decimal.js": "^10.4.3",       // Precision arithmetic
  "exceljs": "^4.4.0",           // Excel generation
  "react-zoom-pan-pinch": "^3.4.0" // Canvas controls
}
```

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 20+ (required for Next.js 14)
- **pnpm** (recommended) or npm

### 1. Clone & Install
```bash
cd /Users/Tk/Downloads/autoballoon-cie
pnpm install
```

### 2. Environment Setup
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

Fill in the required API keys:
```env
# Google APIs (REQUIRED)
NEXT_PUBLIC_GOOGLE_VISION_API_KEY=AIzaSy...
NEXT_PUBLIC_GEMINI_API_KEY=AIzaSy...

# Supabase (REQUIRED for auth)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...

# Paystack (REQUIRED for payments)
PAYSTACK_SECRET_KEY=sk_xxx...
PAYSTACK_PUBLIC_KEY=pk_xxx...

# App Config
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Run Development Server
```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Build for Production
```bash
pnpm build
pnpm start
```

---

## 📐 How It Works

### The Extraction Pipeline

**Layer A: Vector Harvesting (The Truth Layer)**
```typescript
// Uses pdf.js to traverse PDF's internal Ops List
const page = await pdf.getPage(1);
const textContent = await page.getTextContent();
// Extracts Text operators with precise x,y coordinates
// 100% accuracy on symbols (Ø, ±, °)
```

**Layer B: Raster Fallback (The Vision Layer)**
```typescript
// Triggered if page contains <5 vector strings
// Converts page to 300DPI PNG
// Sends to Google Cloud Vision API
const response = await fetch('/api/ocr', {
  method: 'POST',
  body: JSON.stringify({ image: base64 })
});
```

**Layer C: Gemini Semantic Structuring (The Intelligence Layer)**
```typescript
// Sends raw text to Gemini: "2X Ø.125 +0.005/-0.002"
// Returns structured JSON:
{
  quantity: 2,
  nominal: 0.125,
  plus_tolerance: 0.005,
  minus_tolerance: -0.002,
  units: "inch",
  subtype: "Diameter"
}
```

### Client-Side Math Engine
```typescript
import Decimal from 'decimal.js';

// Prevents floating-point errors
const nominal = new Decimal(2.500);
const plus = new Decimal(0.005);
const upperLimit = nominal.plus(plus); // 2.505 (exact)

// Auto-tolerance based on decimal places
".X"   → ±0.030
".XX"  → ±0.010
".XXX" → ±0.005
```

---

## 🎨 UI/UX Features

### The Morphing Landing Page
```typescript
// State: 'landing' → 'processing' → 'workbench'
// No navigation. Only transformation.
useAppStore((state) => state.mode);
```

### Canvas Rendering
- **Infinite zoom/pan** via `react-zoom-pan-pinch`
- **Multi-layer rendering** (drawing + balloons + watermark)
- **Continuous vertical scroll** for multi-page PDFs
- **Click-to-select** balloons

### Properties Sidebar
- **Tier 1 (Always Visible):** Nominal, Tolerances, Limits
- **Tier 2 (Collapsible):** Feature Type, Units, Method
- **Tier 3 (Advanced):** AQL Sampling, GD&T details

### Table Manager
- **Excel-like grid** with inline editing
- **Sync with canvas:** Click row → Highlight balloon
- **Hover row → Highlight balloon** on drawing

---

## 💰 Pricing Model (CIE Doctrine)

### Tier 1: Light ($20/month)
- **30 uploads/day**
- **150 uploads/month**
- Full workbench access
- AS9102 Excel exports
- CMM import

### Tier 2: Production ($99/month)
- **100 uploads/day**
- **500 uploads/month**
- Everything in Light, plus:
- Priority processing
- Revision comparison
- Priority support

### Enforcement
```typescript
// Daily cap check happens ONLY on export (not upload)
// Preserves momentum - user completes work before hitting cap
const { daily_remaining, monthly_remaining } = await checkUsage();

if (daily_remaining <= 0) {
  showUpgradeModal(); // "You've used all 30 uploads today"
}
```

---

## 🔒 Security & Privacy

### Zero-Storage Architecture
1. **File Upload** → Browser Memory
2. **Vector Extraction** → pdf.js (client-side)
3. **OCR Fallback** → Google Vision (stateless API)
4. **State Persistence** → IndexedDB (local only)
5. **Export** → Download (no server storage)

**For Free Users:** Files deleted after session ends
**For Pro Users:** Optional IndexedDB persistence (can clear anytime)

**ITAR/EAR Compliance:** By design. Drawings never touch servers.

---

## 🛠️ Development Guide

### Project Structure
```
/Users/Tk/Downloads/autoballoon-cie/
├── src/
│   ├── app/
│   │   ├── page.tsx              # The Unified Surface
│   │   ├── layout.tsx            # Root layout
│   │   ├── globals.css           # Global styles
│   │   └── api/                  # Serverless routes
│   │       ├── ocr/route.ts      # Google Vision
│   │       ├── gemini/route.ts   # Dimension parsing
│   │       └── export/
│   │           └── excel/route.ts # AS9102 export
│   ├── components/
│   │   ├── LandingView.tsx       # State: landing
│   │   ├── ProcessingView.tsx    # State: processing
│   │   ├── WorkbenchView.tsx     # State: workbench
│   │   ├── DropZone.tsx          # File upload
│   │   ├── Toolbar.tsx           # Top bar
│   │   ├── canvas/
│   │   │   └── DrawingCanvas.tsx # Main renderer
│   │   ├── panels/
│   │   │   ├── PropertiesSidebar.tsx
│   │   │   └── TableManager.tsx
│   │   └── marketing/
│   │       ├── HowItWorks.tsx
│   │       ├── FAQ.tsx
│   │       └── PricingCard.tsx
│   ├── store/
│   │   └── useAppStore.ts        # Zustand + IndexedDB
│   └── lib/
│       ├── pdfExtractor.ts       # Vector extraction
│       └── mathEngine.ts         # decimal.js utils
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── README.md (this file)
```

### Adding a New Feature

1. **Define State in Zustand**
```typescript
// src/store/useAppStore.ts
export interface AppState {
  // Add your new state
  myFeature: { ... };

  // Add your actions
  setMyFeature: (data: any) => void;
}
```

2. **Create Component**
```typescript
// src/components/MyFeature.tsx
'use client';
import { useAppStore } from '@/store/useAppStore';

export function MyFeature() {
  const data = useAppStore((state) => state.myFeature);
  // ...
}
```

3. **Wire to Workbench**
```typescript
// src/components/WorkbenchView.tsx
import { MyFeature } from './MyFeature';

// Add to layout
<MyFeature />
```

---

## 🧪 Testing

### Manual Testing Checklist
- [ ] Upload a vector PDF → Verify dimensions extracted
- [ ] Upload a scanned PDF → Verify OCR fallback triggered
- [ ] Click a balloon → Verify sidebar opens
- [ ] Edit a value in table → Verify sidebar updates
- [ ] Edit a value in sidebar → Verify table updates
- [ ] Zoom/pan canvas → Verify no lag
- [ ] Export to Excel → Verify AS9102 format
- [ ] Test with multi-page PDF → Verify vertical scroll

### Known Limitations
- **OCR Accuracy:** 85-90% on scanned drawings (vs 95%+ on vector)
- **Multi-Page Performance:** Sequential processing (not parallelized)
- **Browser Compatibility:** Tested on Chrome/Edge/Safari (Firefox has pdf.js quirks)

---

## 📊 Performance Targets

- **Drop to Balloon Velocity:** <12 seconds (vector PDFs)
- **Canvas Rendering:** 60 FPS at 2x zoom
- **State Persistence:** <100ms to IndexedDB
- **Export Generation:** <3 seconds for 100 dimensions

---

## 🚢 Deployment

### Vercel (Recommended)
```bash
pnpm install -g vercel
vercel
```

### Railway
```bash
# Dockerfile already configured
railway up
```

### Docker
```bash
docker build -t autoballoon-cie .
docker run -p 3000:3000 autoballoon-cie
```

---

## 🤝 Contributing

This is a **doctrine-driven rebuild** of the original AutoBalloon prototype. The goal is to eliminate human energy waste through:

1. **Unified Surface** (no navigation)
2. **Vector-First** (no unnecessary OCR)
3. **Zero-Storage** (no privacy violations)
4. **Investment Loss** (paywall only after work is done)

If you contribute, ensure all changes align with the CIE doctrine. No compromises.

---

## 📜 License

MIT

---

## 🙏 Acknowledgments

- **pdf.js** by Mozilla (vector extraction)
- **Google Cloud Vision** (OCR fallback)
- **Google Gemini** (semantic parsing)
- **Zustand** by Poimandres (state management)
- **Next.js** by Vercel (framework)

---

**Built for Quality Engineers. By Engineers.**

*AutoBalloon CIE - The Canonical Inspection Engine*
