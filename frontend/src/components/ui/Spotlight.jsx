/**
 * Spotlight — diagonal light sweep SVG effect.
 * Adapted from aceternity/spotlight. Uses inline styles (no Tailwind).
 * Parent must have `position: relative; overflow: hidden`.
 */
export function Spotlight({ fill = "rgba(200,185,154,0.18)", style = {} }) {
  return (
    <svg
      className="animate-spotlight"
      style={{
        pointerEvents: "none",
        position: "absolute",
        zIndex: 0,
        height: "169%",
        width: "138%",
        opacity: 0,
        top: 0,
        left: 0,
        ...style,
      }}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 3787 2842"
      fill="none"
    >
      <g filter="url(#spotlight-blur)">
        <ellipse
          cx="1924.71"
          cy="273.501"
          rx="1924.71"
          ry="273.501"
          transform="matrix(-0.822377 -0.568943 -0.568943 0.822377 3631.88 2291.09)"
          fill={fill}
          fillOpacity="1"
        />
      </g>
      <defs>
        <filter
          id="spotlight-blur"
          x="0.860352"
          y="0.838989"
          width="3785.16"
          height="2840.26"
          filterUnits="userSpaceOnUse"
          colorInterpolationFilters="sRGB"
        >
          <feFlood floodOpacity="0" result="BackgroundImageFix" />
          <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape" />
          <feGaussianBlur stdDeviation="151" result="effect1_foregroundBlur" />
        </filter>
      </defs>
    </svg>
  );
}
