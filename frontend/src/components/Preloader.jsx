import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { splitChars } from '../utils/splitText';

const BAR_LABELS = ['P', 'Q', 'FC', 'QC', 'META', 'SCORE'];
const PRELOADER_TEXT = 'Initializing audit engine';

export default function Preloader() {
  const rootRef = useRef(null);
  const fillRef = useRef(null);
  const textRef = useRef(null);
  const intervalRef = useRef(null);
  const charsRef = useRef([]);

  const exit = () => {
    clearInterval(intervalRef.current);
    const tl = gsap.timeline();
    if (charsRef.current.length) {
      tl.to(charsRef.current, {
        opacity: 0,
        duration: 0.3,
        ease: 'power2.out',
        stagger: { each: 0.01, from: 'random' },
      }, 0.4);
    }
    tl.to('.validex-cinematic .bar__fill .bar-label', {
      autoAlpha: 0,
      duration: 0.6,
      ease: 'power2.out',
      stagger: { each: 0.05, from: 'random' },
    }, 0);
    tl.to('.validex-cinematic .bar__background .bar-label', {
      autoAlpha: 0,
      duration: 0.6,
      ease: 'power2.out',
      stagger: { each: 0.05, from: 'random' },
    }, 0);
    if (rootRef.current) {
      tl.to(rootRef.current, {
        autoAlpha: 0,
        duration: 1,
        ease: 'power2.out',
        pointerEvents: 'none',
      }, 0.7);
    }
    tl.add(() => {
      window.dispatchEvent(new CustomEvent('preloader:done'));
    }, 1.4);
  };

  const simulateProgress = () => {
    let progress = 0;
    intervalRef.current = setInterval(() => {
      progress += Math.random() * 8 + 3;
      if (progress >= 85) {
        progress = 85;
        clearInterval(intervalRef.current);
        if (fillRef.current) fillRef.current.style.setProperty('--progress', '15%');
        setTimeout(() => {
          if (fillRef.current) fillRef.current.style.setProperty('--progress', '0%');
          setTimeout(exit, 300);
        }, 400);
        return;
      }
      const cssProgress = 100 - progress;
      if (fillRef.current) fillRef.current.style.setProperty('--progress', `${cssProgress}%`);
    }, 120);
  };

  useEffect(() => {
    if (textRef.current) {
      charsRef.current = splitChars(textRef.current);
    }

    const isMobile = window.innerWidth <= 1000;
    if (isMobile) {
      setTimeout(exit, 400);
    } else {
      simulateProgress();
    }

    return () => {
      clearInterval(intervalRef.current);
      if (textRef.current) {
        textRef.current.textContent = PRELOADER_TEXT;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="preloader" ref={rootRef}>
      <div className="preloader__ui-container">
        <div className="preloader__bar-container">
          <div className="bar__fill" ref={fillRef}>
            {BAR_LABELS.map(label => (
              <span key={label} className="bar-label">{label}</span>
            ))}
          </div>
          <div className="bar__background">
            {BAR_LABELS.map(label => (
              <span key={label} className="bar-label">{label}</span>
            ))}
          </div>
        </div>
        <div className="ui__text" ref={textRef}>
          {PRELOADER_TEXT}
        </div>
      </div>
    </div>
  );
}
