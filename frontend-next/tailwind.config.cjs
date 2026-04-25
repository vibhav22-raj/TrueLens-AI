/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)", "system-ui"],
        body: ["var(--font-body)", "system-ui"]
      },
      colors: {
        background: "var(--bg)",
        surface: "var(--surface)",
        panel: "var(--panel)",
        accent: "var(--accent)",
        accent2: "var(--accent-2)",
        ink: "var(--ink)"
      },
      boxShadow: {
        glow: "0 0 40px rgba(225, 29, 72, 0.35)",
        soft: "0 20px 50px rgba(2, 1, 8, 0.45)",
        glass: "0 18px 40px rgba(8, 2, 18, 0.6)"
      },
      backgroundImage: {
        mesh: "radial-gradient(circle at 15% 15%, rgba(225,29,72,0.35), transparent 40%), radial-gradient(circle at 85% 20%, rgba(99,102,241,0.25), transparent 45%), radial-gradient(circle at 30% 80%, rgba(190,24,93,0.25), transparent 45%)"
      }
    }
  },
  plugins: []
};
