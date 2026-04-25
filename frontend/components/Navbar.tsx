"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CircleUserRound, FileUp, ShieldCheck, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const isReport = pathname.startsWith("/report");
  const file = searchParams.get("file");

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-white/82 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-900 bg-slate-900 shadow-sm">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <div className="leading-tight">
              <p className="font-serif text-lg">DocIntel</p>
              <p className="text-xs text-text-sub">Contract Intelligence</p>
            </div>
          </Link>

          <Badge className="hidden sm:inline-flex" variant="neutral">
            <Sparkles className="mr-1 h-3.5 w-3.5 text-accent" />
            MVP Flow
          </Badge>
        </div>

        <div className="flex items-center gap-3">
          {isReport && (
            <Button
              variant="ghost"
              onClick={() =>
                router.push(
                  file
                    ? `/workspace?file=${encodeURIComponent(file)}`
                    : "/",
                )
              }
            >
              Back to workspace
            </Button>
          )}
          {!isReport && (
            <Button variant="ghost" onClick={() => router.push("/")}>
              <FileUp className="h-4 w-4" />
              Upload
            </Button>
          )}

          <button
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-white text-text-sub transition-colors hover:text-text"
            aria-label="User account"
          >
            <CircleUserRound className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
