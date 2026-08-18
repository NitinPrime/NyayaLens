"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertCircle,
  BookOpen,
  FileText,
  HelpCircle,
  ListChecks,
  MessageSquare,
  Scale,
  Users,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AppHeader, LabelBadge, PriorityBadge } from "@/components/layout/app-header";
import { api, type Analysis, type Case } from "@/lib/api";

export default function CaseWorkspacePage() {
  const params = useParams();
  const caseId = params.id as string;
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [c, a] = await Promise.all([
          api.getCase(caseId),
          api.getAnalysis(caseId).catch(() => null),
        ]);
        setCaseData(c);
        setAnalysis(a);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load case");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [caseId]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading case analysis...
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-red-600">{error || "Case not found"}</p>
        <Link href="/" className="text-primary underline">
          Return home
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-4">
          <div>
            <h1 className="font-serif text-lg font-bold text-primary">
              {caseData.case_type || "Case Analysis"}
            </h1>
            {caseData.is_demo && <span className="text-xs text-accent">Synthetic demo case</span>}
          </div>
          <Link href={`/cases/${caseId}/chat`}>
            <Button variant="outline" size="sm">
              <MessageSquare className="mr-2 h-4 w-4" />
              Ask a follow-up
            </Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <Section icon={<FileText className="h-5 w-5" />} title="Case summary">
              <p className="text-sm leading-relaxed text-muted-foreground">
                {analysis?.summary || caseData.description}
              </p>
              <div className="mt-3 rounded-md bg-secondary/60 p-3 text-sm">
                <LabelBadge>FACT</LabelBadge>
                <p className="mt-2 text-muted-foreground">The user states that: {caseData.description}</p>
              </div>
            </Section>

            {analysis?.legal_domains?.length ? (
              <Section icon={<Scale className="h-5 w-5" />} title="Legal domain">
                <div className="flex flex-wrap gap-2">
                  {analysis.legal_domains.map((d) => (
                    <span key={d} className="rounded-md border border-border px-3 py-1 text-sm capitalize">
                      {d.replaceAll("_", " ")}
                    </span>
                  ))}
                </div>
              </Section>
            ) : null}

            <Section icon={<Users className="h-5 w-5" />} title={`Parties (${caseData.parties.length})`}>
              {caseData.parties.length === 0 ? (
                <p className="text-sm text-muted-foreground">No parties extracted yet.</p>
              ) : (
                <ul className="space-y-3">
                  {caseData.parties.map((party) => (
                    <li key={party.id} className="rounded-md border border-border p-3">
                      <div className="font-medium">{party.name}</div>
                      <div className="text-xs capitalize text-muted-foreground">{party.role.replace("_", " ")}</div>
                      {party.description && (
                        <p className="mt-1 text-sm text-muted-foreground">{party.description}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <Section icon={<AlertCircle className="h-5 w-5" />} title="Facts">
              <p className="mb-3 text-xs text-muted-foreground">User-provided / extracted facts are labeled separately from inferences.</p>
              {caseData.facts.length === 0 ? (
                <p className="text-sm text-muted-foreground">No facts extracted yet.</p>
              ) : (
                <ul className="space-y-2">
                  {caseData.facts.map((fact) => (
                    <li key={fact.id} className="rounded-md border border-border p-3 text-sm">
                      <LabelBadge>FACT</LabelBadge>
                      <p className="mt-2">{fact.description}</p>
                      <span className="text-xs capitalize text-muted-foreground">{fact.fact_type}</span>
                    </li>
                  ))}
                </ul>
              )}
              {analysis?.inferred_facts?.length ? (
                <ul className="mt-3 space-y-2">
                  {analysis.inferred_facts.map((item) => (
                    <li key={item} className="rounded-md border border-dashed border-border p-3 text-sm">
                      <LabelBadge>INFERENCE</LabelBadge>
                      <p className="mt-2 text-muted-foreground">{item}</p>
                    </li>
                  ))}
                </ul>
              ) : null}
            </Section>

            {analysis?.issues?.length ? (
              <Section title="Key legal issues">
                <ol className="space-y-3">
                  {analysis.issues.map((issue, idx) => (
                    <li key={issue.id} className="rounded-md border border-border p-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">{idx + 1}</span>
                        <PriorityBadge priority={issue.priority} />
                      </div>
                      <p className="mt-1 text-sm font-medium">{issue.issue}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{issue.why_it_matters}</p>
                    </li>
                  ))}
                </ol>
              </Section>
            ) : null}

            {analysis?.retrieved_sources?.length ? (
              <Section icon={<BookOpen className="h-5 w-5" />} title="Relevant laws">
                <div className="space-y-4">
                  {analysis.retrieved_sources.map((source) => {
                    const provision = analysis.legal_analyses
                      .flatMap((a) => a.provisions)
                      .find((p) => p.legal_source.id === source.id);
                    return (
                      <article key={source.id} className="rounded-md border border-border p-4">
                        <LabelBadge>LAW</LabelBadge>
                        <h4 className="mt-2 font-serif font-semibold">
                          {source.title}
                          {source.section ? ` — ${source.section}` : ""}
                        </h4>
                        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{source.text}</p>
                        {provision && (
                          <div className="mt-3 space-y-1 text-sm">
                            <p>
                              <span className="font-medium">Why it may apply: </span>
                              {provision.applicability}
                            </p>
                            <p className="text-muted-foreground">
                              <span className="font-medium text-foreground">ANALYSIS: </span>
                              {provision.explanation}
                            </p>
                            <p className="text-xs text-muted-foreground">Uncertainty: {provision.uncertainty}</p>
                          </div>
                        )}
                        {source.source_url && (
                          <a
                            href={source.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-2 inline-block text-xs text-primary underline"
                          >
                            View source
                          </a>
                        )}
                      </article>
                    );
                  })}
                </div>
              </Section>
            ) : (
              <Section title="Relevant laws">
                <p className="text-sm text-muted-foreground">
                  NyayaLens could not find a sufficiently reliable source supporting a specific legal proposition in the current knowledge base.
                </p>
              </Section>
            )}

            {(analysis?.claimant_argument || analysis?.respondent_argument) && (
              <Section title="Arguments">
                <div className="grid gap-4 md:grid-cols-2">
                  {analysis.claimant_argument && (
                    <div className="rounded-md border border-border p-4">
                      <h4 className="font-serif font-semibold">Supporting the user</h4>
                      <ArgumentBlock argument={analysis.claimant_argument} />
                    </div>
                  )}
                  {analysis.respondent_argument && (
                    <div className="rounded-md border border-border p-4">
                      <h4 className="font-serif font-semibold">Supporting the opposing party</h4>
                      <ArgumentBlock argument={analysis.respondent_argument} />
                    </div>
                  )}
                </div>
              </Section>
            )}

            {analysis?.recommendations?.length ? (
              <Section icon={<ListChecks className="h-5 w-5" />} title="Recommended next steps">
                <ol className="space-y-3">
                  {analysis.recommendations.map((item, idx) => (
                    <li key={item.id} className="rounded-md border border-border p-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">{idx + 1}</span>
                        <PriorityBadge priority={item.priority} />
                      </div>
                      <p className="mt-1 text-sm font-medium">
                        <LabelBadge>RECOMMENDATION</LabelBadge>{" "}
                        {item.action}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">{item.rationale}</p>
                    </li>
                  ))}
                </ol>
              </Section>
            ) : null}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Confidence / uncertainty</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm font-medium capitalize">
                  {analysis?.overall_confidence?.replaceAll("_", " ") || "medium"}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                  {analysis?.uncertainty_explanation ||
                    "Confidence depends on missing facts, evidence quality, and the limits of the demo knowledge base."}
                </p>
              </CardContent>
            </Card>

            <Section icon={<HelpCircle className="h-5 w-5" />} title="Missing information">
              {!analysis?.missing_information?.length ? (
                <p className="text-sm text-muted-foreground">No high-priority gaps identified yet.</p>
              ) : (
                <ul className="space-y-3">
                  {analysis.missing_information.map((item) => (
                    <li key={item.id} className="rounded-md border border-border p-3">
                      <PriorityBadge priority={item.priority} />
                      <p className="mt-1 text-sm font-medium">{item.question}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{item.why_it_matters}</p>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            {analysis?.unsupported_claims?.length ? (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Citation checks</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-xs text-muted-foreground">
                    {analysis.unsupported_claims.map((claim) => (
                      <li key={claim}>{claim}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ) : null}

            {analysis && (
              <Card className="border-accent/30 bg-accent/5">
                <CardContent className="p-4">
                  <p className="text-xs leading-relaxed text-muted-foreground">{analysis.disclaimer}</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ArgumentBlock({
  argument,
}: {
  argument: { strongest_arguments: string[]; possible_defenses: string[]; weaknesses: string[] };
}) {
  return (
    <div className="mt-3 space-y-3 text-sm">
      {argument.strongest_arguments.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase text-muted-foreground">Strongest arguments</p>
          <ul className="mt-1 list-disc pl-4 text-muted-foreground">
            {argument.strongest_arguments.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      )}
      {argument.possible_defenses.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase text-muted-foreground">Possible defenses</p>
          <ul className="mt-1 list-disc pl-4 text-muted-foreground">
            {argument.possible_defenses.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      )}
      {argument.weaknesses.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase text-muted-foreground">Weaknesses</p>
          <ul className="mt-1 list-disc pl-4 text-muted-foreground">
            {argument.weaknesses.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
