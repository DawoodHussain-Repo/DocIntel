import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocIntel - Legal Document Processing",
  description: "Enterprise Legal Document Processing Pipeline",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
