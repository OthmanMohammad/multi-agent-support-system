"use client";

import type { JSX } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Menu, LogOut, User, Settings, ChevronDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ThemeToggle } from "@/components/theme-toggle";
import { navConfig, siteConfig } from "@/config/site";
import { useAuth } from "@/lib/contexts/auth-context";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Header Component
 *
 * Enterprise-grade header with:
 * - Navigation links
 * - User authentication state indicator
 * - User dropdown menu with profile and logout
 * - Theme toggle
 * - Mobile menu support
 */
export const Header = (): JSX.Element => {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, isInitialized, logout } = useAuth();

  // Show loading state only during initial auth check
  const showLoading = !isInitialized || isLoading;

  /**
   * Get user initials for avatar fallback
   */
  const getUserInitials = (name: string | undefined): string => {
    if (!name) return "U";
    const parts = name.split(" ").filter(Boolean);
    const first = parts[0]?.[0] ?? "";
    const second = parts[1]?.[0] ?? "";
    if (first && second) {
      return `${first}${second}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  /**
   * Handle logout
   */
  const handleLogout = async () => {
    await logout();
  };

  /**
   * Navigate to sign in
   */
  const handleSignIn = () => {
    router.push("/auth/signin");
  };

  /**
   * Navigate to sign up
   */
  const handleSignUp = () => {
    router.push("/auth/signup");
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-6">
          {/* Mobile Menu Button */}
          <Button variant="ghost" size="icon" className="md:hidden">
            <Menu className="h-5 w-5" />
            <span className="sr-only">Toggle menu</span>
          </Button>

          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold">{siteConfig.name}</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden gap-6 md:flex">
            {navConfig.mainNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="text-sm font-medium text-foreground-secondary transition-colors hover:text-foreground"
              >
                {item.title}
              </Link>
            ))}
          </nav>
        </div>

        {/* Right Side: Auth & Settings */}
        <div className="flex items-center gap-3">
          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Auth Section */}
          {showLoading ? (
            // Loading skeleton during auth initialization
            <div className="flex items-center gap-2">
              <Skeleton className="h-8 w-8 rounded-full" />
            </div>
          ) : isAuthenticated && user ? (
            // Logged in: Show user menu
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="flex items-center gap-2 px-2"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-accent text-accent-foreground text-xs">
                      {getUserInitials(user.full_name)}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden text-sm font-medium md:inline-block">
                    {user.full_name || user.email}
                  </span>
                  <ChevronDown className="h-4 w-4 text-foreground-secondary" />
                </Button>
              </DropdownMenuTrigger>

              <DropdownMenuContent align="end" className="w-56">
                {/* User Info */}
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{user.full_name}</p>
                    <p className="text-xs text-foreground-secondary truncate">
                      {user.email}
                    </p>
                  </div>
                </DropdownMenuLabel>

                <DropdownMenuSeparator />

                {/* Menu Items */}
                <DropdownMenuItem
                  onClick={() => router.push("/dashboard")}
                  className="cursor-pointer"
                >
                  <User className="mr-2 h-4 w-4" />
                  Dashboard
                </DropdownMenuItem>

                <DropdownMenuItem
                  onClick={() => router.push("/settings")}
                  className="cursor-pointer"
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>

                <DropdownMenuSeparator />

                {/* Logout */}
                <DropdownMenuItem
                  onClick={handleLogout}
                  destructive
                  className="cursor-pointer"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            // Not logged in: Show sign in / sign up buttons
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={handleSignIn}>
                Sign in
              </Button>
              <Button size="sm" onClick={handleSignUp}>
                Sign up
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
