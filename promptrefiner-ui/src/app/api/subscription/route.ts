import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { getRemainingUsage } from "@/services/usage-limit";

/**
 * GET /api/subscription
 * Returns the current user's subscription plan, status, and remaining usage.
 */
export async function GET() {
    try {
        const supabase = await createClient();
        const {
            data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
            return NextResponse.json({ plan: "FREE", status: "none" });
        }

        // Dev bypass
        const isDev =
            process.env.ALLOW_DEV_BYPASS === "true" &&
            process.env.NEXT_PUBLIC_DEV_SUPERUSER === "true";

        if (isDev) {
            return NextResponse.json({ plan: "PRO", status: "active" });
        }

        const { data: sub } = await supabase
            .from("subscriptions")
            .select("plan, status, current_period_end, cancel_at_period_end")
            .eq("user_id", user.id)
            .single();

        const plan = sub && sub.status === "active" ? sub.plan : "FREE";
        const usage = user.email
            ? getRemainingUsage(user.email, plan as string)
            : undefined;

        return NextResponse.json({
            plan,
            status: sub?.status ?? "none",
            currentPeriodEnd: sub?.current_period_end ?? null,
            cancelAtPeriodEnd: sub?.cancel_at_period_end ?? null,
            usage,
        });
    } catch (error) {
        console.error("[subscription] error:", error);
        return NextResponse.json({ plan: "FREE", status: "error" });
    }
}

