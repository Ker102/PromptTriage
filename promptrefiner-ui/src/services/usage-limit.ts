const DAY_MS = 24 * 60 * 60 * 1000;
const MONTH_MS = 30 * 24 * 60 * 60 * 1000;

export type UsageMode = "thinking" | "normal";
type PlanKey = "FREE" | "PRO" | string;

interface ModeLimit {
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

export interface ModeUsageInfo {
  remaining: number;
  limit: number;
  resetsIn: string;
}

export interface UsageSummary {
  thinking: ModeUsageInfo;
  normal: ModeUsageInfo;
}

const usageStore = new Map<string, UsageRecord>();

// Per-mode limits for each plan
const FREE_MODE_LIMITS: Record<UsageMode, ModeLimit> = {
  thinking: { limit: 2, periodMs: DAY_MS, label: "daily" },
  normal: { limit: 3, periodMs: DAY_MS, label: "daily" },
};

const PRO_MODE_LIMITS: Record<UsageMode, ModeLimit> = {
  thinking: { limit: 200, periodMs: MONTH_MS, label: "monthly" },
  normal: { limit: 500, periodMs: MONTH_MS, label: "monthly" },
};

const UNLIMITED: ModeLimit = { limit: null, periodMs: null, label: "unlimited" };

function getModeLimits(plan: PlanKey): Record<UsageMode, ModeLimit> {
  switch (plan) {
    case "FREE":
      return FREE_MODE_LIMITS;
    case "PRO":
      return PRO_MODE_LIMITS;
    default:
      // SCALE and any other plan → unlimited
      return { thinking: UNLIMITED, normal: UNLIMITED };
  }
}

function makeUsageKey(email: string, plan: string, mode: UsageMode) {
  return `${email.toLowerCase()}::${plan.toUpperCase()}::${mode}`;
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

/**
 * Record one usage for the given mode, or throw if the limit is exceeded.
 */
export function recordUsageOrThrow(
  email: string,
  plan: string,
  mode: UsageMode,
) {
  const normalizedPlan = plan.toUpperCase();
  const limits = getModeLimits(normalizedPlan);
  const { limit, periodMs, label } = limits[mode];

  if (!limit || !periodMs) {
    // Unlimited for this plan/mode combo.
    return;
  }

  const now = Date.now();
  const key = makeUsageKey(email, normalizedPlan, mode);
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
    const friendlyMode = mode === "thinking" ? "Thinking Mode" : "Normal Mode";
    const friendlyPlan =
      normalizedPlan.charAt(0) + normalizedPlan.slice(1).toLowerCase();
    throw new Error(
      `You've hit the ${label} ${friendlyMode} limit for the ${friendlyPlan} plan (${limit} uses). Try again in ${resetIn} or upgrade for higher limits.`,
    );
  }

  record.count += 1;
  usageStore.set(key, record);
}

/**
 * Get remaining usage for all modes.
 * Used by the /api/subscription endpoint to show counters in the UI.
 */
export function getRemainingUsage(email: string, plan: string): UsageSummary {
  const normalizedPlan = plan.toUpperCase();
  const limits = getModeLimits(normalizedPlan);
  const now = Date.now();

  function getInfo(mode: UsageMode): ModeUsageInfo {
    const { limit, periodMs } = limits[mode];

    if (!limit || !periodMs) {
      return { remaining: -1, limit: -1, resetsIn: "unlimited" };
    }

    const key = makeUsageKey(email, normalizedPlan, mode);
    const record = usageStore.get(key);

    if (!record || record.resetAt <= now) {
      return { remaining: limit, limit, resetsIn: "—" };
    }

    const remaining = Math.max(0, limit - record.count);
    const resetsIn = formatRemainingMs(record.resetAt - now);
    return { remaining, limit, resetsIn };
  }

  return {
    thinking: getInfo("thinking"),
    normal: getInfo("normal"),
  };
}

export function isFirecrawlAvailable(plan: string): boolean {
  const normalizedPlan = plan.toUpperCase();
  return normalizedPlan !== "FREE";
}
