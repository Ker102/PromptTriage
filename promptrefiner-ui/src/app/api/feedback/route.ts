import { NextResponse } from "next/server";

/**
 * POST /api/feedback
 * 
 * Receives error feedback from the ErrorFeedback component.
 * Sends an email notification to the dev via a simple webhook/email service.
 * Falls back to logging if email is not configured.
 */
export async function POST(req: Request) {
    try {
        const body = await req.json();

        const { errorMessage, feedback, email, context } = body;

        if (!feedback || typeof feedback !== "string") {
            return NextResponse.json(
                { error: "Feedback text is required" },
                { status: 400 }
            );
        }

        // Log feedback to server console (always available)
        console.log("━".repeat(60));
        console.log("📩 USER FEEDBACK RECEIVED");
        console.log("━".repeat(60));
        console.log(`Error: ${errorMessage}`);
        console.log(`Feedback: ${feedback}`);
        if (email) console.log(`Reply-to: ${email}`);
        console.log(`Context:`, JSON.stringify(context, null, 2));
        console.log("━".repeat(60));

        // Option 1: Send email via configured SMTP/webhook
        const feedbackWebhookUrl = process.env.FEEDBACK_WEBHOOK_URL;

        if (feedbackWebhookUrl) {
            try {
                await fetch(feedbackWebhookUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        subject: `[PromptTriage Bug] ${errorMessage?.slice(0, 80)}`,
                        text: [
                            `**Error:** ${errorMessage}`,
                            `**User Feedback:** ${feedback}`,
                            email ? `**Reply-to:** ${email}` : "",
                            `**Context:**`,
                            `- Action: ${context?.action ?? "unknown"}`,
                            `- Modality: ${context?.modality ?? "unknown"}`,
                            `- Model: ${context?.targetModel ?? "unknown"}`,
                            `- Thinking Mode: ${context?.thinkingMode ?? false}`,
                            `- Browser: ${context?.browser ?? "unknown"}`,
                            `- Timestamp: ${context?.timestamp ?? new Date().toISOString()}`,
                            `- URL: ${context?.url ?? "unknown"}`,
                        ]
                            .filter(Boolean)
                            .join("\n"),
                    }),
                });
            } catch (webhookError) {
                console.error("Webhook delivery failed:", webhookError);
                // Don't fail the request — we already logged it
            }
        }

        return NextResponse.json({ status: "received" });
    } catch (error) {
        console.error("Feedback submission error:", error);
        return NextResponse.json(
            { error: "Failed to process feedback" },
            { status: 500 }
        );
    }
}
