/**
 * Meteors — diagonal shooting star effect.
 * From magicui/meteors on 21st.dev. Adapted to use CSS vars + inline styles.
 * Parent must have `position: relative; overflow: hidden`.
 */
export function Meteors({ number = 20, color = "rgba(200,185,154,0.7)" }) {
  return (
    <>
      {Array.from({ length: number }).map((_, idx) => (
        <span
          key={idx}
          className="animate-meteor"
          style={{
            position: "absolute",
            top: 0,
            left: Math.floor(Math.random() * 1000 - 400) + "px",
            width: 1,
            height: 1,
            borderRadius: 9999,
            background: color,
            boxShadow: `0 0 0 1px rgba(255,255,255,0.04)`,
            transform: "rotate(215deg)",
            animationDelay: (Math.random() * 1.5 + 0.1).toFixed(2) + "s",
            animationDuration: (Math.random() * 7 + 3).toFixed(1) + "s",
            pointerEvents: "none",
          }}
        >
          <span style={{
            position: "absolute",
            top: "50%",
            transform: "translateY(-50%)",
            width: 60,
            height: 1,
            background: `linear-gradient(to right, ${color}, transparent)`,
          }} />
        </span>
      ))}
    </>
  );
}
