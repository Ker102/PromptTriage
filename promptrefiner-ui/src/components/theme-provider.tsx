"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = "promptrefiner-theme";

function getSystemPreference(): Theme {
  if (typeof window === "undefined") {
    return "dark";
  }
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function getStoredTheme(): Theme | null {
  if (typeof window === "undefined") {
    return null;
  }
  const stored = window.localStorage.getItem(STORAGE_KEY) as Theme | null;
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return null;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Always start with "dark" to avoid hydration mismatch
  const [theme, setTheme] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);
  const [userSelected, setUserSelected] = useState(false);

  // Read from localStorage after mount to avoid hydration mismatch
  useEffect(() => {
    const stored = getStoredTheme();
    if (stored) {
      setTheme(stored);
      setUserSelected(true); // User had previously selected a theme
    } else {
      // Use system preference if no stored value
      setTheme(getSystemPreference());
    }
    setMounted(true);
  }, []);

  // Apply theme to document
  useEffect(() => {
    if (!mounted) return;
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;

    // Only persist to localStorage if user explicitly selected a theme
    if (userSelected) {
      window.localStorage.setItem(STORAGE_KEY, theme);
    }
  }, [theme, mounted, userSelected]);

  const handleSetTheme = (newTheme: Theme) => {
    setUserSelected(true);
    setTheme(newTheme);
  };

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      setTheme: handleSetTheme,
      toggleTheme: () => {
        setUserSelected(true);
        setTheme((prev) => (prev === "dark" ? "light" : "dark"));
      },
    }),
    [theme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
