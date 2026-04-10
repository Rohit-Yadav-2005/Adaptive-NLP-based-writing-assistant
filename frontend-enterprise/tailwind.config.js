/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0b1020',
        card: '#121a2f',
        accent: '#7c9dff',
        'accent-secondary': '#57e3b0',
        muted: '#9cb0d8',
      },
      backgroundImage: {
        'vibrant-gradient': 'radial-gradient(1000px 420px at 10% -10%, #1a2a57 0%, transparent 60%), radial-gradient(1000px 420px at 90% -20%, #1c3a4f 0%, transparent 60%)',
      }
    },
  },
  plugins: [],
}
