import * as React from "react";

const ThemeToggle: React.FC = () => {
  // This uses the 'dark' class on <html>. You might want a more robust system (e.g., next-themes)
  const [dark, setDark] = React.useState(false);

  React.useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark");
    setDark(isDark);
  }, []);

  const toggleTheme = () => {
    if (dark) {
      document.documentElement.classList.remove("dark");
      setDark(false);
    } else {
      document.documentElement.classList.add("dark");
      setDark(true);
    }
  };

  return (
    <button
      className="rounded p-2 text-lg text-foreground bg-transparent hover:bg-muted transition shadow"
      onClick={toggleTheme}
      aria-label="Toggle theme"
    >
      {dark ? "🌙" : "☀️"}
    </button>
  );
};

export default ThemeToggle;

