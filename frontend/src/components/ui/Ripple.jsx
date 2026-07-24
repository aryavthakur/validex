/**
 * Ripple — concentric pulsing rings.
 * Adapted from magicui/ripple. Uses CSS vars + inline styles (no Tailwind).
 * Parent must have `position: relative; overflow: hidden`.
 */
export function Ripple({
  mainCircleSize = 180,
  mainCircleOpacity = 0.18,
  numCircles = 7,
  color = "200,185,154",
}) {
  return (
    <div style={{
      pointerEvents: "none",
      userSelect: "none",
      position: "absolute",
      inset: 0,
      maskImage: "linear-gradient(to bottom, white 40%, transparent)",
      WebkitMaskImage: "linear-gradient(to bottom, white 40%, transparent)",
    }}>
      {Array.from({ length: numCircles }, (_, i) => {
        const size = mainCircleSize + i * 70;
        const opacity = Math.max(0, mainCircleOpacity - i * 0.022);
        const delay = `${i * 0.12}s`;
        const borderStyle = i === numCircles - 1 ? "dashed" : "solid";
        return (
          <div
            key={i}
            className="animate-ripple"
            style={{
              position: "absolute",
              width: size,
              height: size,
              borderRadius: "50%",
              border: `1px ${borderStyle} rgba(${color},${0.1 + i * 0.025})`,
              background: `rgba(${color},0.02)`,
              opacity,
              animationDelay: delay,
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%) scale(1)",
            }}
          />
        );
      })}
    </div>
  );
}
