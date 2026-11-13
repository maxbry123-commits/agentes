import { motion } from 'framer-motion';

// True path-drawing sidebar glyphs: the SVG strokes themselves animate on hover (not just a transform), then settle. Always fully visible at rest, so a hover that's interrupted mid-flight never leaves a half-drawn icon. Geometry matches the lucide line-icons they replace so the static look is unchanged.

const SPRING = { type: 'spring', stiffness: 380, damping: 20 } as const;

type Props = { size?: number };

const svgBase = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  viewBox: '0 0 24 24',
};

// Panel toggle: the inner divider sweeps left, like the panel collapsing.
export function AnimatedPanelLeft({ size = 18 }: Props) {
  return (
    <motion.svg width={size} height={size} {...svgBase} initial="rest" animate="rest" whileHover="hover">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <motion.line
        x1="9" y1="3" x2="9" y2="21"
        variants={{ rest: { x: 0 }, hover: { x: -2.5 } }}
        transition={SPRING}
      />
    </motion.svg>
  );
}
