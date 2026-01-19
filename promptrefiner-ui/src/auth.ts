import type { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const googleClientId = process.env.GOOGLE_CLIENT_ID;
const googleClientSecret = process.env.GOOGLE_CLIENT_SECRET;

const authSecret = process.env.AUTH_SECRET ?? process.env.NEXTAUTH_SECRET;
if (!authSecret) {
  throw new Error(
    "Missing auth secret. Please set AUTH_SECRET (or NEXTAUTH_SECRET) in your environment.",
  );
}

// Build providers array - only include Google if credentials are configured
const providers: NextAuthOptions["providers"] = [];

if (googleClientId && googleClientSecret) {
  providers.push(
    GoogleProvider({
      clientId: googleClientId,
      clientSecret: googleClientSecret,
    }),
  );
} else {
  // Always warn about missing credentials - this affects auth functionality
  const warningMessage = "⚠️  Google OAuth credentials not configured (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET). Auth features disabled.";

  if (process.env.NODE_ENV === "production") {
    // In production, log error but don't crash - allow app to run with limited functionality
    console.error("[CRITICAL]", warningMessage, "Users will not be able to sign in.");
  } else {
    console.warn(warningMessage, "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.local to enable auth.");
  }
}

export const authOptions: NextAuthOptions = {
  secret: authSecret,
  providers,
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token }) {
      if (!token.subscriptionPlan) {
        token.subscriptionPlan = "FREE";
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.subscriptionPlan =
          (token.subscriptionPlan as string) ?? "FREE";
      }
      return session;
    },
  },
};
