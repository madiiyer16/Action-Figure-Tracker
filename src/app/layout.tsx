import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
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
  title: "FigureTrack — Action Figure Price Tracker",
  description:
    "Compare prices and true landed cost for action figures across AmiAmi, BBTS, HLJ, and more.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-950 text-zinc-100">
        <header className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="font-semibold text-lg tracking-tight hover:text-zinc-300 transition-colors"
          >
            FigureTrack
          </Link>
          <nav className="flex gap-6 text-sm text-zinc-400">
            <Link href="/" className="hover:text-zinc-100 transition-colors">
              Search
            </Link>
            <Link
              href="/watchlist"
              className="hover:text-zinc-100 transition-colors"
            >
              Watchlist
            </Link>
          </nav>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-zinc-800 px-6 py-4 text-xs text-zinc-600 text-center">
          FigureTrack — prices updated every 12 hours
        </footer>
      </body>
    </html>
  );
}
