"use client";

import posthog from "posthog-js";
import { PostHogProvider as PHProvider } from "posthog-js/react";
import { useEffect } from "react";

export function PostHogProvider({ children }: { children: React.ReactNode }) {
    useEffect(() => {
        if (
            typeof window !== "undefined" &&
            process.env.NEXT_PUBLIC_POSTHOG_KEY
        ) {
            posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
                api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com",
                capture_pageview: true,
                capture_pageleave: true,
                autocapture: true,          // auto-capture clicks, inputs, form submissions
                session_recording: {
                    maskAllInputs: false,      // set to true if you have sensitive fields
                    maskTextSelector: "",      // don't mask text by default
                },
                loaded: (ph) => {
                    // Disable in development to keep your dashboard clean
                    if (process.env.NODE_ENV === "development") {
                        ph.opt_out_capturing();
                    }
                },
            });
        }
    }, []);

    if (!process.env.NEXT_PUBLIC_POSTHOG_KEY) {
        return <>{children}</>;
    }

    return <PHProvider client={posthog}>{children}</PHProvider>;
}
