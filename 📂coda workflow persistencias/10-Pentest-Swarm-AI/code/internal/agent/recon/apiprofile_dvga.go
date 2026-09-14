package recon

import "github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"

// dvgaProfile is the API surface of DVGA (Damn Vulnerable GraphQL
// Application), dolevf's intentionally-vulnerable GraphQL API. Unlike a REST
// target, DVGA's entire attack surface sits behind a single POST /graphql
// endpoint — there is no set of distinct paths to enumerate — so the value
// this profile adds is entirely in the Notes: they describe DVGA's
// well-documented planted flaws (introspection, injection in resolver
// arguments, batching/alias-based DoS, and OS command injection in specific
// mutations) so the exploit planner can build real GraphQL attack payloads
// instead of guessing at the schema.
//
// This profile has not been exercised against a live DVGA instance, so no
// chains are included and no exact response shapes are claimed — only the
// endpoint pack with attack-hint notes, describing behavior that is part of
// DVGA's public, documented design (it is deliberately shipped this way as a
// training target) rather than something verified here.
var dvgaProfile = apiProfile{
	name: "dvga",
	// Signature routes: DVGA serves its GraphQL endpoint at /graphql (answers
	// GraphQL requests, so a malformed/empty query returns 400, not 404) and
	// ships the GraphiQL IDE at /graphiql — both exist on DVGA and 404
	// elsewhere.
	signatures: []signatureRoute{
		{method: "POST", path: "/graphql"},
		{method: "GET", path: "/graphiql"},
	},
	build: func(base string) []pipeline.EndpointRecord {
		return []pipeline.EndpointRecord{
			{
				URL:         base + "/graphql",
				Method:      "POST",
				Interesting: true,
				Notes: "DVGA's single GraphQL endpoint. It is deliberately configured with introspection " +
					"ENABLED, so the first move is a standard introspection query (query IntrospectionQuery " +
					"{ __schema { types { name fields { name args { name } } } } }) to dump the full schema — " +
					"every type, field, and mutation name — without any prior knowledge of the API. Use the " +
					"dumped schema to enumerate DVGA's known-vulnerable operations rather than guessing field " +
					"names blind.\n\n" +
					"DVGA ships a documented set of resolvers with planted flaws, in particular a " +
					"pastes/paste family of mutations and queries: createPaste (or similar; confirm exact " +
					"name from introspection) accepts paste content and a \"public\"/burn flag; the " +
					"underlying implementation has been documented to shell out for certain operations, so " +
					"OS COMMAND INJECTION has been demonstrated via crafted input to the paste-processing " +
					"path (classically through a field that gets passed to a system call, e.g. an import-from-" +
					"URL or similar convenience feature) — the exploit chain is: introspect to find the exact " +
					"field, then submit a paste whose value is a shell metacharacter payload (e.g. " +
					"`$(id)` / `; id;` style) and look for command output reflected in the response or a " +
					"time-based delay as a blind fallback.\n\n" +
					"SQL INJECTION has similarly been documented in a search/filter-style query argument " +
					"(e.g. filtering pastes by owner or content) where the argument is concatenated into a " +
					"backing SQL query without sanitisation — probe any string-typed query argument found via " +
					"introspection with standard SQLi payloads (' OR '1'='1, UNION-based probes) and compare " +
					"result-set size/error text against a benign baseline.\n\n" +
					"DENIAL OF SERVICE via GraphQL-specific abuse: (1) query batching — GraphQL allows an " +
					"array of operations in one HTTP request; sending a large batch multiplies backend work " +
					"per request. (2) query aliasing — repeating the same field many times under different " +
					"aliases in one query forces the resolver to run once per alias, which can be combined " +
					"with (3) deeply nested queries (recursive/circular type relationships) to amplify cost " +
					"exponentially. All three are classic GraphQL resource-exhaustion vectors DVGA is built to " +
					"demonstrate; a sharply increased response time or a 5xx/timeout under an aliased or " +
					"deeply nested query (versus a flat baseline query) is the signal, not a guaranteed proof " +
					"— confirm impact conservatively rather than assuming a crash.\n\n" +
					"BROKEN ACCESS CONTROL: some mutations (the app's own admin/debug-style operations, e.g. " +
					"an operation resembling systemUpdate or similar server-management mutation surfaced by " +
					"introspection) are reachable without any authentication token at all, which is itself " +
					"the finding — enumerate mutations from the schema and probe each unauthenticated before " +
					"assuming an auth boundary exists.\n\n" +
					"Recommended order for the planner: (1) introspection dump, (2) enumerate mutations/" +
					"queries and their arg types from the dumped schema, (3) probe each string argument for " +
					"SQLi, (4) probe paste/import-style mutations for command injection, (5) test batching/" +
					"alias/nesting for DoS, (6) call sensitive-looking mutations unauthenticated to check " +
					"access control. Confirm exact field/mutation/argument names against the live schema " +
					"before building a payload — do not hardcode names not seen in the introspection result.",
			},
			{
				URL:    base + "/graphiql",
				Method: "GET",
				Notes: "The GraphiQL IDE is exposed (should not be, in a hardened deployment). It provides " +
					"an interactive schema explorer and autocompletion driven by the same introspection data " +
					"as above — a convenient way to browse the schema by hand before scripting the automated " +
					"probes against /graphql.",
			},
		}
	},
	// No chains: DVGA's attack surface is a single dynamic GraphQL endpoint
	// whose exact schema (mutation/field names, argument shapes) is only
	// known after introspecting a live instance, and this profile has not
	// been run against one. A hardcoded step-by-step chain here would have to
	// guess field names, which risks fabricating behavior that doesn't match
	// the deployed schema version. The Notes above give the planner the
	// documented attack classes and a safe order of operations to build a
	// real chain from the introspected schema instead.
	chains: nil,
}
