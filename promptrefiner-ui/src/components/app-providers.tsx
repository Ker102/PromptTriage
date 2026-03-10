"use client";

import { ThemeProvider } from "@/components/theme-provider";
import { PostHogProvider } from "@/components/posthog-provider";

interface AppProvidersProps {
  children: React.ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <PostHogProvider>
      <ThemeProvider>{children}</ThemeProvider>
    </PostHogProvider>
  );
}
