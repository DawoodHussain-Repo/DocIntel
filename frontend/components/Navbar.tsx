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
    <header className="sticky top-0 z-40 border-b border-border/60 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-6 lg:px-10">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="rounded-lg bg-slate-900 p-1.5 text-white shadow-sm">
              <ShieldCheck size={20} strokeWidth={2.5} />
            </div>
            <span className="text-lg font-semibold tracking-tight text-slate-900">
              DocIntel
            </span>
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
            className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-600 transition-colors hover:bg-slate-200 hover:text-slate-900"
            aria-label="User account"
          >
            <CircleUserRound className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
