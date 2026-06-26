import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine,
  ResponsiveContainer, Cell,
} from "recharts";

// Design tokens (matching index.css — can't use CSS vars in SVG context)
const C = {
  bg:       "#141414",
  text:     "#f0ede8",
  dim:      "rgba(240,237,232,0.28)",
  border:   "rgba(255,255,255,0.07)",
  warm:     "#c8b99a",
  warmDim:  "rgba(200,185,154,0.35)",
  cool:     "rgba(240,237,232,0.18)",
  green:    "#4ade80",
  amber:    "#f59e0b",
  red:      "#f87171",
};

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div style={{
      background: "#1a1a1a", border: `1px solid ${C.border}`,
      borderRadius: 8, padding: "8px 12px",
      fontFamily: "monospace", fontSize: 11,
    }}>
      <div style={{ color: C.dim, marginBottom: 4 }}>
        {d.rangeLabel}
      </div>
      <div style={{ color: C.text }}>
        {d.count} feature{d.count !== 1 ? "s" : ""}
      </div>
    </div>
  );
}

export function HistogramChart({ histogram }) {
  if (!histogram) return (
    <div style={{ color: "rgba(240,237,232,0.5)", fontSize: 13, padding: "12px 0" }}>
      No numeric effect size column detected.
    </div>
  );

  const { counts, bin_edges, column } = histogram;

  const data = counts.map((count, i) => {
    const lo = bin_edges[i];
    const hi = bin_edges[i + 1];
    const mid = (lo + hi) / 2;
    return {
      mid: parseFloat(mid.toFixed(2)),
      count,
      positive: mid >= 0,
      rangeLabel: `${lo.toFixed(2)} to ${hi.toFixed(2)}`,
    };
  });

  const maxCount = Math.max(...counts, 1);

  // Tick values: just show a few meaningful points
  const tickMids = data
    .filter((_, i) => i % Math.ceil(data.length / 7) === 0)
    .map(d => d.mid);

  return (
    <div>
      <div style={{
        fontFamily: "monospace", fontSize: 10,
        color: C.dim, letterSpacing: "0.06em",
        marginBottom: 14,
      }}>
        {column}
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: -20 }} barCategoryGap="4%">
          <XAxis
            dataKey="mid"
            type="number"
            domain={["dataMin", "dataMax"]}
            ticks={tickMids}
            tickFormatter={v => v.toFixed(1)}
            tick={{ fill: C.dim, fontSize: 9, fontFamily: "monospace" }}
            axisLine={{ stroke: C.border }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: C.dim, fontSize: 9, fontFamily: "monospace" }}
            axisLine={false}
            tickLine={false}
            width={32}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <ReferenceLine x={0} stroke={C.dim} strokeDasharray="3 3" strokeWidth={1} />
          <Bar dataKey="count" radius={[2, 2, 0, 0]} maxBarSize={32}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.positive ? C.warm : C.cool} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div style={{
        display: "flex", justifyContent: "center", gap: 20,
        marginTop: 6, fontFamily: "monospace", fontSize: 9, color: C.dim,
      }}>
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: C.cool, display: "inline-block" }} />
          Down-regulated
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: C.warm, display: "inline-block" }} />
          Up-regulated
        </span>
      </div>
    </div>
  );
}
