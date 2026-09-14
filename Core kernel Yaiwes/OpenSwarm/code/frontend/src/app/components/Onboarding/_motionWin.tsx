// Windows-aware shim for framer-motion. On Mac, re-exports the real library; on Windows, motion.* becomes a plain HTML element (no animation, no Framer runtime, no segfault). AnimatePresence passes children through. Onboarding files import from here so a single Mac/Windows fork lives in one place.

import React from 'react';
import * as fm from 'framer-motion';

const IS_WIN = typeof navigator !== 'undefined' && navigator.userAgent.includes('Windows');

const FRAMER_ONLY_PROPS = new Set([
  'initial', 'animate', 'exit', 'transition', 'variants', 'layoutId', 'layout',
  'drag', 'dragConstraints', 'dragElastic', 'dragMomentum', 'dragControls',
  'dragDirectionLock', 'dragListener', 'dragTransition', 'dragSnapToOrigin', 'dragPropagation',
  'onDragStart', 'onDragEnd', 'onDrag', 'onDirectionLock',
  'onAnimationStart', 'onAnimationComplete', 'onUpdate',
  'onLayoutAnimationStart', 'onLayoutAnimationComplete',
  'whileHover', 'whileTap', 'whileFocus', 'whileDrag', 'whileInView',
  'viewport', 'transformTemplate', 'custom', 'inherit',
]);

const stripFramerProps = (props: any) => {
  const out: any = {};
  for (const k in props) {
    if (!FRAMER_ONLY_PROPS.has(k)) out[k] = props[k];
  }
  return out;
};

// Components that drive position via `animate={{ x, y }}` (ACPopup, ACMultiChoice, etc.) would otherwise lose their layout when the animate prop is stripped, because they have no fallback style.transform. We salvage the latest numeric x/y from animate and apply them as a transform so the div lands in the right place; no animation, just static placement. One cached component per tag. CRITICAL: without the cache the Proxy getter returns a NEW forwardRef component on every `motion.div` access, so React sees a different component type each render and REMOUNTS the DOM node every time. A freshly-mounted node has no previous transform to ease from, so CSS transitions never run (getAnimations() stays empty) and the cursor jumps instantly instead of gliding; the breathing pulse never animates either. Caching gives each tag a stable identity so React reconciles in place.
const tagComponentCache: Record<string, any> = {};
const motionShim: any = new Proxy({}, {
  get: (_target, tag: string) => {
    if (!tagComponentCache[tag]) {
      tagComponentCache[tag] = React.forwardRef((props: any, ref: any) => {
        let translate = '';
        const a = props.animate;
        if (a && typeof a === 'object' && !Array.isArray(a)) {
          const ax = typeof a.x === 'number' ? a.x : null;
          const ay = typeof a.y === 'number' ? a.y : null;
          if (ax !== null || ay !== null) {
            translate = `translate(${ax ?? 0}px, ${ay ?? 0}px)`;
          }
        }
        const stripped = stripFramerProps(props);
        if (translate) {
          const existing = stripped.style && stripped.style.transform;
          stripped.style = {
            ...(stripped.style || {}),
            transform: existing ? `${existing} ${translate}` : translate,
          };
        }
        return React.createElement(tag, { ...stripped, ref });
      });
    }
    return tagComponentCache[tag];
  },
});

export const motion: typeof fm.motion = IS_WIN ? motionShim : fm.motion;
export const AnimatePresence: typeof fm.AnimatePresence = IS_WIN
  ? (({ children }: any) => children) as any
  : fm.AnimatePresence;

const animationControlsStub = {
  start: () => Promise.resolve(),
  stop: () => {},
  set: () => {},
  mount: () => () => {},
};
export const useAnimationControls: typeof fm.useAnimationControls = IS_WIN
  ? (() => animationControlsStub as any) as any
  : fm.useAnimationControls;
