import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { stripe } from "@/lib/stripe";

export async function POST(req: Request) {
    try {
        // 1. Authenticate user
        const supabase = await createClient();
        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user?.email) {
            return NextResponse.json(
                { error: "You must be signed in to manage billing." },
                { status: 401 }
            );
        }

        // 2. Find their Stripe customer ID from subscriptions table
        const { data: sub } = await supabase
            .from("subscriptions")
            .select("stripe_customer_id")
            .eq("user_id", user.id)
            .single();

        if (!sub?.stripe_customer_id) {
            return NextResponse.json(
                { error: "No active subscription found." },
                { status: 404 }
            );
        }

        // 3. Create a Customer Portal session
        const origin =
            req.headers.get("origin") ??
            process.env.NEXT_PUBLIC_APP_URL ??
            "http://localhost:3000";

        const session = await stripe.billingPortal.sessions.create({
            customer: sub.stripe_customer_id,
            return_url: `${origin}/pricing`,
        });

        return NextResponse.json({ url: session.url });
    } catch (error) {
        console.error("[billing-portal] error:", error);
        const message =
            error instanceof Error ? error.message : "Portal creation failed.";
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
