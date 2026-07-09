import { useEffect, useRef, useState } from "react";
import leoLogo from "../assets/leo-logo.png";
import lightPaper from "../assets/postcard-paper-light.jpg";
import darkPaper from "../assets/postcard-paper-dark.jpg";
import stampYaleBowlFull from "../assets/postcard-stamp-horizontal-full.png";
import stampSterlingFull from "../assets/postcard-stamp-vertical-full.png";
import stampLeoFull from "../assets/postcard-stamp-leo-full.png";
import stampRugbyFull from "../assets/postcard-stamp-rugby-full.png";
import stampInkFull from "../assets/postcard-stamp-ink-full.png";
import stampCustomFrame from "../assets/postcard-stamp-custom-frame.png";
import stampCustomInsets from "../assets/postcard-stamp-custom-insets.json";
import { usePostcardDateTime } from "./PostcardDateTime";
import { useTheme } from "../theme/ThemeContext";
import type { TicketResponse } from "../api/client";

interface PostcardTicketProps {
  ticket: TicketResponse;
}

type StampInsets = {
  logoTopPct: number;
  logoLeftPct: number;
  logoRightPct: number;
  logoBottomPct: number;
  borderColor: string;
};

type OverlayStamp = {
  mode: "overlay";
  layout: "vertical" | "horizontal" | "square";
  frame: string;
  insets: StampInsets;
  overlaySrc: string;
};

type FullStamp = {
  mode: "full";
  layout: "vertical" | "horizontal";
  full: string;
};

function resolveStamp(ticket: TicketResponse): OverlayStamp | FullStamp {
  const preset = ticket.postcard_stamp_preset;

  if (preset === "yale_bowl") {
    return { mode: "full", layout: "horizontal", full: stampYaleBowlFull };
  }
  if (preset === "sterling") {
    return { mode: "full", layout: "vertical", full: stampSterlingFull };
  }
  if (preset === "leo") {
    return { mode: "full", layout: "vertical", full: stampLeoFull };
  }
  if (preset === "rugby") {
    return { mode: "full", layout: "vertical", full: stampRugbyFull };
  }
  if (preset === "ink") {
    return { mode: "full", layout: "vertical", full: stampInkFull };
  }
  if (preset === "custom") {
    return {
      mode: "overlay",
      layout: "square",
      frame: stampCustomFrame,
      insets: stampCustomInsets,
      overlaySrc:
        ticket.has_custom_watermark ? "/api/v1/ticket/watermark" : leoLogo,
    };
  }

  return { mode: "full", layout: "vertical", full: stampSterlingFull };
}

export function PostcardTicket({ ticket }: PostcardTicketProps) {
  const { theme } = useTheme();
  const { dateText, timeMain, timeSeconds, timePeriod, color } = usePostcardDateTime();
  const stamp = resolveStamp(ticket);
  const paperBg = theme === "dark" ? darkPaper : lightPaper;
  const titleRef = useRef<HTMLSpanElement>(null);
  const [titleWrapped, setTitleWrapped] = useState(false);

  useEffect(() => {
    const el = titleRef.current;
    if (!el) return;

    const checkWrap = () => {
      const lineHeight = parseFloat(getComputedStyle(el).lineHeight);
      setTitleWrapped(el.scrollHeight > lineHeight * 1.4);
    };

    checkWrap();
    const observer = new ResizeObserver(checkWrap);
    observer.observe(el);
    return () => observer.disconnect();
  }, [ticket.title]);

  return (
    <div className="postcard-frame">
      <div
        className="postcard-inner"
        style={{ backgroundImage: `url(${paperBg})` }}
      >
        <div className="postcard-top">
          <div className="postcard-postal" aria-hidden="true">
            {Array.from({ length: 6 }, (_, i) => (
              <span key={i} className="postcard-postal-box" />
            ))}
          </div>
          <div className={`postcard-stamp postcard-stamp-${stamp.layout}`}>
            {stamp.mode === "overlay" && (
              <>
                <img
                  src={stamp.frame}
                  alt=""
                  aria-hidden="true"
                  className="postcard-stamp-frame"
                />
                <div
                  className={`postcard-stamp-overlay${ticket.postcard_stamp_preset === "custom" ? " postcard-stamp-overlay-custom" : ""}`}
                  style={{
                    top: `${stamp.insets.logoTopPct}%`,
                    left: `${stamp.insets.logoLeftPct}%`,
                    right: `${stamp.insets.logoRightPct}%`,
                    bottom: `${stamp.insets.logoBottomPct}%`,
                    ["--postcard-stamp-green" as string]: stamp.insets.borderColor,
                  }}
                >
                  <img
                    src={stamp.overlaySrc}
                    alt="Postage stamp logo"
                    className="postcard-stamp-logo"
                  />
                </div>
              </>
            )}
            {stamp.mode === "full" && (
              <img
                src={stamp.full}
                alt="New Haven postage stamp"
                className="postcard-stamp-frame"
              />
            )}
          </div>
        </div>

        <div className="postcard-qr-section">
          <div className="postcard-qr-wrap">
            <img
              src={`data:image/png;base64,${ticket.qr_code_base64}`}
              alt="Your event QR ticket"
              className="postcard-qr"
            />
          </div>
        </div>

        <div className={`postcard-lines${titleWrapped ? "" : " postcard-lines-single-title"}`}>
          <div className="postcard-line postcard-line-dotted" aria-hidden="true" />
          <div className="postcard-line postcard-line-title">
            <span ref={titleRef} className="postcard-title">{ticket.title}</span>
          </div>
          <div className="postcard-line">
            <span className="postcard-datetime" style={{ color }}>
              {dateText}
            </span>
          </div>
          <div className="postcard-line postcard-line-last">
            <span
              className="postcard-datetime postcard-datetime-time"
              style={{ color }}
              aria-label={`${timeMain}${timeSeconds}${timePeriod ? ` ${timePeriod}` : ""}`}
            >
              <span className="postcard-time">
                <span className="postcard-time-main">{timeMain}</span>
                <span className="postcard-time-seconds">{timeSeconds}</span>
                {timePeriod && (
                  <span className="postcard-time-period">{timePeriod}</span>
                )}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
