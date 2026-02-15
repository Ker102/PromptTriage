"use client";

import { ThemeProvider } from "@/components/theme-provider";

interface AppProvidersProps {
  children: React.ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <ThemeProvider>{children}</ThemeProvider>
  );
}
