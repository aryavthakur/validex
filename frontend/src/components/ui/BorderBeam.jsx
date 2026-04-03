/**
 * BorderBeam — animated light beam that travels around a container's border.
 * Place inside a `position: relative` parent with a defined border-radius.
 * Uses CSS offset-path: rect() (Chrome 116+, Firefox 122+, Safari 17+).
 */
export function BorderBeam({
  size = 120,
  duration = 6,
  colorFrom = "#c8b99a",
  colorTo = "#4ade80",
  borderWidth = 1.5,
  borderRadius = "12px",
  delay = 0,
}) {
  return (
    <div
      className="border-beam"
      style={{
        "--beam-size": size,
        "--beam-duration": duration,
        "--beam-from": colorFrom,
        "--beam-to": colorTo,
        "--beam-delay": `-${delay}s`,
        "--beam-radius": borderRadius,
        pointerEvents: "none",
        position: "absolute",
        inset: 0,
        borderRadius: "inherit",
        border: `${borderWidth}px solid transparent`,
        // mask technique: show only the border strip
        WebkitMask: "linear-gradient(transparent, transparent), linear-gradient(white, white)",
        WebkitMaskClip: "padding-box, border-box",
        WebkitMaskComposite: "destination-in",
        mask: "linear-gradient(transparent, transparent), linear-gradient(white, white)",
        maskClip: "padding-box, border-box",
        maskComposite: "intersect",
      }}
    />
  );
}
