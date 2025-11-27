"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Dropdown Menu Component
 *
 * A simple, accessible dropdown menu built with React.
 * Handles click-outside, keyboard navigation, and proper ARIA attributes.
 */

interface DropdownMenuContextValue {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const DropdownMenuContext =
  React.createContext<DropdownMenuContextValue | null>(null);

function useDropdownMenu() {
  const context = React.useContext(DropdownMenuContext);
  if (!context) {
    throw new Error("Dropdown components must be used within DropdownMenu");
  }
  return context;
}

interface DropdownMenuProps {
  children: React.ReactNode;
}

export function DropdownMenu({ children }: DropdownMenuProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <DropdownMenuContext.Provider value={{ isOpen, setIsOpen }}>
      <div className="relative inline-block text-left">{children}</div>
    </DropdownMenuContext.Provider>
  );
}

interface DropdownMenuTriggerProps {
  children: React.ReactNode;
  className?: string;
  asChild?: boolean;
}

export function DropdownMenuTrigger({
  children,
  className,
  asChild,
}: DropdownMenuTriggerProps) {
  const { isOpen, setIsOpen } = useDropdownMenu();

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(
      children as React.ReactElement<{
        onClick?: (e: React.MouseEvent) => void;
        "aria-expanded"?: boolean;
        "aria-haspopup"?: boolean;
      }>,
      {
        onClick: handleClick,
        "aria-expanded": isOpen,
        "aria-haspopup": true,
      }
    );
  }

  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        className
      )}
      onClick={handleClick}
      aria-expanded={isOpen}
      aria-haspopup
    >
      {children}
    </button>
  );
}

interface DropdownMenuContentProps {
  children: React.ReactNode;
  className?: string;
  align?: "start" | "center" | "end";
}

export function DropdownMenuContent({
  children,
  className,
  align = "end",
}: DropdownMenuContentProps) {
  const { isOpen, setIsOpen } = useDropdownMenu();
  const contentRef = React.useRef<HTMLDivElement>(null);

  // Close on click outside
  React.useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      if (
        contentRef.current &&
        !contentRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, setIsOpen]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      ref={contentRef}
      className={cn(
        "absolute z-50 mt-2 min-w-[12rem] overflow-hidden rounded-md border border-border bg-background p-1 shadow-lg",
        "animate-in fade-in-0 zoom-in-95 slide-in-from-top-2",
        align === "start" && "left-0",
        align === "center" && "left-1/2 -translate-x-1/2",
        align === "end" && "right-0",
        className
      )}
      role="menu"
      aria-orientation="vertical"
    >
      {children}
    </div>
  );
}

interface DropdownMenuItemProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  destructive?: boolean;
}

export function DropdownMenuItem({
  children,
  className,
  onClick,
  disabled = false,
  destructive = false,
}: DropdownMenuItemProps) {
  const { setIsOpen } = useDropdownMenu();

  const handleClick = () => {
    if (disabled) {
      return;
    }
    onClick?.();
    setIsOpen(false);
  };

  return (
    <button
      type="button"
      className={cn(
        "relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors",
        "hover:bg-accent hover:text-accent-foreground",
        "focus:bg-accent focus:text-accent-foreground",
        disabled && "pointer-events-none opacity-50",
        destructive && "text-destructive hover:bg-destructive/10",
        className
      )}
      role="menuitem"
      onClick={handleClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

interface DropdownMenuLabelProps {
  children: React.ReactNode;
  className?: string;
}

export function DropdownMenuLabel({
  children,
  className,
}: DropdownMenuLabelProps) {
  return (
    <div
      className={cn(
        "px-2 py-1.5 text-sm font-semibold text-foreground",
        className
      )}
    >
      {children}
    </div>
  );
}

export function DropdownMenuSeparator({ className }: { className?: string }) {
  return <div className={cn("-mx-1 my-1 h-px bg-border", className)} />;
}
