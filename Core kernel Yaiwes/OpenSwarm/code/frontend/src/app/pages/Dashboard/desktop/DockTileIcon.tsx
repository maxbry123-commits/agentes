import React, { useState } from 'react';
import Box from '@mui/material/Box';
import type { DockEntry } from './dockEntries';

/** A tile shows its real image (site favicon, app thumbnail) OR the generic SVG glyph, never
 * letters and never the glyph peeking out from behind an image. */
export function DockTileIcon({ entry }: { entry: DockEntry }): React.ReactElement {
  const [imageFailed, setImageFailed] = useState(false);
  if (entry.faviconUrl && !imageFailed) {
    return (
      <Box component="img" src={entry.faviconUrl} alt="" onError={() => setImageFailed(true)} sx={{ borderRadius: '6px' }} />
    );
  }
  // An app's own screenshot fills the whole tile: the most personalized mark it can carry.
  if (entry.kind === 'view' && entry.thumbnail && !imageFailed) {
    return (
      <Box component="img" src={entry.thumbnail} alt="" onError={() => setImageFailed(true)}
        sx={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
    );
  }
  return <>{entry.icon}</>;
}
