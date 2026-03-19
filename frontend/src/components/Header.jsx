export default function Header({ onReset }) {
  return (
    <header className="header">
      <a className="header-logo" href="/" onClick={e => { e.preventDefault(); onReset?.(); }}>
        <div className="header-logo-icon">🧪</div>
        Validex
      </a>
      <div className="header-actions">
        {onReset && (
          <button className="btn-ghost" onClick={onReset}>
            ← New audit
          </button>
        )}
      </div>
    </header>
  );
}
