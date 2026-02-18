import { createClient } from "@supabase/supabase-js";

/**
 * Supabase Admin client using the SECRET key (formerly "service_role").
 * Used by Stripe webhooks to write to the subscriptions table (bypasses RLS).
 * NEVER expose this client to the browser.
 */
export function createAdminClient() {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const secretKey = process.env.SUPABASE_SECRET_KEY;

    if (!url || !secretKey) {
        throw new Error(
            "Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SECRET_KEY for admin client."
        );
    }

    return createClient(url, secretKey, {
        auth: {
            autoRefreshToken: false,
            persistSession: false,
        },
    });
}
