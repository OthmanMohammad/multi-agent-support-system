"use client";

import type { JSX } from "react";
import { useState } from "react";
import {
  Check,
  Download,
  File,
  FileJson,
  FileText,
  Printer,
} from "lucide-react";
import type {
  Conversation,
  ConversationMessage as Message,
} from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import {
  exportConversation,
  type ExportFormat,
  getExportSize,
} from "@/lib/utils/export-chat";
import { cn } from "@/lib/utils";

interface ExportDialogProps {
  conversation: Conversation;
  messages: Message[];
  isOpen: boolean;
  onClose: () => void;
}

interface FormatOption {
  format: ExportFormat;
  label: string;
  description: string;
  icon: typeof FileText;
}

const EXPORT_FORMATS: FormatOption[] = [
  {
    format: "markdown",
    label: "Markdown",
    description: "Human-readable format with formatting",
    icon: FileText,
  },
  {
    format: "json",
    label: "JSON",
    description: "Machine-readable format with full data",
    icon: FileJson,
  },
  {
    format: "txt",
    label: "Plain Text",
    description: "Simple text format without formatting",
    icon: File,
  },
  {
    format: "pdf",
    label: "PDF",
    description: "Print to PDF (opens print dialog)",
    icon: Printer,
  },
];

/**
 * Export Dialog Component
 * Modal for exporting conversations in various formats
 */
export function ExportDialog({
  conversation,
  messages,
  isOpen,
  onClose,
}: ExportDialogProps): JSX.Element | null {
  const [selectedFormat, setSelectedFormat] =
    useState<ExportFormat>("markdown");
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  if (!isOpen) {
    return null;
  }

  const handleExport = async (): Promise<void> => {
    setIsExporting(true);

    try {
      await exportConversation({
        format: selectedFormat,
        conversation,
        messages,
        includeMetadata,
      });

      // Close dialog after export
      setTimeout(() => {
        onClose();
        setIsExporting(false);
      }, 1000);
    } catch (error) {
      console.error("Export failed:", error);
      setIsExporting(false);
      // TODO: Show error toast
    }
  };

  const estimatedSize = getExportSize(conversation, messages, selectedFormat);
  const sizeInKB = (estimatedSize / 1024).toFixed(1);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-background p-6 shadow-lg">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold">Export Conversation</h2>
          <p className="mt-1 text-sm text-foreground-secondary">
            Choose a format to download this conversation
          </p>
        </div>

        {/* Format Selection */}
        <div className="mb-6 space-y-2">
          <label className="text-sm font-medium">Format</label>
          <div className="grid grid-cols-2 gap-3">
            {EXPORT_FORMATS.map((formatOption) => {
              const Icon = formatOption.icon;
              const isSelected = selectedFormat === formatOption.format;

              return (
                <button
                  key={formatOption.format}
                  onClick={() => setSelectedFormat(formatOption.format)}
                  className={cn(
                    "relative flex flex-col items-start gap-2 rounded-lg border p-4 text-left transition-colors",
                    isSelected
                      ? "border-accent bg-accent/10"
                      : "border-border bg-surface hover:bg-surface/80"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{formatOption.label}</span>
                    {isSelected && (
                      <Check className="ml-auto h-4 w-4 text-accent-foreground" />
                    )}
                  </div>
                  <p className="text-xs text-foreground-secondary">
                    {formatOption.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Options */}
        <div className="mb-6">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeMetadata}
              onChange={(e) => setIncludeMetadata(e.target.checked)}
              className="h-4 w-4 rounded border-border"
            />
            <span className="text-sm">Include metadata and timestamps</span>
          </label>
        </div>

        {/* Info */}
        <div className="mb-6 rounded-lg bg-surface p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-foreground-secondary">Conversation:</span>
            <span className="font-medium">
              {conversation.primary_intent ||
                `Conversation ${conversation.conversation_id.slice(0, 8)}...`}
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between text-sm">
            <span className="text-foreground-secondary">Messages:</span>
            <span className="font-medium">{messages.length}</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-sm">
            <span className="text-foreground-secondary">Estimated size:</span>
            <span className="font-medium">{sizeInKB} KB</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button
            onClick={handleExport}
            disabled={isExporting}
            className="flex-1"
          >
            {isExporting ? (
              <>
                <Download className="mr-2 h-4 w-4 animate-bounce" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Export
              </>
            )}
          </Button>
        </div>
      </div>
    </>
  );
}
