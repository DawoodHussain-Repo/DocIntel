import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/dm-serif-display/400.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/600.css";

export const metadata: Metadata = {
  title: "DocIntel",
  description: "AI-powered legal contract analysis: summarize, extract, and score risk.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-ink text-text font-sans antialiased">
        <Navbar />
        {children}
      </body>
    </html>
  );
}
