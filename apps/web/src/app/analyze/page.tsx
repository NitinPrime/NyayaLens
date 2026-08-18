"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AppHeader } from "@/components/layout/app-header";
import { api } from "@/lib/api";

const EXAMPLES = [
  "My landlord refuses to return my ₹50,000 security deposit even though I moved out and there is no damage to the property.",
  "I lent my friend ₹80,000 by UPI. He promised to return it in three months. Six months later he refuses.",
  "I bought a laptop online for ₹65,000. The screen failed within two weeks and the seller refused a refund.",
];

export default function AnalyzePage() {
  const router = useRouter();
  const [description, setDescription] = useState("");
  const [parties, setParties] = useState("");
  const [when, setWhen] = useState("");
  const [where, setWhere] = useState("");
  const [amount, setAmount] = useState("");
  const [evidence, setEvidence] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (description.trim().length < 10) {
      setError("Please provide at least 10 characters describing what happened.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const caseData = await api.createCase({
        description: description.trim(),
        incident_date: when || undefined,
        location: where || undefined,
        amount: amount || undefined,
        parties_involved: parties || undefined,
        evidence_available: evidence || undefined,
        additional_context: context || undefined,
      });
      await api.analyzeCase(caseData.id);
      router.push(`/cases/${caseData.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <AppHeader current="/analyze" />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <Card>
          <CardHeader>
            <CardTitle>Describe what happened</CardTitle>
            <p className="text-sm text-muted-foreground">
              Free-text is enough. Optional fields help, but you do not need to fill every box.
              Avoid unnecessary personal identifiers.
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what happened in your own words. You don't need to know the law."
                  className="min-h-[200px] w-full rounded-md border border-border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  disabled={loading}
                  maxLength={50000}
                />
                <div className="mt-1 text-right text-xs text-muted-foreground">
                  {description.length.toLocaleString()} / 50,000
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <Field label="Who was involved? (optional)">
                  <input value={parties} onChange={(e) => setParties(e.target.value)} className={inputClass} disabled={loading} />
                </Field>
                <Field label="When did it happen? (optional, YYYY-MM-DD)">
                  <input type="date" value={when} onChange={(e) => setWhen(e.target.value)} className={inputClass} disabled={loading} />
                </Field>
                <Field label="Where did it happen? (optional)">
                  <input value={where} onChange={(e) => setWhere(e.target.value)} className={inputClass} disabled={loading} />
                </Field>
                <Field label="Approximate amount (optional)">
                  <input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="₹50,000" className={inputClass} disabled={loading} />
                </Field>
              </div>
              <Field label="Evidence available (optional)">
                <input value={evidence} onChange={(e) => setEvidence(e.target.value)} placeholder="UPI receipt, WhatsApp messages, rental agreement..." className={inputClass} disabled={loading} />
              </Field>
              <Field label="Additional context (optional)">
                <textarea value={context} onChange={(e) => setContext(e.target.value)} className={`${inputClass} min-h-[80px]`} disabled={loading} />
              </Field>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing case...
                  </>
                ) : (
                  "Analyze Case"
                )}
              </Button>
            </form>

            <div className="mt-8">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Example cases
              </p>
              <div className="space-y-2">
                {EXAMPLES.map((example) => (
                  <button
                    key={example}
                    type="button"
                    className="block w-full rounded-md border border-border p-3 text-left text-sm text-muted-foreground hover:bg-secondary"
                    onClick={() => setDescription(example)}
                    disabled={loading}
                  >
                    {example}
                  </button>
                ))}
              </div>
              <p className="mt-4 text-xs text-muted-foreground">
                Prefer a guided walkthrough? <Link href="/demo" className="underline">Open Demo Mode</Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

const inputClass =
  "w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}
