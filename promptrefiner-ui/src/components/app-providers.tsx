"use client";

import { SessionProvider } from "next-auth/react";
import type { Session } from "next-auth";
import { ThemeProvider } from "@/components/theme-provider";

interface AppProvidersProps {
  session?: Session | null;
  children: React.ReactNode;
}

export function AppProviders({ session, children }: AppProvidersProps) {
  return (
    <SessionProvider session={session}>
      <ThemeProvider>{children}</ThemeProvider>
    </SessionProvider>
  );
}
