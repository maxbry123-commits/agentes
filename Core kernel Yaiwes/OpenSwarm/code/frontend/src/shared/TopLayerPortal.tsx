import React from 'react';
import { createPortal } from 'react-dom';

// A low-z or transformed ancestor traps position:fixed, so anything that must win every stacking fight mounts on body instead.
const TOP_LAYER = 2147483647;

interface Props {
  children: React.ReactNode;
}

const TopLayerPortal: React.FC<Props> = ({ children }) => createPortal(
  <div style={{ position: 'fixed', inset: 0, zIndex: TOP_LAYER }}>{children}</div>,
  document.body,
);

export default TopLayerPortal;
