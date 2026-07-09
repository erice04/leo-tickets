import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { apiGet } from "../api/client";



type Theme = "light" | "dark";



interface ThemeContextValue {

  theme: Theme;

  toggleTheme: () => void;

  applySiteDefault: (theme: Theme) => void;

}



const ThemeContext = createContext<ThemeContextValue | null>(null);



export function ThemeProvider({ children }: { children: ReactNode }) {

  const [theme, setTheme] = useState<Theme>("light");



  useEffect(() => {

    document.documentElement.setAttribute("data-theme", theme);

  }, [theme]);



  useEffect(() => {

    apiGet<{ default_theme: Theme }>("/api/v1/theme")

      .then(({ default_theme }) => {

        setTheme(default_theme === "dark" ? "dark" : "light");

      })

      .catch(() => {});

  }, []);



  const toggleTheme = () => setTheme((t) => (t === "light" ? "dark" : "light"));



  const applySiteDefault = (next: Theme) => {

    setTheme(next);

  };



  return (

    <ThemeContext.Provider value={{ theme, toggleTheme, applySiteDefault }}>

      {children}

    </ThemeContext.Provider>

  );

}



export function useTheme() {

  const ctx = useContext(ThemeContext);

  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");

  return ctx;

}


