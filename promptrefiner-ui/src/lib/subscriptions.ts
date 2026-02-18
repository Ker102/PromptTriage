import { createClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";

export type SubscriptionPlan = "FREE" | "PRO" | "SCALE";

export interface Subscription {
    id: string;
    user_id: string;
    stripe_customer_id: string;
    stripe_subscription_id: string | null;
    plan: SubscriptionPlan;
    status: string;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
}

/**
 * Get the current user's subscription plan (server-side).
 * Falls back to FREE if no subscription row exists.
 */
export async function getUserPlan(userId: string): Promise<SubscriptionPlan> {
    const supabase = await createClient();
    const { data } = await supabase
        .from("subscriptions")
        .select("plan, status")
        .eq("user_id", userId)
        .single();

    if (!data || data.status !== "active") {
        return "FREE";
    }

    return (data.plan as SubscriptionPlan) ?? "FREE";
}

/**
 * Upsert a subscription record via admin client (bypasses RLS).
 * Called from Stripe webhooks.
 */
export async function upsertSubscription(params: {
    userId: string;
    stripeCustomerId: string;
    stripeSubscriptionId: string;
    plan: SubscriptionPlan;
    status: string;
    currentPeriodStart?: Date;
    currentPeriodEnd?: Date;
    cancelAtPeriodEnd?: boolean;
}) {
    const admin = createAdminClient();

    const { error } = await admin.from("subscriptions").upsert(
        {
            user_id: params.userId,
            stripe_customer_id: params.stripeCustomerId,
            stripe_subscription_id: params.stripeSubscriptionId,
            plan: params.plan,
            status: params.status,
            current_period_start: params.currentPeriodStart?.toISOString() ?? null,
            current_period_end: params.currentPeriodEnd?.toISOString() ?? null,
            cancel_at_period_end: params.cancelAtPeriodEnd ?? false,
        },
        { onConflict: "user_id" }
    );

    if (error) {
        console.error("[subscriptions] upsert failed:", error);
        throw new Error(`Subscription upsert failed: ${error.message}`);
    }
}

/**
 * Find the Supabase user_id linked to a Stripe customer.
 */
export async function findUserByStripeCustomer(
    stripeCustomerId: string
): Promise<string | null> {
    const admin = createAdminClient();

    // First check subscriptions table
    const { data } = await admin
        .from("subscriptions")
        .select("user_id")
        .eq("stripe_customer_id", stripeCustomerId)
        .single();

    if (data?.user_id) {
        return data.user_id;
    }

    // Fallback: look up by email via Stripe customer → auth.users
    return null;
}
