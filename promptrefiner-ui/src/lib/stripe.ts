import Stripe from "stripe";

let _stripe: Stripe | null = null;

/**
 * Lazily initialise the Stripe client.
 * We avoid constructing at import-time so the build doesn't crash when
 * STRIPE_SECRET_KEY is absent (e.g. during static page collection).
 */
function getStripe(): Stripe {
    if (!_stripe) {
        const key = process.env.STRIPE_SECRET_KEY;
        if (!key) {
            throw new Error("STRIPE_SECRET_KEY is not set in environment variables.");
        }
        _stripe = new Stripe(key, {
            apiVersion: "2026-01-28.clover",
            typescript: true,
        });
    }
    return _stripe;
}

/** Proxy export so call-sites can keep using `stripe.xyz()` */
export const stripe = new Proxy({} as Stripe, {
    get(_target, prop) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return (getStripe() as any)[prop];
    },
});

/**
 * Get or create a Stripe customer for a Supabase user.
 * Looks up by email first, then creates if not found.
 */
export async function getOrCreateCustomer(
    email: string,
    userId: string,
    name?: string | null
): Promise<string> {
    const s = getStripe();

    // Search for existing customer by email
    const existing = await s.customers.list({ email, limit: 1 });
    if (existing.data.length > 0) {
        return existing.data[0].id;
    }

    // Create new customer linked to Supabase user
    const customer = await s.customers.create({
        email,
        name: name ?? undefined,
        metadata: { supabase_user_id: userId },
    });

    return customer.id;
}
