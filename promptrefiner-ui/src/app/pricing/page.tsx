"use client";

import Link from "next/link";
import { useState, useEffect } from "react";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "€0",
    cadence: "per month",
    tagline: "For quick experiments and personal tinkering.",
    features: [
      "5 prompt requests per week",
      "Google sign-in access",
      "5 clarifying questions per prompt",
      "Blueprint + refined prompt download",
      "Email support (48h response)",
    ],
  },
  {
    id: "pro",
    name: "Pro",
    price: "€9.99",
    cadence: "per month",
    popular: true,
    tagline: "For teams shipping faster with premium tooling.",
    features: [
      "100 prompt requests per month",
      "Priority AI quota & faster retries",
      "Shared workspaces & version history",
      "Advanced tone & output templates",
      "Firecrawl web enrichment",
      "Slack notifications for completions",
    ],
  },
  {
    id: "scale",
    name: "Scale",
    price: "€49",
    cadence: "per month",
    tagline: "For organizations needing compliance & control.",
    features: [
      "Everything in Pro",
      "Custom model routing & failover",
      "SSO + granular role management",
      "Audit logs & guardrail enforcement",
      "Dedicated success manager",
      "Early access to metaprompt packs",
    ],
  },
];

export default function PricingPage() {
  const [loading, setLoading] = useState(false);
  const [userPlan, setUserPlan] = useState<string>("FREE");

  useEffect(() => {
    fetch("/api/subscription")
      .then((r) => r.json())
      .then((data) => setUserPlan(data.plan ?? "FREE"))
      .catch(() => setUserPlan("FREE"));
  }, []);

  async function handleCheckout() {
    setLoading(true);
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert(data.error || "Something went wrong. Please try again.");
        setLoading(false);
      }
    } catch {
      alert("Could not start checkout. Are you signed in?");
      setLoading(false);
    }
  }

  async function handleManageBilling() {
    setLoading(true);
    try {
      const res = await fetch("/api/billing/portal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert(data.error || "Could not open billing portal.");
        setLoading(false);
      }
    } catch {
      alert("Could not open billing portal.");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-16 px-4 py-24 md:px-6">
        {/* Header */}
        <header className="space-y-4 text-center">
          <p className="text-[11px] font-medium uppercase tracking-[0.35em] text-slate-500">
            Pricing
          </p>
          <h1 className="text-4xl font-bold tracking-tight text-white md:text-5xl">
            Simple, transparent pricing
          </h1>
          <p className="mx-auto max-w-lg text-[15px] leading-relaxed text-slate-400">
            Start free. Upgrade when you need more power.
          </p>
          <div className="pt-2">
            <Link
              href="/"
              className="text-sm text-slate-500 transition-colors hover:text-white"
            >
              ← Back to app
            </Link>
          </div>
        </header>

        {/* Cards */}
        <section className="grid gap-5 md:grid-cols-3">
          {PLANS.map((plan) => {
            const isPro = plan.id === "pro";
            return (
              <div
                key={plan.id}
                className={`
                  relative flex flex-col rounded-2xl transition-all duration-300 hover:-translate-y-0.5
                  ${isPro ? "pricing-card-pro" : ""}
                `}
              >
                {/* Gradient top-line accent for Pro */}
                {isPro && (
                  <div
                    className="absolute inset-x-0 top-0 h-[2px] rounded-t-2xl"
                    style={{
                      background: "linear-gradient(90deg, #7c3aed, #3b82f6, #06b6d4)",
                    }}
                  />
                )}

                <div
                  className={`
                    flex h-full flex-col rounded-2xl border px-6 py-7
                    ${isPro
                      ? "border-white/[0.12] bg-[rgba(15,23,42,0.85)]"
                      : "border-white/[0.06] bg-[rgba(15,23,42,0.45)]"
                    }
                  `}
                >
                  {/* Plan name + badge */}
                  <div className="flex items-center gap-3">
                    <h3 className="text-[13px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                      {plan.name}
                    </h3>
                    {plan.popular && (
                      <span
                        className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-white/90"
                        style={{
                          background: "linear-gradient(135deg, #7c3aed, #3b82f6)",
                        }}
                      >
                        Popular
                      </span>
                    )}
                  </div>

                  {/* Price */}
                  <div className="mt-4 flex items-baseline gap-1">
                    <span className={`text-4xl font-bold tracking-tight ${isPro ? "text-white" : "text-slate-200"}`}>
                      {plan.price}
                    </span>
                    <span className="text-sm text-slate-600">/mo</span>
                  </div>

                  {/* Tagline */}
                  <p className="mt-3 text-[13px] leading-relaxed text-slate-500">
                    {plan.tagline}
                  </p>

                  {/* Divider */}
                  <div className="my-5 h-px bg-white/[0.06]" />

                  {/* Features */}
                  <ul className="flex-1 space-y-3">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2.5 text-[13px]">
                        <svg
                          className={`mt-[3px] h-3.5 w-3.5 flex-shrink-0 ${isPro ? "text-blue-400/70" : plan.id === "scale" ? "text-slate-400/50" : "text-slate-600"
                            }`}
                          viewBox="0 0 16 16"
                          fill="none"
                        >
                          <path
                            d="M3 8.5L6.5 12L13 4"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                        <span className="text-slate-400">{f}</span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA */}
                  <div className="mt-6">
                    <PlanCTA
                      planId={plan.id}
                      userPlan={userPlan}
                      loading={loading}
                      onCheckout={handleCheckout}
                      onManage={handleManageBilling}
                      href={plan.id === "scale" ? "mailto:kristijan@kaelux.dev" : undefined}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </section>

        {/* Contact */}
        <section className="grid gap-8 rounded-2xl border border-white/[0.06] bg-[rgba(15,23,42,0.4)] p-6 md:grid-cols-2 md:p-10">
          <div className="space-y-4">
            <h2 className="text-2xl font-bold tracking-tight text-slate-200">
              Need a custom plan?
            </h2>
            <p className="text-sm leading-relaxed text-slate-500">
              We can tailor PromptTriage to your security, compliance, and
              workflow needs. Reach out for yearly billing or enterprise
              deployment options.
            </p>
            <p className="text-sm text-slate-600">
              <a
                className="text-slate-400 underline underline-offset-4 transition-colors hover:text-white"
                href="mailto:kristijan@kaelux.dev"
              >
                kristijan@kaelux.dev
              </a>
            </p>
          </div>

          <form
            className="space-y-4 rounded-xl border border-white/[0.06] bg-[rgba(15,23,42,0.4)] p-5"
            action="https://formspree.io/f/xdknzjwa"
            method="POST"
          >
            <input
              name="name"
              type="text"
              required
              className="w-full rounded-lg border border-white/[0.06] bg-transparent px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-white/15 focus:outline-none transition-colors"
              placeholder="Name"
            />
            <input
              name="_replyto"
              type="email"
              required
              className="w-full rounded-lg border border-white/[0.06] bg-transparent px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-white/15 focus:outline-none transition-colors"
              placeholder="Work email"
            />
            <textarea
              name="message"
              rows={3}
              required
              className="w-full rounded-lg border border-white/[0.06] bg-transparent px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-white/15 focus:outline-none transition-colors resize-none"
              placeholder="How can we help?"
            />
            <button
              type="submit"
              className="w-full rounded-lg border border-white/[0.08] bg-white/[0.04] py-2.5 text-sm font-medium text-slate-300 transition-all hover:border-white/15 hover:bg-white/[0.08] hover:text-white"
            >
              Send message
            </button>
          </form>
        </section>
      </main>

      <style jsx>{`
        .pricing-card-pro {
          box-shadow:
            0 0 0 1px rgba(124, 58, 237, 0.08),
            0 20px 60px -15px rgba(124, 58, 237, 0.08),
            0 8px 24px -8px rgba(59, 130, 246, 0.06);
        }
        .pricing-card-pro:hover {
          box-shadow:
            0 0 0 1px rgba(124, 58, 237, 0.12),
            0 25px 70px -15px rgba(124, 58, 237, 0.12),
            0 12px 30px -8px rgba(59, 130, 246, 0.08);
        }
      `}</style>
    </div>
  );
}

function PlanCTA({
  planId,
  userPlan,
  loading,
  onCheckout,
  onManage,
  href,
}: {
  planId: string;
  userPlan: string;
  loading: boolean;
  onCheckout: () => void;
  onManage: () => void;
  href?: string;
}) {
  const isPaidUser = userPlan === "PRO" || userPlan === "SCALE";

  if (planId === "free") {
    return (
      <div className="rounded-lg border border-white/[0.06] py-2.5 text-center text-sm text-slate-600">
        {isPaidUser ? "Included" : "Current plan"}
      </div>
    );
  }

  if (planId === "pro") {
    if (isPaidUser) {
      return (
        <button
          onClick={onManage}
          disabled={loading}
          className="w-full rounded-lg border border-white/[0.08] bg-white/[0.04] py-2.5 text-sm font-medium text-slate-300 transition-all hover:border-white/15 hover:bg-white/[0.08] hover:text-white disabled:opacity-50"
        >
          {loading ? "Loading..." : "Manage Subscription"}
        </button>
      );
    }
    return (
      <button
        onClick={onCheckout}
        disabled={loading}
        className="w-full rounded-lg py-2.5 text-sm font-semibold text-white transition-all duration-300 hover:opacity-90 hover:-translate-y-px disabled:opacity-50"
        style={{
          background: "linear-gradient(135deg, #7c3aed, #3b82f6)",
          boxShadow: "0 4px 20px -4px rgba(124, 58, 237, 0.35)",
        }}
      >
        {loading ? "Redirecting..." : "Upgrade to Pro →"}
      </button>
    );
  }

  // Scale
  return (
    <Link
      href={href ?? "mailto:kristijan@kaelux.dev"}
      className="block w-full rounded-lg border border-white/[0.08] bg-white/[0.04] py-2.5 text-center text-sm font-medium text-slate-300 transition-all hover:border-white/15 hover:bg-white/[0.08] hover:text-white"
    >
      Talk to sales →
    </Link>
  );
}
