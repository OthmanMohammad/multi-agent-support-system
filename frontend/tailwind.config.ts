import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    // Completely override fontFamily - Mistral uses ONLY Arial
    fontFamily: {
      sans: ['Arial', 'sans-serif'],
      mono: ['monospace'],
    },
    extend: {
      colors: {
        // Mistral Brand Colors
        brand: {
          red: '#E10500',
          'orange-dark': '#FA500F',
          orange: '#FF8205',
          'orange-light': '#FFAF00',
          yellow: '#FFD800',
        },
        // Light Theme (Primary)
        background: {
          DEFAULT: '#FFFAEB',
          secondary: '#FFF0C3',
          tertiary: '#E9E2CB',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          elevated: '#FFFAEB',
        },
        border: {
          DEFAULT: '#E9E2CB',
          strong: '#D4CDB8',
        },
        text: {
          primary: '#1A1A1A',
          secondary: '#666666',
          tertiary: '#999999',
          inverse: '#FFFFFF',
        },
        // Semantic Colors
        success: {
          DEFAULT: '#22C55E',
          light: '#DCFCE7',
        },
        error: {
          DEFAULT: '#E10500',
          light: '#FEE2E2',
        },
        warning: {
          DEFAULT: '#FFAF00',
          light: '#FEF3C7',
        },
        info: {
          DEFAULT: '#3B82F6',
          light: '#DBEAFE',
        },
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1.16' }],
        '6xl': ['3.75rem', { lineHeight: '1.1' }],
      },
      borderRadius: {
        DEFAULT: '8px',
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        '2xl': '24px',
      },
      boxShadow: {
        sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
      },
      animation: {
        'fade-in': 'fadeIn 150ms ease-out',
        'fade-out': 'fadeOut 150ms ease-in',
        'slide-in-from-top': 'slideInFromTop 200ms ease-out',
        'slide-in-from-bottom': 'slideInFromBottom 200ms ease-out',
        'slide-in-from-left': 'slideInFromLeft 200ms ease-out',
        'slide-in-from-right': 'slideInFromRight 200ms ease-out',
        'scale-in': 'scaleIn 150ms ease-out',
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        spin: 'spin 1s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideInFromTop: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInFromBottom: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInFromLeft: {
          '0%': { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideInFromRight: {
          '0%': { transform: 'translateX(10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        spin: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      transitionDuration: {
        DEFAULT: '150ms',
        fast: '100ms',
        normal: '150ms',
        slow: '200ms',
      },
    },
  },
  plugins: [],
};

export default config;
