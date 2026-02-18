"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Check, Sparkles, Zap, Building2 } from "lucide-react";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "€0",
    cadence: "per month",
    icon: Zap,
    tagline: "Great for quick experiments and personal tinkering.",
    highlight: "Kick off with 5 weekly requests at no cost.",
    features: [
      "Up to 5 prompt requests each week",
      "Google sign-in required to access the workspace",
      "Up to 5 clarifying questions per prompt",
      "Baseline blueprint + refined prompt download",
      "Email support within 48 hours",
    ],
    cta: {
      label: "You're on this plan",
      action: "none" as const,
    },
  },
  {
    id: "pro",
    name: "Pro",
    price: "€9.99",
    cadence: "per month",
    icon: Sparkles,
    badge: "Most Popular",
    tagline: "Ship faster with richer context and collaboration tools.",
    highlight: "Unlock 100 monthly requests and premium tooling.",
    features: [
      "Up to 100 prompt requests every month",
      "Priority AI quota with faster retries",
      "Shared prompt workspaces & version history",
      "Advanced tone + output templates library",
      "Firecrawl web enrichment included",
      "Slack notifications for refinement completions",
    ],
    cta: {
      label: "Upgrade to Pro",
      action: "checkout" as const,
    },
  },
  {
    id: "scale",
    name: "Scale",
    price: "€49",
    cadence: "per month",
    icon: Building2,
    tagline: "Compliance-ready prompt ops for larger organizations.",
    highlight: "Everything in Pro plus enterprise controls.",
    features: [
      "Custom model routing & provider failover",
      "Single sign-on (SSO) + granular roles",
      "Audit logs and guardrail policy enforcement",
      "Dedicated success manager & quarterly reviews",
      "Early access to experimental metaprompt packs",
    ],
    cta: {
      label: "Talk to sales",
      action: "mailto" as const,
      href: "mailto:kristijan@kaelux.dev",
    },
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
      const res = await fetch("/api/checkout", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
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
      const res = await fetch("/api/billing/portal", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) });
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
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-16 px-4 py-20 md:px-6">
        {/* ── Header ───────────────────────────────── */}
        <header className="space-y-5 text-center">
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium uppercase tracking-[0.3em] text-slate-400 backdrop-blur-sm">
            <Sparkles className="h-3.5 w-3.5" />
            Plans & Pricing
          </div>
          <h1 className="hero-gradient-text text-4xl font-bold tracking-tight md:text-5xl lg:text-6xl">
            Scale your prompt operations
            <br />
            <span className="text-white/60">with confidence</span>
          </h1>
          <p className="mx-auto max-w-2xl text-base text-slate-400 md:text-lg">
            Start for free with 5 weekly requests. Upgrade to unlock premium
            tooling, priority AI access, and enterprise-grade controls.
          </p>
        </header>

        {/* ── Back to App ──────────────────────────── */}
        <div className="flex justify-center">
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm font-medium text-slate-300 transition duration-200 hover:border-white/25 hover:bg-white/10 hover:text-white"
          >
            ← Back to app
          </Link>
        </div>

        {/* ── Pricing Cards ────────────────────────── */}
        <section id="pricing" className="grid gap-6 md:grid-cols-3 md:items-start">
          {PLANS.map((plan) => {
            const isPro = plan.id === "pro";
            const Icon = plan.icon;

            return (
              <article
                key={plan.id}
                className="group relative flex flex-col overflow-hidden rounded-2xl transition-all duration-500 hover:-translate-y-1"
                style={{
                  // Pro card gets gradient border via a pseudo-element trick
                  padding: isPro ? "1px" : "0",
                  background: isPro
                    ? "linear-gradient(135deg, rgba(168,85,247,0.5), rgba(59,130,246,0.5), rgba(168,85,247,0.3))"
                    : "transparent",
                }}
              >
                {/* Badge */}
                {plan.badge && (
                  <div className="absolute -right-8 top-6 z-10 rotate-45 bg-gradient-to-r from-violet-600 to-blue-600 px-10 py-1 text-[10px] font-bold uppercase tracking-[0.25em] text-white shadow-lg shadow-violet-500/25">
                    {plan.badge}
                  </div>
                )}

                {/* Inner card */}
                <div
                  className={`
                    relative flex h-full flex-col gap-6 rounded-2xl border p-7
                    ${isPro
                      ? "border-transparent bg-[rgba(15,23,42,0.95)] shadow-[0_0_80px_-20px_rgba(139,92,246,0.25),0_0_40px_-15px_rgba(59,130,246,0.2)]"
                      : "border-white/[0.08] bg-[rgba(15,23,42,0.6)] hover:border-white/15 hover:shadow-[0_30px_80px_-40px_rgba(255,255,255,0.06)]"
                    }
                    backdrop-blur-xl transition-all duration-500
                  `}
                >
                  {/* Plan header */}
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <div className={`
                        flex h-10 w-10 items-center justify-center rounded-xl
                        ${isPro
                          ? "bg-gradient-to-br from-violet-500/20 to-blue-500/20 text-violet-400"
                          : plan.id === "scale"
                            ? "bg-gradient-to-br from-amber-500/15 to-orange-500/15 text-amber-400"
                            : "bg-white/[0.06] text-slate-400"
                        }
                      `}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">
                          {plan.name}
                        </h3>
                      </div>
                    </div>

                    {/* Price */}
                    <div className="flex items-baseline gap-1.5">
                      <span className={`text-4xl font-bold tracking-tight ${isPro ? "text-white" : "text-slate-200"}`}>
                        {plan.price}
                      </span>
                      <span className="text-sm font-medium text-slate-500">
                        /{plan.cadence.split(" ")[1]}
                      </span>
                    </div>
                  </div>

                  {/* Highlight */}
                  <p className={`text-sm font-semibold ${isPro ? "text-violet-300/90" : plan.id === "scale" ? "text-amber-300/80" : "text-slate-400"}`}>
                    {plan.highlight}
                  </p>

                  {/* Divider */}
                  <div className={`h-px w-full ${isPro ? "bg-gradient-to-r from-transparent via-violet-500/30 to-transparent" : "bg-white/[0.06]"}`} />

                  {/* Features */}
                  <ul className="flex-1 space-y-3">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3 text-sm">
                        <div className={`
                          mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full
                          ${isPro
                            ? "bg-violet-500/15 text-violet-400"
                            : plan.id === "scale"
                              ? "bg-amber-500/10 text-amber-400/80"
                              : "bg-white/[0.06] text-slate-500"
                          }
                        `}>
                          <Check className="h-3 w-3" strokeWidth={3} />
                        </div>
                        <span className="text-slate-400 leading-relaxed">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA */}
                  <PlanCallToAction
                    plan={plan}
                    userPlan={userPlan}
                    loading={loading}
                    onCheckout={handleCheckout}
                    onManage={handleManageBilling}
                  />
                </div>
              </article>
            );
          })}
        </section>

        {/* ── Contact Section ──────────────────────── */}
        <section
          id="contact"
          className="grid gap-8 rounded-2xl border border-white/[0.08] bg-[rgba(15,23,42,0.5)] p-6 backdrop-blur-xl md:grid-cols-2 md:p-10"
        >
          <div className="space-y-4">
            <p className="text-xs uppercase tracking-[0.4em] text-slate-500">
              Contact
            </p>
            <h2 className="text-3xl font-bold tracking-tight text-slate-200 md:text-4xl">
              Let&apos;s build prompts that scale with your team
            </h2>
            <p className="text-sm text-slate-400 md:text-base leading-relaxed">
              Need a feature walkthrough, billing help, or enterprise quote? Drop us a note and the PromptTriage team will get back to you within one business day.
            </p>
            <div className="space-y-2 text-sm text-slate-500">
              <p>
                Email{" "}
                <a
                  className="text-slate-300 underline underline-offset-4 hover:text-white transition-colors"
                  href="mailto:kristijan@kaelux.dev"
                >
                  kristijan@kaelux.dev
                </a>
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <form
              className="space-y-4 rounded-2xl border border-white/[0.06] bg-[rgba(15,23,42,0.5)] p-6"
              action="https://formspree.io/f/xdknzjwa"
              method="POST"
            >
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500" htmlFor="contact-name">
                  Name
                </label>
                <input
                  id="contact-name"
                  name="name"
                  type="text"
                  required
                  className="w-full rounded-xl border border-white/[0.08] bg-[rgba(15,23,42,0.6)] px-4 py-3 text-sm text-slate-200 placeholder:text-slate-600 focus:border-violet-500/40 focus:outline-none focus:ring-2 focus:ring-violet-500/10 transition-all"
                  placeholder="Your name"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500" htmlFor="contact-email">
                  Work email
                </label>
                <input
                  id="contact-email"
                  name="_replyto"
                  type="email"
                  required
                  className="w-full rounded-xl border border-white/[0.08] bg-[rgba(15,23,42,0.6)] px-4 py-3 text-sm text-slate-200 placeholder:text-slate-600 focus:border-violet-500/40 focus:outline-none focus:ring-2 focus:ring-violet-500/10 transition-all"
                  placeholder="you@company.com"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500" htmlFor="contact-message">
                  How can we help?
                </label>
                <textarea
                  id="contact-message"
                  name="message"
                  rows={4}
                  required
                  className="w-full rounded-xl border border-white/[0.08] bg-[rgba(15,23,42,0.6)] px-4 py-3 text-sm text-slate-200 placeholder:text-slate-600 focus:border-violet-500/40 focus:outline-none focus:ring-2 focus:ring-violet-500/10 transition-all resize-none"
                  placeholder="Tell us about your workflow or feature request..."
                />
              </div>
              <button
                type="submit"
                className="inline-flex w-full items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] px-5 py-3 text-sm font-semibold text-slate-200 transition-all duration-300 hover:border-white/25 hover:bg-white/10 hover:text-white"
              >
                Send message
              </button>
            </form>
            <p className="text-xs text-slate-600">
              By submitting this form you agree to our processing of your personal data for the purpose of contacting you regarding PromptTriage.
            </p>
          </div>
        </section>

        {/* ── Footer CTA ───────────────────────────── */}
        <footer className="mx-auto max-w-3xl text-center space-y-3">
          <p className="text-lg font-semibold text-slate-300">
            Need a custom deployment or yearly billing?
          </p>
          <p className="text-sm text-slate-500">
            We can tailor PromptTriage to your security, compliance, and
            workflow needs.{" "}
            <Link className="text-violet-400 underline underline-offset-4 hover:text-violet-300 transition-colors" href="mailto:kristijan@kaelux.dev">
              Contact sales
            </Link>{" "}
            for a bespoke quote.
          </p>
        </footer>
      </main>
    </div>
  );
}

function PlanCallToAction({
  plan,
  userPlan,
  loading,
  onCheckout,
  onManage,
}: {
  plan: (typeof PLANS)[number];
  userPlan: string;
  loading: boolean;
  onCheckout: () => void;
  onManage: () => void;
}) {
  const isPro = userPlan === "PRO" || userPlan === "SCALE";
  const isProCard = plan.id === "pro";

  // Free plan card
  if (plan.id === "free") {
    if (isPro) {
      return (
        <span className="inline-flex items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03] px-5 py-3 text-sm font-medium text-slate-500">
          Included in your plan
        </span>
      );
    }
    return (
      <span className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] px-5 py-3 text-sm font-medium text-slate-400">
        ✓ Current plan
      </span>
    );
  }

  // Pro plan card
  if (plan.id === "pro") {
    if (isPro) {
      return (
        <button
          type="button"
          onClick={onManage}
          disabled={loading}
          className="inline-flex w-full items-center justify-center rounded-xl border border-violet-500/20 bg-violet-500/10 px-5 py-3.5 text-sm font-semibold text-violet-300 transition-all duration-300 hover:border-violet-500/40 hover:bg-violet-500/15 hover:text-violet-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Loading..." : "Manage Subscription"}
        </button>
      );
    }
    return (
      <button
        type="button"
        onClick={onCheckout}
        disabled={loading}
        className="group/btn relative inline-flex w-full items-center justify-center overflow-hidden rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 px-5 py-3.5 text-sm font-bold text-white shadow-lg shadow-violet-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-violet-500/30 hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="absolute inset-0 bg-gradient-to-r from-violet-500 to-blue-500 opacity-0 transition-opacity duration-300 group-hover/btn:opacity-100" />
        <span className="relative flex items-center gap-2">
          <Sparkles className="h-4 w-4" />
          {loading ? "Redirecting to checkout..." : "Upgrade to Pro"}
        </span>
      </button>
    );
  }

  // Scale plan card
  return (
    <Link
      href={plan.cta.href ?? "mailto:kristijan@kaelux.dev"}
      className={`inline-flex w-full items-center justify-center rounded-xl border border-amber-500/15 bg-amber-500/[0.06] px-5 py-3.5 text-sm font-semibold text-amber-300/80 transition-all duration-300 hover:border-amber-500/30 hover:bg-amber-500/10 hover:text-amber-200 ${isProCard ? "" : ""}`}
    >
      {plan.cta.label}
    </Link>
  );
}
