import type { Config } from 'tailwindcss';

// =============================================================================
// TAP Design System - Mistral.ai Inspired
// Dark Mode First | Arial Font | Pixel Art Aesthetic
// =============================================================================

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    // Mistral uses Arial for universal appeal and sustainability
    fontFamily: {
      sans: ['Arial', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      mono: ['SF Mono', 'Monaco', 'Cascadia Mono', 'monospace'],
    },
    extend: {
      colors: {
        // =================================================================
        // Mistral Rainbow - Primary Brand Colors
        // =================================================================
        mistral: {
          red: '#EF4444',
          'orange-dark': '#EA580C',
          orange: '#F97316',
          'orange-light': '#FB923C',
          yellow: '#FACC15',
          // Beige shades (for light mode sections if needed)
          'beige-light': '#FEF3E2',
          'beige-medium': '#E8DFD0',
          'beige-dark': '#D4C4A8',
          // Black shades
          black: '#1E1E1E',
          'black-tinted': '#2D2D2D',
        },

        // =================================================================
        // Dark Mode Colors (Default)
        // =================================================================
        background: {
          DEFAULT: '#000000',
          secondary: '#0A0A0A',
          tertiary: '#111111',
          card: '#1A1A1A',
        },
        surface: {
          DEFAULT: '#1A1A1A',
          elevated: '#1F1F1F',
          hover: '#252525',
        },
        border: {
          DEFAULT: '#2A2A2A',
          strong: '#3A3A3A',
          hover: '#4A4A4A',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#A3A3A3',
          tertiary: '#666666',
          muted: '#525252',
          inverse: '#000000',
        },

        // =================================================================
        // Semantic Colors
        // =================================================================
        success: {
          DEFAULT: '#22C55E',
          light: '#166534',
        },
        error: {
          DEFAULT: '#EF4444',
          light: '#7F1D1D',
        },
        warning: {
          DEFAULT: '#F97316',
          light: '#7C2D12',
        },
        info: {
          DEFAULT: '#3B82F6',
          light: '#1E3A8A',
        },
      },

      // =================================================================
      // Typography Scale (Mistral Style)
      // =================================================================
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.01em' }],
        '5xl': ['3rem', { lineHeight: '1.15', letterSpacing: '-0.02em' }],
        '6xl': ['3.75rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        '7xl': ['4.5rem', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
        '8xl': ['6rem', { lineHeight: '1', letterSpacing: '-0.02em' }],
        '9xl': ['8rem', { lineHeight: '0.95', letterSpacing: '-0.02em' }],
      },

      // =================================================================
      // Border Radius (Mistral Style - Minimal)
      // =================================================================
      borderRadius: {
        none: '0',
        sm: '4px',
        DEFAULT: '8px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        '2xl': '20px',
        '3xl': '24px',
        '4xl': '32px',
        full: '9999px',
      },

      // =================================================================
      // Shadows (Subtle for Dark Mode)
      // =================================================================
      boxShadow: {
        sm: '0 1px 2px 0 rgb(0 0 0 / 0.3)',
        DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.4), 0 1px 2px -1px rgb(0 0 0 / 0.4)',
        md: '0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.4)',
        lg: '0 10px 15px -3px rgb(0 0 0 / 0.4), 0 4px 6px -4px rgb(0 0 0 / 0.4)',
        xl: '0 20px 25px -5px rgb(0 0 0 / 0.5), 0 8px 10px -6px rgb(0 0 0 / 0.5)',
        '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.6)',
        card: '0 25px 50px -12px rgb(0 0 0 / 0.25)',
        inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.3)',
      },

      // =================================================================
      // Spacing (Consistent Scale)
      // =================================================================
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '30': '7.5rem',
        '34': '8.5rem',
        '38': '9.5rem',
        '42': '10.5rem',
        '46': '11.5rem',
        '50': '12.5rem',
        '54': '13.5rem',
        '58': '14.5rem',
        '62': '15.5rem',
        '66': '16.5rem',
        '70': '17.5rem',
        '74': '18.5rem',
        '78': '19.5rem',
        '82': '20.5rem',
        '86': '21.5rem',
        '90': '22.5rem',
        '94': '23.5rem',
        '98': '24.5rem',
        '128': '32rem',
      },

      // =================================================================
      // Animations (Mistral Style - Smooth & Purposeful)
      // =================================================================
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'fade-up': 'fadeUp 0.6s ease-out',
        'fade-down': 'fadeDown 0.6s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.4s ease-out',
        'slide-in-left': 'slideInLeft 0.4s ease-out',
        'slide-in-up': 'slideInUp 0.4s ease-out',
        'slide-in-down': 'slideInDown 0.4s ease-out',
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        spin: 'spin 1s linear infinite',
        'pixel-shimmer': 'pixelShimmer 2s ease-in-out infinite',
        'rainbow-slide': 'rainbowSlide 3s ease-in-out infinite',
        typewriter: 'typewriter 2s steps(40) forwards',
        blink: 'blink 1s step-end infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        spin: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        pixelShimmer: {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
        rainbowSlide: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        typewriter: {
          '0%': { width: '0' },
          '100%': { width: '100%' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },

      // =================================================================
      // Transitions
      // =================================================================
      transitionDuration: {
        DEFAULT: '200ms',
        fast: '100ms',
        normal: '200ms',
        slow: '300ms',
      },
      transitionTimingFunction: {
        DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
        'ease-out-expo': 'cubic-bezier(0.19, 1, 0.22, 1)',
      },

      // =================================================================
      // Z-Index Scale
      // =================================================================
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },

      // =================================================================
      // Container
      // =================================================================
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
    },
  },
  plugins: [],
};

export default config;
