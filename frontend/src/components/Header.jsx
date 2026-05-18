import { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function Header({ onLaunch }) {
  const logoRef = useRef(null);
  const ctaRef = useRef(null);

  useEffect(() => {
    gsap.set([logoRef.current, ctaRef.current], { autoAlpha: 0 });

    const handleDone = () => {
      gsap.to([logoRef.current, ctaRef.current], {
        autoAlpha: 1,
        duration: 0.8,
        ease: 'power2.out',
        stagger: 0.1,
      });
    };

    window.addEventListener('preloader:done', handleDone);
    return () => window.removeEventListener('preloader:done', handleDone);
  }, []);

  return (
    <>
      <div className="header__logo" ref={logoRef}>
        <span className="type__title-secondary">VALIDEX</span>
      </div>
      <div className="header__cta" ref={ctaRef}>
        <button className="global__btn type--ghost" onClick={onLaunch}>
          RUN AUDIT →
        </button>
      </div>
    </>
  );
}
