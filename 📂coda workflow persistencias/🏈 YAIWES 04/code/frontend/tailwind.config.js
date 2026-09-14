/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0f0f12',
          800: '#161619',
          700: '#1e1e22',
          600: '#27272c',
          500: '#36363d',
          400: '#4a4a53',
        },
        cyber: {
          blue: '#00d4ff',
          purple: '#8b5cf6',
          green: '#10b981',
          orange: '#f59e0b',
          red: '#ef4444',
          pink: '#ec4899',
        },
      },
    },
  },
  plugins: [],
}
