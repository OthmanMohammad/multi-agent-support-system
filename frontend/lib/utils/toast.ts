import { toast as sonnerToast } from "sonner";

/**
 * Toast utility wrapper for sonner
 * Provides typed toast methods with consistent styling
 */
export const toast = {
  success: (message: string, options?: { description?: string }) =>
    sonnerToast.success(message, options),

  error: (message: string, options?: { description?: string; action?: { label: string; onClick: () => void } }) =>
    sonnerToast.error(message, options),

  info: (message: string, options?: { description?: string }) =>
    sonnerToast.info(message, options),

  warning: (message: string, options?: { description?: string }) =>
    sonnerToast.warning(message, options),

  loading: (message: string) =>
    sonnerToast.loading(message),

  promise: <T>(
    promise: Promise<T>,
    options: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: unknown) => string);
    }
  ) => sonnerToast.promise(promise, options),
};

/**
 * File upload toast helpers
 */
export const fileToast = {
  sizeLimit: (maxSize: string) =>
    toast.error(`File too large`, { description: `Maximum file size is ${maxSize}` }),

  typeError: (allowedTypes: string[]) =>
    toast.error(`Invalid file type`, {
      description: `Allowed types: ${allowedTypes.join(", ")}`,
    }),

  uploadSuccess: (fileName: string) =>
    toast.success(`File uploaded`, { description: fileName }),

  uploadError: (fileName: string) =>
    toast.error(`Upload failed`, { description: fileName }),
};
