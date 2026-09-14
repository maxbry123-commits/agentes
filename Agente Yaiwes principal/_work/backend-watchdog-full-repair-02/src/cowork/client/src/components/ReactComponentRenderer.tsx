import React, { useState, useEffect, useMemo, useRef } from "react";
import * as Recharts from "recharts";

interface Props {
  src: string; // URL to the compiled .jsx.js file
}

// Drop transient cache-bust params ("t") so repeated parent renders with a
// fresh Date.now() don't re-trigger the fetch/compile loop. The file path
// change (adding/removing a .jsx.js) still invalidates this key.
function stableSrcKey(src: string): string {
  try {
    const u = new URL(src, window.location.origin);
    u.searchParams.delete("t");
    return u.pathname + (u.search || "");
  } catch {
    return src.split("&t=")[0].split("?t=")[0];
  }
}

export default function ReactComponentRenderer({ src }: Props) {
  const [Component, setComponent] = useState<React.ComponentType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);
  const srcRef = useRef(src);
  srcRef.current = src;

  const cacheKey = useMemo(() => stableSrcKey(src), [src]);

  useEffect(() => {
    mountedRef.current = true;
    setError(null);
    setComponent(null);

    fetch(srcRef.current)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
        return res.text();
      })
      .then((code) => {
        if (!mountedRef.current) return;

        // Strip the metadata comment line
        const jsCode = code.replace(/^\/\/ __REACT_META__=.*\n/, "");

        // Create a function that receives React and Recharts, returns the component
        const factory = new Function("React", "Recharts", jsCode);
        const Comp = factory(React, Recharts);

        if (Comp) {
          setComponent(() => Comp);
        } else {
          setError("No component returned from compiled code");
        }
      })
      .catch((err) => {
        if (mountedRef.current) setError(err.message);
      });

    return () => {
      mountedRef.current = false;
    };
  }, [cacheKey]);

  if (error) {
    return <div style={{ color: "#e53935", padding: 16, fontFamily: "monospace", whiteSpace: "pre-wrap", fontSize: 13 }}>Error: {error}</div>;
  }

  if (!Component) {
    return <div style={{ padding: 16, color: "#888" }}>Loading component...</div>;
  }

  return (
    <ErrorBoundary>
      <Component />
    </ErrorBoundary>
  );
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { error: string | null }> {
  state = { error: null as string | null };

  static getDerivedStateFromError(err: Error) {
    return { error: err.message };
  }

  render() {
    if (this.state.error) {
      return <div style={{ color: "#e53935", padding: 16, fontFamily: "monospace", whiteSpace: "pre-wrap", fontSize: 13 }}>Runtime error: {this.state.error}</div>;
    }
    return this.props.children;
  }
}
