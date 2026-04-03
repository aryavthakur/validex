import React from "react";

// Render this once at the root of the app (or inside each toggle — it's deduplicated by id)
export function GooeyFilter() {
  return (
    <svg style={{ position: "fixed", width: 0, height: 0, pointerEvents: "none" }}>
      <defs>
        <filter id="goo-toggle">
          <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
          <feColorMatrix
            in="blur"
            mode="matrix"
            values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7"
            result="goo"
          />
          <feComposite in="SourceGraphic" in2="goo" operator="atop" />
        </filter>
      </defs>
    </svg>
  );
}

export function LiquidToggle({ checked = false, onChange, label, sub }) {
  const [isChecked, setIsChecked] = React.useState(checked);

  React.useEffect(() => {
    setIsChecked(checked);
  }, [checked]);

  const handleChange = (e) => {
    setIsChecked(e.target.checked);
    onChange?.(e.target.checked);
  };

  return (
    <div className="toggle-row">
      <div>
        <div className="toggle-label">{label}</div>
        {sub && <div className="toggle-sub">{sub}</div>}
      </div>
      <label style={{
        position: "relative",
        display: "block",
        cursor: "pointer",
        height: 32,
        width: 52,
        flexShrink: 0,
        transform: "translateZ(0)",
        backfaceVisibility: "hidden",
        WebkitBackfaceVisibility: "hidden",
      }}>
        <input
          type="checkbox"
          checked={isChecked}
          onChange={handleChange}
          style={{
            height: "100%",
            width: "100%",
            cursor: "pointer",
            appearance: "none",
            WebkitAppearance: "none",
            borderRadius: 9999,
            backgroundColor: isChecked ? "#275EFE" : "rgba(255,255,255,0.12)",
            outline: "none",
            transition: "background-color 0.5s ease",
            transform: "translate3d(0,0,0)",
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        />
        <svg
          viewBox="0 0 52 32"
          filter="url(#goo-toggle)"
          style={{
            pointerEvents: "none",
            position: "absolute",
            inset: 0,
            fill: "white",
            transform: "translate3d(0,0,0)",
            width: "100%",
            height: "100%",
          }}
        >
          <circle
            cx="16"
            cy="16"
            r="10"
            style={{
              transformOrigin: "16px 16px",
              transform: `translateX(${isChecked ? "12px" : "0px"}) scale(${isChecked ? "0" : "1"})`,
              transition: "transform 0.5s ease",
            }}
          />
          <circle
            cx="36"
            cy="16"
            r="10"
            style={{
              transformOrigin: "36px 16px",
              transform: `translateX(${isChecked ? "0px" : "-12px"}) scale(${isChecked ? "1" : "0"})`,
              transition: "transform 0.5s ease",
            }}
          />
          {isChecked && (
            <circle
              cx="35"
              cy="-1"
              r="2.5"
              style={{ transition: "transform 0.7s ease" }}
            />
          )}
        </svg>
      </label>
    </div>
  );
}
