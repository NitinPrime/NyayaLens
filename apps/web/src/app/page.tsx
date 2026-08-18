import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AppHeader } from "@/components/layout/app-header";
import { BookOpen, FileSearch, MessageSquare, Shield } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <AppHeader />
      <main>
        <section className="mx-auto max-w-4xl px-6 py-20 text-center">
          <h1 className="font-serif text-4xl font-bold tracking-tight text-primary md:text-5xl">
            Understand your legal situation before you take your next step.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
            Describe what happened in plain language. NyayaLens structures the facts, retrieves
            potentially relevant Indian legal sources, and shows both sides — with citations, not
            guesswork.
          </p>
          <div className="mt-10 flex justify-center gap-4">
            <Link href="/analyze">
              <Button size="lg">Analyze a Case</Button>
            </Link>
            <Link href="/demo">
              <Button size="lg" variant="outline">
                Explore Demo
              </Button>
            </Link>
          </div>
        </section>

        <section className="border-t border-border bg-secondary/30 py-16">
          <div className="mx-auto grid max-w-5xl gap-6 px-6 md:grid-cols-4">
            <Step n="1" title="Describe what happened" text="Use ordinary language. You do not need to know the law." />
            <Step n="2" title="AI structures the case" text="Parties, facts, issues, and missing information are extracted without inventing details." />
            <Step n="3" title="Relevant law is retrieved" text="Provisions come from the knowledge base. Unsupported citations are flagged." />
            <Step n="4" title="Arguments and next steps" text="Both sides are analyzed, then practical next steps are suggested." />
          </div>
        </section>

        <section className="mx-auto grid max-w-5xl gap-8 px-6 py-16 md:grid-cols-2">
          <Feature
            icon={<FileSearch className="h-5 w-5" />}
            title="Structured research, not a chatbot"
            description="Facts, inferences, retrieved law, and analysis are labeled separately so you can see why a conclusion was reached."
          />
          <Feature
            icon={<BookOpen className="h-5 w-5" />}
            title="Sources you can inspect"
            description="Each legal claim is tied to a retrieved provision when one exists. If none is found, the system says so."
          />
          <Feature
            icon={<Shield className="h-5 w-5" />}
            title="Both-side analysis"
            description="The system looks for weaknesses in the user's position as actively as it looks for supporting arguments."
          />
          <Feature
            icon={<MessageSquare className="h-5 w-5" />}
            title="Follow-up questions"
            description="Ask about evidence, agreements, or hypotheticals while staying grounded in the same case and sources."
          />
        </section>
      </main>
      <footer className="border-t border-border px-6 py-8 text-center text-sm text-muted-foreground">
        This tool provides general legal information and research assistance. It is not a substitute
        for advice from a qualified lawyer.
      </footer>
    </div>
  );
}

function Step({ n, title, text }: { n: string; title: string; text: string }) {
  return (
    <div>
      <div className="mb-2 font-serif text-sm font-bold text-accent">{n}</div>
      <h3 className="font-serif font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{text}</p>
    </div>
  );
}

function Feature({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="mb-3 text-accent">{icon}</div>
      <h3 className="font-serif text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
