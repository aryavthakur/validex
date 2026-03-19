function Toggle({ label, sub, checked, onChange }) {
  return (
    <div className="toggle-row">
      <div>
        <div className="toggle-label">{label}</div>
        {sub && <div className="toggle-sub">{sub}</div>}
      </div>
      <label className="toggle-switch">
        <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
        <span className="toggle-track" />
      </label>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div className="form-field">
      <label className="form-label">{label}</label>
      {children}
    </div>
  );
}

export default function ContextForm({ context, onChange, onRun, running, filename, error }) {
  const set = (key) => (val) => onChange(prev => ({ ...prev, [key]: val }));

  return (
    <div className="card" style={{ position: "sticky", top: 80 }}>
      <div className="card-title">Study Context</div>

      <Field label="Metabolomics type">
        <select className="form-select" value={context.metabolomics_type} onChange={e => set("metabolomics_type")(e.target.value)}>
          <option value="untargeted">Untargeted</option>
          <option value="targeted">Targeted</option>
        </select>
      </Field>

      <Field label="Study goal">
        <select className="form-select" value={context.study_goal} onChange={e => set("study_goal")(e.target.value)}>
          <option value="exploratory">Exploratory</option>
          <option value="confirmatory">Confirmatory</option>
        </select>
      </Field>

      <Field label="Design type">
        <select className="form-select" value={context.design_type} onChange={e => set("design_type")(e.target.value)}>
          <option value="independent">Independent groups</option>
          <option value="paired">Paired / repeated measures</option>
          <option value="longitudinal">Longitudinal / time-series</option>
        </select>
      </Field>

      <Field label="Group structure">
        <select className="form-select" value={context.group_count} onChange={e => set("group_count")(e.target.value)}>
          <option value="two_groups">Two groups</option>
          <option value="multi_group">Multi-group (3+)</option>
        </select>
      </Field>

      <Field label="Alpha threshold">
        <input className="form-input" value={context.alpha} onChange={e => set("alpha")(e.target.value)} placeholder="0.05" />
      </Field>

      <Field label="Comparison label (optional)">
        <input className="form-input" value={context.comparison_label} onChange={e => set("comparison_label")(e.target.value)} placeholder="e.g. Control vs Disease" />
      </Field>

      <div style={{ margin: "4px 0 14px" }}>
        <Toggle
          label="Batch effects likely"
          sub="Multiple runs / instruments"
          checked={context.has_batches}
          onChange={set("has_batches")}
        />
        <Toggle
          label="Small sample size"
          sub="Affects overclaiming risk"
          checked={context.small_n}
          onChange={set("small_n")}
        />
      </div>

      <Field label="Notes (optional)">
        <textarea
          className="form-textarea"
          value={context.notes}
          onChange={e => set("notes")(e.target.value)}
          placeholder="Design notes, QC decisions, anything relevant…"
        />
      </Field>

      <button
        className={`btn-run${running ? " running" : ""}`}
        onClick={onRun}
        disabled={running}
      >
        {running ? (
          <>
            <div className="spinner" />
            Running audit…
          </>
        ) : (
          "▶ Run Audit"
        )}
      </button>

      {error && <div className="error-box">⚠ {error}</div>}
    </div>
  );
}
