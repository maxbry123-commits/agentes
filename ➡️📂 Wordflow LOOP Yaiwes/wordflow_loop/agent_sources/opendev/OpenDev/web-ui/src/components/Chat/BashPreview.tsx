interface BashPreviewProps {
  output: string;
  maxLines?: number;
}

/**
 * Renders a collapsed bash output preview.
 * For outputs > maxLines: shows first 2 lines + "... +N lines" + last 2 lines.
 * Strips ANSI escape sequences.
 */
export function BashPreview({ output, maxLines = 4 }: BashPreviewProps) {
  if (!output) return null;

  // Strip ANSI escape sequences
  const cleaned = output.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '');
  const lines = cleaned.split('\n').filter(l => l.length > 0);

  if (lines.length <= maxLines) {
    return (
      <div className="font-mono text-sm text-text-300 leading-6">
        {lines.map((line, i) => (
          <div key={i} className="truncate">{line}</div>
        ))}
      </div>
    );
  }

  const firstTwo = lines.slice(0, 2);
  const lastTwo = lines.slice(-2);
  const hiddenCount = lines.length - 4;

  return (
    <div className="font-mono text-sm text-text-300 leading-6">
      {firstTwo.map((line, i) => (
        <div key={`first-${i}`} className="truncate">{line}</div>
      ))}
      <div className="text-text-400 italic">… +{hiddenCount} lines</div>
      {lastTwo.map((line, i) => (
        <div key={`last-${i}`} className="truncate">{line}</div>
      ))}
    </div>
  );
}
