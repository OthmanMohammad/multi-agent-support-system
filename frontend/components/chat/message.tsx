"use client";

import type { JSX } from "react";
import { useState } from "react";
import { format } from "date-fns";
import { Copy, Check, User, Bot } from "lucide-react";
import type { Message as BackendMessage } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import { CodeBlock, InlineCode } from "./code-block";

// Unified message type that works with both backend and frontend
interface MessageType {
  id?: string;
  role: string;
  content: string;
  timestamp?: string;
  createdAt?: Date | string;
  agent_name?: string | null;
}

interface MessageProps {
  message: MessageType;
  isStreaming?: boolean;
}

/**
 * Message Component
 * Individual message with markdown rendering and actions
 */
export function Message({ message, isStreaming = false }: MessageProps): JSX.Element {
  const [isCopied, setIsCopied] = useState(false);
  // Handle both uppercase (Prisma) and lowercase (backend) role values
  const isUser = message.role.toLowerCase() === "user";

  const handleCopy = async (): Promise<void> => {
    await navigator.clipboard.writeText(message.content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "group relative flex gap-4",
        isUser && "flex-row-reverse"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-accent" : "bg-surface"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-accent-foreground" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn("flex-1 space-y-2", isUser && "flex flex-col items-end")}>
        <div
          className={cn(
            "rounded-lg px-4 py-3",
            isUser
              ? "bg-accent text-accent-foreground"
              : "bg-surface",
            isStreaming && "animate-pulse"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  // Custom link component for security
                  a: ({ node, ...props }) => (
                    <a {...props} target="_blank" rel="noopener noreferrer" />
                  ),
                  // Custom code block with copy button
                  code: ({ node, inline, className, children, ...props }) => {
                    const codeString = String(children).replace(/\n$/, "");
                    return inline ? (
                      <InlineCode>{codeString}</InlineCode>
                    ) : (
                      <CodeBlock className={className} language={className?.replace("language-", "")}>
                        {codeString}
                      </CodeBlock>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div
          className={cn(
            "flex items-center gap-2 px-2 text-xs text-foreground-secondary",
            isUser && "flex-row-reverse"
          )}
        >
          <span>{format(new Date(message.timestamp || message.createdAt || new Date()), "HH:mm")}</span>

          {!isUser && !isStreaming && (
            <Button
              size="icon"
              variant="ghost"
              className="h-6 w-6 opacity-0 transition-opacity group-hover:opacity-100"
              onClick={handleCopy}
            >
              {isCopied ? (
                <Check className="h-3 w-3" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
