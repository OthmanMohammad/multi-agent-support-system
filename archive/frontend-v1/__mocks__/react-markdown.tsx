import type { ReactNode } from "react";

interface ReactMarkdownProps {
  children?: string;
  className?: string;
}

export default function ReactMarkdown({
  children,
}: ReactMarkdownProps): ReactNode {
  return <div data-testid="markdown">{children}</div>;
}
