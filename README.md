# AutoBalloon

**Automatic dimension ballooning for manufacturing blueprints.**

Get your AS9102 Excel report in 10 seconds. AI-powered dimension detection for First Article Inspection.

![AutoBalloon](https://autoballoon.space/og-image.png)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Google Cloud API Key (Vision API)
- Gemini API Key
- Supabase account
- Paystack account (for payments)
- Resend account (for emails)

### Local Development

1. **Clone and setup environment:**

```bash
cd autoballoon

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your API keys

# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Frontend setup (new terminal):**

```bash
cd frontend
npm install

# Start frontend
npm run dev
```

3. **Access the app:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Development

```bash
# Copy environment variables
cp backend/.env.example .env

# Start all services
docker-compose up --build
```

## 📁 Project Structure

```
autoballoon/
├── backend/
│   ├── api/                  # FastAPI routes
│   │   ├── routes.py         # Core processing endpoints
│   │   ├── auth_routes.py    # Authentication (magic links)
│   │   ├── payment_routes.py # Paystack integration
│   │   ├── usage_routes.py   # Usage tracking
│   │   └── history_routes.py # Pro user history
│   ├── services/             # Business logic
│   │   ├── file_service.py   # PDF/image processing
│   │   ├── ocr_service.py    # Google Cloud Vision
│   │   ├── vision_service.py # Gemini AI
│   │   ├── detection_service.py # OCR + Gemini fusion
│   │   ├── grid_service.py   # Zone detection
│   │   ├── export_service.py # CSV/Excel export
│   │   ├── auth_service.py   # Authentication
│   │   ├── payment_service.py # Paystack
│   │   ├── usage_service.py  # Usage limits
│   │   ├── history_service.py # Cloud storage
│   │   └── email_service.py  # Resend emails
│   ├── models/               # Pydantic schemas
│   ├── config.py             # Configuration
│   ├── main.py               # FastAPI app
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── DropZone.jsx  # Main upload component
│   │   │   ├── PaywallModal.jsx
│   │   │   ├── Navbar.jsx
│   │   │   └── ...
│   │   ├── pages/            # Route pages
│   │   │   ├── LandingPage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── VerifyPage.jsx
│   │   │   └── SuccessPage.jsx
│   │   ├── context/          # React context
│   │   │   └── AuthContext.jsx
│   │   ├── hooks/            # Custom hooks
│   │   │   └── useUsage.js
│   │   └── constants/
│   │       └── config.js
│   ├── Dockerfile
│   └── nginx.conf
├── supabase/
│   └── migrations/           # Database schema
└── docker-compose.yml
```

## 🗄️ Database Setup (Supabase)

1. Create a new Supabase project at https://app.supabase.com
2. Go to SQL Editor
3. Run the migration file: `supabase/migrations/001_initial_schema.sql`
4. Copy your credentials from Project Settings > API:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_KEY` (service_role key)

## 💳 Payment Setup (Paystack)

1. Create a Paystack account at https://dashboard.paystack.com
2. Go to Settings > API Keys & Webhooks
3. Copy your keys:
   - `PAYSTACK_PUBLIC_KEY`
   - `PAYSTACK_SECRET_KEY`
4. Create a subscription plan:
   - Go to Products > Plans
   - Create plan: $99/month (or NGN equivalent)
   - Copy the plan code: `PAYSTACK_PLAN_CODE`
5. Set up webhook:
   - URL: `https://yourdomain.com/api/payments/webhook`
   - Events: charge.success, subscription.create, subscription.disable

## 📧 Email Setup (Resend)

1. Create account at https://resend.com
2. Verify your domain (autoballoon.space)
3. Get API key from https://resend.com/api-keys
4. Set `RESEND_API_KEY` and `EMAIL_FROM`

## 🚀 Production Deployment

### AWS Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Route 53                              │
│                   autoballoon.space                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐      ┌─────────────────────┐
│     CloudFront      │      │    App Runner       │
│  (Frontend - S3)    │      │    (Backend)        │
└─────────────────────┘      └─────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
            ┌───────────┐    ┌───────────┐    ┌───────────┐
            │  Supabase │    │  Paystack │    │   Resend  │
            │  (DB)     │    │ (Payments)│    │  (Email)  │
            └───────────┘    └───────────┘    └───────────┘
```

### Deployment Steps

1. **Frontend (S3 + CloudFront):**

```bash
cd frontend

# Build for production
VITE_API_URL=https://api.autoballoon.space/api \
VITE_APP_URL=https://autoballoon.space \
npm run build

# Upload to S3
aws s3 sync dist/ s3://autoballoon-frontend --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

2. **Backend (App Runner):**

```bash
cd backend

# Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

docker build -t autoballoon-backend .
docker tag autoballoon-backend:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/autoballoon-backend:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/autoballoon-backend:latest

# App Runner will auto-deploy from ECR
```

3. **Environment Variables (AWS Secrets Manager):**

Store all sensitive keys in Secrets Manager and reference them in App Runner.

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLOUD_API_KEY` | Google Cloud Vision API | Yes |
| `GEMINI_API_KEY` | Gemini AI API | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes |
| `PAYSTACK_PUBLIC_KEY` | Paystack public key | Yes |
| `PAYSTACK_SECRET_KEY` | Paystack secret key | Yes |
| `PAYSTACK_PLAN_CODE` | Subscription plan code | Yes |
| `RESEND_API_KEY` | Resend email API key | Yes |
| `JWT_SECRET` | Secret for JWT tokens | Yes |
| `APP_URL` | Frontend URL | Yes |

## 📊 Business Model

- **Free Tier:** 3 drawings/month, no signup required
- **Pro:** $99/month unlimited (Early Adopter pricing, locked in forever)
- **Future Price:** $199/month

## 🛠️ API Endpoints

### Processing
- `POST /api/process` - Upload and process blueprint
- `POST /api/export` - Export to CSV/Excel

### Authentication
- `POST /api/auth/magic-link` - Request login link
- `POST /api/auth/verify` - Verify magic link token
- `GET /api/auth/me` - Get current user

### Payments
- `GET /api/payments/pricing` - Get pricing info
- `POST /api/payments/create-checkout` - Create Paystack checkout
- `GET /api/payments/verify/:reference` - Verify payment
- `POST /api/payments/webhook` - Paystack webhook

### Usage
- `GET /api/usage/check` - Check usage limits
- `POST /api/usage/increment` - Increment usage

### History (Pro only)
- `GET /api/history` - List history
- `POST /api/history` - Save to history
- `DELETE /api/history/:id` - Delete entry

## 📄 License

Proprietary - All rights reserved.

## 🤝 Support

- Email: support@autoballoon.space
- Documentation: https://docs.autoballoon.space
