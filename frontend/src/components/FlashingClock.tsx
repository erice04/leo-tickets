import { useEffect, useState } from "react";
import { useTheme } from "../theme/ThemeContext";

const COLORS_LIGHT = ["var(--yale-navy)", "var(--yale-flash-light)"];
const COLORS_DARK = ["var(--yale-gold)", "#ffffff"];

export function FlashingClock({ className }: { className?: string }) {
  const { theme } = useTheme();
  const colors = theme === "dark" ? COLORS_DARK : COLORS_LIGHT;
  const [text, setText] = useState("");
  const [colorIndex, setColorIndex] = useState(0);

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      const hours = now.getHours().toString().padStart(2, "0");
      const minutes = now.getMinutes().toString().padStart(2, "0");
      const seconds = now.getSeconds().toString().padStart(2, "0");
      const month = (now.getMonth() + 1).toString().padStart(2, "0");
      const day = now.getDate().toString().padStart(2, "0");
      const year = now.getFullYear();
      setText(`${hours}:${minutes}:${seconds}  ${month}-${day}-${year}`);
      setColorIndex((i) => (i + 1) % colors.length);
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [colors.length]);

  return (
    <p
      className={`flashing-clock${className ? ` ${className}` : ""}`}
      style={{
        color: colors[colorIndex],
      }}
    >
      {text}
    </p>
  );
}
