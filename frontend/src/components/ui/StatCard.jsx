import { motion } from "framer-motion";

export default function StatCard({ value, label, warn = false }) {
  const glowColor = warn ? "rgba(245,158,11,0.25)" : "rgba(255,255,255,0.12)";
  const textGradient = warn
    ? "linear-gradient(to right, #fcd34d, #f59e0b, #fcd34d)"
    : "linear-gradient(to right, #f0ede8, #c8b99a, #f0ede8)";

  return (
    <div style={{
      position: "relative",
      borderRadius: 14,
      overflow: "hidden",
      padding: 1.5,
      background: warn
        ? "linear-gradient(135deg, rgba(245,158,11,0.3), rgba(20,20,20,0.8), rgba(245,158,11,0.1))"
        : "linear-gradient(135deg, rgba(255,255,255,0.12), rgba(20,20,20,0.8), rgba(255,255,255,0.04))",
      flex: 1,
      minWidth: 0,
    }}>
      {/* Moving halo */}
      <motion.div
        style={{
          position: "absolute",
          width: 36,
          height: 36,
          borderRadius: "50%",
          background: glowColor,
          filter: "blur(14px)",
          zIndex: 0,
        }}
        animate={{
          top: ["10%", "10%", "65%", "65%", "10%"],
          left: ["10%", "72%", "72%", "10%", "10%"],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
      />

      {/* Inner card */}
      <div style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
        minHeight: 90,
        borderRadius: 13,
        border: "1px solid rgba(255,255,255,0.06)",
        background: "linear-gradient(135deg, var(--bg-card) 0%, var(--bg-raised) 100%)",
        backdropFilter: "blur(8px)",
        gap: 5,
        padding: "18px 16px",
        zIndex: 1,
      }}>
        {/* Rotating blur ray */}
        <motion.div
          style={{
            position: "absolute",
            width: "75%",
            height: 24,
            borderRadius: "50%",
            background: glowColor,
            filter: "blur(14px)",
            opacity: 0.6,
          }}
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
        />

        {/* Value */}
        <motion.div
          style={{
            fontSize: 28,
            fontFamily: "var(--font-serif)",
            fontWeight: 700,
            background: textGradient,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            position: "relative",
            lineHeight: 1,
          }}
          animate={{
            filter: [
              "drop-shadow(0 0 5px rgba(255,255,255,0.3))",
              "drop-shadow(0 0 1px rgba(255,255,255,0.05))",
              "drop-shadow(0 0 5px rgba(255,255,255,0.3))",
            ],
          }}
          transition={{ duration: 4, repeat: Infinity }}
        >
          {value}
        </motion.div>

        {/* Label */}
        <div style={{
          fontSize: 10,
          fontFamily: "var(--font-mono)",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--text-dim)",
          position: "relative",
        }}>
          {label}
        </div>

        {/* Top line */}
        <motion.div
          style={{
            position: "absolute",
            top: "14%",
            width: "75%",
            height: 1,
            background: "linear-gradient(to right, rgba(255,255,255,0.18), transparent)",
          }}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 6, repeat: Infinity }}
        />
        {/* Bottom line */}
        <motion.div
          style={{
            position: "absolute",
            bottom: "14%",
            width: "75%",
            height: 1,
            background: "linear-gradient(to left, rgba(255,255,255,0.18), transparent)",
          }}
          animate={{ opacity: [1, 0.4, 1] }}
          transition={{ duration: 6, repeat: Infinity }}
        />
      </div>
    </div>
  );
}
