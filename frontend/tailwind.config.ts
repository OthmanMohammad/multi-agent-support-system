import type { Config } from 'tailwindcss';

// =============================================================================
// TAP Design System - CORRECT Mistral.ai Style
// Beige/Cream Backgrounds | DM Sans Font | Sharp Corners
// =============================================================================

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    // DM Sans everywhere
    fontFamily: {
      sans: ['"DM Sans"', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      mono: ['SF Mono', 'Monaco', 'Cascadia Mono', 'monospace'],
    },
    extend: {
      colors: {
        // =================================================================
        // CORRECT Mistral Rainbow - From Brand Guide
        // =================================================================
        mistral: {
          red: '#E10500',
          'orange-dark': '#FA500F',
          orange: '#FF8205',        // Primary brand orange
          'orange-light': '#FFAF00',
          yellow: '#FFD800',
        },

        // =================================================================
        // Beige/Cream Backgrounds - Mistral's Actual Theme
        // =================================================================
        beige: {
          light: '#FFFAEB',         // Main page background
          medium: '#FFF0C3',        // Cards, elevated surfaces
          dark: '#E9E2CB',          // Borders, dividers
        },

        // =================================================================
        // From Mistral CSS Variables
        // =================================================================
        'mistral-brown': '#352B22',
        'mistral-cream': '#FBF9E5',
        'mistral-burnt': '#BA5417',
        'mistral-amber': '#EE9926',
        'mistral-tan': '#C9B390',
        'mistral-gray': '#ADB4B4',

        // =================================================================
        // Light Theme Colors (Default - Mistral Style)
        // =================================================================
        background: {
          DEFAULT: '#FFFAEB',       // Beige light
          secondary: '#FFF0C3',     // Beige medium
          tertiary: '#FBF9E5',      // Cream
          card: '#FFFFFF',          // White cards
        },
        surface: {
          DEFAULT: '#FFFFFF',       // White
          elevated: '#FFFAEB',      // Beige light
          hover: '#FFF0C3',         // Beige medium
        },
        border: {
          DEFAULT: '#E9E2CB',       // Beige dark
          strong: '#C9B390',        // Tan
          hover: '#BA5417',         // Burnt orange on hover
        },
        text: {
          primary: '#352B22',       // Dark brown
          secondary: '#5A4A3A',     // Medium brown
          tertiary: '#8A7A6A',      // Light brown
          muted: '#ADB4B4',         // Gray
          inverse: '#FFFFFF',       // White
        },

        // =================================================================
        // Black (for specific dark sections)
        // =================================================================
        black: {
          DEFAULT: '#000000',
          tinted: '#1E1E1E',
        },

        // =================================================================
        // Semantic Colors
        // =================================================================
        success: {
          DEFAULT: '#22C55E',
          light: '#DCFCE7',
        },
        error: {
          DEFAULT: '#E10500',
          light: '#FEE2E2',
        },
        warning: {
          DEFAULT: '#FF8205',
          light: '#FEF3C7',
        },
        info: {
          DEFAULT: '#3B82F6',
          light: '#DBEAFE',
        },
      },

      // =================================================================
      // Typography Scale
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
      // Border Radius - SHARP CORNERS (Mistral Style)
      // =================================================================
      borderRadius: {
        none: '0',
        sm: '0',          // Sharp!
        DEFAULT: '0',     // Sharp!
        md: '0',          // Sharp!
        lg: '0',          // Sharp!
        xl: '0',          // Sharp!
        '2xl': '0',       // Sharp!
        '3xl': '0',       // Sharp!
        '4xl': '0',       // Sharp!
        full: '9999px',   // Only for avatars/badges
      },

      // =================================================================
      // Shadows (Light theme appropriate)
      // =================================================================
      boxShadow: {
        sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
        '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
        card: '0 4px 12px rgb(0 0 0 / 0.08)',
        inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
      },

      // =================================================================
      // Spacing
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
      // Animations
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
