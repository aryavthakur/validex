import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const FAULT_LABELS = [
  'MISSING FDR',
  'UNCLEAR EFFECT SIZE',
  'INVALID P-VALUE RANGE',
  'METADATA GAP',
];
const LABEL_THRESHOLDS = [0.30, 0.50, 0.65, 0.80];

export default function ScrollTransition() {
  const sectionRef = useRef(null);
  const containerRef = useRef(null);
  const labelsRef = useRef([]);
  const triggersRef = useRef([]);

  const isStaticMode =
    typeof window !== 'undefined' &&
    (window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
      window.innerWidth < 1000);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mobile = window.innerWidth < 1000;

    if (reduced || mobile) return;

    const handleDone = () => {
      const trigger = ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: 'bottom bottom',
        scrub: 1,
        onUpdate: self => {
          const p = self.progress;
          if (containerRef.current) {
            containerRef.current.style.setProperty('--progress', `${(1 - p) * 100}%`);
          }
          labelsRef.current.forEach((label, i) => {
            if (label) {
              label.style.opacity = p >= LABEL_THRESHOLDS[i] ? '1' : '0';
            }
          });
        },
      });
      triggersRef.current.push(trigger);
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      triggersRef.current.forEach(t => t.kill());
    };
  }, []);

  return (
    <section
      className="home__section section__transition"
      ref={sectionRef}
      id="scroll-transition"
    >
      <div className="wrapper">
        <div
          className="transition__block-container"
          ref={containerRef}
          style={{ '--progress': isStaticMode ? '0%' : '100%' }}
        >
          <div className="transition__block">
            <img
              src="/assets/images/transition-cube@2x.png"
              alt="Validation matrix fragmenting"
              loading="lazy"
            />
            <img
              src="/assets/images/secondary-transition@2x.png"
              alt=""
              className="transition__secondary"
              loading="lazy"
            />
            <div className="transition__icons">
              {FAULT_LABELS.map((label, i) => (
                <span
                  key={label}
                  className="transition__fault-label type__hints"
                  ref={el => { labelsRef.current[i] = el; }}
                  style={{ opacity: isStaticMode ? 1 : 0 }}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
          <div className="transition__text type__title-secondary">
            DETECTED. SCORED. EXPLAINED.
          </div>
        </div>
      </div>
    </section>
  );
}
