'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  MessageSquare,
  Users,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';

import { Logo } from '@/components/shared';
import { Button, Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui';
import { useAuthStore } from '@/lib/stores/auth-store';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/chat', icon: MessageSquare, label: 'Chat' },
  { href: '/customers', icon: Users, label: 'Customers' },
  { href: '/settings', icon: Settings, label: 'Settings' },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'flex flex-col border-r border-border bg-surface transition-all duration-200',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border">
        {!collapsed && <Logo size="sm" />}
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setCollapsed(!collapsed)}
          className={cn(collapsed && 'mx-auto')}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

          const NavLink = (
            <Link
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-orange/10 text-brand-orange'
                  : 'text-text-secondary hover:bg-background-secondary hover:text-text-primary',
                collapsed && 'justify-center'
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );

          if (collapsed) {
            return (
              <Tooltip key={item.href} delayDuration={0}>
                <TooltipTrigger asChild>{NavLink}</TooltipTrigger>
                <TooltipContent side="right">{item.label}</TooltipContent>
              </Tooltip>
            );
          }

          return <div key={item.href}>{NavLink}</div>;
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-border">
        {collapsed ? (
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => logout()}
                className="w-full text-text-secondary hover:text-error"
              >
                <LogOut className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Sign Out</TooltipContent>
          </Tooltip>
        ) : (
          <Button
            variant="ghost"
            onClick={() => logout()}
            className="w-full justify-start gap-3 text-text-secondary hover:text-error hover:bg-error-light"
          >
            <LogOut className="h-5 w-5" />
            Sign Out
          </Button>
        )}
      </div>
    </aside>
  );
}
