/**
 * LemonSqueezy Webhook Handler
 *
 * Processes subscription events:
 * - subscription_created
 * - subscription_updated
 * - subscription_cancelled
 * - subscription_expired
 * - subscription_payment_success
 *
 * Security:
 * - HMAC signature verification
 * - Idempotency via webhook_events table
 * - Service role key for database access
 */

import { NextRequest, NextResponse } from 'next/server';
import { verifyWebhookSignature, processWebhookEvent } from '@/lib/lemonsqueezy';
import { getServiceSupabase } from '@/lib/supabase';

export async function POST(request: NextRequest) {
  try {
    // Get raw body for signature verification
    const rawBody = await request.text();
    const signature = request.headers.get('x-signature');

    if (!signature) {
      console.error('Missing webhook signature');
      return NextResponse.json({ error: 'Missing signature' }, { status: 401 });
    }

    // Verify signature
    const webhookSecret = process.env.LEMONSQUEEZY_WEBHOOK_SECRET!;
    const isValid = verifyWebhookSignature(rawBody, signature, webhookSecret);

    if (!isValid) {
      console.error('Invalid webhook signature');
      return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
    }

    // Parse event
    const event = JSON.parse(rawBody);
    const eventType = event.meta?.event_name;
    const eventId = event.meta?.custom_data?.lemonsqueezy_event_id;

    console.log('Webhook received:', eventType, eventId);

    // Get service Supabase client (bypasses RLS)
    const supabase = getServiceSupabase();

    // Check if event already processed (idempotency)
    if (eventId) {
      const { data: existingEvent } = await supabase
        .from('webhook_events')
        .select('id')
        .eq('lemonsqueezy_event_id', eventId)
        .single();

      if (existingEvent) {
        console.log('Event already processed:', eventId);
        return NextResponse.json({ message: 'Event already processed' });
      }
    }

    // Log webhook event
    const { data: webhookLog } = await supabase
      .from('webhook_events')
      .insert({
        event_type: eventType,
        lemonsqueezy_event_id: eventId,
        payload: event,
        processed: false,
      })
      .select()
      .single();

    // Process event
    const { action, subscriptionData } = await processWebhookEvent(event);

    // Extract relevant data
    const subscriptionId = event.data.id;
    const customerId = subscriptionData.customer_id?.toString();
    const variantId = subscriptionData.variant_id?.toString();
    const status = subscriptionData.status;
    const renewsAt = subscriptionData.renews_at;
    const endsAt = subscriptionData.ends_at;
    const customData = event.meta?.custom_data;
    const userId = customData?.user_id;

    // Determine plan type from variant ID
    const tier20Variant = process.env.LEMONSQUEEZY_TIER_20_VARIANT_ID;
    const tier99Variant = process.env.LEMONSQUEEZY_TIER_99_VARIANT_ID;
    let planType: 'tier_20' | 'tier_99' | null = null;

    if (variantId === tier20Variant) {
      planType = 'tier_20';
    } else if (variantId === tier99Variant) {
      planType = 'tier_99';
    }

    if (!planType) {
      console.error('Unknown variant ID:', variantId);
      throw new Error('Unknown variant ID');
    }

    // Handle subscription_created
    if (action === 'created') {
      // Find user by email (from LemonSqueezy customer email)
      const customerEmail = subscriptionData.user_email;

      let targetUserId = userId;

      if (!targetUserId && customerEmail) {
        // Try to find user by email
        const { data: authUser } = await supabase.auth.admin.getUserByEmail(customerEmail);
        targetUserId = authUser?.user?.id;
      }

      if (!targetUserId) {
        console.error('Cannot determine user ID for subscription');
        throw new Error('User not found');
      }

      // Update or create user record
      const { error: userError } = await supabase
        .from('users')
        .upsert({
          id: targetUserId,
          email: customerEmail,
          is_pro: true,
          subscription_status: planType,
          subscription_tier: planType,
          lemonsqueezy_customer_id: customerId,
          lemonsqueezy_subscription_id: subscriptionId,
          subscription_started_at: new Date().toISOString(),
          subscription_ends_at: endsAt,
        });

      if (userError) {
        console.error('Failed to update user:', userError);
        throw userError;
      }

      // Create subscription record
      const { error: subError } = await supabase
        .from('subscriptions')
        .insert({
          user_id: targetUserId,
          lemonsqueezy_subscription_id: subscriptionId,
          lemonsqueezy_customer_id: customerId,
          lemonsqueezy_variant_id: variantId,
          lemonsqueezy_product_id: subscriptionData.product_id?.toString(),
          plan_type: planType,
          status: status,
          renews_at: renewsAt,
          ends_at: endsAt,
          currency: subscriptionData.currency,
          price_cents: subscriptionData.total_price_cents,
        });

      if (subError) {
        console.error('Failed to create subscription:', subError);
        throw subError;
      }

      console.log('Subscription created:', subscriptionId, planType);
    }

    // Handle subscription_updated
    if (action === 'updated') {
      // Update subscription record
      const { error: subError } = await supabase
        .from('subscriptions')
        .update({
          status: status,
          renews_at: renewsAt,
          ends_at: endsAt,
        })
        .eq('lemonsqueezy_subscription_id', subscriptionId);

      if (subError) {
        console.error('Failed to update subscription:', subError);
        throw subError;
      }

      // Update user record
      const { error: userError } = await supabase
        .from('users')
        .update({
          subscription_status: status === 'active' ? planType : 'cancelled',
          subscription_ends_at: endsAt,
        })
        .eq('lemonsqueezy_subscription_id', subscriptionId);

      if (userError) {
        console.error('Failed to update user:', userError);
        throw userError;
      }

      console.log('Subscription updated:', subscriptionId, status);
    }

    // Handle subscription_cancelled / subscription_expired
    if (action === 'cancelled') {
      // Update subscription record
      const { error: subError } = await supabase
        .from('subscriptions')
        .update({
          status: 'cancelled',
          ends_at: endsAt,
        })
        .eq('lemonsqueezy_subscription_id', subscriptionId);

      if (subError) {
        console.error('Failed to update subscription:', subError);
        throw subError;
      }

      // Update user record
      const { error: userError } = await supabase
        .from('users')
        .update({
          is_pro: false,
          subscription_status: 'cancelled',
          subscription_tier: null,
          subscription_ends_at: endsAt,
        })
        .eq('lemonsqueezy_subscription_id', subscriptionId);

      if (userError) {
        console.error('Failed to update user:', userError);
        throw userError;
      }

      console.log('Subscription cancelled:', subscriptionId);
    }

    // Mark webhook as processed
    if (webhookLog) {
      await supabase
        .from('webhook_events')
        .update({ processed: true })
        .eq('id', webhookLog.id);
    }

    return NextResponse.json({ message: 'Webhook processed', action, subscriptionId });
  } catch (error: any) {
    console.error('Webhook processing error:', error);

    // Log error to database
    const supabase = getServiceSupabase();
    await supabase
      .from('webhook_events')
      .update({ error: error.message })
      .eq('lemonsqueezy_event_id', error.eventId);

    return NextResponse.json(
      { error: 'Webhook processing failed', message: error.message },
      { status: 500 }
    );
  }
}
