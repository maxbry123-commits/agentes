"""Mutual TLS (mTLS) certificate management.

Generates and manages CA, server, and client certificates for
secure communication between frontend and backend. Certificates are
stored in the ~/.cognithor/certs/ directory.

Workflow:
  1. ensure_mtls_certs() checks whether certificates exist
  2. If not: generates CA -> Server-Cert -> Client-Cert
  3. Uvicorn runs with ssl_certfile/ssl_keyfile/ssl_ca_certs
  4. Vite proxy uses client cert for requests to the backend
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

log = logging.getLogger(__name__)

_CERT_VALIDITY_DAYS = 3650  # 10 Jahre (lokaler Einsatz)
_KEY_SIZE = 2048


def _generate_key() -> rsa.RSAPrivateKey:
    """Generates an RSA-2048 private key."""
    return rsa.generate_private_key(public_exponent=65537, key_size=_KEY_SIZE)


def _write_key(key: rsa.RSAPrivateKey, path: Path) -> None:
    """Writes a private key as a PEM file."""
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)


def _write_cert(cert: x509.Certificate, path: Path) -> None:
    """Writes a certificate as a PEM file."""
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def generate_ca(certs_dir: Path) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """Generates a self-signed CA certificate.

    Args:
        certs_dir: Directory for ca.pem and ca-key.pem.

    Returns:
        Tuple of (CA Private Key, CA Certificate).
    """
    key = _generate_key()
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Cognithor Local CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Cognithor Root CA"),
        ]
    )

    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=_CERT_VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    _write_key(key, certs_dir / "ca-key.pem")
    _write_cert(cert, certs_dir / "ca.pem")
    log.info("CA certificate generated: %s", certs_dir / "ca.pem")
    return key, cert


def generate_server_cert(
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    certs_dir: Path,
) -> None:
    """Generates a server certificate, signed by the CA.

    Contains SANs for localhost and 127.0.0.1.

    Args:
        ca_key: CA Private Key.
        ca_cert: CA Certificate.
        certs_dir: Directory for server.pem and server-key.pem.
    """
    import ipaddress

    from cryptography.x509 import DNSName, IPAddress

    key = _generate_key()
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Cognithor"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=_CERT_VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    DNSName("localhost"),
                    IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                    IPAddress(ipaddress.IPv6Address("::1")),
                ]
            ),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    _write_key(key, certs_dir / "server-key.pem")
    _write_cert(cert, certs_dir / "server.pem")
    log.info("Server certificate generated: %s", certs_dir / "server.pem")


def generate_client_cert(
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    certs_dir: Path,
) -> None:
    """Generates a client certificate for the frontend, signed by the CA.

    Args:
        ca_key: CA Private Key.
        ca_cert: CA Certificate.
        certs_dir: Directory for client.pem and client-key.pem.
    """
    key = _generate_key()
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Cognithor"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Cognithor Frontend"),
        ]
    )

    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=_CERT_VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    _write_key(key, certs_dir / "client-key.pem")
    _write_cert(cert, certs_dir / "client.pem")
    log.info("Client certificate generated: %s", certs_dir / "client.pem")


def ensure_mtls_certs(config: Any = None) -> Path | None:
    """Ensures mTLS certificates exist. Generates them if needed.

    Args:
        config: CognithorConfig instance. Checks config.security.mtls.enabled.

    Returns:
        Path to the certs directory, or None if mTLS is disabled.
    """
    # Check if mTLS is enabled
    security = getattr(config, "security", None)
    mtls_cfg = getattr(security, "mtls", None)
    if mtls_cfg is None or not getattr(mtls_cfg, "enabled", False):
        return None

    # Determine certificates directory
    certs_dir_str = getattr(mtls_cfg, "certs_dir", "")
    if certs_dir_str:
        certs_dir = Path(certs_dir_str).expanduser().resolve()
    else:
        cognithor_home = getattr(config, "cognithor_home", Path.home() / ".cognithor")
        certs_dir = Path(cognithor_home) / "certs"

    certs_dir.mkdir(parents=True, exist_ok=True)

    # Check if all required files exist
    required_files = [
        "ca.pem",
        "ca-key.pem",
        "server.pem",
        "server-key.pem",
        "client.pem",
        "client-key.pem",
    ]
    all_exist = all((certs_dir / f).exists() for f in required_files)

    if all_exist:
        log.info("mTLS certificates present: %s", certs_dir)
        return certs_dir

    if not getattr(mtls_cfg, "auto_generate", True):
        log.warning("mTLS enabled but certificates missing and auto_generate=False")
        return None

    # Generate all certificates
    log.info("Generating mTLS certificates in %s", certs_dir)
    ca_key, ca_cert = generate_ca(certs_dir)
    generate_server_cert(ca_key, ca_cert, certs_dir)
    generate_client_cert(ca_key, ca_cert, certs_dir)

    log.info("mTLS certificates successfully generated")
    return certs_dir
