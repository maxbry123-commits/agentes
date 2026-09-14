import { beforeAll, expect, test } from "bun:test"

function seedRequiredEnv() {
  process.env.DATABASE_URL = process.env.DATABASE_URL ?? "mysql://root:password@127.0.0.1:3306/openwork_test"
  process.env.DEN_DB_ENCRYPTION_KEY = process.env.DEN_DB_ENCRYPTION_KEY ?? "x".repeat(32)
  process.env.BETTER_AUTH_SECRET = process.env.BETTER_AUTH_SECRET ?? "y".repeat(32)
  process.env.BETTER_AUTH_URL = process.env.BETTER_AUTH_URL ?? "http://127.0.0.1:8790"
}

let authProtection: typeof import("../src/auth-protection.js")

beforeAll(async () => {
  seedRequiredEnv()
  authProtection = await import("../src/auth-protection.js")
})

test("email password lockout starts at threshold and resets after the failure window", () => {
  const now = 1_700_000_000_000
  expect(authProtection.getLoginLockoutStatus({
    count: authProtection.LOGIN_LOCKOUT_FAILURE_THRESHOLD - 1,
    lastRequest: now,
  }, now)).toEqual({ locked: false, retryAfterSeconds: 0 })

  expect(authProtection.getLoginLockoutStatus({
    count: authProtection.LOGIN_LOCKOUT_FAILURE_THRESHOLD,
    lastRequest: now,
  }, now)).toEqual({
    locked: true,
    retryAfterSeconds: authProtection.LOGIN_LOCKOUT_BASE_MS / 1000,
  })

  expect(authProtection.getLoginLockoutStatus({
    count: authProtection.LOGIN_LOCKOUT_FAILURE_THRESHOLD,
    lastRequest: now - authProtection.LOGIN_LOCKOUT_FAILURE_WINDOW_MS - 1,
  }, now)).toEqual({ locked: false, retryAfterSeconds: 0 })
})

test("email password lockout duration progresses but is capped", () => {
  expect(authProtection.getLoginLockoutDurationMs(authProtection.LOGIN_LOCKOUT_FAILURE_THRESHOLD)).toBe(authProtection.LOGIN_LOCKOUT_BASE_MS)
  expect(authProtection.getLoginLockoutDurationMs(authProtection.LOGIN_LOCKOUT_FAILURE_THRESHOLD + 1)).toBe(authProtection.LOGIN_LOCKOUT_BASE_MS * 2)
  expect(authProtection.getLoginLockoutDurationMs(authProtection.LOGIN_LOCKOUT_FAILURE_THRESHOLD + 10)).toBe(authProtection.LOGIN_LOCKOUT_MAX_MS)
})

test("email password sign-in parsing normalizes the account identifier", async () => {
  const request = new Request("http://den.local/api/auth/sign-in/email", {
    body: JSON.stringify({ email: " User@Example.COM ", password: "secret" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })

  await expect(authProtection.readEmailSignInAttempt(request)).resolves.toEqual({
    email: "user@example.com",
  })

  const ignored = new Request("http://den.local/api/auth/sign-in/social", {
    method: "POST",
  })
  await expect(authProtection.readEmailSignInAttempt(ignored)).resolves.toBeNull()
})

test("breached password screening reads password fields only on password creation routes", async () => {
  const signUp = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "created-password" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  await expect(authProtection.readPasswordForBreachCheck(signUp)).resolves.toBe("created-password")

  const reset = new Request("http://den.local/api/auth/reset-password", {
    body: JSON.stringify({ newPassword: "reset-password" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  await expect(authProtection.readPasswordForBreachCheck(reset)).resolves.toBe("reset-password")

  const signIn = new Request("http://den.local/api/auth/sign-in/email", {
    body: JSON.stringify({ email: "user@example.com", password: "existing-password" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  await expect(authProtection.readPasswordForBreachCheck(signIn)).resolves.toBeNull()
})

test("breached password screening uses k-anonymity range responses", async () => {
  let requestedUrl = ""
  const compromised = await authProtection.isPasswordCompromised("password", async (input) => {
    requestedUrl = input
    return new Response("1E4C9B93F3F0682250B6CF8331B7EE68FD8:3303003\n", { status: 200 })
  })

  expect(requestedUrl).toBe("https://api.pwnedpasswords.com/range/5BAA6")
  expect(compromised).toBe(true)

  await expect(authProtection.isPasswordCompromised("password", async () => new Response("00000000000000000000000000000000000:1\n", { status: 200 }))).resolves.toBe(false)
})

test("breached password response blocks compromised passwords and fails closed on screening errors", async () => {
  const request = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "password" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })

  const blocked = await authProtection.getBreachedPasswordResponse(
    request,
    async () => new Response("1E4C9B93F3F0682250B6CF8331B7EE68FD8:3303003\n", { status: 200 }),
  )
  expect(blocked?.status).toBe(400)
  await expect(blocked?.json()).resolves.toEqual({
    error: "password_compromised",
    message: "This password appeared in a data breach. Choose a different one.",
  })

  const unavailable = await authProtection.getBreachedPasswordResponse(
    request,
    async () => new Response("", { status: 503 }),
  )
  expect(unavailable?.status).toBe(503)
  await expect(unavailable?.json()).resolves.toEqual({
    error: "password_screening_unavailable",
    message: "Something went wrong. Please try again in a moment.",
  })
})

test("password policy response rejects passwords that miss mandatory requirements on creation routes", async () => {
  const tooShort = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "Aa1!" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const rejected = await authProtection.getPasswordPolicyResponse(tooShort)
  expect(rejected?.status).toBe(400)
  await expect(rejected?.json()).resolves.toEqual({
    error: "password_too_short",
    message: `Password must be at least ${authProtection.MIN_PASSWORD_LENGTH} characters.`,
  })

  const tooLong = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: `Aa1!${"x".repeat(authProtection.MAX_PASSWORD_LENGTH - 3)}` }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const overLimit = await authProtection.getPasswordPolicyResponse(tooLong)
  expect(overLimit?.status).toBe(400)
  await expect(overLimit?.json()).resolves.toEqual({
    error: "password_too_long",
    message: `Password must be at most ${authProtection.MAX_PASSWORD_LENGTH} characters.`,
  })

  const missingUppercase = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "lowercase1!" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const noUppercase = await authProtection.getPasswordPolicyResponse(missingUppercase)
  expect(noUppercase?.status).toBe(400)
  await expect(noUppercase?.json()).resolves.toEqual({
    error: "password_missing_uppercase",
    message: "Password must include at least one uppercase letter.",
  })

  const missingLowercase = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "UPPERCASE1!" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const noLowercase = await authProtection.getPasswordPolicyResponse(missingLowercase)
  expect(noLowercase?.status).toBe(400)
  await expect(noLowercase?.json()).resolves.toEqual({
    error: "password_missing_lowercase",
    message: "Password must include at least one lowercase letter.",
  })

  const missingSpecialCharacter = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "Password1" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const noSpecialCharacter = await authProtection.getPasswordPolicyResponse(missingSpecialCharacter)
  expect(noSpecialCharacter?.status).toBe(400)
  await expect(noSpecialCharacter?.json()).resolves.toEqual({
    error: "password_missing_special_character",
    message: "Password must include at least one special character.",
  })

  const missingDigit = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "Password!" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const noDigit = await authProtection.getPasswordPolicyResponse(missingDigit)
  expect(noDigit?.status).toBe(400)
  await expect(noDigit?.json()).resolves.toEqual({
    error: "password_missing_digit",
    message: "Password must include at least one digit.",
  })

  const validSignup = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "ValidPass1!" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  await expect(authProtection.getPasswordPolicyResponse(validSignup)).resolves.toBeNull()

  const validChange = new Request("http://den.local/api/auth/change-password", {
    body: JSON.stringify({ newPassword: "ChangedPass1!" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  await expect(authProtection.getPasswordPolicyResponse(validChange)).resolves.toBeNull()

  const invalidChange = new Request("http://den.local/api/auth/change-password", {
    body: JSON.stringify({ newPassword: "ChangedPass!" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const rejectedChange = await authProtection.getPasswordPolicyResponse(invalidChange)
  expect(rejectedChange?.status).toBe(400)
  await expect(rejectedChange?.json()).resolves.toMatchObject({
    error: "password_missing_digit",
  })

  const signIn = new Request("http://den.local/api/auth/sign-in/email", {
    body: JSON.stringify({ email: "user@example.com", password: "x" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  await expect(authProtection.getPasswordPolicyResponse(signIn)).resolves.toBeNull()
})

test("weak password response rejects low-strength signup passwords with feedback", async () => {
  const weak = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", name: "Example User", password: "aaaaaaaa" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const rejected = await authProtection.getWeakPasswordResponse(weak)
  expect(rejected?.status).toBe(400)
  await expect(rejected?.json()).resolves.toMatchObject({
    error: "password_too_weak",
    message: "Repeated characters like \"aaa\" are easy to guess.",
    feedback: {
      warning: "Repeated characters like \"aaa\" are easy to guess.",
      suggestions: [
        "Add more words that are less common.",
        "Avoid repeated words and characters.",
      ],
    },
  })

  const commonPattern = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", name: "Example User", password: "Password1*" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  const predictable = await authProtection.getWeakPasswordResponse(commonPattern)
  expect(predictable?.status).toBe(400)
  await expect(predictable?.json()).resolves.toMatchObject({
    error: "password_too_weak",
    message: "This is similar to a commonly used password.",
    feedback: {
      warning: "This is similar to a commonly used password.",
      suggestions: [
        "Add more words that are less common.",
        "Capitalize more than the first letter.",
      ],
    },
  })

  const strong = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", name: "Example User", password: "correct horse battery staple" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  await expect(authProtection.getWeakPasswordResponse(strong)).resolves.toBeNull()

  const signIn = new Request("http://den.local/api/auth/sign-in/email", {
    body: JSON.stringify({ email: "user@example.com", password: "aaaaaaaa" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  await expect(authProtection.getWeakPasswordResponse(signIn)).resolves.toBeNull()
})

test("breached password response can skip screening for isolated deployments", async () => {
  const request = new Request("http://den.local/api/auth/sign-up/email", {
    body: JSON.stringify({ email: "user@example.com", password: "password" }),
    headers: { "content-type": "application/json" },
    method: "POST",
  })
  let fetchCount = 0

  const response = await authProtection.getBreachedPasswordResponse(
    request,
    async () => {
      fetchCount += 1
      return new Response("1E4C9B93F3F0682250B6CF8331B7EE68FD8:3303003\n", { status: 200 })
    },
    false,
  )

  expect(response).toBeNull()
  expect(fetchCount).toBe(0)
})
