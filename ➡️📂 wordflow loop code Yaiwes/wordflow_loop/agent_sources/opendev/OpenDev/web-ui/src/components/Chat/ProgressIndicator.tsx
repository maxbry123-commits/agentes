import React, { useEffect, useState } from 'react';
import { SPINNER_FRAMES, THINKING_VERBS, SPINNER_COLORS } from '../../constants/spinner';

interface ProgressIndicatorProps {
  progressMessage: string | null;
}

export const ProgressIndicator = React.memo(function ProgressIndicator({ progressMessage }: ProgressIndicatorProps) {
  // Spinner animation state
  const [spinnerIndex, setSpinnerIndex] = useState(0);
  const [verbIndex, setVerbIndex] = useState(0);
  const [colorIndex, setColorIndex] = useState(0);

  // Animate spinner when loading
  useEffect(() => {
    const spinnerInterval = setInterval(() => {
      setSpinnerIndex(prev => (prev + 1) % SPINNER_FRAMES.length);
      setColorIndex(prev => (prev + 1) % SPINNER_COLORS.length);
    }, 100); // Match terminal speed: 100ms

    const verbInterval = setInterval(() => {
      setVerbIndex(prev => (prev + 1) % THINKING_VERBS.length);
    }, 2000); // Change verb every 2 seconds

    return () => {
      clearInterval(spinnerInterval);
      clearInterval(verbInterval);
    };
  }, []);

  return (
    <div className="bg-bg-000 border border-border-300/15 rounded-lg px-4 py-3 animate-fade-in">
      <div className="flex items-center gap-3">
        <span className={`text-base font-medium ${SPINNER_COLORS[colorIndex]} transition-colors duration-100`}>
          {SPINNER_FRAMES[spinnerIndex]}
        </span>
        <span className="text-sm text-text-300 font-medium">
          {progressMessage ? progressMessage : `${THINKING_VERBS[verbIndex]}...`}
        </span>
      </div>
    </div>
  );
});
