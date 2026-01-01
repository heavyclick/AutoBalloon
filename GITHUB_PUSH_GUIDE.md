# GitHub Push Guide - AutoBalloon CIE

**How to Push Your New Codebase to GitHub**

---

## Strategy: Archive Old, Push New

I recommend this approach:

1. **Archive old code** - Create a backup branch called `archive/old-app`
2. **Push new code to main** - Replace with CIE v3.0
3. **Preserve history** - Old commits remain accessible
4. **Clean transition** - Main branch shows new app

This way:
- ✅ Old code isn't lost (can reference later)
- ✅ Git history preserved
- ✅ Clean main branch with new architecture
- ✅ Easy to compare old vs new if needed

---

## Step-by-Step Instructions

### Prerequisites

1. You should be in the new codebase directory:
   ```bash
   cd /Users/Tk/Downloads/autoballoon-cie
   ```

2. You should have Git installed:
   ```bash
   git --version
   # Should show: git version 2.x.x
   ```

3. You should be logged into GitHub on your machine:
   ```bash
   gh auth status
   # OR check: git config user.name
   ```

---

## Part 1: Archive Old Code

First, let's preserve your old code:

### Step 1: Clone Old Repo (if not already local)

```bash
# Navigate to a temp location
cd /Users/Tk/Downloads

# Clone your existing repo
git clone https://github.com/heavyclick/autoballoon.git autoballoon-old

# Enter the directory
cd autoballoon-old
```

### Step 2: Create Archive Branch

```bash
# Create a new branch for the old code
git checkout -b archive/old-app

# Push to GitHub
git push origin archive/old-app
```

**Result:** Your old code is now safely stored in the `archive/old-app` branch on GitHub.

---

## Part 2: Push New Code to Main

Now let's replace the main branch with your new CIE codebase:

### Step 3: Initialize Git in New Codebase

```bash
# Navigate to new codebase
cd /Users/Tk/Downloads/autoballoon-cie

# Initialize git (if not already)
git init

# Check current status
git status
```

### Step 4: Create .gitignore

Make sure you have a proper `.gitignore` file:

```bash
# I'll create this for you below
```

### Step 5: Add Remote

```bash
# Add your GitHub repo as remote
git remote add origin https://github.com/heavyclick/autoballoon.git

# Verify
git remote -v
# Should show:
# origin  https://github.com/heavyclick/autoballoon.git (fetch)
# origin  https://github.com/heavyclick/autoballoon.git (push)
```

### Step 6: Stage All Files

```bash
# Add all files to staging
git add .

# Check what will be committed
git status
```

### Step 7: Create Initial Commit

```bash
git commit -m "feat: AutoBalloon CIE v3.0 - Complete Rebuild

- Rebuilt from scratch following CIE Doctrine
- Next.js 14 with App Router
- Vector-first PDF extraction (pdf.js)
- AI-powered dimension parsing (Google Gemini)
- LemonSqueezy subscription management
- Supabase PostgreSQL with RLS
- Railway deployment configuration
- Investment Loss paywall doctrine
- Zero-storage security model

Core Features Complete (10/12 phases):
✅ Phase 1: Foundation (Next.js, TypeScript, TailwindCSS)
✅ Phase 2: Unified Surface (single-route architecture)
✅ Phase 3: Vector Extraction (pdf.js)
✅ Phase 4: Gemini Semantic Structuring
✅ Phase 5: Canvas Rendering (react-zoom-pan-pinch)
✅ Phase 6: Properties Sidebar + Table Manager
✅ Phase 8: Client-Side Math Engine (decimal.js)
✅ Phase 9: Export System (AS9102 Excel)
✅ Phase 10: Paywall + Pricing (LemonSqueezy)
✅ Railway Deployment Configuration

Pending Features:
⏸️ Phase 7: Manual Balloon Addition
⏸️ Phase 11: CMM Import
⏸️ Phase 12: Revision Compare

Old codebase archived in 'archive/old-app' branch.
Production-ready: 85% complete
Doctrine compliance: 95%

See IMPLEMENTATION_STATUS.md for full details.
"
```

### Step 8: Force Push to Main

⚠️ **Warning:** This will replace the main branch. Old code is safe in `archive/old-app` branch.

```bash
# Force push to main (replacing old code)
git push -f origin main
```

**Alternative (safer):** If you want to keep both codebases:

```bash
# Push to a new branch instead
git checkout -b cie-v3
git push origin cie-v3

# Then manually merge or switch default branch in GitHub settings
```

---

## Part 3: Update GitHub Repository

### Step 9: Update README on GitHub

1. Go to https://github.com/heavyclick/autoballoon
2. Edit README.md (or it will auto-display the new one)
3. Add project description, setup instructions

### Step 10: Add Topics/Tags

1. Go to repository settings
2. Add topics:
   - `autoballoon`
   - `engineering-drawings`
   - `as9102`
   - `fai`
   - `quality-inspection`
   - `nextjs`
   - `typescript`
   - `ai`
   - `lemonsqueezy`
   - `supabase`

### Step 11: Update Repository Description

```
AutoBalloon CIE - AI-powered AS9102 ballooning and inspection report automation. Upload drawings, get ballooned PDFs and Excel reports in seconds.
```

---

## Part 4: Verify Push

### Step 12: Check GitHub

1. Visit https://github.com/heavyclick/autoballoon
2. Verify files are there:
   - `src/` directory
   - `README.md`
   - `package.json`
   - `IMPLEMENTATION_STATUS.md`
   - etc.

3. Check branches:
   - `main` - new CIE codebase
   - `archive/old-app` - old codebase (safe)

### Step 13: Set Default Branch (if needed)

If you pushed to `cie-v3` branch instead of `main`:

1. Go to Settings → Branches
2. Change default branch to `cie-v3`
3. Optionally rename `cie-v3` to `main` later

---

## Automated Commands (Copy-Paste)

Here's the full sequence you can copy-paste:

```bash
# ============================================
# PART 1: Archive Old Code
# ============================================

# Clone old repo
cd /Users/Tk/Downloads
git clone https://github.com/heavyclick/autoballoon.git autoballoon-old
cd autoballoon-old

# Create archive branch
git checkout -b archive/old-app
git push origin archive/old-app

echo "✅ Old code archived in 'archive/old-app' branch"

# ============================================
# PART 2: Push New Code
# ============================================

# Go to new codebase
cd /Users/Tk/Downloads/autoballoon-cie

# Initialize git
git init

# Add remote
git remote add origin https://github.com/heavyclick/autoballoon.git

# Stage all files
git add .

# Commit
git commit -m "feat: AutoBalloon CIE v3.0 - Complete Rebuild

- Rebuilt from scratch following CIE Doctrine
- Next.js 14 with App Router
- Vector-first PDF extraction (pdf.js)
- AI-powered dimension parsing (Google Gemini)
- LemonSqueezy subscription management
- Supabase PostgreSQL with RLS
- Railway deployment configuration

Core Features Complete (10/12 phases)
Production-ready: 85% complete

Old codebase archived in 'archive/old-app' branch.
See IMPLEMENTATION_STATUS.md for details.
"

# Push to main (replace old code)
git push -f origin main

echo "✅ New code pushed to main branch"
echo "🌐 Check: https://github.com/heavyclick/autoballoon"
```

---

## Alternative: Create New Repository

If you prefer to keep the old repo untouched and create a fresh one:

```bash
# Go to new codebase
cd /Users/Tk/Downloads/autoballoon-cie

# Initialize git
git init

# Stage files
git add .

# Commit
git commit -m "feat: AutoBalloon CIE v3.0 - Initial Release"

# Create new repo on GitHub (use gh CLI)
gh repo create autoballoon-cie --public --source=. --remote=origin --push

# OR manually:
# 1. Go to https://github.com/new
# 2. Create repo: autoballoon-cie
# 3. Copy the remote URL
# 4. Run:
#    git remote add origin https://github.com/heavyclick/autoballoon-cie.git
#    git push -u origin main
```

---

## .gitignore File

Make sure you have this `.gitignore`:

```gitignore
# See https://help.github.com/articles/ignoring-files/ for more about ignoring files.

# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local
.env.local
.env

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

## After Pushing

### Update Old Repo (Optional)

If you want to add a notice to the old code:

1. Go to `archive/old-app` branch on GitHub
2. Add a README notice:
   ```markdown
   # ⚠️ ARCHIVED - Old AutoBalloon App

   This branch contains the original AutoBalloon codebase.

   **New Version:** The main branch now contains AutoBalloon CIE v3.0,
   a complete rebuild following the Canonical Inspection Engine doctrine.

   See main branch for the current production code.
   ```

### Connect to Railway

After pushing to GitHub:

1. Go to https://railway.app/new
2. Select "Deploy from GitHub repo"
3. Choose `autoballoon` repository
4. Railway will auto-detect Next.js and deploy
5. Add environment variables
6. Deploy!

---

## Troubleshooting

### "Permission denied (publickey)"

**Solution:**
```bash
# Use HTTPS instead of SSH
git remote set-url origin https://github.com/heavyclick/autoballoon.git

# Or set up SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"
# Follow GitHub SSH setup guide
```

### "Updates were rejected because the remote contains work"

**Solution:**
```bash
# Force push (this is expected when replacing code)
git push -f origin main
```

### "Git not initialized"

**Solution:**
```bash
cd /Users/Tk/Downloads/autoballoon-cie
git init
```

---

## Summary

**What you're doing:**
1. ✅ Old code safe in `archive/old-app` branch
2. ✅ New CIE code in `main` branch
3. ✅ Git history preserved
4. ✅ Ready for Railway deployment

**Next steps:**
1. Push code to GitHub (commands above)
2. Deploy to Railway (see RAILWAY_DEPLOYMENT.md)
3. Test production webhooks
4. Launch! 🚀

---

**Ready to push?** Copy the commands from "Automated Commands" section above and run them!
