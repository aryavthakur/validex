import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import '../styles/validex-cinematic.css';
import Preloader from './Preloader';
import SmoothScroll from './SmoothScroll';
import Header from './Header';
import HeroSection from './HeroSection';
import ScrollTransition from './ScrollTransition';
import AuditModules from './AuditModules';
import ProductDemo from './ProductDemo';
import WorkflowSection from './WorkflowSection';
import FinalCTA from './FinalCTA';

gsap.registerPlugin(ScrollTrigger);

export default function ValidexLanding({ onLaunch, onFileAccepted }) {
  const landingRef = useRef(null);

  useEffect(() => {
    const onDone = () => {
      window.__validexReady = true;
      requestAnimationFrame(() => ScrollTrigger.refresh());
    };

    window.addEventListener('preloader:done', onDone);

    return () => {
      window.removeEventListener('preloader:done', onDone);
      ScrollTrigger.getAll().forEach(trigger => {
        if (trigger.trigger && landingRef.current?.contains(trigger.trigger)) trigger.kill();
      });
      delete window.__validexReady;
    };
  }, []);

  return (
    <div className="validex-cinematic" ref={landingRef}>
      <Preloader />
      <SmoothScroll>
        <Header onLaunch={onLaunch} />
        <HeroSection />
        <ScrollTransition />
        <AuditModules />
        <ProductDemo onLaunch={onLaunch} onFileAccepted={onFileAccepted} />
        <WorkflowSection />
        <FinalCTA onLaunch={onLaunch} />
      </SmoothScroll>
    </div>
  );
}
