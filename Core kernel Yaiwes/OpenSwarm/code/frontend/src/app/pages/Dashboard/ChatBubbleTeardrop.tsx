import React from 'react';

// Custom near-circular speech bubble with a teardrop tail at the bottom-left. The bubble body is a rounded square with corner radius ~half the body size, so it reads as a circle. Matches Image #57; MUI rounded chat glyphs either fill the bubble or omit the tail.
export default function ChatBubbleTeardrop(props: { sx?: { fontSize?: number } }) {
  const size = props.sx?.fontSize ?? 18;
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth={2}
      strokeLinecap="round" strokeLinejoin="round"
      style={{ display: 'block' }}
    >
      <path d="M 8 3 H 16 A 5 5 0 0 1 21 8 V 13 A 5 5 0 0 1 16 18 H 11 L 6 22 L 8 18 A 5 5 0 0 1 3 13 V 8 A 5 5 0 0 1 8 3 Z" />
    </svg>
  );
}
