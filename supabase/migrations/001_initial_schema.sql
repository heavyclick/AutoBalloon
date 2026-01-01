-- AutoBalloon CIE Database Schema
-- Supabase PostgreSQL with Row Level Security

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  is_pro BOOLEAN DEFAULT FALSE,
  subscription_status TEXT DEFAULT 'free', -- 'free', 'tier_20', 'tier_99', 'cancelled'
  subscription_tier TEXT, -- 'tier_20', 'tier_99'
  lemonsqueezy_customer_id TEXT,
  lemonsqueezy_subscription_id TEXT,
  subscription_started_at TIMESTAMP WITH TIME ZONE,
  subscription_ends_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Usage tracking table
CREATE TABLE IF NOT EXISTS public.usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  visitor_id TEXT, -- For anonymous users (fingerprint)

  -- Counters
  daily_count INTEGER DEFAULT 0,
  monthly_count INTEGER DEFAULT 0,

  -- Reset tracking
  daily_reset_at DATE DEFAULT CURRENT_DATE,
  monthly_reset_at DATE DEFAULT DATE_TRUNC('month', CURRENT_DATE),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Unique constraint: one record per user OR visitor
  UNIQUE(user_id),
  UNIQUE(visitor_id),
  CHECK (user_id IS NOT NULL OR visitor_id IS NOT NULL)
);

-- Subscriptions table (LemonSqueezy webhook data)
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,

  -- LemonSqueezy IDs
  lemonsqueezy_subscription_id TEXT UNIQUE NOT NULL,
  lemonsqueezy_customer_id TEXT NOT NULL,
  lemonsqueezy_order_id TEXT,
  lemonsqueezy_product_id TEXT,
  lemonsqueezy_variant_id TEXT,

  -- Subscription details
  plan_type TEXT NOT NULL, -- 'tier_20', 'tier_99'
  status TEXT NOT NULL, -- 'active', 'cancelled', 'expired', 'paused', 'past_due'

  -- Dates
  starts_at TIMESTAMP WITH TIME ZONE,
  ends_at TIMESTAMP WITH TIME ZONE,
  trial_ends_at TIMESTAMP WITH TIME ZONE,
  renews_at TIMESTAMP WITH TIME ZONE,

  -- Pricing
  currency TEXT,
  price_cents INTEGER,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Webhook events log (for debugging)
CREATE TABLE IF NOT EXISTS public.webhook_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_type TEXT NOT NULL,
  lemonsqueezy_event_id TEXT,
  payload JSONB NOT NULL,
  processed BOOLEAN DEFAULT FALSE,
  error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON public.users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_usage_user_id ON public.usage(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_visitor_id ON public.usage(visitor_id);
CREATE INDEX IF NOT EXISTS idx_usage_daily_reset ON public.usage(daily_reset_at);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON public.webhook_events(processed);

-- Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.webhook_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Users: Can read own data
CREATE POLICY "Users can read own data"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

-- Users: Can update own data
CREATE POLICY "Users can update own data"
  ON public.users FOR UPDATE
  USING (auth.uid() = id);

-- Usage: Users can read own usage
CREATE POLICY "Users can read own usage"
  ON public.usage FOR SELECT
  USING (auth.uid() = user_id);

-- Usage: Service role can manage all usage
CREATE POLICY "Service role can manage usage"
  ON public.usage FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Subscriptions: Users can read own subscriptions
CREATE POLICY "Users can read own subscriptions"
  ON public.subscriptions FOR SELECT
  USING (auth.uid() = user_id);

-- Subscriptions: Service role can manage all
CREATE POLICY "Service role can manage subscriptions"
  ON public.subscriptions FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Webhook events: Only service role can access
CREATE POLICY "Service role can manage webhook events"
  ON public.webhook_events FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Functions

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON public.users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_updated_at
  BEFORE UPDATE ON public.usage
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at
  BEFORE UPDATE ON public.subscriptions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to reset daily usage counters
CREATE OR REPLACE FUNCTION reset_daily_usage()
RETURNS void AS $$
BEGIN
  UPDATE public.usage
  SET daily_count = 0,
      daily_reset_at = CURRENT_DATE
  WHERE daily_reset_at < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Function to reset monthly usage counters
CREATE OR REPLACE FUNCTION reset_monthly_usage()
RETURNS void AS $$
BEGIN
  UPDATE public.usage
  SET monthly_count = 0,
      monthly_reset_at = DATE_TRUNC('month', CURRENT_DATE)
  WHERE monthly_reset_at < DATE_TRUNC('month', CURRENT_DATE);
END;
$$ LANGUAGE plpgsql;

-- Scheduled jobs (run via pg_cron or external cron)
-- Note: Enable pg_cron extension in Supabase dashboard if available
-- Otherwise, use external cron to call these functions via API

-- Comments
COMMENT ON TABLE public.users IS 'Extended user profiles with subscription data';
COMMENT ON TABLE public.usage IS 'Daily and monthly upload usage tracking';
COMMENT ON TABLE public.subscriptions IS 'LemonSqueezy subscription records';
COMMENT ON TABLE public.webhook_events IS 'LemonSqueezy webhook event log';
