/**
 * Toast utilities using Sonner
 *
 * Re-exports sonner's toast with consistent styling and custom helpers
 */

import { toast as sonnerToast, type ExternalToast } from "sonner";

/**
 * Re-export sonner toast with all methods
 */
export const toast = sonnerToast;

/**
 * File-related toast helpers
 */
export const fileToast = {
  /**
   * Show error for file size exceeding limit
   */
  sizeLimit: (maxSize: string) => {
    sonnerToast.error("File too large", {
      description: `Maximum file size is ${maxSize}`,
    });
  },

  /**
   * Show error for unsupported file type
   */
  typeError: (allowedTypes: string[]) => {
    const types = allowedTypes
      .map((t) => {
        // Extract extension from mime type
        const ext = t.split("/").pop() || t;
        return ext.toUpperCase();
      })
      .join(", ");

    sonnerToast.error("Invalid file type", {
      description: `Allowed types: ${types}`,
    });
  },

  /**
   * Show success for file upload
   */
  uploadSuccess: (fileName: string) => {
    sonnerToast.success("File uploaded", {
      description: fileName,
    });
  },

  /**
   * Show error for file upload failure
   */
  uploadError: (fileName?: string) => {
    sonnerToast.error("Upload failed", {
      description: fileName ? `Failed to upload ${fileName}` : "Please try again",
    });
  },

  /**
   * Show file processing progress
   */
  processing: (fileName: string): string | number => {
    return sonnerToast.loading("Processing file...", {
      description: fileName,
    });
  },
};

/**
 * API-related toast helpers
 */
export const apiToast = {
  /**
   * Show error for API failure
   */
  error: (message: string, options?: ExternalToast) => {
    sonnerToast.error(message, {
      description: "Please try again or contact support",
      ...options,
    });
  },

  /**
   * Show success for API operation
   */
  success: (message: string, options?: ExternalToast) => {
    sonnerToast.success(message, options);
  },

  /**
   * Show loading toast and return dismiss function
   */
  loading: (message: string): string | number => {
    return sonnerToast.loading(message);
  },

  /**
   * Dismiss a toast by ID
   */
  dismiss: (toastId: string | number) => {
    sonnerToast.dismiss(toastId);
  },
};

/**
 * Notification helpers
 */
export const notificationToast = {
  /**
   * Show new message notification
   */
  newMessage: (from: string, preview: string) => {
    sonnerToast.info("New message", {
      description: `${from}: ${preview.substring(0, 50)}${preview.length > 50 ? "..." : ""}`,
    });
  },

  /**
   * Show agent response notification
   */
  agentResponse: (agentName: string) => {
    sonnerToast.info(`${agentName} is responding`, {
      duration: 2000,
    });
  },
};
