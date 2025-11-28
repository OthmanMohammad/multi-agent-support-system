// =============================================================================
// THAT AGENTS PROJECT - COMPLETE PIXEL ICON LIBRARY
// =============================================================================
// Usage: <Icon name="agent-router" size={24} className="text-orange-500" />
// All icons are pixel-art style SVGs that match Mistral.ai aesthetic
// =============================================================================

import React from 'react';

interface IconProps {
  name: string;
  size?: number;
  className?: string;
}

// =============================================================================
// MAIN ICON COMPONENT
// =============================================================================
export const Icon: React.FC<IconProps> = ({ name, size = 24, className = '' }) => {
  const icon = icons[name];
  if (!icon) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      {icon}
    </svg>
  );
};

// =============================================================================
// ICON DEFINITIONS (Pixel Art Style - Grid Based)
// =============================================================================
const icons: Record<string, React.ReactNode> = {
  // ===========================================================================
  // LOGO & BRAND
  // ===========================================================================

  // Main Logo - Pixel "T" with network nodes
  logo: (
    <>
      {/* Top bar of T */}
      <rect x="4" y="4" width="16" height="4" fill="currentColor" />
      {/* Stem of T */}
      <rect x="10" y="8" width="4" height="12" fill="currentColor" />
      {/* Network nodes */}
      <rect x="2" y="6" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="20" y="6" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="6" y="14" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="16" y="14" width="2" height="2" fill="currentColor" opacity="0.6" />
    </>
  ),

  // Logo Mark Only (simplified)
  'logo-mark': (
    <>
      <rect x="4" y="4" width="16" height="3" fill="currentColor" />
      <rect x="10" y="7" width="4" height="13" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // NAVIGATION ICONS
  // ===========================================================================

  menu: (
    <>
      <rect x="4" y="6" width="16" height="2" fill="currentColor" />
      <rect x="4" y="11" width="16" height="2" fill="currentColor" />
      <rect x="4" y="16" width="16" height="2" fill="currentColor" />
    </>
  ),

  close: (
    <>
      <rect x="6" y="5" width="2" height="2" fill="currentColor" />
      <rect x="8" y="7" width="2" height="2" fill="currentColor" />
      <rect x="10" y="9" width="2" height="2" fill="currentColor" />
      <rect x="12" y="11" width="2" height="2" fill="currentColor" />
      <rect x="14" y="13" width="2" height="2" fill="currentColor" />
      <rect x="16" y="15" width="2" height="2" fill="currentColor" />
      <rect x="16" y="5" width="2" height="2" fill="currentColor" />
      <rect x="14" y="7" width="2" height="2" fill="currentColor" />
      <rect x="12" y="9" width="2" height="2" fill="currentColor" />
      <rect x="10" y="11" width="2" height="2" fill="currentColor" />
      <rect x="8" y="13" width="2" height="2" fill="currentColor" />
      <rect x="6" y="15" width="2" height="2" fill="currentColor" />
    </>
  ),

  'arrow-right': (
    <>
      <rect x="4" y="11" width="12" height="2" fill="currentColor" />
      <rect x="14" y="9" width="2" height="2" fill="currentColor" />
      <rect x="16" y="11" width="2" height="2" fill="currentColor" />
      <rect x="14" y="13" width="2" height="2" fill="currentColor" />
    </>
  ),

  'arrow-left': (
    <>
      <rect x="8" y="11" width="12" height="2" fill="currentColor" />
      <rect x="8" y="9" width="2" height="2" fill="currentColor" />
      <rect x="6" y="11" width="2" height="2" fill="currentColor" />
      <rect x="8" y="13" width="2" height="2" fill="currentColor" />
    </>
  ),

  'arrow-up': (
    <>
      <rect x="11" y="6" width="2" height="12" fill="currentColor" />
      <rect x="9" y="8" width="2" height="2" fill="currentColor" />
      <rect x="11" y="6" width="2" height="2" fill="currentColor" />
      <rect x="13" y="8" width="2" height="2" fill="currentColor" />
    </>
  ),

  'arrow-down': (
    <>
      <rect x="11" y="6" width="2" height="12" fill="currentColor" />
      <rect x="9" y="14" width="2" height="2" fill="currentColor" />
      <rect x="11" y="16" width="2" height="2" fill="currentColor" />
      <rect x="13" y="14" width="2" height="2" fill="currentColor" />
    </>
  ),

  'chevron-down': (
    <>
      <rect x="6" y="9" width="2" height="2" fill="currentColor" />
      <rect x="8" y="11" width="2" height="2" fill="currentColor" />
      <rect x="10" y="13" width="2" height="2" fill="currentColor" />
      <rect x="12" y="13" width="2" height="2" fill="currentColor" />
      <rect x="14" y="11" width="2" height="2" fill="currentColor" />
      <rect x="16" y="9" width="2" height="2" fill="currentColor" />
    </>
  ),

  'chevron-up': (
    <>
      <rect x="6" y="13" width="2" height="2" fill="currentColor" />
      <rect x="8" y="11" width="2" height="2" fill="currentColor" />
      <rect x="10" y="9" width="2" height="2" fill="currentColor" />
      <rect x="12" y="9" width="2" height="2" fill="currentColor" />
      <rect x="14" y="11" width="2" height="2" fill="currentColor" />
      <rect x="16" y="13" width="2" height="2" fill="currentColor" />
    </>
  ),

  'chevron-right': (
    <>
      <rect x="9" y="6" width="2" height="2" fill="currentColor" />
      <rect x="11" y="8" width="2" height="2" fill="currentColor" />
      <rect x="13" y="10" width="2" height="2" fill="currentColor" />
      <rect x="13" y="12" width="2" height="2" fill="currentColor" />
      <rect x="11" y="14" width="2" height="2" fill="currentColor" />
      <rect x="9" y="16" width="2" height="2" fill="currentColor" />
    </>
  ),

  'chevron-left': (
    <>
      <rect x="13" y="6" width="2" height="2" fill="currentColor" />
      <rect x="11" y="8" width="2" height="2" fill="currentColor" />
      <rect x="9" y="10" width="2" height="2" fill="currentColor" />
      <rect x="9" y="12" width="2" height="2" fill="currentColor" />
      <rect x="11" y="14" width="2" height="2" fill="currentColor" />
      <rect x="13" y="16" width="2" height="2" fill="currentColor" />
    </>
  ),

  'external-link': (
    <>
      {/* Box */}
      <rect x="4" y="8" width="2" height="12" fill="currentColor" />
      <rect x="4" y="18" width="12" height="2" fill="currentColor" />
      <rect x="14" y="10" width="2" height="10" fill="currentColor" />
      {/* Arrow */}
      <rect x="10" y="4" width="10" height="2" fill="currentColor" />
      <rect x="18" y="4" width="2" height="8" fill="currentColor" />
      <rect x="10" y="12" width="2" height="2" fill="currentColor" />
      <rect x="12" y="10" width="2" height="2" fill="currentColor" />
      <rect x="14" y="8" width="2" height="2" fill="currentColor" />
      <rect x="16" y="6" width="2" height="2" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // ACTION ICONS
  // ===========================================================================

  search: (
    <>
      {/* Circle */}
      <rect x="6" y="4" width="8" height="2" fill="currentColor" />
      <rect x="4" y="6" width="2" height="8" fill="currentColor" />
      <rect x="14" y="6" width="2" height="8" fill="currentColor" />
      <rect x="6" y="14" width="8" height="2" fill="currentColor" />
      {/* Handle */}
      <rect x="14" y="14" width="2" height="2" fill="currentColor" />
      <rect x="16" y="16" width="2" height="2" fill="currentColor" />
      <rect x="18" y="18" width="2" height="2" fill="currentColor" />
    </>
  ),

  settings: (
    <>
      {/* Gear teeth */}
      <rect x="10" y="2" width="4" height="2" fill="currentColor" />
      <rect x="10" y="20" width="4" height="2" fill="currentColor" />
      <rect x="2" y="10" width="2" height="4" fill="currentColor" />
      <rect x="20" y="10" width="2" height="4" fill="currentColor" />
      {/* Diagonal teeth */}
      <rect x="4" y="4" width="2" height="2" fill="currentColor" />
      <rect x="18" y="4" width="2" height="2" fill="currentColor" />
      <rect x="4" y="18" width="2" height="2" fill="currentColor" />
      <rect x="18" y="18" width="2" height="2" fill="currentColor" />
      {/* Center circle */}
      <rect x="8" y="8" width="8" height="8" fill="currentColor" />
    </>
  ),

  copy: (
    <>
      {/* Back rectangle */}
      <rect x="8" y="4" width="10" height="2" fill="currentColor" />
      <rect x="8" y="4" width="2" height="12" fill="currentColor" />
      <rect x="16" y="4" width="2" height="12" fill="currentColor" />
      <rect x="8" y="14" width="4" height="2" fill="currentColor" />
      {/* Front rectangle */}
      <rect x="4" y="8" width="10" height="2" fill="currentColor" />
      <rect x="4" y="8" width="2" height="12" fill="currentColor" />
      <rect x="12" y="8" width="2" height="12" fill="currentColor" />
      <rect x="4" y="18" width="10" height="2" fill="currentColor" />
    </>
  ),

  check: (
    <>
      <rect x="4" y="12" width="2" height="2" fill="currentColor" />
      <rect x="6" y="14" width="2" height="2" fill="currentColor" />
      <rect x="8" y="16" width="2" height="2" fill="currentColor" />
      <rect x="10" y="14" width="2" height="2" fill="currentColor" />
      <rect x="12" y="12" width="2" height="2" fill="currentColor" />
      <rect x="14" y="10" width="2" height="2" fill="currentColor" />
      <rect x="16" y="8" width="2" height="2" fill="currentColor" />
      <rect x="18" y="6" width="2" height="2" fill="currentColor" />
    </>
  ),

  plus: (
    <>
      <rect x="11" y="4" width="2" height="16" fill="currentColor" />
      <rect x="4" y="11" width="16" height="2" fill="currentColor" />
    </>
  ),

  minus: (
    <>
      <rect x="4" y="11" width="16" height="2" fill="currentColor" />
    </>
  ),

  trash: (
    <>
      {/* Lid */}
      <rect x="4" y="4" width="16" height="2" fill="currentColor" />
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      {/* Can body */}
      <rect x="6" y="6" width="2" height="14" fill="currentColor" />
      <rect x="16" y="6" width="2" height="14" fill="currentColor" />
      <rect x="6" y="18" width="12" height="2" fill="currentColor" />
      {/* Lines */}
      <rect x="10" y="8" width="2" height="8" fill="currentColor" />
      <rect x="14" y="8" width="2" height="8" fill="currentColor" />
    </>
  ),

  edit: (
    <>
      {/* Pencil body */}
      <rect x="14" y="4" width="2" height="2" fill="currentColor" />
      <rect x="12" y="6" width="2" height="2" fill="currentColor" />
      <rect x="10" y="8" width="2" height="2" fill="currentColor" />
      <rect x="8" y="10" width="2" height="2" fill="currentColor" />
      <rect x="6" y="12" width="2" height="2" fill="currentColor" />
      <rect x="4" y="14" width="2" height="2" fill="currentColor" />
      {/* Tip */}
      <rect x="4" y="16" width="2" height="4" fill="currentColor" />
      <rect x="4" y="18" width="4" height="2" fill="currentColor" />
      {/* Top */}
      <rect x="16" y="4" width="4" height="2" fill="currentColor" />
      <rect x="18" y="6" width="2" height="4" fill="currentColor" />
      <rect x="16" y="8" width="2" height="2" fill="currentColor" />
      <rect x="14" y="10" width="2" height="2" fill="currentColor" />
    </>
  ),

  refresh: (
    <>
      {/* Top arc */}
      <rect x="8" y="4" width="8" height="2" fill="currentColor" />
      <rect x="16" y="6" width="2" height="4" fill="currentColor" />
      <rect x="16" y="2" width="2" height="4" fill="currentColor" />
      <rect x="18" y="4" width="2" height="2" fill="currentColor" />
      {/* Bottom arc */}
      <rect x="8" y="18" width="8" height="2" fill="currentColor" />
      <rect x="6" y="14" width="2" height="4" fill="currentColor" />
      <rect x="6" y="18" width="2" height="4" fill="currentColor" />
      <rect x="4" y="18" width="2" height="2" fill="currentColor" />
      {/* Sides */}
      <rect x="4" y="8" width="2" height="6" fill="currentColor" />
      <rect x="18" y="10" width="2" height="6" fill="currentColor" />
    </>
  ),

  download: (
    <>
      <rect x="11" y="4" width="2" height="10" fill="currentColor" />
      <rect x="7" y="12" width="2" height="2" fill="currentColor" />
      <rect x="9" y="14" width="2" height="2" fill="currentColor" />
      <rect x="11" y="16" width="2" height="2" fill="currentColor" />
      <rect x="13" y="14" width="2" height="2" fill="currentColor" />
      <rect x="15" y="12" width="2" height="2" fill="currentColor" />
      {/* Base */}
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      <rect x="4" y="14" width="2" height="4" fill="currentColor" />
      <rect x="18" y="14" width="2" height="4" fill="currentColor" />
    </>
  ),

  upload: (
    <>
      <rect x="11" y="10" width="2" height="10" fill="currentColor" />
      <rect x="7" y="8" width="2" height="2" fill="currentColor" />
      <rect x="9" y="6" width="2" height="2" fill="currentColor" />
      <rect x="11" y="4" width="2" height="2" fill="currentColor" />
      <rect x="13" y="6" width="2" height="2" fill="currentColor" />
      <rect x="15" y="8" width="2" height="2" fill="currentColor" />
      {/* Base */}
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      <rect x="4" y="14" width="2" height="4" fill="currentColor" />
      <rect x="18" y="14" width="2" height="4" fill="currentColor" />
    </>
  ),

  filter: (
    <>
      <rect x="2" y="4" width="20" height="2" fill="currentColor" />
      <rect x="4" y="6" width="2" height="2" fill="currentColor" />
      <rect x="18" y="6" width="2" height="2" fill="currentColor" />
      <rect x="6" y="8" width="12" height="2" fill="currentColor" />
      <rect x="8" y="10" width="2" height="2" fill="currentColor" />
      <rect x="14" y="10" width="2" height="2" fill="currentColor" />
      <rect x="10" y="12" width="4" height="2" fill="currentColor" />
      <rect x="11" y="14" width="2" height="6" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // USER & AUTH ICONS
  // ===========================================================================

  user: (
    <>
      {/* Head */}
      <rect x="8" y="4" width="8" height="2" fill="currentColor" />
      <rect x="6" y="6" width="2" height="6" fill="currentColor" />
      <rect x="16" y="6" width="2" height="6" fill="currentColor" />
      <rect x="8" y="12" width="8" height="2" fill="currentColor" />
      {/* Body */}
      <rect x="4" y="16" width="4" height="4" fill="currentColor" />
      <rect x="8" y="14" width="8" height="2" fill="currentColor" />
      <rect x="8" y="16" width="8" height="4" fill="currentColor" />
      <rect x="16" y="16" width="4" height="4" fill="currentColor" />
    </>
  ),

  users: (
    <>
      {/* First user */}
      <rect x="4" y="4" width="6" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="4" fill="currentColor" />
      <rect x="10" y="6" width="2" height="4" fill="currentColor" />
      <rect x="4" y="10" width="6" height="2" fill="currentColor" />
      <rect x="2" y="14" width="10" height="2" fill="currentColor" />
      <rect x="2" y="16" width="10" height="4" fill="currentColor" />
      {/* Second user (offset) */}
      <rect x="14" y="4" width="6" height="2" fill="currentColor" />
      <rect x="12" y="6" width="2" height="4" fill="currentColor" />
      <rect x="20" y="6" width="2" height="4" fill="currentColor" />
      <rect x="14" y="10" width="6" height="2" fill="currentColor" />
      <rect x="12" y="14" width="10" height="2" fill="currentColor" />
      <rect x="12" y="16" width="10" height="4" fill="currentColor" />
    </>
  ),

  lock: (
    <>
      {/* Shackle */}
      <rect x="8" y="4" width="8" height="2" fill="currentColor" />
      <rect x="6" y="6" width="2" height="6" fill="currentColor" />
      <rect x="16" y="6" width="2" height="6" fill="currentColor" />
      {/* Body */}
      <rect x="4" y="10" width="16" height="2" fill="currentColor" />
      <rect x="4" y="10" width="2" height="10" fill="currentColor" />
      <rect x="18" y="10" width="2" height="10" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      {/* Keyhole */}
      <rect x="10" y="13" width="4" height="2" fill="currentColor" />
      <rect x="11" y="15" width="2" height="2" fill="currentColor" />
    </>
  ),

  unlock: (
    <>
      {/* Shackle (open) */}
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      <rect x="6" y="4" width="2" height="4" fill="currentColor" />
      <rect x="16" y="4" width="2" height="8" fill="currentColor" />
      {/* Body */}
      <rect x="4" y="10" width="14" height="2" fill="currentColor" />
      <rect x="4" y="10" width="2" height="10" fill="currentColor" />
      <rect x="16" y="10" width="2" height="10" fill="currentColor" />
      <rect x="4" y="18" width="14" height="2" fill="currentColor" />
      {/* Keyhole */}
      <rect x="9" y="13" width="4" height="2" fill="currentColor" />
      <rect x="10" y="15" width="2" height="2" fill="currentColor" />
    </>
  ),

  logout: (
    <>
      {/* Door frame */}
      <rect x="4" y="4" width="10" height="2" fill="currentColor" />
      <rect x="4" y="4" width="2" height="16" fill="currentColor" />
      <rect x="4" y="18" width="10" height="2" fill="currentColor" />
      {/* Arrow */}
      <rect x="10" y="11" width="10" height="2" fill="currentColor" />
      <rect x="16" y="9" width="2" height="2" fill="currentColor" />
      <rect x="18" y="11" width="2" height="2" fill="currentColor" />
      <rect x="16" y="13" width="2" height="2" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // CHAT INTERFACE ICONS
  // ===========================================================================

  send: (
    <>
      <rect x="4" y="10" width="12" height="2" fill="currentColor" />
      <rect x="4" y="12" width="2" height="4" fill="currentColor" />
      <rect x="14" y="6" width="2" height="6" fill="currentColor" />
      <rect x="16" y="8" width="2" height="4" fill="currentColor" />
      <rect x="18" y="10" width="2" height="2" fill="currentColor" />
      <rect x="16" y="12" width="2" height="2" fill="currentColor" />
      <rect x="14" y="14" width="2" height="2" fill="currentColor" />
      <rect x="6" y="14" width="8" height="2" fill="currentColor" />
    </>
  ),

  message: (
    <>
      {/* Bubble */}
      <rect x="4" y="4" width="16" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="10" fill="currentColor" />
      <rect x="20" y="6" width="2" height="10" fill="currentColor" />
      <rect x="4" y="16" width="6" height="2" fill="currentColor" />
      <rect x="12" y="16" width="8" height="2" fill="currentColor" />
      {/* Tail */}
      <rect x="6" y="18" width="2" height="2" fill="currentColor" />
      <rect x="4" y="20" width="2" height="2" fill="currentColor" />
      {/* Lines */}
      <rect x="6" y="8" width="12" height="2" fill="currentColor" />
      <rect x="6" y="12" width="8" height="2" fill="currentColor" />
    </>
  ),

  chat: (
    <>
      {/* First bubble */}
      <rect x="2" y="4" width="12" height="2" fill="currentColor" />
      <rect x="2" y="4" width="2" height="8" fill="currentColor" />
      <rect x="12" y="4" width="2" height="8" fill="currentColor" />
      <rect x="2" y="10" width="12" height="2" fill="currentColor" />
      {/* Second bubble */}
      <rect x="10" y="12" width="12" height="2" fill="currentColor" />
      <rect x="10" y="12" width="2" height="8" fill="currentColor" />
      <rect x="20" y="12" width="2" height="8" fill="currentColor" />
      <rect x="10" y="18" width="12" height="2" fill="currentColor" />
    </>
  ),

  attach: (
    <>
      <rect x="10" y="2" width="6" height="2" fill="currentColor" />
      <rect x="16" y="4" width="2" height="12" fill="currentColor" />
      <rect x="8" y="6" width="2" height="14" fill="currentColor" />
      <rect x="10" y="18" width="6" height="2" fill="currentColor" />
      <rect x="6" y="8" width="2" height="10" fill="currentColor" />
      <rect x="8" y="16" width="2" height="2" fill="currentColor" />
      <rect x="10" y="4" width="2" height="2" fill="currentColor" />
      <rect x="14" y="14" width="2" height="2" fill="currentColor" />
      <rect x="12" y="14" width="2" height="4" fill="currentColor" />
    </>
  ),

  microphone: (
    <>
      {/* Mic head */}
      <rect x="9" y="2" width="6" height="2" fill="currentColor" />
      <rect x="7" y="4" width="2" height="8" fill="currentColor" />
      <rect x="15" y="4" width="2" height="8" fill="currentColor" />
      <rect x="9" y="12" width="6" height="2" fill="currentColor" />
      {/* Stand */}
      <rect x="5" y="10" width="2" height="4" fill="currentColor" />
      <rect x="17" y="10" width="2" height="4" fill="currentColor" />
      <rect x="5" y="14" width="14" height="2" fill="currentColor" />
      <rect x="11" y="16" width="2" height="4" fill="currentColor" />
      <rect x="8" y="20" width="8" height="2" fill="currentColor" />
    </>
  ),

  'thumbs-up': (
    <>
      <rect x="6" y="10" width="2" height="10" fill="currentColor" />
      <rect x="8" y="8" width="2" height="2" fill="currentColor" />
      <rect x="10" y="6" width="2" height="2" fill="currentColor" />
      <rect x="10" y="4" width="4" height="2" fill="currentColor" />
      <rect x="14" y="6" width="2" height="4" fill="currentColor" />
      <rect x="8" y="10" width="10" height="2" fill="currentColor" />
      <rect x="8" y="12" width="12" height="2" fill="currentColor" />
      <rect x="8" y="14" width="12" height="2" fill="currentColor" />
      <rect x="8" y="16" width="12" height="2" fill="currentColor" />
      <rect x="8" y="18" width="10" height="2" fill="currentColor" />
    </>
  ),

  'thumbs-down': (
    <>
      <rect x="6" y="4" width="2" height="10" fill="currentColor" />
      <rect x="8" y="14" width="2" height="2" fill="currentColor" />
      <rect x="10" y="16" width="2" height="2" fill="currentColor" />
      <rect x="10" y="18" width="4" height="2" fill="currentColor" />
      <rect x="14" y="14" width="2" height="4" fill="currentColor" />
      <rect x="8" y="12" width="10" height="2" fill="currentColor" />
      <rect x="8" y="10" width="12" height="2" fill="currentColor" />
      <rect x="8" y="8" width="12" height="2" fill="currentColor" />
      <rect x="8" y="6" width="12" height="2" fill="currentColor" />
      <rect x="8" y="4" width="10" height="2" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // AGENT TIER ICONS (Your 4 Tiers)
  // ===========================================================================

  // Tier 1: Essential - Foundation/Base icon
  'tier-essential': (
    <>
      {/* Foundation blocks */}
      <rect x="4" y="16" width="16" height="4" fill="currentColor" />
      <rect x="6" y="12" width="12" height="4" fill="currentColor" />
      <rect x="8" y="8" width="8" height="4" fill="currentColor" />
      <rect x="10" y="4" width="4" height="4" fill="currentColor" />
    </>
  ),

  // Tier 2: Revenue - Dollar/Growth icon
  'tier-revenue': (
    <>
      {/* Dollar sign */}
      <rect x="11" y="2" width="2" height="4" fill="currentColor" />
      <rect x="8" y="6" width="8" height="2" fill="currentColor" />
      <rect x="6" y="8" width="4" height="2" fill="currentColor" />
      <rect x="8" y="10" width="8" height="2" fill="currentColor" />
      <rect x="14" y="12" width="4" height="2" fill="currentColor" />
      <rect x="8" y="14" width="8" height="2" fill="currentColor" />
      <rect x="11" y="16" width="2" height="4" fill="currentColor" />
      {/* Growth arrow */}
      <rect x="16" y="4" width="2" height="2" fill="currentColor" />
      <rect x="18" y="2" width="4" height="2" fill="currentColor" />
      <rect x="20" y="4" width="2" height="4" fill="currentColor" />
    </>
  ),

  // Tier 3: Operational - Gear/Cog icon
  'tier-operational': (
    <>
      {/* Outer gear */}
      <rect x="10" y="2" width="4" height="2" fill="currentColor" />
      <rect x="10" y="20" width="4" height="2" fill="currentColor" />
      <rect x="2" y="10" width="2" height="4" fill="currentColor" />
      <rect x="20" y="10" width="2" height="4" fill="currentColor" />
      <rect x="4" y="4" width="2" height="2" fill="currentColor" />
      <rect x="18" y="4" width="2" height="2" fill="currentColor" />
      <rect x="4" y="18" width="2" height="2" fill="currentColor" />
      <rect x="18" y="18" width="2" height="2" fill="currentColor" />
      {/* Inner circle */}
      <rect x="8" y="8" width="8" height="8" fill="currentColor" />
    </>
  ),

  // Tier 4: Advanced - Brain/AI icon
  'tier-advanced': (
    <>
      {/* Brain shape */}
      <rect x="6" y="4" width="12" height="2" fill="currentColor" />
      <rect x="4" y="6" width="4" height="2" fill="currentColor" />
      <rect x="16" y="6" width="4" height="2" fill="currentColor" />
      <rect x="4" y="8" width="2" height="8" fill="currentColor" />
      <rect x="18" y="8" width="2" height="8" fill="currentColor" />
      <rect x="6" y="16" width="12" height="2" fill="currentColor" />
      {/* Neural connections */}
      <rect x="8" y="8" width="2" height="2" fill="currentColor" />
      <rect x="14" y="8" width="2" height="2" fill="currentColor" />
      <rect x="10" y="10" width="4" height="2" fill="currentColor" />
      <rect x="8" y="12" width="2" height="2" fill="currentColor" />
      <rect x="14" y="12" width="2" height="2" fill="currentColor" />
      {/* Stem */}
      <rect x="10" y="18" width="4" height="2" fill="currentColor" />
      <rect x="11" y="20" width="2" height="2" fill="currentColor" />
    </>
  ),

  // Router Agent
  'agent-router': (
    <>
      {/* Central node */}
      <rect x="10" y="10" width="4" height="4" fill="currentColor" />
      {/* Connections */}
      <rect x="4" y="4" width="4" height="4" fill="currentColor" />
      <rect x="16" y="4" width="4" height="4" fill="currentColor" />
      <rect x="4" y="16" width="4" height="4" fill="currentColor" />
      <rect x="16" y="16" width="4" height="4" fill="currentColor" />
      {/* Lines */}
      <rect x="8" y="6" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="14" y="6" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="8" y="16" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="14" y="16" width="2" height="2" fill="currentColor" opacity="0.6" />
    </>
  ),

  // Knowledge Base Agent
  'agent-knowledge': (
    <>
      {/* Book shape */}
      <rect x="4" y="4" width="16" height="2" fill="currentColor" />
      <rect x="4" y="4" width="2" height="16" fill="currentColor" />
      <rect x="18" y="4" width="2" height="16" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      {/* Pages */}
      <rect x="11" y="4" width="2" height="16" fill="currentColor" />
      {/* Lines */}
      <rect x="6" y="8" width="4" height="2" fill="currentColor" />
      <rect x="6" y="12" width="4" height="2" fill="currentColor" />
      <rect x="14" y="8" width="4" height="2" fill="currentColor" />
      <rect x="14" y="12" width="4" height="2" fill="currentColor" />
    </>
  ),

  // Support Agent
  'agent-support': (
    <>
      {/* Headset */}
      <rect x="6" y="4" width="12" height="2" fill="currentColor" />
      <rect x="4" y="6" width="2" height="8" fill="currentColor" />
      <rect x="18" y="6" width="2" height="8" fill="currentColor" />
      {/* Ear cups */}
      <rect x="2" y="8" width="4" height="6" fill="currentColor" />
      <rect x="18" y="8" width="4" height="6" fill="currentColor" />
      {/* Mic */}
      <rect x="16" y="14" width="2" height="4" fill="currentColor" />
      <rect x="12" y="18" width="6" height="2" fill="currentColor" />
      <rect x="12" y="16" width="2" height="2" fill="currentColor" />
    </>
  ),

  // Sales Agent
  'agent-sales': (
    <>
      {/* Handshake representation */}
      <rect x="2" y="10" width="8" height="4" fill="currentColor" />
      <rect x="14" y="10" width="8" height="4" fill="currentColor" />
      <rect x="10" y="8" width="4" height="8" fill="currentColor" />
      {/* Arrow up (growth) */}
      <rect x="11" y="2" width="2" height="4" fill="currentColor" />
      <rect x="9" y="4" width="2" height="2" fill="currentColor" />
      <rect x="13" y="4" width="2" height="2" fill="currentColor" />
    </>
  ),

  // Analytics Agent
  'agent-analytics': (
    <>
      {/* Chart bars */}
      <rect x="4" y="14" width="4" height="6" fill="currentColor" />
      <rect x="10" y="10" width="4" height="10" fill="currentColor" />
      <rect x="16" y="6" width="4" height="14" fill="currentColor" />
      {/* Trend line */}
      <rect x="4" y="4" width="2" height="2" fill="currentColor" />
      <rect x="8" y="6" width="2" height="2" fill="currentColor" />
      <rect x="12" y="4" width="2" height="2" fill="currentColor" />
      <rect x="16" y="2" width="2" height="2" fill="currentColor" />
    </>
  ),

  // Security Agent
  'agent-security': (
    <>
      {/* Shield */}
      <rect x="6" y="2" width="12" height="2" fill="currentColor" />
      <rect x="4" y="4" width="2" height="10" fill="currentColor" />
      <rect x="18" y="4" width="2" height="10" fill="currentColor" />
      <rect x="6" y="14" width="2" height="4" fill="currentColor" />
      <rect x="16" y="14" width="2" height="4" fill="currentColor" />
      <rect x="8" y="18" width="2" height="2" fill="currentColor" />
      <rect x="14" y="18" width="2" height="2" fill="currentColor" />
      <rect x="10" y="20" width="4" height="2" fill="currentColor" />
      {/* Check */}
      <rect x="8" y="10" width="2" height="2" fill="currentColor" />
      <rect x="10" y="12" width="2" height="2" fill="currentColor" />
      <rect x="12" y="10" width="2" height="2" fill="currentColor" />
      <rect x="14" y="8" width="2" height="2" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // STATUS ICONS
  // ===========================================================================

  success: (
    <>
      {/* Circle */}
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      <rect x="4" y="4" width="4" height="2" fill="currentColor" />
      <rect x="16" y="4" width="4" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="4" fill="currentColor" />
      <rect x="20" y="6" width="2" height="4" fill="currentColor" />
      <rect x="2" y="14" width="2" height="4" fill="currentColor" />
      <rect x="20" y="14" width="2" height="4" fill="currentColor" />
      <rect x="4" y="18" width="4" height="2" fill="currentColor" />
      <rect x="16" y="18" width="4" height="2" fill="currentColor" />
      <rect x="8" y="20" width="8" height="2" fill="currentColor" />
      {/* Check */}
      <rect x="6" y="11" width="2" height="2" fill="currentColor" />
      <rect x="8" y="13" width="2" height="2" fill="currentColor" />
      <rect x="10" y="15" width="2" height="2" fill="currentColor" />
      <rect x="12" y="13" width="2" height="2" fill="currentColor" />
      <rect x="14" y="11" width="2" height="2" fill="currentColor" />
      <rect x="16" y="9" width="2" height="2" fill="currentColor" />
    </>
  ),

  error: (
    <>
      {/* Circle */}
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      <rect x="4" y="4" width="4" height="2" fill="currentColor" />
      <rect x="16" y="4" width="4" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="4" fill="currentColor" />
      <rect x="20" y="6" width="2" height="4" fill="currentColor" />
      <rect x="2" y="14" width="2" height="4" fill="currentColor" />
      <rect x="20" y="14" width="2" height="4" fill="currentColor" />
      <rect x="4" y="18" width="4" height="2" fill="currentColor" />
      <rect x="16" y="18" width="4" height="2" fill="currentColor" />
      <rect x="8" y="20" width="8" height="2" fill="currentColor" />
      {/* X */}
      <rect x="8" y="8" width="2" height="2" fill="currentColor" />
      <rect x="10" y="10" width="2" height="2" fill="currentColor" />
      <rect x="12" y="12" width="2" height="2" fill="currentColor" />
      <rect x="14" y="14" width="2" height="2" fill="currentColor" />
      <rect x="14" y="8" width="2" height="2" fill="currentColor" />
      <rect x="12" y="10" width="2" height="2" fill="currentColor" />
      <rect x="10" y="12" width="2" height="2" fill="currentColor" />
      <rect x="8" y="14" width="2" height="2" fill="currentColor" />
    </>
  ),

  warning: (
    <>
      {/* Triangle */}
      <rect x="11" y="4" width="2" height="2" fill="currentColor" />
      <rect x="10" y="6" width="4" height="2" fill="currentColor" />
      <rect x="9" y="8" width="6" height="2" fill="currentColor" />
      <rect x="8" y="10" width="8" height="2" fill="currentColor" />
      <rect x="7" y="12" width="10" height="2" fill="currentColor" />
      <rect x="6" y="14" width="12" height="2" fill="currentColor" />
      <rect x="5" y="16" width="14" height="2" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
    </>
  ),

  info: (
    <>
      {/* Circle */}
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      <rect x="4" y="4" width="4" height="2" fill="currentColor" />
      <rect x="16" y="4" width="4" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="4" fill="currentColor" />
      <rect x="20" y="6" width="2" height="4" fill="currentColor" />
      <rect x="2" y="14" width="2" height="4" fill="currentColor" />
      <rect x="20" y="14" width="2" height="4" fill="currentColor" />
      <rect x="4" y="18" width="4" height="2" fill="currentColor" />
      <rect x="16" y="18" width="4" height="2" fill="currentColor" />
      <rect x="8" y="20" width="8" height="2" fill="currentColor" />
      {/* i */}
      <rect x="11" y="6" width="2" height="2" fill="currentColor" />
      <rect x="11" y="10" width="2" height="6" fill="currentColor" />
      <rect x="9" y="10" width="2" height="2" fill="currentColor" />
    </>
  ),

  loading: (
    <>
      {/* Spinner segments */}
      <rect x="11" y="2" width="2" height="4" fill="currentColor" />
      <rect x="16" y="4" width="2" height="2" fill="currentColor" opacity="0.8" />
      <rect x="18" y="8" width="4" height="2" fill="currentColor" opacity="0.6" />
      <rect x="18" y="14" width="2" height="2" fill="currentColor" opacity="0.4" />
      <rect x="11" y="18" width="2" height="4" fill="currentColor" opacity="0.3" />
      <rect x="4" y="14" width="2" height="2" fill="currentColor" opacity="0.4" />
      <rect x="2" y="8" width="4" height="2" fill="currentColor" opacity="0.6" />
      <rect x="4" y="4" width="2" height="2" fill="currentColor" opacity="0.8" />
    </>
  ),

  // ===========================================================================
  // DASHBOARD ICONS
  // ===========================================================================

  chart: (
    <>
      {/* Axes */}
      <rect x="4" y="4" width="2" height="16" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      {/* Line */}
      <rect x="6" y="14" width="2" height="2" fill="currentColor" />
      <rect x="8" y="12" width="2" height="2" fill="currentColor" />
      <rect x="10" y="10" width="2" height="2" fill="currentColor" />
      <rect x="12" y="8" width="2" height="2" fill="currentColor" />
      <rect x="14" y="10" width="2" height="2" fill="currentColor" />
      <rect x="16" y="6" width="2" height="2" fill="currentColor" />
      <rect x="18" y="4" width="2" height="2" fill="currentColor" />
    </>
  ),

  'bar-chart': (
    <>
      {/* Bars */}
      <rect x="4" y="12" width="4" height="8" fill="currentColor" />
      <rect x="10" y="8" width="4" height="12" fill="currentColor" />
      <rect x="16" y="4" width="4" height="16" fill="currentColor" />
    </>
  ),

  'pie-chart': (
    <>
      {/* Circle segments */}
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      <rect x="4" y="4" width="4" height="2" fill="currentColor" />
      <rect x="16" y="4" width="4" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="6" fill="currentColor" />
      <rect x="20" y="6" width="2" height="6" fill="currentColor" />
      <rect x="2" y="12" width="2" height="6" fill="currentColor" />
      <rect x="20" y="12" width="2" height="6" fill="currentColor" />
      <rect x="4" y="18" width="4" height="2" fill="currentColor" />
      <rect x="16" y="18" width="4" height="2" fill="currentColor" />
      <rect x="8" y="20" width="8" height="2" fill="currentColor" />
      {/* Slice line */}
      <rect x="12" y="4" width="2" height="8" fill="currentColor" />
      <rect x="12" y="12" width="8" height="2" fill="currentColor" />
    </>
  ),

  calendar: (
    <>
      {/* Top hooks */}
      <rect x="6" y="2" width="2" height="4" fill="currentColor" />
      <rect x="16" y="2" width="2" height="4" fill="currentColor" />
      {/* Frame */}
      <rect x="4" y="4" width="16" height="2" fill="currentColor" />
      <rect x="4" y="4" width="2" height="16" fill="currentColor" />
      <rect x="18" y="4" width="2" height="16" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      {/* Header line */}
      <rect x="4" y="8" width="16" height="2" fill="currentColor" />
      {/* Date dots */}
      <rect x="7" y="12" width="2" height="2" fill="currentColor" />
      <rect x="11" y="12" width="2" height="2" fill="currentColor" />
      <rect x="15" y="12" width="2" height="2" fill="currentColor" />
      <rect x="7" y="15" width="2" height="2" fill="currentColor" />
      <rect x="11" y="15" width="2" height="2" fill="currentColor" />
    </>
  ),

  clock: (
    <>
      {/* Circle */}
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      <rect x="4" y="4" width="4" height="2" fill="currentColor" />
      <rect x="16" y="4" width="4" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="4" fill="currentColor" />
      <rect x="20" y="6" width="2" height="4" fill="currentColor" />
      <rect x="2" y="14" width="2" height="4" fill="currentColor" />
      <rect x="20" y="14" width="2" height="4" fill="currentColor" />
      <rect x="4" y="18" width="4" height="2" fill="currentColor" />
      <rect x="16" y="18" width="4" height="2" fill="currentColor" />
      <rect x="8" y="20" width="8" height="2" fill="currentColor" />
      {/* Hands */}
      <rect x="11" y="6" width="2" height="6" fill="currentColor" />
      <rect x="13" y="10" width="4" height="2" fill="currentColor" />
    </>
  ),

  bell: (
    <>
      {/* Bell top */}
      <rect x="10" y="2" width="4" height="2" fill="currentColor" />
      {/* Bell body */}
      <rect x="8" y="4" width="8" height="2" fill="currentColor" />
      <rect x="6" y="6" width="2" height="8" fill="currentColor" />
      <rect x="16" y="6" width="2" height="8" fill="currentColor" />
      <rect x="4" y="14" width="16" height="2" fill="currentColor" />
      {/* Clapper */}
      <rect x="10" y="18" width="4" height="2" fill="currentColor" />
    </>
  ),

  home: (
    <>
      {/* Roof */}
      <rect x="11" y="2" width="2" height="2" fill="currentColor" />
      <rect x="9" y="4" width="2" height="2" fill="currentColor" />
      <rect x="13" y="4" width="2" height="2" fill="currentColor" />
      <rect x="7" y="6" width="2" height="2" fill="currentColor" />
      <rect x="15" y="6" width="2" height="2" fill="currentColor" />
      <rect x="5" y="8" width="2" height="2" fill="currentColor" />
      <rect x="17" y="8" width="2" height="2" fill="currentColor" />
      <rect x="3" y="10" width="2" height="2" fill="currentColor" />
      <rect x="19" y="10" width="2" height="2" fill="currentColor" />
      {/* House body */}
      <rect x="5" y="10" width="2" height="10" fill="currentColor" />
      <rect x="17" y="10" width="2" height="10" fill="currentColor" />
      <rect x="5" y="18" width="14" height="2" fill="currentColor" />
      {/* Door */}
      <rect x="10" y="14" width="4" height="6" fill="currentColor" />
    </>
  ),

  folder: (
    <>
      <rect x="2" y="6" width="8" height="2" fill="currentColor" />
      <rect x="10" y="4" width="4" height="2" fill="currentColor" />
      <rect x="10" y="6" width="12" height="2" fill="currentColor" />
      <rect x="2" y="8" width="2" height="12" fill="currentColor" />
      <rect x="20" y="8" width="2" height="12" fill="currentColor" />
      <rect x="2" y="18" width="20" height="2" fill="currentColor" />
    </>
  ),

  database: (
    <>
      {/* Top ellipse */}
      <rect x="6" y="2" width="12" height="2" fill="currentColor" />
      <rect x="4" y="4" width="2" height="2" fill="currentColor" />
      <rect x="18" y="4" width="2" height="2" fill="currentColor" />
      <rect x="6" y="6" width="12" height="2" fill="currentColor" />
      {/* Body */}
      <rect x="4" y="6" width="2" height="12" fill="currentColor" />
      <rect x="18" y="6" width="2" height="12" fill="currentColor" />
      {/* Middle line */}
      <rect x="6" y="11" width="12" height="2" fill="currentColor" />
      {/* Bottom ellipse */}
      <rect x="6" y="18" width="12" height="2" fill="currentColor" />
      <rect x="4" y="16" width="2" height="2" fill="currentColor" />
      <rect x="18" y="16" width="2" height="2" fill="currentColor" />
    </>
  ),

  server: (
    <>
      {/* Top section */}
      <rect x="4" y="2" width="16" height="2" fill="currentColor" />
      <rect x="4" y="2" width="2" height="8" fill="currentColor" />
      <rect x="18" y="2" width="2" height="8" fill="currentColor" />
      <rect x="4" y="8" width="16" height="2" fill="currentColor" />
      {/* Dots */}
      <rect x="7" y="5" width="2" height="2" fill="currentColor" />
      <rect x="11" y="5" width="2" height="2" fill="currentColor" />
      {/* Bottom section */}
      <rect x="4" y="12" width="16" height="2" fill="currentColor" />
      <rect x="4" y="12" width="2" height="8" fill="currentColor" />
      <rect x="18" y="12" width="2" height="8" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      {/* Dots */}
      <rect x="7" y="15" width="2" height="2" fill="currentColor" />
      <rect x="11" y="15" width="2" height="2" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // SOCIAL ICONS
  // ===========================================================================

  github: (
    <>
      {/* Octocat simplified */}
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      <rect x="6" y="4" width="2" height="2" fill="currentColor" />
      <rect x="16" y="4" width="2" height="2" fill="currentColor" />
      <rect x="4" y="6" width="2" height="10" fill="currentColor" />
      <rect x="18" y="6" width="2" height="10" fill="currentColor" />
      <rect x="6" y="16" width="4" height="2" fill="currentColor" />
      <rect x="14" y="16" width="4" height="2" fill="currentColor" />
      <rect x="6" y="18" width="2" height="2" fill="currentColor" />
      <rect x="8" y="20" width="4" height="2" fill="currentColor" />
      <rect x="16" y="18" width="2" height="2" fill="currentColor" />
      {/* Eyes */}
      <rect x="8" y="8" width="2" height="2" fill="currentColor" />
      <rect x="14" y="8" width="2" height="2" fill="currentColor" />
    </>
  ),

  twitter: (
    <>
      {/* X shape */}
      <rect x="4" y="4" width="2" height="2" fill="currentColor" />
      <rect x="6" y="6" width="2" height="2" fill="currentColor" />
      <rect x="8" y="8" width="2" height="2" fill="currentColor" />
      <rect x="10" y="10" width="2" height="2" fill="currentColor" />
      <rect x="12" y="12" width="2" height="2" fill="currentColor" />
      <rect x="14" y="14" width="2" height="2" fill="currentColor" />
      <rect x="16" y="16" width="2" height="2" fill="currentColor" />
      <rect x="18" y="18" width="2" height="2" fill="currentColor" />
      <rect x="18" y="4" width="2" height="2" fill="currentColor" />
      <rect x="16" y="6" width="2" height="2" fill="currentColor" />
      <rect x="14" y="8" width="2" height="2" fill="currentColor" />
      <rect x="8" y="14" width="2" height="2" fill="currentColor" />
      <rect x="6" y="16" width="2" height="2" fill="currentColor" />
      <rect x="4" y="18" width="2" height="2" fill="currentColor" />
    </>
  ),

  linkedin: (
    <>
      {/* Frame */}
      <rect x="4" y="4" width="16" height="2" fill="currentColor" />
      <rect x="4" y="4" width="2" height="16" fill="currentColor" />
      <rect x="18" y="4" width="2" height="16" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      {/* in text */}
      <rect x="7" y="8" width="2" height="2" fill="currentColor" />
      <rect x="7" y="11" width="2" height="5" fill="currentColor" />
      <rect x="11" y="11" width="2" height="5" fill="currentColor" />
      <rect x="13" y="11" width="2" height="2" fill="currentColor" />
      <rect x="15" y="11" width="2" height="5" fill="currentColor" />
    </>
  ),

  discord: (
    <>
      {/* Controller/gamepad shape */}
      <rect x="4" y="8" width="16" height="2" fill="currentColor" />
      <rect x="2" y="10" width="2" height="6" fill="currentColor" />
      <rect x="20" y="10" width="2" height="6" fill="currentColor" />
      <rect x="4" y="16" width="6" height="2" fill="currentColor" />
      <rect x="14" y="16" width="6" height="2" fill="currentColor" />
      {/* Eyes */}
      <rect x="7" y="11" width="3" height="3" fill="currentColor" />
      <rect x="14" y="11" width="3" height="3" fill="currentColor" />
    </>
  ),

  email: (
    <>
      {/* Envelope */}
      <rect x="2" y="6" width="20" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="12" fill="currentColor" />
      <rect x="20" y="6" width="2" height="12" fill="currentColor" />
      <rect x="2" y="16" width="20" height="2" fill="currentColor" />
      {/* V shape */}
      <rect x="4" y="8" width="2" height="2" fill="currentColor" />
      <rect x="6" y="10" width="2" height="2" fill="currentColor" />
      <rect x="8" y="12" width="2" height="2" fill="currentColor" />
      <rect x="10" y="14" width="4" height="2" fill="currentColor" />
      <rect x="14" y="12" width="2" height="2" fill="currentColor" />
      <rect x="16" y="10" width="2" height="2" fill="currentColor" />
      <rect x="18" y="8" width="2" height="2" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // WORKFLOW ICONS
  // ===========================================================================

  workflow: (
    <>
      {/* Nodes */}
      <rect x="2" y="10" width="4" height="4" fill="currentColor" />
      <rect x="10" y="4" width="4" height="4" fill="currentColor" />
      <rect x="10" y="16" width="4" height="4" fill="currentColor" />
      <rect x="18" y="10" width="4" height="4" fill="currentColor" />
      {/* Connections */}
      <rect x="6" y="11" width="4" height="2" fill="currentColor" opacity="0.6" />
      <rect x="14" y="11" width="4" height="2" fill="currentColor" opacity="0.6" />
      <rect x="11" y="8" width="2" height="4" fill="currentColor" opacity="0.6" />
      <rect x="11" y="12" width="2" height="4" fill="currentColor" opacity="0.6" />
    </>
  ),

  sequential: (
    <>
      <rect x="2" y="10" width="4" height="4" fill="currentColor" />
      <rect x="8" y="11" width="2" height="2" fill="currentColor" />
      <rect x="10" y="10" width="4" height="4" fill="currentColor" />
      <rect x="16" y="11" width="2" height="2" fill="currentColor" />
      <rect x="18" y="10" width="4" height="4" fill="currentColor" />
    </>
  ),

  parallel: (
    <>
      <rect x="2" y="10" width="4" height="4" fill="currentColor" />
      {/* Three parallel branches */}
      <rect x="8" y="4" width="8" height="4" fill="currentColor" />
      <rect x="8" y="10" width="8" height="4" fill="currentColor" />
      <rect x="8" y="16" width="8" height="4" fill="currentColor" />
      <rect x="18" y="10" width="4" height="4" fill="currentColor" />
      {/* Connectors */}
      <rect x="6" y="6" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="6" y="11" width="2" height="2" fill="currentColor" opacity="0.6" />
      <rect x="6" y="17" width="2" height="2" fill="currentColor" opacity="0.6" />
    </>
  ),

  debate: (
    <>
      {/* Two nodes facing each other */}
      <rect x="4" y="8" width="6" height="8" fill="currentColor" />
      <rect x="14" y="8" width="6" height="8" fill="currentColor" />
      {/* Arrows between */}
      <rect x="10" y="10" width="4" height="2" fill="currentColor" />
      <rect x="10" y="12" width="4" height="2" fill="currentColor" />
    </>
  ),

  escalate: (
    <>
      {/* Up arrow */}
      <rect x="11" y="4" width="2" height="12" fill="currentColor" />
      <rect x="7" y="8" width="2" height="2" fill="currentColor" />
      <rect x="9" y="6" width="2" height="2" fill="currentColor" />
      <rect x="13" y="6" width="2" height="2" fill="currentColor" />
      <rect x="15" y="8" width="2" height="2" fill="currentColor" />
      {/* Base */}
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // ADDITIONAL UTILITY ICONS
  // ===========================================================================

  zap: (
    <>
      <rect x="12" y="2" width="4" height="2" fill="currentColor" />
      <rect x="10" y="4" width="4" height="2" fill="currentColor" />
      <rect x="8" y="6" width="4" height="2" fill="currentColor" />
      <rect x="6" y="8" width="10" height="2" fill="currentColor" />
      <rect x="10" y="10" width="4" height="2" fill="currentColor" />
      <rect x="12" y="12" width="4" height="2" fill="currentColor" />
      <rect x="10" y="14" width="4" height="2" fill="currentColor" />
      <rect x="8" y="16" width="4" height="2" fill="currentColor" />
      <rect x="6" y="18" width="4" height="2" fill="currentColor" />
    </>
  ),

  star: (
    <>
      <rect x="11" y="2" width="2" height="4" fill="currentColor" />
      <rect x="9" y="6" width="6" height="2" fill="currentColor" />
      <rect x="4" y="8" width="16" height="2" fill="currentColor" />
      <rect x="6" y="10" width="4" height="2" fill="currentColor" />
      <rect x="14" y="10" width="4" height="2" fill="currentColor" />
      <rect x="8" y="12" width="2" height="4" fill="currentColor" />
      <rect x="14" y="12" width="2" height="4" fill="currentColor" />
      <rect x="6" y="16" width="2" height="2" fill="currentColor" />
      <rect x="16" y="16" width="2" height="2" fill="currentColor" />
      <rect x="4" y="18" width="2" height="2" fill="currentColor" />
      <rect x="18" y="18" width="2" height="2" fill="currentColor" />
    </>
  ),

  cpu: (
    <>
      {/* Main chip */}
      <rect x="6" y="6" width="12" height="12" fill="currentColor" />
      {/* Pins */}
      <rect x="8" y="2" width="2" height="4" fill="currentColor" />
      <rect x="14" y="2" width="2" height="4" fill="currentColor" />
      <rect x="8" y="18" width="2" height="4" fill="currentColor" />
      <rect x="14" y="18" width="2" height="4" fill="currentColor" />
      <rect x="2" y="8" width="4" height="2" fill="currentColor" />
      <rect x="2" y="14" width="4" height="2" fill="currentColor" />
      <rect x="18" y="8" width="4" height="2" fill="currentColor" />
      <rect x="18" y="14" width="4" height="2" fill="currentColor" />
    </>
  ),

  globe: (
    <>
      {/* Circle */}
      <rect x="8" y="2" width="8" height="2" fill="currentColor" />
      <rect x="4" y="4" width="4" height="2" fill="currentColor" />
      <rect x="16" y="4" width="4" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="4" fill="currentColor" />
      <rect x="20" y="6" width="2" height="4" fill="currentColor" />
      <rect x="2" y="14" width="2" height="4" fill="currentColor" />
      <rect x="20" y="14" width="2" height="4" fill="currentColor" />
      <rect x="4" y="18" width="4" height="2" fill="currentColor" />
      <rect x="16" y="18" width="4" height="2" fill="currentColor" />
      <rect x="8" y="20" width="8" height="2" fill="currentColor" />
      {/* Lines */}
      <rect x="2" y="11" width="20" height="2" fill="currentColor" />
      <rect x="11" y="2" width="2" height="20" fill="currentColor" />
    </>
  ),

  // ===========================================================================
  // ADDITIONAL ICONS (Added for completeness)
  // ===========================================================================

  // Tier Professional - Star/Premium icon
  'tier-professional': (
    <>
      {/* Star shape */}
      <rect x="11" y="2" width="2" height="4" fill="currentColor" />
      <rect x="9" y="6" width="6" height="2" fill="currentColor" />
      <rect x="4" y="8" width="16" height="2" fill="currentColor" />
      <rect x="6" y="10" width="4" height="2" fill="currentColor" />
      <rect x="14" y="10" width="4" height="2" fill="currentColor" />
      <rect x="8" y="12" width="2" height="4" fill="currentColor" />
      <rect x="14" y="12" width="2" height="4" fill="currentColor" />
      <rect x="6" y="16" width="2" height="2" fill="currentColor" />
      <rect x="16" y="16" width="2" height="2" fill="currentColor" />
      <rect x="4" y="18" width="2" height="2" fill="currentColor" />
      <rect x="18" y="18" width="2" height="2" fill="currentColor" />
    </>
  ),

  // Tier Enterprise - Building/Enterprise icon
  'tier-enterprise': (
    <>
      {/* Main building */}
      <rect x="6" y="4" width="12" height="2" fill="currentColor" />
      <rect x="6" y="4" width="2" height="16" fill="currentColor" />
      <rect x="16" y="4" width="2" height="16" fill="currentColor" />
      <rect x="6" y="18" width="12" height="2" fill="currentColor" />
      {/* Windows */}
      <rect x="9" y="7" width="2" height="2" fill="currentColor" />
      <rect x="13" y="7" width="2" height="2" fill="currentColor" />
      <rect x="9" y="11" width="2" height="2" fill="currentColor" />
      <rect x="13" y="11" width="2" height="2" fill="currentColor" />
      {/* Door */}
      <rect x="10" y="15" width="4" height="5" fill="currentColor" />
    </>
  ),

  // Connect - Connection/plug icon
  connect: (
    <>
      {/* Left plug */}
      <rect x="4" y="10" width="6" height="4" fill="currentColor" />
      <rect x="2" y="8" width="2" height="2" fill="currentColor" />
      <rect x="2" y="14" width="2" height="2" fill="currentColor" />
      {/* Right plug */}
      <rect x="14" y="10" width="6" height="4" fill="currentColor" />
      <rect x="20" y="8" width="2" height="2" fill="currentColor" />
      <rect x="20" y="14" width="2" height="2" fill="currentColor" />
      {/* Connection */}
      <rect x="10" y="11" width="4" height="2" fill="currentColor" />
    </>
  ),

  // Book icon
  book: (
    <>
      {/* Book cover */}
      <rect x="4" y="4" width="16" height="2" fill="currentColor" />
      <rect x="4" y="4" width="2" height="16" fill="currentColor" />
      <rect x="18" y="4" width="2" height="16" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      {/* Spine */}
      <rect x="8" y="4" width="2" height="16" fill="currentColor" />
      {/* Pages */}
      <rect x="11" y="8" width="6" height="2" fill="currentColor" />
      <rect x="11" y="12" width="4" height="2" fill="currentColor" />
    </>
  ),

  // Mail icon (alias for email)
  mail: (
    <>
      {/* Envelope */}
      <rect x="2" y="6" width="20" height="2" fill="currentColor" />
      <rect x="2" y="6" width="2" height="12" fill="currentColor" />
      <rect x="20" y="6" width="2" height="12" fill="currentColor" />
      <rect x="2" y="16" width="20" height="2" fill="currentColor" />
      {/* V shape */}
      <rect x="4" y="8" width="2" height="2" fill="currentColor" />
      <rect x="6" y="10" width="2" height="2" fill="currentColor" />
      <rect x="8" y="12" width="2" height="2" fill="currentColor" />
      <rect x="10" y="14" width="4" height="2" fill="currentColor" />
      <rect x="14" y="12" width="2" height="2" fill="currentColor" />
      <rect x="16" y="10" width="2" height="2" fill="currentColor" />
      <rect x="18" y="8" width="2" height="2" fill="currentColor" />
    </>
  ),

  // Building icon
  building: (
    <>
      {/* Main structure */}
      <rect x="4" y="4" width="16" height="2" fill="currentColor" />
      <rect x="4" y="4" width="2" height="16" fill="currentColor" />
      <rect x="18" y="4" width="2" height="16" fill="currentColor" />
      <rect x="4" y="18" width="16" height="2" fill="currentColor" />
      {/* Windows */}
      <rect x="7" y="7" width="2" height="2" fill="currentColor" />
      <rect x="11" y="7" width="2" height="2" fill="currentColor" />
      <rect x="15" y="7" width="2" height="2" fill="currentColor" />
      <rect x="7" y="11" width="2" height="2" fill="currentColor" />
      <rect x="11" y="11" width="2" height="2" fill="currentColor" />
      <rect x="15" y="11" width="2" height="2" fill="currentColor" />
      {/* Door */}
      <rect x="10" y="15" width="4" height="5" fill="currentColor" />
    </>
  ),

  // Eye icon
  eye: (
    <>
      {/* Eye outline */}
      <rect x="6" y="8" width="12" height="2" fill="currentColor" />
      <rect x="4" y="10" width="2" height="4" fill="currentColor" />
      <rect x="18" y="10" width="2" height="4" fill="currentColor" />
      <rect x="6" y="14" width="12" height="2" fill="currentColor" />
      {/* Pupil */}
      <rect x="10" y="10" width="4" height="4" fill="currentColor" />
    </>
  ),

  // Eye-off icon
  'eye-off': (
    <>
      {/* Eye outline */}
      <rect x="6" y="8" width="12" height="2" fill="currentColor" />
      <rect x="4" y="10" width="2" height="4" fill="currentColor" />
      <rect x="18" y="10" width="2" height="4" fill="currentColor" />
      <rect x="6" y="14" width="12" height="2" fill="currentColor" />
      {/* Slash */}
      <rect x="4" y="4" width="2" height="2" fill="currentColor" />
      <rect x="6" y="6" width="2" height="2" fill="currentColor" />
      <rect x="8" y="8" width="2" height="2" fill="currentColor" />
      <rect x="10" y="10" width="2" height="2" fill="currentColor" />
      <rect x="12" y="12" width="2" height="2" fill="currentColor" />
      <rect x="14" y="14" width="2" height="2" fill="currentColor" />
      <rect x="16" y="16" width="2" height="2" fill="currentColor" />
      <rect x="18" y="18" width="2" height="2" fill="currentColor" />
    </>
  ),
};

// =============================================================================
// EXPORT ALL ICON NAMES (for reference)
// =============================================================================
export const iconNames = Object.keys(icons);

// =============================================================================
// HELPER: Get icons by category
// =============================================================================
export const iconCategories = {
  brand: ['logo', 'logo-mark'],
  navigation: [
    'menu',
    'close',
    'arrow-right',
    'arrow-left',
    'arrow-up',
    'arrow-down',
    'chevron-down',
    'chevron-up',
    'chevron-right',
    'chevron-left',
    'external-link',
  ],
  actions: [
    'search',
    'settings',
    'copy',
    'check',
    'plus',
    'minus',
    'trash',
    'edit',
    'refresh',
    'download',
    'upload',
    'filter',
  ],
  user: ['user', 'users', 'lock', 'unlock', 'logout'],
  chat: ['send', 'message', 'chat', 'attach', 'microphone', 'thumbs-up', 'thumbs-down'],
  tiers: ['tier-essential', 'tier-revenue', 'tier-operational', 'tier-advanced'],
  agents: [
    'agent-router',
    'agent-knowledge',
    'agent-support',
    'agent-sales',
    'agent-analytics',
    'agent-security',
  ],
  status: ['success', 'error', 'warning', 'info', 'loading'],
  dashboard: [
    'chart',
    'bar-chart',
    'pie-chart',
    'calendar',
    'clock',
    'bell',
    'home',
    'folder',
    'database',
    'server',
  ],
  social: ['github', 'twitter', 'linkedin', 'discord', 'email'],
  workflow: ['workflow', 'sequential', 'parallel', 'debate', 'escalate'],
  utility: ['zap', 'star', 'cpu', 'globe'],
};

export default Icon;
