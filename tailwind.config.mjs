/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        'wera-green': '#10b981',
        'bg-dark': '#09090b',
        'card-bg': '#18181b',
        'border-zinc': '#27272a',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Cascadia Mono', 'JetBrains Mono', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};