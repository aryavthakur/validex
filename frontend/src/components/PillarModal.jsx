export default function PillarModal({ module, onClose }) {
  if (!module) return null;

  return (
    <div className="pillar-modal" role="dialog" aria-modal="true">
      <button className="pillar-modal__backdrop" aria-label="Close pillar detail" onClick={onClose} />
      <div className="pillar-modal__panel">
        <div className="pillar-modal__top">
          <p className="type__hints">AUDIT LAYER</p>
          <button className="pillar-modal__close" onClick={onClose}>CLOSE</button>
        </div>

        <h3 className="type__title-secondary">{module.label}</h3>
        <p className="pillar-modal__description type__body">{module.description}</p>

        <div className="pillar-modal__checks">
          {module.checks.map((check) => (
            <div className="pillar-modal__check" key={check}>
              <span className="pillar-modal__dot" />
              <span className="type__body">{check}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
