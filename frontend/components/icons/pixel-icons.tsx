// Mistral-style pixelated icons
// These are 8-bit style icons inspired by Mistral AI's model icons

interface PixelIconProps {
  className?: string;
  size?: number;
}

// Agent icon - pixelated robot face
export function PixelAgentIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      {/* Head outline */}
      <rect x="3" y="2" width="10" height="10" fill="currentColor" />
      {/* Eyes */}
      <rect x="5" y="4" width="2" height="2" fill="white" />
      <rect x="9" y="4" width="2" height="2" fill="white" />
      {/* Mouth */}
      <rect x="5" y="8" width="6" height="1" fill="white" />
      {/* Antenna */}
      <rect x="7" y="0" width="2" height="2" fill="currentColor" />
      {/* Body */}
      <rect x="5" y="12" width="6" height="4" fill="currentColor" />
    </svg>
  );
}

// Chat icon - pixelated speech bubble
export function PixelChatIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      <rect x="1" y="2" width="14" height="9" fill="currentColor" />
      <rect x="3" y="11" width="2" height="2" fill="currentColor" />
      <rect x="1" y="13" width="2" height="2" fill="currentColor" />
      {/* Dots */}
      <rect x="4" y="5" width="2" height="2" fill="white" />
      <rect x="7" y="5" width="2" height="2" fill="white" />
      <rect x="10" y="5" width="2" height="2" fill="white" />
    </svg>
  );
}

// Lightning/Speed icon - pixelated bolt
export function PixelLightningIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      <rect x="8" y="0" width="4" height="2" fill="currentColor" />
      <rect x="6" y="2" width="4" height="2" fill="currentColor" />
      <rect x="4" y="4" width="4" height="2" fill="currentColor" />
      <rect x="4" y="6" width="8" height="2" fill="currentColor" />
      <rect x="6" y="8" width="4" height="2" fill="currentColor" />
      <rect x="8" y="10" width="4" height="2" fill="currentColor" />
      <rect x="6" y="12" width="4" height="2" fill="currentColor" />
      <rect x="4" y="14" width="4" height="2" fill="currentColor" />
    </svg>
  );
}

// Shield icon - pixelated security
export function PixelShieldIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      <rect x="2" y="1" width="12" height="2" fill="currentColor" />
      <rect x="1" y="3" width="14" height="6" fill="currentColor" />
      <rect x="2" y="9" width="12" height="2" fill="currentColor" />
      <rect x="3" y="11" width="10" height="2" fill="currentColor" />
      <rect x="5" y="13" width="6" height="2" fill="currentColor" />
      <rect x="7" y="15" width="2" height="1" fill="currentColor" />
      {/* Checkmark */}
      <rect x="5" y="5" width="2" height="2" fill="white" />
      <rect x="7" y="7" width="2" height="2" fill="white" />
      <rect x="9" y="3" width="2" height="4" fill="white" />
    </svg>
  );
}

// Chart icon - pixelated analytics
export function PixelChartIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      {/* Bars */}
      <rect x="2" y="10" width="3" height="5" fill="currentColor" />
      <rect x="6" y="6" width="3" height="9" fill="currentColor" />
      <rect x="10" y="2" width="3" height="13" fill="currentColor" />
      {/* Base line */}
      <rect x="1" y="15" width="14" height="1" fill="currentColor" />
    </svg>
  );
}

// Users icon - pixelated people
export function PixelUsersIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      {/* Person 1 */}
      <rect x="2" y="2" width="4" height="4" fill="currentColor" />
      <rect x="1" y="7" width="6" height="5" fill="currentColor" />
      {/* Person 2 */}
      <rect x="10" y="2" width="4" height="4" fill="currentColor" />
      <rect x="9" y="7" width="6" height="5" fill="currentColor" />
      {/* Shared base */}
      <rect x="3" y="12" width="10" height="3" fill="currentColor" />
    </svg>
  );
}

// Sparkle/AI icon - pixelated star
export function PixelSparkleIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      {/* Center */}
      <rect x="7" y="7" width="2" height="2" fill="currentColor" />
      {/* Vertical */}
      <rect x="7" y="1" width="2" height="5" fill="currentColor" />
      <rect x="7" y="10" width="2" height="5" fill="currentColor" />
      {/* Horizontal */}
      <rect x="1" y="7" width="5" height="2" fill="currentColor" />
      <rect x="10" y="7" width="5" height="2" fill="currentColor" />
      {/* Diagonals */}
      <rect x="3" y="3" width="2" height="2" fill="currentColor" />
      <rect x="11" y="3" width="2" height="2" fill="currentColor" />
      <rect x="3" y="11" width="2" height="2" fill="currentColor" />
      <rect x="11" y="11" width="2" height="2" fill="currentColor" />
    </svg>
  );
}

// Cube/Model icon - pixelated 3D cube
export function PixelCubeIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      {/* Top face */}
      <rect x="4" y="1" width="8" height="1" fill="currentColor" />
      <rect x="3" y="2" width="10" height="1" fill="currentColor" />
      <rect x="2" y="3" width="12" height="3" fill="currentColor" />
      {/* Front face */}
      <rect x="2" y="6" width="7" height="8" fill="currentColor" />
      {/* Right face - slightly lighter feel */}
      <rect x="9" y="6" width="5" height="6" fill="currentColor" opacity="0.7" />
      <rect x="10" y="12" width="4" height="1" fill="currentColor" opacity="0.7" />
      <rect x="11" y="13" width="3" height="1" fill="currentColor" opacity="0.7" />
    </svg>
  );
}

// Rainbow M logo - Mistral style
export function PixelMLogoIcon({ className = '', size = 32 }: PixelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      className={className}
      style={{ imageRendering: 'pixelated' }}
    >
      {/* Left vertical */}
      <rect x="1" y="3" width="3" height="10" fill="#EE4B2B" />
      {/* Left diagonal up */}
      <rect x="4" y="3" width="2" height="2" fill="#FF5F1F" />
      <rect x="5" y="5" width="2" height="2" fill="#FF7000" />
      {/* Center peak */}
      <rect x="6" y="7" width="4" height="2" fill="#FFA500" />
      {/* Right diagonal down */}
      <rect x="9" y="5" width="2" height="2" fill="#FF7000" />
      <rect x="10" y="3" width="2" height="2" fill="#FF5F1F" />
      {/* Right vertical */}
      <rect x="12" y="3" width="3" height="10" fill="#FFD700" />
    </svg>
  );
}
