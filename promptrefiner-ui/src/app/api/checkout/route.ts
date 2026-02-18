import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { stripe, getOrCreateCustomer } from "@/lib/stripe";

export async function POST(req: Request) {
    try {
        // 1. Authenticate user
        const supabase = await createClient();
        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user?.email) {
            return NextResponse.json(
                { error: "You must be signed in to subscribe." },
                { status: 401 }
            );
        }

        // 2. Parse request body
        const body = await req.json();
        const priceId = body.priceId ?? process.env.STRIPE_PRO_PRICE_ID;

        if (!priceId) {
            return NextResponse.json(
                { error: "No price ID configured. Contact support." },
                { status: 500 }
            );
        }

        // 3. Get or create Stripe customer
        const customerId = await getOrCreateCustomer(
            user.email,
            user.id,
            user.user_metadata?.full_name ?? user.user_metadata?.name
        );

        // 4. Create Checkout Session
        const origin = req.headers.get("origin") ?? process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

        const session = await stripe.checkout.sessions.create({
            customer: customerId,
            mode: "subscription",
            line_items: [{ price: priceId, quantity: 1 }],
            success_url: `${origin}/?upgraded=true`,
            cancel_url: `${origin}/pricing`,
            subscription_data: {
                metadata: {
                    supabase_user_id: user.id,
                },
            },
            metadata: {
                supabase_user_id: user.id,
            },
        });

        return NextResponse.json({ url: session.url });
    } catch (error) {
        console.error("[checkout] error:", error);
        const message =
            error instanceof Error ? error.message : "Checkout creation failed.";
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
