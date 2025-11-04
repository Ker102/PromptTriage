import Link from "next/link";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
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
      label: "You’re on this plan",
      href: "/",
      variant: "outlined" as const,
    },
  },
  {
    id: "pro",
    name: "Pro",
    price: "$29",
    cadence: "per month",
    tagline: "Ship faster with richer context and collaboration tools.",
    highlight: "Unlock 100 monthly requests and premium tooling.",
    features: [
      "Up to 100 prompt requests every month",
      "Priority Gemini quota with faster retries",
      "Shared prompt workspaces & version history",
      "Advanced tone + output templates library",
      "Firecrawl web enrichment included",
      "Slack notifications for refinement completions",
    ],
    cta: {
      label: "Upgrade to Pro",
      href: "/checkout/pro",
      variant: "primary" as const,
    },
  },
  {
    id: "scale",
    name: "Scale",
    price: "$99",
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
      href: "mailto:hello@promptrefiner.app",
      variant: "ghost" as const,
    },
  },
];

export const metadata = {
  title: "PromptRefiner Pricing",
  description:
    "Choose the plan that fits your prompt orchestration workflow—from Free experimentation to enterprise-scale refinement.",
};

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-16">
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
            className="inline-flex items-center justify-center rounded-full border border-[rgba(148,163,184,0.35)] bg-[var(--surface-card)] px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-soft transition duration-200 hover:-translate-y-0.5 hover:border-[rgba(148,163,184,0.55)] hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400"
          >
            Back to app
          </Link>
        </div>

        <section className="grid gap-6 md:grid-cols-3">
          {PLANS.map((plan) => (
            <article
              key={plan.id}
              className={`flex flex-col gap-5 rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-6 backdrop-blur transition duration-300 hover:-translate-y-1 hover:border-cyan-400/40 hover:shadow-[0_45px_95px_-70px_rgba(56,189,248,0.65)] ${
                plan.id === "pro" ? "md:-translate-y-4 md:shadow-[0_60px_110px_-80px_rgba(16,185,129,0.55)]" : ""
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
                    <span className="mt-1 h-2 w-2 rounded-full bg-gradient-to-br from-cyan-400 to-emerald-400" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              <PlanCallToAction
                href={plan.cta.href}
                label={plan.cta.label}
                variant={plan.cta.variant}
              />
            </article>
          ))}
        </section>

        <footer className="mx-auto max-w-4xl rounded-3xl border border-[var(--surface-border)] bg-[var(--surface-card)] p-8 text-center text-sm text-muted">
          <p className="text-soft text-lg font-semibold">
            Need a custom deployment or yearly billing?
          </p>
          <p className="mt-2">
            We can tailor PromptRefiner to your security, compliance, and
            workflow needs. <Link className="text-cyan-300 underline underline-offset-4 hover:text-white" href="mailto:hello@promptrefiner.app">Contact sales</Link> for a bespoke quote.
          </p>
        </footer>
      </main>
    </div>
  );
}

function PlanCallToAction({
  href,
  label,
  variant,
}: {
  href: string;
  label: string;
  variant: "primary" | "outlined" | "ghost";
}) {
  if (variant === "ghost") {
    return (
      <Link
        href={href}
        className="inline-flex items-center justify-center rounded-full border border-[var(--surface-border)] bg-transparent px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-soft transition duration-300 hover:-translate-y-0.5 hover:scale-[1.03] hover:border-[rgba(148,163,184,0.65)] hover:text-white"
      >
        {label}
      </Link>
    );
  }

  if (variant === "outlined") {
    return (
      <span className="inline-flex items-center justify-center rounded-full border border-emerald-400/40 bg-emerald-400/10 px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-emerald-200">
        {label}
      </span>
    );
  }

  return (
    <Link
      href={href}
      className="inline-flex items-center justify-center rounded-full border border-cyan-400/50 bg-gradient-to-r from-cyan-500/25 via-emerald-500/20 to-cyan-500/25 px-5 py-2 text-sm font-semibold uppercase tracking-[0.28em] text-soft shadow-[0_20px_45px_-28px_rgba(34,211,238,0.85)] transition duration-300 hover:-translate-y-0.5 hover:scale-[1.04] hover:border-cyan-300 hover:text-white"
    >
      {label}
    </Link>
  );
}
