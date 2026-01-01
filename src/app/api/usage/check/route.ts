/**
 * Usage Check API
 *
 * Returns current usage statistics and remaining quota
 *
 * Supports:
 * - Authenticated users (via Supabase auth)
 * - Anonymous users (via visitor fingerprint)
 */

import { NextRequest, NextResponse } from 'next/server';
import { supabase, getCurrentUser, getUsageRecord } from '@/lib/supabase';

export async function GET(request: NextRequest) {
  try {
    // Get visitor ID from query params (for anonymous users)
    const visitorId = request.nextUrl.searchParams.get('visitor_id');

    // Get current user (if authenticated)
    const user = await getCurrentUser();
    const userId = user?.id;

    if (!userId && !visitorId) {
      return NextResponse.json(
        { error: 'No user ID or visitor ID provided' },
        { status: 400 }
      );
    }

    // Get usage record
    const record = await getUsageRecord(userId, visitorId);

    if (!record) {
      return NextResponse.json(
        { error: 'Usage record not found' },
        { status: 404 }
      );
    }

    // Determine caps based on subscription tier
    let dailyCap = 0;
    let monthlyCap = 0;

    if (user?.subscription_tier === 'tier_20') {
      dailyCap = parseInt(process.env.TIER_20_DAILY_CAP || '30');
      monthlyCap = parseInt(process.env.TIER_20_MONTHLY_CAP || '150');
    } else if (user?.subscription_tier === 'tier_99') {
      dailyCap = parseInt(process.env.TIER_99_DAILY_CAP || '100');
      monthlyCap = parseInt(process.env.TIER_99_MONTHLY_CAP || '500');
    }

    // Calculate remaining
    const dailyRemaining = dailyCap > 0 ? Math.max(0, dailyCap - record.daily_count) : 999;
    const monthlyRemaining = monthlyCap > 0 ? Math.max(0, monthlyCap - record.monthly_count) : 999;

    // Check if at limit
    const atDailyLimit = dailyCap > 0 && record.daily_count >= dailyCap;
    const atMonthlyLimit = monthlyCap > 0 && record.monthly_count >= monthlyCap;

    return NextResponse.json({
      usage: {
        daily: record.daily_count,
        monthly: record.monthly_count,
      },
      caps: {
        daily: dailyCap,
        monthly: monthlyCap,
      },
      remaining: {
        daily: dailyRemaining,
        monthly: monthlyRemaining,
      },
      limits: {
        daily: atDailyLimit,
        monthly: atMonthlyLimit,
        any: atDailyLimit || atMonthlyLimit,
      },
      subscription: {
        tier: user?.subscription_tier || 'free',
        status: user?.subscription_status || 'free',
        is_pro: user?.is_pro || false,
      },
      reset_dates: {
        daily: record.daily_reset_at,
        monthly: record.monthly_reset_at,
      },
    });
  } catch (error: any) {
    console.error('Usage check error:', error);
    return NextResponse.json(
      { error: 'Failed to check usage', message: error.message },
      { status: 500 }
    );
  }
}

/**
 * Increment usage counter
 * Called after successful upload/processing
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { visitor_id } = body;

    // Get current user
    const user = await getCurrentUser();
    const userId = user?.id;

    if (!userId && !visitor_id) {
      return NextResponse.json(
        { error: 'No user ID or visitor ID provided' },
        { status: 400 }
      );
    }

    // Increment usage
    const { incrementUsage } = await import('@/lib/supabase');
    const result = await incrementUsage(userId, visitor_id);

    if (!result.success) {
      return NextResponse.json(
        {
          error: 'Usage limit reached',
          remaining: result.remaining,
        },
        { status: 429 }
      );
    }

    return NextResponse.json({
      success: true,
      remaining: result.remaining,
    });
  } catch (error: any) {
    console.error('Usage increment error:', error);
    return NextResponse.json(
      { error: 'Failed to increment usage', message: error.message },
      { status: 500 }
    );
  }
}
