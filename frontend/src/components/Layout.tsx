import { Link } from "react-router-dom";
import { useTheme } from "../theme/ThemeContext";

interface LayoutProps {
  children: React.ReactNode;
  showLogout?: boolean;
  leftLink?: { to: string; label: string };
}

export function Layout({ children, showLogout = false, leftLink }: LayoutProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div>
          {leftLink && (
            <Link to={leftLink.to} className="btn btn-secondary">
              {leftLink.label}
            </Link>
          )}
        </div>
        <div className="top-bar-actions">
          <button
            type="button"
            className="btn-icon"
            onClick={toggleTheme}
            aria-label="Toggle dark mode"
            title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
          >
            {theme === "light" ? "☾" : "☀"}
          </button>
          {showLogout && (
            <a href="/google/logout" className="btn btn-primary">
              Logout
            </a>
          )}
        </div>
      </header>
      {children}
    </div>
  );
}
