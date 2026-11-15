import React, { useCallback, useRef } from 'react';

// Arc's theme-device dials: grain is a wavy line with a pill thumb, intensity is a round dotted
// knob. Strokes ride currentColor so the same dials read on the dark device and light Settings.

export const SquiggleSlider: React.FC<{ value: number; onChange: (v: number) => void; width?: number }> = ({ value, onChange, width = 170 }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [dragging, setDragging] = React.useState(false);
  const apply = useCallback((clientX: number) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    onChange(Math.min(1, Math.max(0, (clientX - r.left) / r.width)));
  }, [onChange]);
  const H = 30;
  const wavePath = Array.from({ length: 61 }, (unused, i) => {
    const x = (i / 60) * width;
    const y = H / 2 + Math.sin((i / 60) * Math.PI * 2 * 5) * 6;
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  return (
    <div
      ref={ref}
      title="Grain"
      onPointerDown={(e) => { setDragging(true); e.currentTarget.setPointerCapture?.(e.pointerId); apply(e.clientX); }}
      onPointerMove={(e) => { if (dragging) apply(e.clientX); }}
      onPointerUp={() => setDragging(false)}
      onPointerCancel={() => setDragging(false)}
      onLostPointerCapture={() => setDragging(false)}
      style={{ position: 'relative', width, height: H, cursor: dragging ? 'grabbing' : 'grab', touchAction: 'none', flexShrink: 0 }}
    >
      <svg width={width} height={H} style={{ display: 'block', pointerEvents: 'none' }}>
        <path d={wavePath} stroke="currentColor" strokeOpacity={0.5} strokeWidth={2} fill="none" strokeLinecap="round" />
      </svg>
      <div style={{
        position: 'absolute', top: '50%', left: value * width, transform: 'translate(-50%, -50%)',
        width: 14, height: 26, borderRadius: 999, background: '#fff',
        boxShadow: '0 1px 5px rgba(0,0,0,0.4)', pointerEvents: 'none',
      }} />
    </div>
  );
};

export const Knob: React.FC<{ value: number; onChange: (v: number) => void; size?: number }> = ({ value, onChange, size = 34 }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const [grabbing, setGrabbing] = React.useState(false);
  // A real knob turns RELATIVE to where you grabbed it; jumping to the grab angle feels broken.
  const start = useRef<{ deg: number; value: number } | null>(null);
  const angle = -135 + value * 270;
  const pointerDeg = useCallback((clientX: number, clientY: number): number => {
    const el = ref.current;
    if (!el) return 0;
    const r = el.getBoundingClientRect();
    return Math.atan2(clientX - (r.left + r.width / 2), (r.top + r.height / 2) - clientY) * (180 / Math.PI);
  }, []);
  const end = (): void => { setGrabbing(false); start.current = null; };
  return (
    <div
      ref={ref}
      title="Intensity"
      onPointerDown={(e) => {
        setGrabbing(true);
        e.currentTarget.setPointerCapture?.(e.pointerId);
        start.current = { deg: pointerDeg(e.clientX, e.clientY), value };
      }}
      onPointerMove={(e) => {
        if (!grabbing || !start.current) return;
        let delta = pointerDeg(e.clientX, e.clientY) - start.current.deg;
        // Crossing the +-180 seam must not spin the knob a full turn.
        if (delta > 180) delta -= 360;
        if (delta < -180) delta += 360;
        onChange(Math.min(1, Math.max(0, start.current.value + delta / 270)));
      }}
      onPointerUp={end}
      onPointerCancel={end}
      onLostPointerCapture={end}
      style={{
        position: 'relative', width: size + 10, height: size + 10, display: 'flex', alignItems: 'center',
        justifyContent: 'center', cursor: grabbing ? 'grabbing' : 'grab', touchAction: 'none', flexShrink: 0,
      }}
    >
      <div style={{ position: 'absolute', inset: 0, borderRadius: 999, border: '2px dotted currentColor', opacity: 0.4, pointerEvents: 'none' }} />
      <div style={{ width: size - 8, height: size - 8, borderRadius: 999, background: '#3a3835', transform: `rotate(${angle}deg)`, display: 'flex', justifyContent: 'center', pointerEvents: 'none' }}>
        <div style={{ width: 3, height: 9, borderRadius: 2, background: '#fff', marginTop: 2 }} />
      </div>
    </div>
  );
};
