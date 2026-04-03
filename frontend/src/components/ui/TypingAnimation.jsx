import { useEffect, useState } from "react";

/**
 * TypingAnimation — reveals text character by character.
 * From magicui/typing-animation on 21st.dev.
 */
export function TypingAnimation({ text, duration = 40, className = "", style = {} }) {
  const [displayed, setDisplayed] = useState("");
  const [i, setI] = useState(0);

  // Reset when text changes
  useEffect(() => {
    setDisplayed("");
    setI(0);
  }, [text]);

  useEffect(() => {
    if (i >= text.length) return;
    const id = setTimeout(() => {
      setDisplayed(text.slice(0, i + 1));
      setI(i + 1);
    }, duration);
    return () => clearTimeout(id);
  }, [duration, i, text]);

  return (
    <span className={className} style={style}>
      {displayed}
      <span style={{
        display: "inline-block",
        width: "1ch",
        animation: "cursor-blink 1s step-start infinite",
        opacity: i < text.length ? 1 : 0,
      }}>▋</span>
    </span>
  );
}
