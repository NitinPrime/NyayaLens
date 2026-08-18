"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppHeader } from "@/components/layout/app-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type CaseSummary } from "@/lib/api";

export default function DashboardPage() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listCases()
      .then(setCases)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"));
  }, []);

  const analyzed = cases.filter((c) => c.has_analysis).length;
  const domains = cases.reduce<Record<string, number>>((acc, c) => {
    const key = c.case_type || "Unclassified";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-background">
      <AppHeader current="/dashboard" />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="font-serif text-2xl font-bold">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Counts are from this local workspace. No fabricated accuracy metrics.
        </p>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <Stat label="Total cases" value={cases.length} />
          <Stat label="Analyses completed" value={analyzed} />
          <Stat label="Awaiting analysis" value={cases.length - analyzed} />
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Legal domains</CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(domains).length === 0 ? (
                <p className="text-sm text-muted-foreground">No cases yet.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {Object.entries(domains).map(([name, count]) => (
                    <li key={name} className="flex justify-between">
                      <span>{name}</span>
                      <span className="text-muted-foreground">{count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent activity</CardTitle>
            </CardHeader>
            <CardContent>
              {cases.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Analyze a case to see it here. <Link href="/analyze" className="underline">Start</Link>
                </p>
              ) : (
                <ul className="space-y-3">
                  {cases.slice(0, 8).map((c) => (
                    <li key={c.id}>
                      <Link href={`/cases/${c.id}`} className="text-sm font-medium hover:underline">
                        {c.title || c.case_type || "Untitled case"}
                      </Link>
                      <p className="text-xs text-muted-foreground">
                        {c.has_analysis ? "Analysis complete" : "Created"} · {new Date(c.created_at).toLocaleString()}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="p-5">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="mt-1 font-serif text-3xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}
