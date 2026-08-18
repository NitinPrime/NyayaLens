"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type LegalSource } from "@/lib/api";

export default function AdminSourcesPage() {
  const [sources, setSources] = useState<LegalSource[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LegalSource[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .listSources()
      .then(setSources)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load sources"));
  }, []);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim().length < 3) return;
    setBusy(true);
    setError(null);
    try {
      setResults(await api.searchLegal(query.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setBusy(false);
    }
  }

  const shown = results ?? sources;

  return (
    <div className="min-h-screen bg-background">
      <AppHeader current="/admin/sources" />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="font-serif text-2xl font-bold">Legal knowledge base</h1>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          This is a curated demo corpus used for retrieval. It is not a complete collection of Indian
          law. Re-indexing is done by running <code>python scripts/ingest_legal_sources.py</code> so
          sources can be updated independently of application code.
        </p>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        <form onSubmit={search} className="mt-6 flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search provisions by meaning or keywords"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <Button type="submit" disabled={busy}>
            {busy ? "Searching..." : "Search"}
          </Button>
          {results && (
            <Button type="button" variant="outline" onClick={() => setResults(null)}>
              Show all
            </Button>
          )}
        </form>

        <p className="mt-4 text-xs text-muted-foreground">
          {shown.length} provision{shown.length === 1 ? "" : "s"} {results ? "in search results" : "indexed"}
        </p>

        <div className="mt-4 space-y-3">
          {shown.map((source) => (
            <Card key={source.id}>
              <CardHeader>
                <CardTitle className="text-base">
                  {source.title}
                  {source.section ? ` — ${source.section}` : ""}
                </CardTitle>
                <p className="text-xs capitalize text-muted-foreground">
                  {source.source_type} · {source.jurisdiction}
                  {source.version ? ` · ${source.version}` : ""}
                </p>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-muted-foreground">{source.text}</p>
                {source.source_url && (
                  <a href={source.source_url} className="mt-2 inline-block text-xs text-primary underline" target="_blank" rel="noreferrer">
                    {source.source_url}
                  </a>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
}
