"use client";

import Link from "next/link";
import { useState, useEffect } from "react";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "€0",
    cadence: "per month",
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
      variant: "outlined" as const,
    },
  },
  {
    id: "pro",
    name: "Pro",
    price: "€9.99",
    cadence: "per month",
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
      variant: "primary" as const,
    },
  },
  {
    id: "scale",
    name: "Scale",
    price: "€49",
    cadence: "per month",
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
      href: "mailto:hello@promptrefiner.app",
      variant: "ghost" as const,
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
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-4 py-16 md:px-6">
        <header className="space-y-4 text-center">
          <p className="text-xs uppercase tracking-[0.4em] text-muted">
            Plans & Pricing
          </p>
          <h1 className="hero-gradient-text text-4xl font-semibold md:text-5xl">
            Scale your prompt operations with confidence
          </h1>
          <p className="mx-auto max-w-3xl text-base text-muted md:text-lg">
            Start for free and upgrade when you need premium guardrails,
            collaboration tooling, and enterprise controls. Every account begins
            on the <span className="text-soft font-semibold">Free</span> plan.
          </p>
        </header>

        <div className="flex justify-center">
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full border border-[rgba(148,163,184,0.35)] bg-[var(--surface-card)] px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-soft transition duration-200 hover:-translate-y-0.5 hover:border-[rgba(148,163,184,0.55)] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/60"
          >
            Back to app
          </Link>
        </div>

        <section id="pricing" className="grid gap-6 md:grid-cols-3">
          {PLANS.map((plan) => (
            <article
              key={plan.id}
              className={`flex flex-col gap-5 rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-6 backdrop-blur transition duration-300 hover:-translate-y-1 hover:border-white/20 hover:shadow-[0_45px_95px_-70px_rgba(255,255,255,0.12)] ${plan.id === "pro" ? "md:-translate-y-4 md:shadow-[0_60px_110px_-80px_rgba(16,185,129,0.55)]" : ""
                }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.4em] text-muted">
                  <span>{plan.name}</span>
                  <span>{plan.cadence}</span>
                </div>
                <p className="text-soft text-3xl font-semibold">
                  {plan.price}
                  <span className="text-base font-medium text-muted">/{plan.cadence.split(" ")[1]}</span>
                </p>
              </div>
              <p className="text-sm font-semibold text-soft">{plan.highlight}</p>
              <p className="text-sm text-muted">{plan.tagline}</p>
              <ul className="space-y-3 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-soft)] p-4 text-sm text-muted">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <span className="mt-1 h-2 w-2 rounded-full bg-white/90" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              <PlanCallToAction
                plan={plan}
                userPlan={userPlan}
                loading={loading}
                onCheckout={handleCheckout}
                onManage={handleManageBilling}
              />
            </article>
          ))}
        </section>

        <section
          id="contact"
          className="grid gap-8 rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-6 md:p-10 md:grid-cols-2"
        >
          <div className="space-y-4">
            <p className="text-xs uppercase tracking-[0.4em] text-muted">
              Contact
            </p>
            <h2 className="text-3xl font-semibold text-soft md:text-4xl">
              Let&apos;s build prompts that scale with your team
            </h2>
            <p className="text-sm text-muted md:text-base">
              Need a feature walkthrough, billing help, or enterprise quote? Drop us a note and the PromptTriage team will get back to you within one business day.
            </p>
            <div className="space-y-2 text-sm text-muted">
              <p>
                Email{" "}
                <a
                  className="text-slate-300 underline underline-offset-4 hover:text-white"
                  href="mailto:hello@promptrefiner.app"
                >
                  hello@promptrefiner.app
                </a>
              </p>
              <p>
                Slack Community{" "}
                <a
                  className="text-slate-300 underline underline-offset-4 hover:text-white"
                  href="https://promptrefiner.app/slack"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  promptrefiner.app/slack
                </a>
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <form
              className="space-y-4 rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card-soft)] p-6"
              action="https://formspree.io/f/xdknzjwa"
              method="POST"
            >
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.3em] text-muted" htmlFor="contact-name">
                  Name
                </label>
                <input
                  id="contact-name"
                  name="name"
                  type="text"
                  required
                  className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card)] px-4 py-3 text-sm text-soft placeholder:text-muted focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20"
                  placeholder="Your name"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.3em] text-muted" htmlFor="contact-email">
                  Work email
                </label>
                <input
                  id="contact-email"
                  name="_replyto"
                  type="email"
                  required
                  className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card)] px-4 py-3 text-sm text-soft placeholder:text-muted focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20"
                  placeholder="you@company.com"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-[0.3em] text-muted" htmlFor="contact-message">
                  How can we help?
                </label>
                <textarea
                  id="contact-message"
                  name="message"
                  rows={4}
                  required
                  className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface-card)] px-4 py-3 text-sm text-soft placeholder:text-muted focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20"
                  placeholder="Tell us about your workflow or feature request..."
                />
              </div>
              <button
                type="submit"
                className="inline-flex items-center justify-center rounded-full border border-white/25 bg-gradient-to-r from-white/15 via-white/10 to-white/15 px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-soft shadow-[0_20px_45px_-28px_rgba(255,255,255,0.25)] transition duration-300 hover:-translate-y-0.5 hover:scale-[1.04] hover:border-white/50 hover:text-white"
              >
                Send message
              </button>
            </form>
            <p className="text-xs text-muted">
              By submitting this form you agree to our processing of your personal data for the purpose of contacting you regarding PromptTriage.
            </p>
          </div>
        </section>

        <footer className="mx-auto max-w-4xl rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-5 md:p-8 text-center text-sm text-muted">
          <p className="text-soft text-lg font-semibold">
            Need a custom deployment or yearly billing?
          </p>
          <p className="mt-2">
            We can tailor PromptTriage to your security, compliance, and
            workflow needs. <Link className="text-slate-300 underline underline-offset-4 hover:text-white" href="mailto:hello@promptrefiner.app">Contact sales</Link> for a bespoke quote.
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
  plan: typeof PLANS[number];
  userPlan: string;
  loading: boolean;
  onCheckout: () => void;
  onManage: () => void;
}) {
  const isPro = userPlan === "PRO" || userPlan === "SCALE";

  // Free plan card
  if (plan.id === "free") {
    if (isPro) {
      return (
        <span className="inline-flex items-center justify-center rounded-full border border-white/20 bg-white/5 px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-slate-300">
          Included
        </span>
      );
    }
    return (
      <span className="inline-flex items-center justify-center rounded-full border border-white/20 bg-white/5 px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-slate-300">
        You&apos;re on this plan
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
          className="inline-flex items-center justify-center rounded-full border border-white/25 bg-gradient-to-r from-white/15 via-white/10 to-white/15 px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-soft shadow-[0_20px_45px_-28px_rgba(255,255,255,0.25)] transition duration-300 hover:-translate-y-0.5 hover:scale-[1.04] hover:border-white/50 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
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
        className="inline-flex items-center justify-center rounded-full border border-white/25 bg-gradient-to-r from-white/15 via-white/10 to-white/15 px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-soft shadow-[0_20px_45px_-28px_rgba(255,255,255,0.25)] transition duration-300 hover:-translate-y-0.5 hover:scale-[1.04] hover:border-white/50 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Redirecting..." : "Upgrade to Pro"}
      </button>
    );
  }

  // Scale plan card
  return (
    <Link
      href={plan.cta.href ?? "mailto:hello@promptrefiner.app"}
      className="inline-flex items-center justify-center rounded-full border border-[var(--surface-border)] bg-transparent px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-soft transition duration-300 hover:-translate-y-0.5 hover:scale-[1.03] hover:border-[rgba(148,163,184,0.65)] hover:text-white"
    >
      {plan.cta.label}
    </Link>
  );
}
