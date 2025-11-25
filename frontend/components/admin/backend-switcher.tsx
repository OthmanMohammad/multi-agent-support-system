"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useSwitchBackend } from "@/lib/api/hooks";
import { Button } from "@/components/ui/button";
import { toast } from "@/lib/utils/toast";

export function BackendSwitcher(): JSX.Element {
  const [provider, setProvider] = useState<"openai" | "anthropic">("openai");
  const { switchBackend, isPending } = useSwitchBackend();

  const handleSwitch = async () => {
    const result = await switchBackend(provider);
    if (result.success) {
      toast.success(`Switched to ${provider}`);
    } else {
      toast.error("Failed to switch backend");
    }
  };

  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <h3 className="mb-4 font-semibold">AI Provider</h3>
      <div className="space-y-4">
        <div className="flex gap-4">
          {(["openai", "anthropic"] as const).map((p) => (
            <Button
              key={p}
              variant={provider === p ? "default" : "outline"}
              onClick={() => setProvider(p)}
            >
              {p === "openai" ? "OpenAI" : "Anthropic"}
            </Button>
          ))}
        </div>
        <Button onClick={handleSwitch} disabled={isPending}>
          {isPending ? "Switching..." : "Switch Provider"}
        </Button>
      </div>
    </div>
  );
}
