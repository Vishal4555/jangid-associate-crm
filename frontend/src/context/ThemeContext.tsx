import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark";
type ThemeContextValue = { theme: Theme; toggleTheme: () => void };
const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() =>
    localStorage.getItem("ja-theme") === "dark" ? "dark" : "light",
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("ja-theme", theme);
  }, [theme]);

  return <ThemeContext.Provider value={{ theme, toggleTheme: () => setTheme((value) => value === "light" ? "dark" : "light") }}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
}
