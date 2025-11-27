import { Card, CardContent, CardHeader, Skeleton, Spinner } from '@/components/ui';

// Full page loading
export function PageLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <Spinner size="lg" className="mb-4" />
        <p className="text-text-secondary">Loading...</p>
      </div>
    </div>
  );
}

// Card content loading
export function CardLoading() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-1/3" />
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-4 w-2/3" />
      </CardContent>
    </Card>
  );
}

// Table/list loading
interface ListLoadingProps {
  rows?: number;
}

export function ListLoading({ rows = 5 }: ListLoadingProps) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 border border-border rounded-lg">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-8 w-20" />
        </div>
      ))}
    </div>
  );
}

// Stats cards loading
export function StatsLoading() {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-8 w-16" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Chat loading skeleton
export function ChatLoading() {
  return (
    <div className="flex h-full gap-6">
      <Card className="w-80 flex flex-col shrink-0">
        <div className="p-4 border-b border-border">
          <Skeleton className="h-6 w-32" />
        </div>
        <div className="p-2 space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-3">
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-3 w-2/3" />
            </div>
          ))}
        </div>
      </Card>
      <Card className="flex-1 flex flex-col">
        <div className="p-4 border-b border-border">
          <Skeleton className="h-6 w-32 mb-1" />
          <Skeleton className="h-4 w-24" />
        </div>
        <div className="flex-1 p-4 space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <Skeleton className="h-20 w-2/3 rounded-lg" />
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-border">
          <Skeleton className="h-10 w-full rounded-md" />
        </div>
      </Card>
    </div>
  );
}

// Dashboard loading
export function DashboardLoading() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-48 mb-2" />
        <Skeleton className="h-4 w-64" />
      </div>
      <StatsLoading />
      <div className="grid gap-6 lg:grid-cols-2">
        <CardLoading />
        <CardLoading />
      </div>
    </div>
  );
}

// Settings loading
export function SettingsLoading() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-4 w-48" />
      </div>
      <div className="flex gap-6">
        <Card className="w-64 shrink-0">
          <CardContent className="p-2 space-y-1">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-lg" />
            ))}
          </CardContent>
        </Card>
        <Card className="flex-1">
          <CardContent className="p-6 space-y-6">
            <div className="space-y-2">
              <Skeleton className="h-6 w-1/4" />
              <Skeleton className="h-4 w-2/3" />
            </div>
            <Skeleton className="h-px w-full" />
            <div className="flex gap-4">
              <Skeleton className="h-20 w-20 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-8 w-32" />
                <Skeleton className="h-3 w-40" />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-10 w-full" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-10 w-full" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Button loading state
interface ButtonLoadingProps {
  className?: string;
}

export function ButtonLoading({ className }: ButtonLoadingProps) {
  return (
    <span className={className}>
      <Spinner size="sm" className="mr-2" />
      Loading...
    </span>
  );
}

// Inline loading
export function InlineLoading() {
  return (
    <div className="flex items-center gap-2 text-text-secondary">
      <Spinner size="sm" />
      <span className="text-sm">Loading...</span>
    </div>
  );
}
