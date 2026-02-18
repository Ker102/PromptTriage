import { NextResponse } from "next/server";
import { headers } from "next/headers";
import { stripe } from "@/lib/stripe";
import {
    upsertSubscription,
    findUserByStripeCustomer,
} from "@/lib/subscriptions";
import type Stripe from "stripe";

// Disable Next.js body parsing — Stripe needs the raw body for signature verification
export const runtime = "nodejs";

export async function POST(req: Request) {
    const body = await req.text();
    const headersList = await headers();
    const signature = headersList.get("stripe-signature");

    if (!signature) {
        return NextResponse.json(
            { error: "Missing stripe-signature header." },
            { status: 400 }
        );
    }

    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
    if (!webhookSecret) {
        console.error("[stripe-webhook] STRIPE_WEBHOOK_SECRET is not configured.");
        return NextResponse.json(
            { error: "Webhook secret not configured." },
            { status: 500 }
        );
    }

    let event: Stripe.Event;

    try {
        event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
    } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        console.error(`[stripe-webhook] Signature verification failed: ${message}`);
        return NextResponse.json(
            { error: `Webhook signature verification failed: ${message}` },
            { status: 400 }
        );
    }

    try {
        switch (event.type) {
            case "checkout.session.completed": {
                const session = event.data.object as Stripe.Checkout.Session;
                await handleCheckoutCompleted(session);
                break;
            }
            case "customer.subscription.updated": {
                const subscription = event.data.object as Stripe.Subscription;
                await handleSubscriptionUpdated(subscription);
                break;
            }
            case "customer.subscription.deleted": {
                const subscription = event.data.object as Stripe.Subscription;
                await handleSubscriptionDeleted(subscription);
                break;
            }
            default:
                console.log(`[stripe-webhook] Unhandled event type: ${event.type}`);
        }
    } catch (error) {
        console.error(`[stripe-webhook] Handler error for ${event.type}:`, error);
        return NextResponse.json(
            { error: "Webhook handler failed." },
            { status: 500 }
        );
    }

    return NextResponse.json({ received: true });
}

// ── Handlers ──────────────────────────────────────────────

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
    const customerId = session.customer as string;
    const subscriptionId = session.subscription as string;
    const userId = session.metadata?.supabase_user_id;

    if (!userId) {
        console.error("[stripe-webhook] No supabase_user_id in session metadata.");
        return;
    }

    // Fetch the subscription to get period details
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const sub = await stripe.subscriptions.retrieve(subscriptionId) as any;

    await upsertSubscription({
        userId,
        stripeCustomerId: customerId,
        stripeSubscriptionId: subscriptionId,
        plan: "PRO",
        status: "active",
        currentPeriodStart: sub.current_period_start ? new Date(sub.current_period_start * 1000) : undefined,
        currentPeriodEnd: sub.current_period_end ? new Date(sub.current_period_end * 1000) : undefined,
        cancelAtPeriodEnd: sub.cancel_at_period_end ?? false,
    });

    console.log(`[stripe-webhook] ✅ Checkout completed for user ${userId} → PRO`);
}

async function handleSubscriptionUpdated(subscription: Stripe.Subscription) {
    const customerId = subscription.customer as string;
    const userId =
        subscription.metadata?.supabase_user_id ??
        (await findUserByStripeCustomer(customerId));

    if (!userId) {
        console.error(
            `[stripe-webhook] Cannot find user for customer ${customerId}`
        );
        return;
    }

    // Map Stripe status to our plan
    const isActive = ["active", "trialing"].includes(subscription.status);
    const plan = isActive ? "PRO" : "FREE";
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const sub = subscription as any;

    await upsertSubscription({
        userId,
        stripeCustomerId: customerId,
        stripeSubscriptionId: subscription.id,
        plan,
        status: subscription.status,
        currentPeriodStart: sub.current_period_start ? new Date(sub.current_period_start * 1000) : undefined,
        currentPeriodEnd: sub.current_period_end ? new Date(sub.current_period_end * 1000) : undefined,
        cancelAtPeriodEnd: sub.cancel_at_period_end ?? false,
    });

    console.log(
        `[stripe-webhook] 🔄 Subscription updated for user ${userId}: ${subscription.status} → ${plan}`
    );
}

async function handleSubscriptionDeleted(subscription: Stripe.Subscription) {
    const customerId = subscription.customer as string;
    const userId =
        subscription.metadata?.supabase_user_id ??
        (await findUserByStripeCustomer(customerId));

    if (!userId) {
        console.error(
            `[stripe-webhook] Cannot find user for customer ${customerId}`
        );
        return;
    }

    await upsertSubscription({
        userId,
        stripeCustomerId: customerId,
        stripeSubscriptionId: subscription.id,
        plan: "FREE",
        status: "canceled",
        cancelAtPeriodEnd: false,
    });

    console.log(
        `[stripe-webhook] ❌ Subscription deleted for user ${userId} → FREE`
    );
}
