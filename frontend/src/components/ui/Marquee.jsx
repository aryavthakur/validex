/**
 * Marquee — infinite horizontal scrolling ticker.
 * Adapted from magicui/marquee. Uses CSS vars + inline styles (no Tailwind).
 * Parent must set overflow: hidden.
 */
export function Marquee({
  reverse = false,
  pauseOnHover = false,
  children,
  repeat = 4,
  gap = "1.5rem",
  duration = "40s",
  style = {},
  ...props
}) {
  const trackClass = [
    "marquee-track",
    reverse ? "marquee-reverse" : "",
    pauseOnHover ? "marquee-pause-hover" : "",
  ].filter(Boolean).join(" ");

  return (
    <div
      {...props}
      style={{
        display: "flex",
        flexDirection: "row",
        overflow: "hidden",
        gap,
        "--gap": gap,
        "--duration": duration,
        ...style,
      }}
    >
      {Array(repeat).fill(0).map((_, i) => (
        <div
          key={i}
          className={trackClass}
          style={{ display: "flex", flexShrink: 0, gap, justifyContent: "space-around" }}
        >
          {children}
        </div>
      ))}
    </div>
  );
}
