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
    <div className="min-h-screen relative flex flex-col font-sans bg-black selection:bg-cyan-500/30">
      {/* 1. TOP BLACK SECTION */}
      <section className="relative w-full bg-black text-white pt-24 pb-24 z-10">
        <header className="mx-auto max-w-6xl px-4 text-center space-y-5 relative z-20">
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400 font-semibold">
            Plans & Pricing
          </p>
          <h1 className="hero-gradient-text text-4xl font-bold tracking-tight md:text-6xl">
            Scale your prompt operations<br className="hidden md:block" /> with confidence
          </h1>
          <p className="mx-auto max-w-2xl text-base text-slate-300 md:text-lg leading-relaxed">
            Start for free and upgrade when you need premium guardrails,
            collaboration tooling, and enterprise controls. Every account begins
            on the <span className="font-semibold text-white">Free</span> plan.
          </p>
          <div className="pt-6 flex justify-center">
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-full border border-white/20 bg-white/5 px-6 py-2.5 text-xs font-semibold uppercase tracking-[0.2em] text-slate-300 transition-all duration-300 hover:-translate-y-0.5 hover:border-white/40 hover:text-white"
            >
              Back to app
            </Link>
          </div>
        </header>
      </section>

      {/* 2. BLACK TO WHITE TRANSITION */}
      <div className="relative w-full h-[300px] md:h-[500px] bg-white">
        <div
          className="absolute inset-0 w-full h-full"
          style={{
            backgroundImage: 'url("/Same_scene_but_4k_202602182323.jpeg")',
            backgroundSize: '100% 100%'
          }}
        />
      </div>

      {/* 3. WHITE CONTENT SECTION */}
      <section className="relative w-full bg-white text-slate-900 pb-20 z-10">
        {/* Floating Background Crystals with Shadows */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
          <img
            src="/whitebgcrystals/Layer 0 - 15whitebg.png"
            alt="Decorative crystal"
            className="absolute -left-16 top-10 w-72 h-auto drop-shadow-2xl"
          />
          <img
            src="/whitebgcrystals/Layer 0 - 6whitebg.png"
            alt="Decorative crystal"
            className="absolute -right-12 top-64 w-56 h-auto drop-shadow-2xl"
          />
          <img
            src="/whitebgcrystals/Layer 0 - 12whitebg.png"
            alt="Decorative crystal"
            className="absolute left-8 bottom-80 w-64 h-auto drop-shadow-2xl"
          />
          <img
            src="/whitebgcrystals/Layer 0 - 5whitebg.png"
            alt="Decorative crystal"
            className="absolute right-8 bottom-[22rem] w-72 h-auto drop-shadow-2xl"
          />
        </div>

        <main className="relative mx-auto max-w-6xl px-4 z-20 space-y-24 -mt-24 md:-mt-40 lg:-mt-56">

          {/* Pricing Cards */}
          <section id="pricing" className="grid gap-8 md:grid-cols-3 items-stretch">
            {PLANS.map((plan) => (
              <article
                key={plan.id}
                className={`flex flex-col gap-6 rounded-3xl border border-slate-200/60 bg-white/70 backdrop-blur-xl p-8 shadow-xl transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl hover:border-slate-300/80
                  ${plan.id === "pro" ? "md:-translate-y-4 ring-1 ring-slate-900/5 hover:ring-slate-900/10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.12)]" : "shadow-[0_10px_40px_-15px_rgba(0,0,0,0.06)]"}
                `}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-[0.3em] text-slate-500">
                    <span>{plan.name}</span>
                    {plan.id === "pro" && <span className="rounded-full bg-slate-900 px-3 py-1 text-[10px] text-white tracking-widest">Popular</span>}
                  </div>
                  <p className="text-5xl font-bold tracking-tight text-slate-900">
                    {plan.price}
                    <span className="text-lg font-medium text-slate-500 tracking-normal">/{plan.cadence.split(" ")[1]}</span>
                  </p>
                </div>

                <div className="space-y-1 py-2">
                  <p className="font-semibold text-slate-900">{plan.highlight}</p>
                  <p className="text-sm text-slate-600 leading-relaxed">{plan.tagline}</p>
                </div>

                <ul className="space-y-4 rounded-2xl border border-slate-100 bg-slate-50/50 p-5 pl-2 text-sm text-slate-700 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3">
                      <svg className="h-5 w-5 shrink-0 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="leading-tight">{feature}</span>
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

          {/* Contact Section */}
          <section
            id="contact"
            className="relative rounded-3xl border border-slate-200/60 bg-white/50 backdrop-blur-xl p-8 md:p-12 shadow-xl hover:shadow-2xl transition-all duration-300 overflow-visible"
          >
            {/* Crystals peeking behind the contact card */}
            <div className="absolute inset-0 -z-10 overflow-visible pointer-events-none">
              <img
                src="/whitebgcrystals/Layer 0 - 18whitebg.png"
                alt=""
                className="absolute -left-24 -bottom-12 w-56 h-auto drop-shadow-2xl"
              />
              <img
                src="/whitebgcrystals/Layer 0 - 14whitebg.png"
                alt=""
                className="absolute -right-20 -top-16 w-64 h-auto drop-shadow-2xl"
              />
              <img
                src="/whitebgcrystals/Layer 0 - 4whitebg.png"
                alt=""
                className="absolute right-1/4 -bottom-10 w-40 h-auto drop-shadow-2xl"
              />
            </div>

            <div className="grid gap-12 md:grid-cols-2 relative z-10">

              <div className="space-y-6 relative z-10 p-2">
                <p className="text-xs font-bold uppercase tracking-[0.3em] text-slate-500">
                  Contact
                </p>
                <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-5xl md:leading-tight">
                  Let&apos;s build prompts that scale with your team
                </h2>
                <p className="text-base text-slate-600 leading-relaxed">
                  Need a feature walkthrough, billing help, or enterprise quote? Drop us a note and the PromptTriage team will get back to you within one business day.
                </p>
                <div className="pt-4 space-y-3 text-sm font-medium text-slate-600">
                  <p className="flex items-center gap-2">
                    <span className="w-16 uppercase tracking-wider text-xs text-slate-400">Email</span>
                    <a className="text-slate-900 underline decoration-slate-300 underline-offset-4 hover:decoration-slate-900 transition-colors" href="mailto:hello@promptrefiner.app">
                      hello@promptrefiner.app
                    </a>
                  </p>
                  <p className="flex items-center gap-2">
                    <span className="w-16 uppercase tracking-wider text-xs text-slate-400">Slack</span>
                    <a className="text-slate-900 underline decoration-slate-300 underline-offset-4 hover:decoration-slate-900 transition-colors" href="https://promptrefiner.app/slack" target="_blank" rel="noopener noreferrer">
                      Join our Community
                    </a>
                  </p>
                </div>
              </div>

              <div className="relative z-10">
                <form
                  className="space-y-5 rounded-3xl border border-slate-200 bg-white p-6 md:p-8 shadow-lg shadow-slate-200/50"
                  action="https://formspree.io/f/xdknzjwa"
                  method="POST"
                >
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500" htmlFor="contact-name">
                      Name
                    </label>
                    <input
                      id="contact-name"
                      name="name"
                      type="text"
                      required
                      className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3.5 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-slate-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-slate-900/5"
                      placeholder="Your name"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500" htmlFor="contact-email">
                      Work email
                    </label>
                    <input
                      id="contact-email"
                      name="_replyto"
                      type="email"
                      required
                      className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3.5 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-slate-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-slate-900/5"
                      placeholder="you@company.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500" htmlFor="contact-message">
                      How can we help?
                    </label>
                    <textarea
                      id="contact-message"
                      name="message"
                      rows={4}
                      required
                      className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3.5 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-slate-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-slate-900/5"
                      placeholder="Tell us about your workflow or feature request..."
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full inline-flex items-center justify-center rounded-xl bg-slate-900 px-5 py-4 text-sm font-bold uppercase tracking-[0.2em] text-white shadow-md transition-all hover:-translate-y-0.5 hover:shadow-xl hover:bg-slate-800"
                  >
                    Send message
                  </button>
                </form>
                <p className="mt-4 px-2 text-center text-[11px] text-slate-500 leading-relaxed">
                  By submitting this form you agree to our processing of your personal data for the purpose of contacting you.
                </p>
              </div>
            </div>
          </section>

        </main>
      </section>

      {/* 4. WHITE TO BLACK TRANSITION */}
      <div className="relative w-full h-[300px] md:h-[400px] bg-black mt-auto">
        <div
          className="absolute inset-0 w-full h-full"
          style={{
            backgroundImage: 'url("/Using_my_brand_4k_202602182321.jpeg")',
            backgroundSize: '100% 100%'
          }}
        />
      </div>

      {/* 5. BOTTOM BLACK SECTION */}
      <section className="relative w-full bg-black text-white pt-10 pb-32 z-10 px-4">
        <footer className="relative z-20 mx-auto max-w-4xl text-center">
          {/* Adding some subtle dark crystals at the bottom */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none flex justify-center items-center space-x-10 md:space-x-40 -z-10 -mt-20">
            <img src="/blackbgcrystals/Layer 0 - 8blackbg.png" alt="" className="w-64" />
            <img src="/blackbgcrystals/Layer 0 - 18blackbg.png" alt="" className="w-48" />
          </div>

          <div className="mx-auto max-w-3xl rounded-3xl border border-white/10 bg-white/5 p-8 md:p-12 backdrop-blur-md">
            <h3 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              Need a custom deployment or yearly billing?
            </h3>
            <p className="mt-4 text-sm md:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
              We can tailor PromptTriage to your security, compliance, and
              workflow needs. <br className="hidden sm:block" />
              <Link className="text-white underline decoration-white/30 underline-offset-4 hover:decoration-white transition-colors font-medium" href="mailto:hello@promptrefiner.app">Contact sales</Link> for a bespoke quote.
            </p>
          </div>
        </footer>
      </section>
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
        <span className="mt-2 inline-flex w-full items-center justify-center rounded-xl bg-slate-100 px-5 py-3.5 text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
          Included
        </span>
      );
    }
    return (
      <span className="mt-2 inline-flex w-full items-center justify-center rounded-xl bg-slate-900/5 px-5 py-3.5 text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
        Current Plan
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
          className="mt-2 w-full inline-flex items-center justify-center rounded-xl bg-slate-900 px-5 py-3.5 text-xs font-bold uppercase tracking-[0.2em] text-white shadow-lg shadow-slate-900/20 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-slate-900/30 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
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
        className="mt-2 w-full inline-flex items-center justify-center rounded-xl bg-slate-900 px-5 py-3.5 text-xs font-bold uppercase tracking-[0.2em] text-white shadow-lg shadow-slate-900/20 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-slate-900/30 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Redirecting..." : "Upgrade to Pro"}
      </button>
    );
  }

  // Scale plan card
  return (
    <Link
      href={plan.cta.href ?? "mailto:hello@promptrefiner.app"}
      className="mt-2 w-full inline-flex items-center justify-center rounded-xl border-2 border-slate-200 bg-transparent px-5 py-3 text-xs font-bold uppercase tracking-[0.2em] text-slate-600 transition-all duration-300 hover:border-slate-900 hover:bg-slate-900 hover:text-white active:scale-95"
    >
      {plan.cta.label}
    </Link>
  );
}
