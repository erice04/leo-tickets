import { useEffect, useState } from "react";
import { useTheme } from "../theme/ThemeContext";

const COLORS_LIGHT = ["var(--yale-navy)", "var(--yale-flash-light)"];
const COLORS_DARK = ["var(--yale-gold)", "#ffffff"];

function formatDate(now: Date) {
  return now.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function formatTimeParts(now: Date) {
  const withPeriod = now.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  const periodMatch = withPeriod.match(/\s(AM|PM)$/i);
  const period = periodMatch ? periodMatch[1] : "";
  const main = withPeriod.replace(/\s(AM|PM)$/i, "");
  const seconds = String(now.getSeconds()).padStart(2, "0");
  return { main, seconds, period };
}

export function usePostcardDateTime() {
  const { theme } = useTheme();
  const colors = theme === "dark" ? COLORS_DARK : COLORS_LIGHT;
  const [dateText, setDateText] = useState("");
  const [timeMain, setTimeMain] = useState("");
  const [timeSeconds, setTimeSeconds] = useState("");
  const [timePeriod, setTimePeriod] = useState("");
  const [colorIndex, setColorIndex] = useState(0);

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      const { main, seconds, period } = formatTimeParts(now);
      setDateText(formatDate(now));
      setTimeMain(main);
      setTimeSeconds(seconds);
      setTimePeriod(period);
      setColorIndex((i) => (i + 1) % colors.length);
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [colors.length]);

  return {
    dateText,
    timeMain,
    timeSeconds,
    timePeriod,
    color: colors[colorIndex],
  };
}
