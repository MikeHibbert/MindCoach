/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      screens: {
        'mobile': {'max': '767px'},
        'tablet': {'min': '768px', 'max': '1023px'},
        'desktop': {'min': '1024px'},
        'reduced-motion': {'raw': '(prefers-reduced-motion: reduce)'},
        'high-contrast': {'raw': '(prefers-contrast: high)'},
      },
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        secondary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        // High contrast colors for accessibility
        'high-contrast': {
          'text': '#000000',
          'background': '#ffffff',
          'primary': '#0000ff',
          'secondary': '#666666',
          'success': '#008000',
          'warning': '#ff8c00',
          'error': '#ff0000',
        }
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        // Touch target sizes
        '11': '2.75rem', // 44px
        '14': '3.5rem',  // 56px
      },
      fontSize: {
        // Accessible font sizes
        'xs': ['0.75rem', { lineHeight: '1.5' }],
        'sm': ['0.875rem', { lineHeight: '1.5' }],
        'base': ['1rem', { lineHeight: '1.6' }],
        'lg': ['1.125rem', { lineHeight: '1.6' }],
        'xl': ['1.25rem', { lineHeight: '1.5' }],
        '2xl': ['1.5rem', { lineHeight: '1.4' }],
        '3xl': ['1.875rem', { lineHeight: '1.3' }],
        '4xl': ['2.25rem', { lineHeight: '1.2' }],
      },
      ringWidth: {
        '3': '3px',
      },
      borderWidth: {
        '3': '3px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-in-out',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    // Custom plugin for accessibility utilities
    function({ addUtilities, theme }) {
      const newUtilities = {
        '.focus-visible-only': {
          '&:focus:not(:focus-visible)': {
            outline: 'none',
          },
          '&:focus-visible': {
            outline: `3px solid ${theme('colors.blue.600')}`,
            'outline-offset': '2px',
          },
        },
        '.skip-link': {
          position: 'absolute',
          top: '-40px',
          left: '6px',
          background: '#000',
          color: '#fff',
          padding: '8px',
          'text-decoration': 'none',
          'z-index': '1000',
          'border-radius': '4px',
          '&:focus': {
            top: '6px',
          },
        },
      };
      addUtilities(newUtilities);
    },
  ],
}