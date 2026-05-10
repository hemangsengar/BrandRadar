import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "BrandRadar — Sponsorship Sniper for Indian Creators",
  description:
    "Paste your YouTube channel URL. Get 25 brands ready to sponsor you tomorrow.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        {children}
        <footer className="fixed bottom-0 left-0 right-0 text-center text-xs text-zinc-700 py-1.5 pointer-events-none select-none">
          Demo: youtube.com/@hemang — 17,142 subs. ₹0 in sponsorships last quarter.
          Building this so it&apos;s never zero again.
        </footer>
      </body>
    </html>
  );
}
