import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { getOptionalSession } from "@/lib/dal";
import { logout } from "@/app/actions/auth";

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

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const session = await getOptionalSession();

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
          <nav className="flex gap-6 text-sm text-zinc-400 items-center">
            <Link href="/" className="hover:text-zinc-100 transition-colors">
              Search
            </Link>
            <Link
              href="/watchlist"
              className="hover:text-zinc-100 transition-colors"
            >
              Watchlist
            </Link>
            {session ? (
              <form action={logout}>
                <button
                  type="submit"
                  className="hover:text-zinc-100 transition-colors"
                >
                  Sign out
                </button>
              </form>
            ) : (
              <Link href="/login" className="hover:text-zinc-100 transition-colors">
                Sign in
              </Link>
            )}
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
