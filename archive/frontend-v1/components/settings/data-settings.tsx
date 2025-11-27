"use client";

import type { JSX } from "react";
import { useState } from "react";
import { Download, Trash2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/lib/utils/toast";

/**
 * Data Settings Component
 * Export, import, and manage user data
 */
export function DataSettings(): JSX.Element {
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  const handleExportData = async (): Promise<void> => {
    setIsExporting(true);

    try {
      // TODO: Implement actual data export
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const data = {
        conversations: [],
        messages: [],
        preferences: {},
        exportedAt: new Date().toISOString(),
      };

      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `user-data-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);

      toast.success("Data exported", {
        description: "Your data has been downloaded",
      });
    } catch (_error) {
      toast.error("Export failed", {
        description: "Failed to export your data",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleImportData = async (
    e: React.ChangeEvent<HTMLInputElement>
  ): Promise<void> => {
    const file = e.target.files?.[0];
    if (!file) {
      return;
    }

    setIsImporting(true);

    try {
      const text = await file.text();
      // Validate JSON by parsing
      JSON.parse(text);

      // TODO: Validate and import data
      await new Promise((resolve) => setTimeout(resolve, 1500));

      toast.success("Data imported", {
        description: "Your data has been restored",
      });
    } catch (_error) {
      toast.error("Import failed", {
        description: "Invalid data file",
      });
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Data Management</h2>
        <p className="mt-1 text-sm text-foreground-secondary">
          Export, import, and manage your data
        </p>
      </div>

      {/* Export Data */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Download className="h-5 w-5" />
          <h3 className="font-semibold">Export Data</h3>
        </div>
        <p className="mb-4 text-sm text-foreground-secondary">
          Download all your conversations, messages, and settings as a JSON file
        </p>
        <Button onClick={handleExportData} disabled={isExporting}>
          {isExporting ? "Exporting..." : "Export All Data"}
        </Button>
      </div>

      {/* Import Data */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Upload className="h-5 w-5" />
          <h3 className="font-semibold">Import Data</h3>
        </div>
        <p className="mb-4 text-sm text-foreground-secondary">
          Restore your data from a previously exported file
        </p>
        <input
          type="file"
          accept=".json"
          onChange={handleImportData}
          className="hidden"
          id="import-file"
        />
        <Button
          onClick={() => document.getElementById("import-file")?.click()}
          disabled={isImporting}
          variant="outline"
        >
          {isImporting ? "Importing..." : "Import Data"}
        </Button>
      </div>

      {/* Clear Data */}
      <div className="rounded-lg border border-destructive bg-destructive/5 p-6">
        <div className="mb-4 flex items-center gap-2">
          <Trash2 className="h-5 w-5 text-destructive" />
          <h3 className="font-semibold text-destructive">Clear All Data</h3>
        </div>
        <p className="mb-4 text-sm text-foreground-secondary">
          Permanently delete all your conversations and messages
        </p>
        <Button variant="destructive">Clear All Data</Button>
      </div>
    </div>
  );
}
