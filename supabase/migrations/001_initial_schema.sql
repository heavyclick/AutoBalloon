-- AutoBalloon Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    is_pro BOOLEAN DEFAULT FALSE,
    paystack_customer_code TEXT,
    paystack_subscription_code TEXT,
    history_enabled BOOLEAN DEFAULT TRUE,
    grandfathered_price INTEGER DEFAULT 99, -- Locked-in price in dollars
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for email lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================
-- USAGE TRACKING TABLE
-- Tracks both anonymous (visitor_id) and authenticated (user_id) usage
-- ============================================
CREATE TABLE IF NOT EXISTS usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    visitor_id TEXT, -- For anonymous users (stored in localStorage)
    count INTEGER DEFAULT 0,
    month_year TEXT NOT NULL, -- Format: "2025-01"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Either user_id OR visitor_id must be set, not both
    CONSTRAINT usage_user_or_visitor CHECK (
        (user_id IS NOT NULL AND visitor_id IS NULL) OR 
        (user_id IS NULL AND visitor_id IS NOT NULL)
    ),
    
    -- Unique per user per month
    CONSTRAINT unique_user_month UNIQUE (user_id, month_year),
    -- Unique per visitor per month  
    CONSTRAINT unique_visitor_month UNIQUE (visitor_id, month_year)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_usage_user_id ON usage(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_visitor_id ON usage(visitor_id);
CREATE INDEX IF NOT EXISTS idx_usage_month_year ON usage(month_year);

-- ============================================
-- HISTORY TABLE
-- Permanent storage for Pro users (replaces localStorage)
-- ============================================
CREATE TABLE IF NOT EXISTS history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    thumbnail TEXT, -- Base64 encoded or S3 URL
    dimensions JSONB DEFAULT '[]'::jsonb,
    image_data TEXT, -- Base64 encoded or S3 URL
    grid JSONB,
    dimension_count INTEGER DEFAULT 0,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for user's history (sorted by date)
CREATE INDEX IF NOT EXISTS idx_history_user_id ON history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_created_at ON history(created_at DESC);

-- ============================================
-- MAGIC LINKS TABLE
-- Passwordless authentication tokens
-- ============================================
CREATE TABLE IF NOT EXISTS magic_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for token lookups
CREATE INDEX IF NOT EXISTS idx_magic_links_token ON magic_links(token);
CREATE INDEX IF NOT EXISTS idx_magic_links_email ON magic_links(email);

-- Clean up expired tokens (run via cron or Supabase scheduled function)
CREATE INDEX IF NOT EXISTS idx_magic_links_expires ON magic_links(expires_at);

-- ============================================
-- SUBSCRIPTIONS TABLE
-- Track Paystack subscription details
-- ============================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paystack_subscription_code TEXT UNIQUE,
    paystack_plan_code TEXT,
    status TEXT NOT NULL DEFAULT 'active', -- active, cancelled, past_due, expired
    amount INTEGER NOT NULL, -- Amount in kobo/cents
    currency TEXT DEFAULT 'NGN',
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for user subscriptions
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- ============================================
-- PAYMENT EVENTS TABLE
-- Log all Paystack webhook events for debugging
-- ============================================
CREATE TABLE IF NOT EXISTS payment_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    paystack_reference TEXT,
    email TEXT,
    amount INTEGER,
    currency TEXT,
    status TEXT,
    raw_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for debugging
CREATE INDEX IF NOT EXISTS idx_payment_events_email ON payment_events(email);
CREATE INDEX IF NOT EXISTS idx_payment_events_type ON payment_events(event_type);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply to usage table
DROP TRIGGER IF EXISTS update_usage_updated_at ON usage;
CREATE TRIGGER update_usage_updated_at
    BEFORE UPDATE ON usage
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply to subscriptions table
DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE history ENABLE ROW LEVEL SECURITY;
ALTER TABLE magic_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (for backend)
-- These policies allow the service_role key full access

CREATE POLICY "Service role full access to users" ON users
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access to usage" ON usage
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access to history" ON history
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access to magic_links" ON magic_links
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access to subscriptions" ON subscriptions
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access to payment_events" ON payment_events
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- CLEANUP FUNCTION (Optional - for scheduled jobs)
-- ============================================

-- Function to clean up expired magic links
CREATE OR REPLACE FUNCTION cleanup_expired_magic_links()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM magic_links 
    WHERE expires_at < NOW() OR used = TRUE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old anonymous usage records (older than 3 months)
CREATE OR REPLACE FUNCTION cleanup_old_anonymous_usage()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    cutoff_month TEXT;
BEGIN
    cutoff_month := TO_CHAR(NOW() - INTERVAL '3 months', 'YYYY-MM');
    
    DELETE FROM usage 
    WHERE visitor_id IS NOT NULL 
    AND month_year < cutoff_month;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
