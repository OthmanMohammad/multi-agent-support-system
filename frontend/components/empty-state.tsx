import { type LucideIcon } from 'lucide-react';
import { type ReactNode } from 'react';

import { Button, Card, CardContent } from '@/components/ui';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  children?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action, children }: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="p-12 text-center">
        <div className="flex justify-center mb-4">
          <div className="p-4 rounded-full bg-background-secondary">
            <Icon className="h-8 w-8 text-text-tertiary" />
          </div>
        </div>
        <h3 className="text-lg font-semibold text-text-primary mb-2">{title}</h3>
        <p className="text-text-secondary max-w-sm mx-auto mb-6">{description}</p>
        {action && (
          <Button onClick={action.onClick}>
            {action.label}
          </Button>
        )}
        {children}
      </CardContent>
    </Card>
  );
}

// Specific empty states for common scenarios
interface SearchEmptyStateProps {
  query: string;
  onClear?: () => void;
}

export function SearchEmptyState({ query, onClear }: SearchEmptyStateProps) {
  return (
    <div className="py-12 text-center">
      <p className="text-text-secondary mb-2">
        No results found for <span className="font-medium text-text-primary">"{query}"</span>
      </p>
      <p className="text-sm text-text-tertiary mb-4">
        Try adjusting your search or filters
      </p>
      {onClear && (
        <Button variant="outline" size="sm" onClick={onClear}>
          Clear Search
        </Button>
      )}
    </div>
  );
}

interface ListEmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function ListEmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
}: ListEmptyStateProps) {
  return (
    <div className="py-8 text-center">
      <div className="flex justify-center mb-3">
        <div className="p-3 rounded-full bg-background-secondary">
          <Icon className="h-6 w-6 text-text-tertiary" />
        </div>
      </div>
      <h4 className="font-medium text-text-primary mb-1">{title}</h4>
      <p className="text-sm text-text-secondary max-w-xs mx-auto mb-4">{description}</p>
      {actionLabel && onAction && (
        <Button variant="outline" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
