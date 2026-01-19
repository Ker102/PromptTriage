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
} else if (process.env.NODE_ENV === "development") {
  console.warn(
    "⚠️  Google OAuth credentials not configured. Auth features disabled.",
    "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.local to enable auth.",
  );
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
