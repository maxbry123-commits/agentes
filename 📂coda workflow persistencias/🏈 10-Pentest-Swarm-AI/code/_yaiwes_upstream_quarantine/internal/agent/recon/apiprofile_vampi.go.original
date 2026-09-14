package recon

import "github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"

// vampiProfile is the API surface of VAmPI (erev0s' Vulnerable API), a small
// Flask REST API purpose-built to demonstrate the OWASP API Security Top 10.
// It has no crawlable front end — every route is a bare JSON endpoint — so
// without this profile the exploit agent never sees the surface where VAmPI's
// planted flaws (BOLA, mass assignment, excessive data exposure, broken
// authentication) live.
//
// Routes and body shapes below come from VAmPI's published API (its own
// /createdb bootstrap route and documented users/v1 and books/v1 surface).
// Notes are written for the exploit planner: concrete body shapes for
// register/login so it can build a real httpreq chain rather than guessing.
// No chains are included here — this profile has not been verified against a
// live instance, so only the endpoint pack (with attack-hint notes) is
// provided; leave chain construction to the planner.
var vampiProfile = apiProfile{
	name: "vampi",
	// Signature routes: VAmPI mounts / (a landing/index route with version
	// info) and /users/v1 (list users) at the app root — both exist (non-404)
	// on VAmPI and 404 on an unrelated target.
	signatures: []signatureRoute{
		{method: "GET", path: "/"},
		{method: "GET", path: "/users/v1"},
	},
	build: func(base string) []pipeline.EndpointRecord {
		return []pipeline.EndpointRecord{
			{
				URL:    base + "/createdb",
				Method: "GET",
				Notes: "Resets/recreates VAmPI's SQLite database to its seeded initial state (a handful of " +
					"users and books). Useful to restore a known-good starting point before an attack run; not " +
					"itself a vulnerability, but it is unauthenticated infrastructure that a real API should " +
					"never expose.",
			},
			{
				URL:         base + "/users/v1",
				Method:      "GET",
				Interesting: true,
				Notes: "EXCESSIVE DATA EXPOSURE: unauthenticated GET returns the full list of registered " +
					"users. Depending on version this may already include sensitive fields (email, admin flag); " +
					"compare against /users/v1/_debug below, which is the confirmed full-field dump.",
			},
			{
				URL:         base + "/users/v1/_debug",
				Method:      "GET",
				Interesting: true,
				Notes: "EXCESSIVE DATA EXPOSURE (flagship). Unauthenticated GET dumps every user record " +
					"including plaintext/hashed passwords and emails — a debug route left enabled in " +
					"production. A 200 response containing a \"password\" field for users other than the " +
					"caller's own proves the finding. No authentication required to reach it.",
			},
			{
				URL:    base + "/users/v1/register",
				Method: "POST",
				Notes: "Registration. Body (JSON): " +
					`{"username":"atk_{{nonce}}","password":"Attacker@123","email":"atk_{{nonce}}@example.com"}. ` +
					"MASS ASSIGNMENT: VAmPI's register handler accepts extra client-supplied fields beyond the " +
					"documented three and persists them verbatim — repeat the request with an added " +
					`"admin":true field (e.g. {"username":"atk2_{{nonce}}","password":"Attacker@123",` +
					`"email":"atk2_{{nonce}}@example.com","admin":true}) and then confirm via login + ` +
					"/users/v1/{username} (or /users/v1/_debug) that the created account carries admin " +
					"privilege it was never granted through the UI/business logic. Use {{nonce}} to keep the " +
					"username/email unique across runs.",
			},
			{
				URL:    base + "/users/v1/login",
				Method: "POST",
				Notes: "Login. Body (JSON): " +
					`{"username":"atk_{{nonce}}","password":"Attacker@123"}. ` +
					"On success the response carries a JWT (commonly under an \"auth_token\" field) — capture " +
					"it with --capture jwt=$.auth_token and send it on later requests as " +
					"--header 'Authorization: Bearer {{jwt}}'. Confirm the exact field name from a live " +
					"response before wiring the capture path, since VAmPI's response shape has drifted across " +
					"releases.",
			},
			{
				URL:         base + "/users/v1/{{victim_username}}",
				Method:      "GET",
				Interesting: true,
				Parameters:  []string{"username"},
				Notes: "BOLA/BFLA: fetch another user's profile by username with the attacker's own token " +
					"(Authorization: Bearer {{jwt}}). VAmPI's ownership check on this route is missing/weak, " +
					"so a 200 returning a victim's own record (not the caller's) proves broken object-level " +
					"authorization. Harvest a candidate {{victim_username}} from /users/v1 or /users/v1/_debug " +
					"first.",
			},
			{
				URL:        base + "/users/v1/{{victim_username}}",
				Method:     "DELETE",
				Parameters: []string{"username"},
				Notes: "BFLA: delete another user's account with the attacker's own token (Authorization: " +
					"Bearer {{jwt}}). A 200/204 deleting a user other than the caller proves broken " +
					"function-level authorization — an ordinary user can destroy other accounts. Destructive: " +
					"run against a throwaway victim account created for the test, and re-run /createdb " +
					"afterward to restore state.",
			},
			{
				URL:        base + "/users/v1/{{victim_username}}/password",
				Method:     "PUT",
				Parameters: []string{"username"},
				Notes: "UNAUTHORIZED WRITE (BFLA): change another user's password with the attacker's own " +
					"token. Body (JSON): {\"password\":\"Pwned@123\"}. A 200 response — followed by a " +
					"successful login as the victim with the new password — proves the attacker fully " +
					"took over an account they never owned.",
			},
			{
				URL:        base + "/users/v1/{{victim_username}}/email",
				Method:     "PUT",
				Parameters: []string{"username"},
				Notes: "UNAUTHORIZED WRITE (BFLA): change another user's email with the attacker's own " +
					`token. Body (JSON): {"email":"pwned_{{nonce}}@example.com"}. A 200 response proves the ` +
					"attacker can silently redirect a victim's account-recovery flow.",
			},
			{
				URL:    base + "/books/v1",
				Method: "GET",
				Notes: "Authenticated GET (Authorization: Bearer {{jwt}}) — lists books, each tied to an " +
					"owning user. Harvest a book {{title}} belonging to another user here to drive the BOLA " +
					"read below.",
			},
			{
				URL:         base + "/books/v1/{{victim_book_title}}",
				Method:      "GET",
				Interesting: true,
				Parameters:  []string{"title"},
				Notes: "BOLA: read another user's book (and, depending on version, an attached secret " +
					"field) by title, using the attacker's own token (Authorization: Bearer {{jwt}}). A 200 " +
					"returning a book owned by someone other than the caller proves the object-level " +
					"authorization is missing on this route too — the same class of flaw as the users/v1 " +
					"BOLA above, on a second resource type.",
			},
		}
	},
	// No chains: this profile has not been exercised against a live VAmPI
	// instance, so exact response shapes (JWT field name, book secret field,
	// _debug schema) are not confirmed. The endpoint notes above give the
	// exploit planner everything needed to build the register -> login ->
	// harvest -> cross-user-read/write chains itself.
	chains: nil,
}
