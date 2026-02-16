"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { useTheme } from "@/components/theme-provider";
import { motion } from "framer-motion";
import { ArrowUpRight, Moon, Sun, Sparkles, Shield, Zap } from "lucide-react";

export default function LoginPage() {
    const [supabase] = useState(() => createClient());
    const [loading, setLoading] = useState(false);
    const { theme, toggleTheme } = useTheme();
    const isLight = theme === "light";

    const handleGoogleSignIn = async () => {
        setLoading(true);
        await supabase.auth.signInWithOAuth({
            provider: "google",
            options: {
                redirectTo: `${window.location.origin}/auth/callback`,
            },
        });
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-[var(--background)] px-6 text-[var(--foreground)]">
            {/* Theme toggle — top right */}
            <div className="fixed right-6 top-6 z-50">
                <button
                    type="button"
                    onClick={toggleTheme}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[rgba(148,163,184,0.2)] bg-transparent text-[var(--text-muted)] transition duration-300 hover:scale-110 hover:border-[rgba(148,163,184,0.5)] hover:text-[var(--foreground)]"
                    aria-label="Toggle theme"
                >
                    {isLight ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
                </button>
            </div>

            {/* Main card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="flex w-full max-w-md flex-col items-center gap-8"
            >
                {/* Branding */}
                <div className="flex flex-col items-center gap-4 text-center">
                    <Link
                        href="https://kaelux.dev"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.35em] text-[var(--text-muted)] transition duration-300 hover:text-[var(--foreground)]"
                    >
                        <span>A Kaelux Technologies Product</span>
                        <ArrowUpRight className="h-3.5 w-3.5" />
                    </Link>

                    <h1 className="hero-gradient-text text-3xl font-semibold md:text-4xl">
                        PromptTriage
                    </h1>

                    <p className="max-w-sm text-sm text-[var(--text-muted)] md:text-base">
                        Write better prompts. Get better results. Sign in to access
                        RAG-powered prompt refinement.
                    </p>
                </div>

                {/* Auth card */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="w-full rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-8 backdrop-blur-xl"
                >
                    <div className="flex flex-col gap-6">
                        <div className="text-center">
                            <h2 className="text-lg font-semibold text-[var(--text-soft)]">
                                Welcome
                            </h2>
                            <p className="mt-1 text-sm text-[var(--text-muted)]">
                                Sign in with your Google account to continue
                            </p>
                        </div>

                        <button
                            type="button"
                            onClick={handleGoogleSignIn}
                            disabled={loading}
                            className="group flex w-full items-center justify-center gap-3 rounded-2xl border border-[rgba(148,163,184,0.25)] bg-[var(--surface-card-soft)] px-6 py-3.5 text-sm font-semibold text-[var(--text-soft)] transition duration-300 hover:-translate-y-0.5 hover:border-[rgba(148,163,184,0.5)] hover:text-[var(--foreground)] hover:shadow-[0_20px_50px_-20px_rgba(255,255,255,0.15)] disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {/* Google icon */}
                            <svg
                                className="h-5 w-5"
                                viewBox="0 0 24 24"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path
                                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                                    fill="#4285F4"
                                />
                                <path
                                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                    fill="#34A853"
                                />
                                <path
                                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                    fill="#FBBC05"
                                />
                                <path
                                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                    fill="#EA4335"
                                />
                            </svg>
                            {loading ? "Redirecting..." : "Continue with Google"}
                        </button>

                        <p className="text-center text-xs text-[var(--text-muted)]">
                            By signing in, you agree to our terms of service and privacy
                            policy.
                        </p>
                    </div>
                </motion.div>

                {/* Feature highlights */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                    className="grid w-full grid-cols-3 gap-3"
                >
                    {[
                        {
                            icon: <Sparkles className="h-4 w-4" />,
                            label: "28,000+ Patterns",
                        },
                        {
                            icon: <Zap className="h-4 w-4" />,
                            label: "Multi-Modal",
                        },
                        {
                            icon: <Shield className="h-4 w-4" />,
                            label: "RAG-Powered",
                        },
                    ].map((feature) => (
                        <div
                            key={feature.label}
                            className="flex flex-col items-center gap-2 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-soft)] p-4 text-center"
                        >
                            <span className="text-[var(--text-muted)]">{feature.icon}</span>
                            <span className="text-xs font-medium text-[var(--text-muted)]">
                                {feature.label}
                            </span>
                        </div>
                    ))}
                </motion.div>

                {/* Pricing link */}
                <p className="text-xs text-[var(--text-muted)]">
                    Curious about plans?{" "}
                    <Link
                        href="/pricing"
                        className="text-[var(--text-soft)] underline underline-offset-4 transition hover:text-[var(--foreground)]"
                    >
                        View pricing
                    </Link>
                </p>
            </motion.div>
        </div>
    );
}
