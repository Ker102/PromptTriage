import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppProviders } from "@/components/app-providers";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "PromptTriage | RAG-Powered Prompt Engineering Platform",
  description:
    "Transform rough ideas into production-ready AI prompts with RAG retrieval, modality-specific optimization, and Context7 MCP integration.",
  keywords: ["prompt engineering", "RAG", "AI prompts", "Gemini", "LLM", "system prompts", "Context7"],
  authors: [{ name: "Kaelux Technologies" }],
  openGraph: {
    title: "PromptTriage — Write Better Prompts, Get Better Results",
    description: "RAG-powered prompt refinement for Text, Image, Video, and System Prompts.",
    type: "website",
    siteName: "PromptTriage",
  },
  twitter: {
    card: "summary_large_image",
    title: "PromptTriage — Write Better Prompts, Get Better Results",
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
      <body className={`${inter.variable} font-sans antialiased`}>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
