import { useEffect, useRef } from "react";
import { useMotionValue, useSpring, useInView } from "framer-motion";

/**
 * NumberTicker — counts up to `value` with a spring animation when in view.
 * From magicui/number-ticker on 21st.dev.
 */
export function NumberTicker({ value, delay = 0, decimalPlaces = 0, style = {} }) {
  const ref = useRef(null);
  const motionValue = useMotionValue(0);
  const springValue = useSpring(motionValue, { damping: 60, stiffness: 100 });
  const isInView = useInView(ref, { once: true, margin: "0px" });

  useEffect(() => {
    if (!isInView) return;
    const t = setTimeout(() => motionValue.set(value), delay * 1000);
    return () => clearTimeout(t);
  }, [motionValue, isInView, delay, value]);

  useEffect(() =>
    springValue.on("change", (latest) => {
      if (ref.current) {
        ref.current.textContent = Intl.NumberFormat("en-US", {
          minimumFractionDigits: decimalPlaces,
          maximumFractionDigits: decimalPlaces,
        }).format(Number(latest.toFixed(decimalPlaces)));
      }
    }),
    [springValue, decimalPlaces]
  );

  return <span ref={ref} style={style} />;
}
