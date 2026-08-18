"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, type ChatMessage } from "@/lib/api";

export default function CaseChatPage() {
  const params = useParams();
  const caseId = params.id as string;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listMessages(caseId)
      .then(setMessages)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load chat"))
      .finally(() => setLoading(false));
  }, [caseId]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim().length < 3) return;
    setSending(true);
    setError(null);
    const pending = input.trim();
    setInput("");
    try {
      const result = await api.sendMessage(caseId, pending);
      const history = await api.listMessages(caseId);
      setMessages(history.length ? history : [result.message]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send");
      setInput(pending);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />
      <main className="mx-auto flex min-h-[calc(100vh-8rem)] max-w-3xl flex-col px-6 py-8">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="font-serif text-xl font-bold">Case chat</h1>
          <Link href={`/cases/${caseId}`} className="text-sm text-primary underline">
            Back to analysis
          </Link>
        </div>
        <p className="mb-4 text-xs text-muted-foreground">
          Follow-up answers still use retrieved legal sources where legal claims are involved. This is
          not legal advice.
        </p>
        <Card className="flex flex-1 flex-col">
          <CardContent className="flex flex-1 flex-col p-4">
            <div className="flex-1 space-y-3 overflow-y-auto">
              {loading && <p className="text-sm text-muted-foreground">Loading conversation...</p>}
              {!loading && messages.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Ask about evidence, agreements, limitation, or what would change this analysis.
                </p>
              )}
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`rounded-md p-3 text-sm ${
                    m.role === "user" ? "ml-8 bg-primary text-primary-foreground" : "mr-8 border border-border"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  {m.citations?.length > 0 && (
                    <ul className="mt-2 space-y-1 text-xs opacity-80">
                      {m.citations.map((c) => (
                        <li key={c.id}>Source: {c.claim}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
            <form onSubmit={send} className="mt-4 flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Does the agreement change this?"
                className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                disabled={sending}
              />
              <Button type="submit" disabled={sending}>
                {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Send"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
