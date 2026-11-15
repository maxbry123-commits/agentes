"""Inject the published-app runtime API into served HTML.

A published app talks only to its own origin. This shim wires the two capabilities
the edge hosts cheaply, same-origin, so an app's JS can use them without knowing
about Tigris, the cloud, or budgets:

  window.OUTPUT_COMPUTE(input)  -> runs the app's sandboxed backend.py (/__compute),
                                   resolves to its `result` dict.
  window.OUTPUT_LLM(body)       -> a metered Claude call (/__llm), resolves to the
                                   raw fetch Response (stream it, or await .json()).

The shape matches the desktop's _build_data_injection so an app written once works
in the App Builder preview AND when published. We do NOT precompute results here
(a published page has many visitors with different inputs); the app drives compute
itself via OUTPUT_COMPUTE."""
from __future__ import annotations

_RUNTIME_SHIM = """<script>
(function () {
  window.OUTPUT_BACKEND_URL = "";
  window.OUTPUT_INPUT = window.OUTPUT_INPUT || {};
  window.OUTPUT_BACKEND_RESULT = window.OUTPUT_BACKEND_RESULT || null;
  window.OUTPUT_COMPUTE = async function (input) {
    var r = await fetch("/__compute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input_data: input || {} }),
    });
    var d = await r.json().catch(function () { return {}; });
    if (!r.ok) throw new Error(d && d.error ? d.error : "compute failed");
    return d.result;
  };
  window.OUTPUT_LLM = async function (body) {
    return fetch("/__llm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  };
})();
</script>"""


def inject_runtime(html: bytes) -> bytes:
    """Insert the runtime shim into an HTML document (before </head>, else before
    <body>, else prepend). Returns bytes so callers can serve it directly."""
    try:
        text = html.decode("utf-8")
    except UnicodeDecodeError:
        return html  # not text we can safely rewrite; serve as-is
    if "</head>" in text:
        out = text.replace("</head>", _RUNTIME_SHIM + "\n</head>", 1)
    elif "<body" in text:
        out = text.replace("<body", _RUNTIME_SHIM + "\n<body", 1)
    else:
        out = _RUNTIME_SHIM + "\n" + text
    return out.encode("utf-8")
