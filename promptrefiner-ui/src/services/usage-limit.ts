const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const MONTH_MS = 30 * 24 * 60 * 60 * 1000;

type PlanKey = "FREE" | "PRO" | string;

interface PlanLimit {
  limit: number | null;
  periodMs: number | null;
  label: string;
}

interface UsageRecord {
  count: number;
  resetAt: number;
  limit: number;
  periodMs: number;
}

const usageStore = new Map<string, UsageRecord>();

const PLAN_LIMITS: Record<PlanKey, PlanLimit> = {
  FREE: { limit: 5, periodMs: WEEK_MS, label: "weekly" },
  PRO: { limit: 100, periodMs: MONTH_MS, label: "monthly" },
};

function getPlanLimit(plan: PlanKey): PlanLimit {
  const fallback: PlanLimit = { limit: null, periodMs: null, label: "monthly" };
  return PLAN_LIMITS[plan] ?? fallback;
}

function makeUsageKey(email: string, plan: string) {
  return `${email.toLowerCase()}::${plan.toUpperCase()}`;
}

function formatRemainingMs(ms: number): string {
  if (ms <= 0) {
    return "soon";
  }
  const minutes = Math.floor(ms / (60 * 1000));
  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? "" : "s"}`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} hour${hours === 1 ? "" : "s"}`;
  }
  const days = Math.ceil(hours / 24);
  return `${days} day${days === 1 ? "" : "s"}`;
}

export function recordUsageOrThrow(email: string, plan: string) {
  const normalizedPlan = plan.toUpperCase();
  const { limit, periodMs, label } = getPlanLimit(normalizedPlan);
  const friendlyPlan =
    normalizedPlan.charAt(0) + normalizedPlan.slice(1).toLowerCase();

  if (!limit || !periodMs) {
    // Unlimited for plans without explicit cap.
    return;
  }

  const now = Date.now();
  const key = makeUsageKey(email, normalizedPlan);

  const record = usageStore.get(key);

  if (!record || record.resetAt <= now) {
    usageStore.set(key, {
      count: 1,
      resetAt: now + periodMs,
      limit,
      periodMs,
    });
    return;
  }

  if (record.count >= limit) {
    const resetIn = formatRemainingMs(record.resetAt - now);
    throw new Error(
      `You've hit the ${label} limit for the ${friendlyPlan} plan. Try again in ${resetIn} or upgrade for higher limits.`,
    );
  }

  record.count += 1;
  usageStore.set(key, record);
}

export function isFirecrawlAvailable(plan: string): boolean {
  const normalizedPlan = plan.toUpperCase();
  return normalizedPlan !== "FREE";
}
