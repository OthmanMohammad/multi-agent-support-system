import type { JSX } from "react";
import { Bot } from "lucide-react";

/**
 * Typing Indicator Component
 * Animated dots to show AI is typing
 */
export function TypingIndicator(): JSX.Element {
  return (
    <div className="flex gap-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface">
        <Bot className="h-4 w-4" />
      </div>

      <div className="flex items-center gap-1 rounded-lg bg-surface px-4 py-3">
        <div className="h-2 w-2 animate-bounce rounded-full bg-foreground-secondary [animation-delay:-0.3s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-foreground-secondary [animation-delay:-0.15s]" />
        <div className="h-2 w-2 animate-bounce rounded-full bg-foreground-secondary" />
      </div>
    </div>
  );
}
