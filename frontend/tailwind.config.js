/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          accent: '#10b981',
          danger: '#f43f5e',
        },
      },
    },
  },
  plugins: [],
}
