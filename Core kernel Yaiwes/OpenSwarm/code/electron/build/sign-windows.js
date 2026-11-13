// Custom Windows signing hook for electron-builder.
// Uses Azure Trusted Signing via signtool + Microsoft.Trusted.Signing.Client dlib.
//
// Required env vars (set as GitHub Actions secrets and passed through to the job):
//   AZURE_TENANT_ID                  Directory (tenant) ID of the app registration
//   AZURE_CLIENT_ID                  Application (client) ID of the app registration
//   AZURE_CLIENT_SECRET              Client secret value
//   AZURE_SIGNING_ENDPOINT           e.g. https://eus.codesigning.azure.net
//   AZURE_SIGNING_ACCOUNT            Trusted Signing account name (e.g. mist-code-signing)
//   AZURE_SIGNING_CERT_PROFILE       Certificate profile name (created inside the account)
//
// Optional env vars:
//   AZURE_SIGNING_DLIB               Absolute path to Azure.CodeSigning.Dlib.dll (default: resolved from AZURE_SIGNING_DLIB_DIR)
//   AZURE_SIGNING_DLIB_DIR           Directory containing Azure.CodeSigning.Dlib.dll (default: ./Microsoft.Trusted.Signing.Client/bin/x64)
//   SIGNTOOL_PATH                    Absolute path to signtool.exe (default: "signtool", relying on PATH)
//   AZURE_TIMESTAMP_URL              Timestamp server (default: http://timestamp.acs.microsoft.com)
//   CSC_IDENTITY_AUTO_DISCOVERY      Set to "false" to skip signing entirely (dev builds)

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const REQUIRED_ENV = [
  'AZURE_TENANT_ID',
  'AZURE_CLIENT_ID',
  'AZURE_CLIENT_SECRET',
  'AZURE_SIGNING_ENDPOINT',
  'AZURE_SIGNING_ACCOUNT',
  'AZURE_SIGNING_CERT_PROFILE',
];

function resolveDlib() {
  if (process.env.AZURE_SIGNING_DLIB) return process.env.AZURE_SIGNING_DLIB;
  const dir = process.env.AZURE_SIGNING_DLIB_DIR
    || path.join(process.cwd(), 'Microsoft.Trusted.Signing.Client', 'bin', 'x64');
  return path.join(dir, 'Azure.CodeSigning.Dlib.dll');
}

exports.default = async function signWindows(configuration) {
  const targetPath = configuration && configuration.path;
  if (!targetPath) {
    console.log('[sign-windows] No target path provided — skipping');
    return;
  }

  if (process.env.CSC_IDENTITY_AUTO_DISCOVERY === 'false') {
    console.log(`[sign-windows] CSC_IDENTITY_AUTO_DISCOVERY=false — skipping ${targetPath}`);
    return;
  }

  const missing = REQUIRED_ENV.filter((k) => !process.env[k]);
  if (missing.length) {
    console.log(`[sign-windows] Skipping ${targetPath} — missing env: ${missing.join(', ')}`);
    return;
  }

  const dlib = resolveDlib();
  if (!fs.existsSync(dlib)) {
    throw new Error(
      `[sign-windows] Azure.CodeSigning.Dlib.dll not found at ${dlib}. `
      + `Install the Microsoft.Trusted.Signing.Client NuGet package or set AZURE_SIGNING_DLIB.`,
    );
  }

  const metadata = {
    Endpoint: process.env.AZURE_SIGNING_ENDPOINT,
    CodeSigningAccountName: process.env.AZURE_SIGNING_ACCOUNT,
    CertificateProfileName: process.env.AZURE_SIGNING_CERT_PROFILE,
    ExcludeEnvironmentCredential: 'false',
  };
  const metadataPath = path.join(os.tmpdir(), `ts-metadata-${process.pid}-${Date.now()}.json`);
  fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2));

  const signtool = process.env.SIGNTOOL_PATH || 'signtool.exe';
  const timestampUrl = process.env.AZURE_TIMESTAMP_URL || 'http://timestamp.acs.microsoft.com';
  const args = [
    'sign',
    '/v',
    '/fd', 'SHA256',
    '/tr', timestampUrl,
    '/td', 'SHA256',
    '/dlib', dlib,
    '/dmdf', metadataPath,
    targetPath,
  ];

  try {
    console.log(`[sign-windows] signtool ${args.join(' ')}`);
    execFileSync(signtool, args, { stdio: 'inherit' });
    console.log(`[sign-windows] Signed ${targetPath}`);
  } finally {
    try { fs.unlinkSync(metadataPath); } catch (_) { /* ignore */ }
  }
};
