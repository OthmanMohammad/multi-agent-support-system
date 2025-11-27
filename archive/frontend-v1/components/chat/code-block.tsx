"use client";

import type { JSX } from "react";
import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "@/lib/utils/toast";

interface CodeBlockProps {
  children: string;
  className?: string;
  language?: string;
}

/**
 * Code Block Component with Copy Button
 * Enhanced code block with syntax highlighting and copy functionality
 */
export function CodeBlock({
  children,
  className,
  language,
}: CodeBlockProps): JSX.Element {
  const [isCopied, setIsCopied] = useState(false);

  // Extract language from className (format: "language-javascript")
  const lang = language || className?.replace("language-", "") || "text";

  const handleCopy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(children);
      setIsCopied(true);
      toast.success("Code copied to clipboard");
      setTimeout(() => setIsCopied(false), 2000);
    } catch (_error) {
      toast.error("Failed to copy code");
    }
  };

  return (
    <div className="group relative my-4">
      {/* Language Label & Copy Button */}
      <div className="flex items-center justify-between rounded-t-lg border border-b-0 border-border bg-surface px-4 py-2">
        <span className="text-xs font-mono font-semibold uppercase text-foreground-secondary">
          {lang}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-6 px-2 opacity-0 transition-opacity group-hover:opacity-100"
        >
          {isCopied ? (
            <>
              <Check className="mr-1 h-3 w-3 text-green-500" />
              <span className="text-xs">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="mr-1 h-3 w-3" />
              <span className="text-xs">Copy</span>
            </>
          )}
        </Button>
      </div>

      {/* Code Content */}
      <pre className="overflow-x-auto rounded-b-lg border border-border bg-[#0d1117] p-4">
        <code className={cn("text-sm", className)}>{children}</code>
      </pre>
    </div>
  );
}

/**
 * Inline Code Component
 * For inline code snippets
 */
export function InlineCode({ children }: { children: string }): JSX.Element {
  return (
    <code className="rounded bg-surface px-1.5 py-0.5 font-mono text-sm text-accent">
      {children}
    </code>
  );
}
