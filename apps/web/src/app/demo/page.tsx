"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export const DEMO_CASES = [
  {
    id: "deposit",
    title: "Security deposit dispute",
    domain: "Tenancy / property",
    description:
      "My landlord refuses to return my ₹50,000 security deposit even though I moved out last month and there is no damage to the property. The rent was paid on time. I have UPI records of the deposit payment.",
  },
  {
    id: "fraud",
    title: "Online payment fraud",
    domain: "Cyber law",
    description:
      "Someone called claiming to be from my bank and asked me to share an OTP to reverse a failed UPI transaction. I shared the OTP and ₹42,000 was transferred from my account. I have call logs and SMS alerts.",
  },
  {
    id: "consumer",
    title: "Consumer product dispute",
    domain: "Consumer law",
    description:
      "I purchased a laptop online for ₹65,000 in January 2025. Within two weeks, the screen started flickering. The seller refused a refund citing their no-return policy. I have the invoice, payment receipt, and email correspondence.",
  },
  {
    id: "employment",
    title: "Employment termination",
    domain: "Employment law",
    description:
      "I worked as a software engineer for a startup for 14 months without a written contract. I was terminated without notice in March 2025. The company owes me two months salary and has not paid my final settlement. I have salary slips and email communications.",
  },
  {
    id: "harassment",
    title: "Cyber harassment",
    domain: "Cyber law",
    description:
      "An unknown account has been sending obscene images and threatening messages to my phone and social media for two weeks. I have screenshots of the messages and profile URLs. I have not yet filed a police complaint.",
  },
];

export default function DemoPage() {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runDemo(id: string, description: string) {
    setBusy(id);
    setError(null);
    try {
      const caseData = await api.createCase({ description, is_demo: true, title: "Synthetic demo case" });
      await api.analyzeCase(caseData.id);
      router.push(`/cases/${caseData.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run demo");
      setBusy(null);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <AppHeader current="/demo" />
      <main className="mx-auto max-w-3xl px-6 py-12">
        <div className="mb-8">
          <h1 className="font-serif text-2xl font-bold">Demo Mode</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Synthetic examples only. They demonstrate retrieval across different legal domains and
            do not use real personal data. The knowledge base is a curated demo corpus, not the
            entirety of Indian law.
          </p>
        </div>
        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
        <div className="space-y-4">
          {DEMO_CASES.map((demo) => (
            <Card key={demo.id}>
              <CardHeader>
                <CardTitle className="text-base">{demo.title}</CardTitle>
                <span className="text-xs text-accent">Synthetic example · {demo.domain}</span>
              </CardHeader>
              <CardContent>
                <p className="mb-4 text-sm text-muted-foreground">{demo.description}</p>
                <Button onClick={() => runDemo(demo.id, demo.description)} disabled={busy !== null}>
                  {busy === demo.id ? "Analyzing..." : "Analyze this case"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
