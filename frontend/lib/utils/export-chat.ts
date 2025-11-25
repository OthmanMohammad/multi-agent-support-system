/**
 * Chat Export Utilities
 *
 * Functions for exporting conversations in various formats
 */

import type { Conversation, ConversationMessage } from "@/lib/types/api";

export type ExportFormat = "markdown" | "json" | "txt" | "pdf";

interface ExportOptions {
  format: ExportFormat;
  conversation: Conversation;
  messages: ConversationMessage[];
  includeMetadata?: boolean;
}

/**
 * Export conversation to the specified format
 */
export async function exportConversation(options: ExportOptions): Promise<void> {
  const { format, conversation, messages, includeMetadata = true } = options;

  let content: string;
  let filename: string;
  let mimeType: string;

  switch (format) {
    case "markdown":
      content = formatAsMarkdown(conversation, messages, includeMetadata);
      filename = `conversation-${conversation.conversation_id}.md`;
      mimeType = "text/markdown";
      break;

    case "json":
      content = formatAsJSON(conversation, messages, includeMetadata);
      filename = `conversation-${conversation.conversation_id}.json`;
      mimeType = "application/json";
      break;

    case "txt":
      content = formatAsText(conversation, messages, includeMetadata);
      filename = `conversation-${conversation.conversation_id}.txt`;
      mimeType = "text/plain";
      break;

    case "pdf":
      // For PDF, we open print dialog
      printConversation(conversation, messages, includeMetadata);
      return;

    default:
      throw new Error(`Unsupported export format: ${format}`);
  }

  // Create and trigger download
  downloadFile(content, filename, mimeType);
}

/**
 * Get estimated file size for export
 */
export function getExportSize(
  _conversation: Conversation,
  messages: ConversationMessage[],
  format: ExportFormat
): number {
  // Rough estimation based on format overhead
  const baseSize = messages.reduce((acc, msg) => acc + msg.content.length, 0);

  switch (format) {
    case "markdown":
      return Math.round(baseSize * 1.3); // MD formatting adds ~30%
    case "json":
      return Math.round(baseSize * 2.0); // JSON structure adds ~100%
    case "txt":
      return Math.round(baseSize * 1.1); // Minimal overhead
    case "pdf":
      return Math.round(baseSize * 1.5); // PDF overhead
    default:
      return baseSize;
  }
}

/**
 * Format conversation as Markdown
 */
function formatAsMarkdown(
  conversation: Conversation,
  messages: ConversationMessage[],
  includeMetadata: boolean
): string {
  const lines: string[] = [];

  // Title
  lines.push(`# Conversation Export`);
  lines.push("");

  // Metadata
  if (includeMetadata) {
    lines.push("## Details");
    lines.push("");
    lines.push(`- **ID**: ${conversation.conversation_id}`);
    lines.push(`- **Status**: ${conversation.status}`);
    lines.push(`- **Started**: ${formatDate(conversation.started_at)}`);
    lines.push(`- **Last Updated**: ${formatDate(conversation.last_updated)}`);
    if (conversation.primary_intent) {
      lines.push(`- **Primary Intent**: ${conversation.primary_intent}`);
    }
    if (conversation.agent_history.length > 0) {
      lines.push(`- **Agents**: ${conversation.agent_history.join(", ")}`);
    }
    lines.push("");
  }

  // Messages
  lines.push("## Messages");
  lines.push("");

  for (const message of messages) {
    const role = message.role === "user" ? "User" : message.agent_name || "Assistant";
    const timestamp = includeMetadata ? ` (${formatDate(message.timestamp)})` : "";

    lines.push(`### ${role}${timestamp}`);
    lines.push("");
    lines.push(message.content);
    lines.push("");
  }

  return lines.join("\n");
}

/**
 * Format conversation as JSON
 */
function formatAsJSON(
  conversation: Conversation,
  messages: ConversationMessage[],
  includeMetadata: boolean
): string {
  const data = includeMetadata
    ? {
        conversation: {
          id: conversation.conversation_id,
          status: conversation.status,
          started_at: conversation.started_at,
          last_updated: conversation.last_updated,
          primary_intent: conversation.primary_intent,
          agent_history: conversation.agent_history,
        },
        messages: messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
          agent_name: msg.agent_name,
          timestamp: msg.timestamp,
        })),
        exported_at: new Date().toISOString(),
      }
    : {
        messages: messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        })),
      };

  return JSON.stringify(data, null, 2);
}

/**
 * Format conversation as plain text
 */
function formatAsText(
  conversation: Conversation,
  messages: ConversationMessage[],
  includeMetadata: boolean
): string {
  const lines: string[] = [];

  // Header
  lines.push("CONVERSATION EXPORT");
  lines.push("=".repeat(40));
  lines.push("");

  // Metadata
  if (includeMetadata) {
    lines.push(`ID: ${conversation.conversation_id}`);
    lines.push(`Status: ${conversation.status}`);
    lines.push(`Started: ${formatDate(conversation.started_at)}`);
    lines.push("");
    lines.push("-".repeat(40));
    lines.push("");
  }

  // Messages
  for (const message of messages) {
    const role = message.role === "user" ? "USER" : (message.agent_name || "ASSISTANT").toUpperCase();
    const timestamp = includeMetadata ? ` [${formatDate(message.timestamp)}]` : "";

    lines.push(`${role}${timestamp}:`);
    lines.push(message.content);
    lines.push("");
  }

  return lines.join("\n");
}

/**
 * Open print dialog for PDF export
 */
function printConversation(
  conversation: Conversation,
  messages: ConversationMessage[],
  includeMetadata: boolean
): void {
  // Create a printable HTML document
  const content = formatAsMarkdown(conversation, messages, includeMetadata);

  // Create new window for printing
  const printWindow = window.open("", "_blank");
  if (!printWindow) {
    throw new Error("Failed to open print window. Please check popup blocker.");
  }

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Conversation Export</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          max-width: 800px;
          margin: 0 auto;
          padding: 40px 20px;
          line-height: 1.6;
        }
        h1 { font-size: 24px; margin-bottom: 20px; }
        h2 { font-size: 18px; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
        h3 { font-size: 14px; margin-top: 20px; color: #666; }
        p { margin: 10px 0; }
        ul { margin: 10px 0; padding-left: 20px; }
        pre { background: #f5f5f5; padding: 10px; overflow-x: auto; }
        @media print {
          body { padding: 0; }
        }
      </style>
    </head>
    <body>
      ${markdownToHTML(content)}
    </body>
    </html>
  `);

  printWindow.document.close();
  printWindow.focus();

  // Wait for content to load, then print
  setTimeout(() => {
    printWindow.print();
  }, 250);
}

/**
 * Simple markdown to HTML conversion for print
 */
function markdownToHTML(markdown: string): string {
  return markdown
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^(.+)$/gm, (match) => {
      if (match.startsWith("<")) return match;
      return `<p>${match}</p>`;
    })
    .replace(/<p><\/p>/g, "");
}

/**
 * Trigger file download
 */
function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.style.display = "none";

  document.body.appendChild(link);
  link.click();

  // Cleanup
  setTimeout(() => {
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, 100);
}

/**
 * Format date string to readable format
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
