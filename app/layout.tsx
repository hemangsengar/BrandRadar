import type { Metadata } from "next";
import { Syne, Space_Mono, DM_Sans } from "next/font/google";
import "./globals.css";

const syne = Syne({
  weight: ["400", "600", "700", "800"],
  variable: "--font-syne",
  subsets: ["latin"],
  display: "swap",
});

const spaceMono = Space_Mono({
  weight: ["400", "700"],
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

const dmSans = DM_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "BrandRadar — Sponsorship Intelligence for Indian Creators",
  description:
    "Paste your YouTube channel. Get brands ready to sponsor you tomorrow.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${syne.variable} ${spaceMono.variable} ${dmSans.variable} h-full`}
    >
      <body className="min-h-full flex flex-col antialiased">
        {children}
        <footer className="fixed bottom-0 left-0 right-0 text-center text-[11px] py-2 pointer-events-none select-none" style={{ color: "#C4BFB9", fontFamily: "var(--font-sans)" }}>
          built at anakin.io hackathon · bengaluru may 2026
        </footer>
      </body>
    </html>
  );
}
