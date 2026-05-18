import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { splitWords } from '../utils/splitText';

export default function FinalCTA({ onLaunch }) {
  const sectionRef = useRef(null);
  const cubeRef = useRef(null);
  const btnRef = useRef(null);
  const titleRef = useRef(null);
  const triggersRef = useRef([]);
  const loopsRef = useRef([]);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!reduced && cubeRef.current) {
      gsap.set(cubeRef.current, { opacity: 0, scale: 0.8 });
    }

    const handleDone = () => {
      const trigger = ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top 70%',
        once: true,
        onEnter: () => {
          if (reduced) return;

          if (cubeRef.current) {
            gsap.to(cubeRef.current, {
              opacity: 1,
              scale: 1,
              duration: 1,
              ease: 'power3.out',
            });

            const floatLoop = gsap.to(cubeRef.current, {
              y: -8,
              duration: 4,
              ease: 'sine.inOut',
              yoyo: true,
              repeat: -1,
              delay: 1,
            });
            loopsRef.current.push(floatLoop);
          }

          if (titleRef.current) {
            const words = splitWords(titleRef.current);
            gsap.from(words, {
              y: 20,
              opacity: 0,
              duration: 0.7,
              stagger: 0.04,
              ease: 'power3.out',
              delay: 0.3,
            });
          }

          if (btnRef.current) {
            const pulseLoop = gsap.to(btnRef.current, {
              scale: 1.02,
              duration: 1.5,
              ease: 'sine.inOut',
              yoyo: true,
              repeat: -1,
              delay: 1.2,
            });
            loopsRef.current.push(pulseLoop);
          }
        },
      });
      triggersRef.current.push(trigger);
    };

    window.addEventListener('preloader:done', handleDone);
    return () => {
      window.removeEventListener('preloader:done', handleDone);
      triggersRef.current.forEach(t => t.kill());
      loopsRef.current.forEach(l => l.kill());
    };
  }, []);

  return (
    <section className="section__primary-transition" ref={sectionRef} id="final-cta">
      <div className="section__background">
        <div className="wrapper">
          <div className="title__block">
            <img
              ref={cubeRef}
              src="/assets/images/stats-cube@2x.png"
              alt="Validation complete"
              loading="lazy"
            />
            <h2 className="type__title-main" ref={titleRef}>
              Turn statistical uncertainty into an audit trail
            </h2>
            <button
              ref={btnRef}
              className="global__btn type--primary"
              onClick={onLaunch}
            >
              LAUNCH VALIDEX
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
