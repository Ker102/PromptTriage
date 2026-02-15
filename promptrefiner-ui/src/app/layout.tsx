import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AppProviders } from "@/components/app-providers";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PromptTriage | RAG-Powered Prompt Engineering Platform",
  description:
    "Transform rough ideas into production-ready AI prompts with RAG retrieval, modality-specific optimization, and Context7 MCP integration.",
  keywords: ["prompt engineering", "RAG", "AI prompts", "Gemini", "LLM", "system prompts", "Context7"],
  authors: [{ name: "Ker102" }],
  openGraph: {
    title: "PromptTriage — AI-Ready Prompt Engineering",
    description: "RAG-powered prompt refinement for Text, Image, Video, and System Prompts.",
    type: "website",
    siteName: "PromptTriage",
  },
  twitter: {
    card: "summary_large_image",
    title: "PromptTriage — AI-Ready Prompt Engineering",
    description: "RAG-powered prompt refinement for Text, Image, Video, and System Prompts.",
  },
  metadataBase: new URL("https://prompttriage.dev"),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
