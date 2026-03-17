import type { Metadata } from "next";
import { JetBrains_Mono, Space_Grotesk } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const display = Space_Grotesk({ subsets: ["latin"], variable: "--font-display" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Gods-eye Command Center",
  description: "Defensive SOC Command Center (local-first)"
};

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/assets", label: "Assets" },
  { href: "/findings", label: "Findings" },
  { href: "/alerts", label: "Alerts" },
  { href: "/playbooks", label: "Playbooks" },
  { href: "/executions", label: "Executions" },
  { href: "/topology", label: "Topology" },
  { href: "/settings", label: "Settings" }
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable}`}>
      <body className="min-h-screen">
        <div className="mx-auto max-w-7xl px-5 py-6">
          <header className="rise-in flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="text-sm text-[var(--muted)]">Defensive SOC Command Center</div>
              <div className="text-2xl font-semibold tracking-tight">Gods-eye</div>
            </div>
            <nav className="flex flex-wrap gap-2">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-full border border-[var(--stroke)] bg-[var(--card)] px-3 py-1 text-sm text-white/90 backdrop-blur hover:bg-[var(--card2)]"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>

          <main className="mt-6">{children}</main>
          <footer className="mt-10 text-xs text-white/55">
            v1 defensive-only. See scope in repository docs.
          </footer>
        </div>
      </body>
    </html>
  );
}

