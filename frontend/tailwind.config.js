/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0B0F14',
          900: '#121821',
          800: '#1A222D',
          700: '#242F3D',
          600: '#39475A',
        },
        paper: {
          100: '#F5F1E8',
          200: '#E8E2D3',
        },
        amber: {
          DEFAULT: '#E8A33D',
          light: '#F2BC6C',
        },
        rose: {
          DEFAULT: '#D65F5F',
          light: '#E58888',
        },
        mint: {
          DEFAULT: '#4FD1C5',
          light: '#7EE0D6',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      backgroundImage: {
        scanlines:
          'repeating-linear-gradient(180deg, rgba(245,241,232,0.04) 0px, rgba(245,241,232,0.04) 1px, transparent 1px, transparent 3px)',
      },
    },
  },
  plugins: [],
}
