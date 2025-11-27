import { AlertCircle } from 'lucide-react';

interface FieldErrorProps {
  message?: string;
}

export function FieldError({ message }: FieldErrorProps) {
  if (!message) return null;

  return (
    <div className="flex items-center gap-1.5 text-sm text-error mt-1.5">
      <AlertCircle className="h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
