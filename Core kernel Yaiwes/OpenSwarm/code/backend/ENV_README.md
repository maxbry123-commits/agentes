# Environment Variables Setup Guide

Copy `.env.example` to `.env` and fill in the values below. This guide walks you through getting every single one.

```bash
cp .env.example .env
```

---

## `BACKEND_PORT`

The port the backend server runs on. The default is fine — only change it if something else is already using port 8324.

```
BACKEND_PORT=8324
```

---

## `GOOGLE_OAUTH_CLIENT_ID` & `GOOGLE_OAUTH_CLIENT_SECRET`

These let users sign in with their Google account.

### Step 1 — Go to Google Cloud Console

1. Open https://console.cloud.google.com/
2. Sign in with your Google account (or create one).

### Step 2 — Create a project

1. Click the project dropdown at the very top of the page (it says "Select a project" or shows your current project name).
2. Click **New Project** in the top-right of the popup.
3. Name it something like `OpenSwarm`.
4. Click **Create**.
5. Wait a few seconds, then click the project dropdown again and select your new `OpenSwarm` project.

### Step 3 — Enable the Google+ API (required for OAuth)

1. In the left sidebar, click **APIs & Services** > **Library**.
2. Search for `Google+ API` (or `Google Identity`).
3. Click on it, then click **Enable**.

### Step 4 — Configure the OAuth consent screen

1. In the left sidebar, click **APIs & Services** > **OAuth consent screen**.
2. Select **External** (unless you're inside a Google Workspace org and only want internal users).
3. Click **Create**.
4. Fill in the required fields:
   - **App name**: `OpenSwarm`
   - **User support email**: your email
   - **Developer contact email**: your email
5. Click **Save and Continue**.
6. On the **Scopes** page, click **Add or Remove Scopes**.
   - Check `email` and `profile` (the `openid` scope is added automatically).
   - Click **Update**, then **Save and Continue**.
7. On the **Test users** page, click **Add Users**, enter your own email, click **Add**, then **Save and Continue**.
8. Click **Back to Dashboard**.

### Step 5 — Create OAuth credentials

1. In the left sidebar, click **APIs & Services** > **Credentials**.
2. Click **+ Create Credentials** at the top.
3. Select **OAuth client ID**.
4. For **Application type**, select **Web application**.
5. **Name**: `OpenSwarm` (or anything you want).
6. Under **Authorized redirect URIs**, click **+ Add URI** and add:
   ```
   http://localhost:8324/api/auth/google/callback
   ```
   (Replace `8324` with your `BACKEND_PORT` if you changed it.)
7. Click **Create**.

### Step 6 — Copy the values

A popup appears with your credentials:

- **Client ID** — copy this into `GOOGLE_OAUTH_CLIENT_ID`
- **Client Secret** — copy this into `GOOGLE_OAUTH_CLIENT_SECRET`

```
GOOGLE_OAUTH_CLIENT_ID=123456789-xxxxxxxxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxx
```

---

## `APPLE_ID`

This is the email address you use to sign in to your Apple Developer account.

1. If you don't have one, go to https://developer.apple.com/programs/ and click **Enroll**. It costs $99/year.
2. Once enrolled, your `APPLE_ID` is just the email you signed up with.

```
APPLE_ID=you@example.com
```

---

## `APPLE_TEAM_ID`

Your 10-character Apple Developer team identifier.

1. Go to https://developer.apple.com/account
2. Sign in.
3. Look at the top-right — your name is shown. Click it, or scroll down.
4. Under **Membership Details** (or at https://developer.apple.com/account#MembershipDetailsCard), you'll see **Team ID**.
5. It looks like `ABCDE12345`. Copy it.

```
APPLE_TEAM_ID=ABCDE12345
```

---

## `APPLE_APP_SPECIFIC_PASSWORD`

Apple doesn't let you use your regular password for automated tools. You need to generate a special one-time password.

### Step 1 — Turn on two-factor authentication (if you haven't already)

1. On your Mac, go to **System Settings** > **[your name]** > **Sign-In & Security** > **Two-Factor Authentication**.
2. Turn it on and follow the prompts.

### Step 2 — Generate the app-specific password

1. Go to https://account.apple.com/
2. Sign in with your Apple ID.
3. In the **Sign-In and Security** section, click **App-Specific Passwords**.
4. Click **Generate an app-specific password** (or the **+** button).
5. Enter a label like `OpenSwarm Notarization`.
6. Click **Create**.
7. Apple shows you a password in the format `xxxx-xxxx-xxxx-xxxx`. **Copy it now** — you can't see it again.

```
APPLE_APP_SPECIFIC_PASSWORD=abcd-efgh-ijkl-mnop
```

---

## macOS Signing Certificate (no env var, but required)

Before you can sign and notarize, you need a **Developer ID Application** certificate installed in your macOS Keychain. This is what Apple uses to verify that the app was built by you.

### Step 1 — Open Xcode

1. Open **Xcode** on your Mac (install it from the Mac App Store if you don't have it).
2. Go to **Xcode** menu > **Settings** (or **Preferences** on older versions).
3. Click the **Accounts** tab.
4. Click **+** in the bottom-left and sign in with your Apple ID.

### Step 2 — Create the certificate

1. Select your account in the list, then click **Manage Certificates...** in the bottom-right.
2. Click the **+** in the bottom-left of the popup.
3. Select **Developer ID Application**.
4. Click **Create**.

That's it — the certificate is now in your macOS Keychain. `electron-builder` will auto-discover it during builds. You don't need to set any env var for this.

### Alternative — manual method (without Xcode)

1. Go to https://developer.apple.com/account/resources/certificates/list
2. Click the **+** button.
3. Select **Developer ID Application**, click **Continue**.
4. You'll be asked to upload a **Certificate Signing Request (CSR)**:
   - Open **Keychain Access** on your Mac.
   - In the menu bar: **Keychain Access** > **Certificate Assistant** > **Request a Certificate From a Certificate Authority**.
   - Enter your email, leave CA Email blank, select **Saved to disk**, click **Continue**.
   - Save the `.certSigningRequest` file.
5. Upload that file on the Apple Developer page, click **Continue**.
6. Download the `.cer` file.
7. Double-click it — it installs into your Keychain.

---

## `GH_TOKEN`

A GitHub Personal Access Token that lets the build script upload release artifacts to GitHub Releases.

### Step 1 — Go to GitHub token settings

1. Go to https://github.com/settings/tokens
2. Sign in if needed.

### Step 2 — Create a token

1. Click **Generate new token** > **Generate new token (classic)**.
2. **Note**: `OpenSwarm Releases` (or whatever you want).
3. **Expiration**: pick a duration (90 days, or "No expiration" if you don't want to rotate it).
4. **Scopes**: check the **`repo`** checkbox (this gives full access to your repositories, which is needed to create releases and upload assets).
5. Click **Generate token** at the bottom.
6. **Copy the token now** — it starts with `ghp_` and you won't be able to see it again.

```
GH_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Final `.env` example

```
BACKEND_PORT=8324

GOOGLE_OAUTH_CLIENT_ID=123456789-xxxxxxxxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxx

APPLE_ID=you@example.com
APPLE_APP_SPECIFIC_PASSWORD=abcd-efgh-ijkl-mnop
APPLE_TEAM_ID=ABCDE12345

GH_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Running a production build

Once your `.env` is filled in, just run:

```bash
./scripts/build-app.sh --publish
```

The build script automatically loads `backend/.env`, so you don't need to source it yourself. This will build the app, sign it with your certificate, notarize it with Apple, and upload the `.dmg` and `.zip` to a GitHub Release.
