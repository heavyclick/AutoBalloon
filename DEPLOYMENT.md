# Deployment Guide - AutoBalloon CIE v3.0

This guide covers deploying CIE to production environments.

---

## 🌐 Deployment Options

### 1. Vercel (Fastest, Recommended)

**Advantages:**
- Zero-config Next.js deployment
- Automatic HTTPS + CDN
- Serverless functions out of the box
- Free tier available

**Steps:**
```bash
# Install Vercel CLI
pnpm install -g vercel

# Login
vercel login

# Deploy
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_GOOGLE_VISION_API_KEY
vercel env add NEXT_PUBLIC_GEMINI_API_KEY
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_ROLE_KEY
vercel env add PAYSTACK_SECRET_KEY
vercel env add PAYSTACK_PUBLIC_KEY

# Deploy to production
vercel --prod
```

**Custom Domain:**
```bash
vercel domains add autoballoon.space
```

---

### 2. Railway

**Advantages:**
- Simple Dockerfile deployment
- Postgres database included
- Fair pricing ($5/month base)

**Steps:**
1. Create `railway.json`:
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "npm start",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100
  }
}
```

2. Deploy:
```bash
railway login
railway init
railway up
```

3. Set environment variables in Railway dashboard

---

### 3. Docker (Self-Hosted)

**Create production Dockerfile:**
```dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN corepack enable pnpm && pnpm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

**Build and run:**
```bash
docker build -t autoballoon-cie .
docker run -p 3000:3000 --env-file .env autoballoon-cie
```

---

## 🔐 Environment Variables (Production)

### Required
```env
# Google APIs
NEXT_PUBLIC_GOOGLE_VISION_API_KEY=AIzaSy...
NEXT_PUBLIC_GEMINI_API_KEY=AIzaSy...

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...

# Paystack
PAYSTACK_SECRET_KEY=sk_live_xxx...
PAYSTACK_PUBLIC_KEY=pk_live_xxx...

# App
NEXT_PUBLIC_APP_URL=https://autoballoon.space
NODE_ENV=production
```

### Optional
```env
# Pricing Caps
TIER_20_DAILY_CAP=30
TIER_20_MONTHLY_CAP=150
TIER_99_DAILY_CAP=100
TIER_99_MONTHLY_CAP=500

# Feature Flags
ENABLE_REVISION_COMPARE=true
ENABLE_CMM_IMPORT=true
```

---

## 📊 Performance Optimization

### 1. Next.js Static Optimization
```javascript
// next.config.js
module.exports = {
  output: 'standalone',

  // Enable React Compiler (experimental)
  experimental: {
    reactCompiler: true,
  },

  // Image optimization
  images: {
    domains: ['autoballoon.space'],
    formats: ['image/avif', 'image/webp'],
  },
}
```

### 2. CDN Configuration (Cloudflare)
```
Cache Rules:
- /_next/static/* → Cache everything, 1 year
- /api/* → Do not cache
- / → Cache HTML, 1 hour
```

### 3. Database Indexes (Supabase)
```sql
-- Speed up usage queries
CREATE INDEX idx_usage_user_month ON usage(user_id, created_at DESC);

-- Speed up history queries
CREATE INDEX idx_history_user_created ON history(user_id, created_at DESC);
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions (Example)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Run type check
        run: pnpm run type-check

      - name: Build
        run: pnpm run build
        env:
          NEXT_PUBLIC_GOOGLE_VISION_API_KEY: ${{ secrets.GOOGLE_VISION_API_KEY }}
          NEXT_PUBLIC_GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}

      - name: Deploy to Vercel
        run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

---

## 📈 Monitoring

### 1. Vercel Analytics
```typescript
// src/app/layout.tsx
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

### 2. Error Tracking (Sentry)
```bash
pnpm add @sentry/nextjs
```

```typescript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
});
```

### 3. Performance Monitoring
```typescript
// Track extraction time
const start = performance.now();
await extractPDFPages(file);
const duration = performance.now() - start;

// Log to analytics
analytics.track('pdf_extraction_complete', {
  duration_ms: duration,
  pages: totalPages,
});
```

---

## 🛡️ Security Checklist

- [ ] All API keys in environment variables (never in code)
- [ ] HTTPS enabled (automatic on Vercel/Railway)
- [ ] CORS configured for API routes
- [ ] Rate limiting on API endpoints
- [ ] Input validation on all forms
- [ ] Content Security Policy (CSP) headers
- [ ] Supabase RLS policies enabled

### CSP Headers
```javascript
// next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.jsdelivr.net;
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: blob:;
      font-src 'self' data:;
      connect-src 'self' https://vision.googleapis.com https://generativelanguage.googleapis.com https://*.supabase.co;
    `.replace(/\s{2,}/g, ' ').trim()
  }
];

module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ];
  },
};
```

---

## 📞 Support & Maintenance

**Logs:**
- Vercel: `vercel logs --follow`
- Railway: Railway dashboard → Logs tab
- Docker: `docker logs -f container_id`

**Database Backups:**
```bash
# Supabase automatic daily backups
# Manual backup:
supabase db dump > backup_$(date +%Y%m%d).sql
```

**Rollback:**
```bash
# Vercel
vercel rollback

# Railway
railway rollback [deployment_id]
```

---

**Production Checklist:**
- [ ] All environment variables set
- [ ] Database migrations run
- [ ] HTTPS configured
- [ ] Custom domain configured
- [ ] Analytics enabled
- [ ] Error tracking enabled
- [ ] Backups configured
- [ ] Monitoring dashboard set up
- [ ] Load tested (100 concurrent users)
- [ ] SEO meta tags configured

---

*Last updated: 2024-12-19*
