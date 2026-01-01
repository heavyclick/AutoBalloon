/**
 * Create LemonSqueezy Checkout Session
 *
 * Security:
 * - API key stays server-side
 * - Validates plan type
 * - Pre-fills customer email if authenticated
 */

import { NextRequest, NextResponse } from 'next/server';
import { createCheckout } from '@/lib/lemonsqueezy';
import { supabase } from '@/lib/supabase';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { plan_type, visitor_id } = body;

    // Validate plan type
    if (!plan_type || !['tier_20', 'tier_99'].includes(plan_type)) {
      return NextResponse.json(
        { error: 'Invalid plan type' },
        { status: 400 }
      );
    }

    // Get variant ID from environment
    const variantId = plan_type === 'tier_20'
      ? process.env.LEMONSQUEEZY_TIER_20_VARIANT_ID!
      : process.env.LEMONSQUEEZY_TIER_99_VARIANT_ID!;

    if (!variantId) {
      return NextResponse.json(
        { error: 'Product variant not configured' },
        { status: 500 }
      );
    }

    // Get current user email (if authenticated)
    const { data: { user } } = await supabase.auth.getUser();
    const email = user?.email;

    // Create checkout session
    const { checkoutUrl } = await createCheckout({
      email,
      variantId,
      customData: {
        user_id: user?.id,
        visitor_id,
        plan_type,
      },
    });

    return NextResponse.json({ checkoutUrl });
  } catch (error: any) {
    console.error('Checkout creation error:', error);
    return NextResponse.json(
      { error: 'Failed to create checkout', message: error.message },
      { status: 500 }
    );
  }
}
