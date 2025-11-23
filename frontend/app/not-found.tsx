import type { JSX } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * 404 Not Found Page
 * Shown when a page doesn't exist
 */
export default function NotFound(): JSX.Element {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto mb-4 text-6xl font-bold text-accent">404</div>
          <CardTitle>Page Not Found</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-foreground-secondary">
            The page you&apos;re looking for doesn&apos;t exist or has been
            moved.
          </p>

          <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
            <Button asChild variant="default">
              <Link href="/">Go to Homepage</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/chat">Start a Chat</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
