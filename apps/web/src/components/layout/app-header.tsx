import Link from "next/link";
import { Scale } from "lucide-react";

export function AppHeader({ current }: { current?: string }) {
  const links = [
    { href: "/analyze", label: "Analyze" },
    { href: "/demo", label: "Demo" },
    { href: "/dashboard", label: "Dashboard" },
    { href: "/admin/sources", label: "Sources" },
  ];

  return (
    <header className="border-b border-border bg-card">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <Scale className="h-6 w-6 text-primary" />
          <span className="font-serif text-lg font-bold text-primary">NyayaLens</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={
                current === link.href
                  ? "font-medium text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    high: "bg-red-100 text-red-800",
    medium: "bg-amber-100 text-amber-800",
    low: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium uppercase ${colors[priority] || colors.low}`}>
      {priority}
    </span>
  );
}

export function LabelBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded bg-secondary px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
      {children}
    </span>
  );
}
