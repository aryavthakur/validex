import { motion } from "framer-motion";

function FloatingPaths({ position }: { position: number }) {
    const paths = Array.from({ length: 36 }, (_, i) => ({
        id: i,
        d: `M-${380 - i * 5 * position} -${189 + i * 6}C-${
            380 - i * 5 * position
        } -${189 + i * 6} -${312 - i * 5 * position} ${216 - i * 6} ${
            152 - i * 5 * position
        } ${343 - i * 6}C${616 - i * 5 * position} ${470 - i * 6} ${
            684 - i * 5 * position
        } ${875 - i * 6} ${684 - i * 5 * position} ${875 - i * 6}`,
        width: 0.4 + i * 0.02,
    }));

    return (
        <svg
            className="w-full h-full"
            viewBox="0 0 696 316"
            fill="none"
            preserveAspectRatio="xMidYMid slice"
        >
            {paths.map((path) => (
                <motion.path
                    key={path.id}
                    d={path.d}
                    stroke="white"
                    strokeWidth={path.width}
                    strokeOpacity={0.03 + path.id * 0.006}
                    initial={{ pathLength: 0.3, opacity: 0.4 }}
                    animate={{
                        pathLength: 1,
                        opacity: [0.2, 0.4, 0.2],
                        pathOffset: [0, 1, 0],
                    }}
                    transition={{
                        duration: 25 + Math.random() * 15,
                        repeat: Number.POSITIVE_INFINITY,
                        ease: "linear",
                    }}
                />
            ))}
        </svg>
    );
}

export function AnimatedBackground() {
    return (
        <div
            style={{
                position: "fixed",
                inset: 0,
                zIndex: 0,
                pointerEvents: "none",
                overflow: "hidden",
            }}
        >
            <FloatingPaths position={1} />
            <div style={{ position: "absolute", inset: 0 }}>
                <FloatingPaths position={-1} />
            </div>
        </div>
    );
}
