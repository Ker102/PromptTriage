import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user?: DefaultSession["user"] & {
      subscriptionPlan?: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    subscriptionPlan?: string;
  }
}
