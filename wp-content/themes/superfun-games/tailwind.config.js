/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./*.{html,js,php}"],
  darkMode: 'selector',
  theme: {
    extend: {
      colors: {
        green: {
          100: '#ccffe5',
          200: '#99ffcc',
          300: '#66ffb2',
          400: '#33ff99',
          500: '#00FF85', // Primary green
          600: '#00e67a',
          700: '#00cc6e',
          800: '#00b362',
          900: '#009957',
        },
      },
      animation: {
        "spin-slow": 'spin 7s linear infinite',
        marquee: 'marquee 45s linear infinite',
        marquee2: 'marquee2 45s linear infinite',
      },
      keyframes: {
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        marquee2: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0%)' },
        },
      },
    }
  },
  plugins: [],
};
