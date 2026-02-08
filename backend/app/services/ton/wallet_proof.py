from __future__ import annotations

import base64
import binascii
import hashlib
import struct
from datetime import datetime, timezone
from urllib.parse import urlparse

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.settings import Settings

TON_PROOF_MESSAGE_PREFIX = b"ton-proof-item-v2/"
TON_CONNECT_PREFIX = b"\xff\xffton-connect"
MAX_PROOF_CLOCK_SKEW_SECONDS = 30


class TonProofVerificationError(ValueError):
    pass


def resolve_ton_proof_domain(settings: Settings) -> str:
    manifest_url = settings.TONCONNECT_MANIFEST_URL
    if not manifest_url:
        raise TonProofVerificationError("TONCONNECT_MANIFEST_URL is not configured")

    parsed = urlparse(manifest_url)
    if not parsed.hostname:
        raise TonProofVerificationError("TONCONNECT_MANIFEST_URL must include a hostname")

    return parsed.hostname.lower()


def build_ton_proof_digest(
    *,
    address: str,
    domain_value: str,
    timestamp: int,
    payload: str,
) -> bytes:
    workchain, address_hash = parse_ton_address(address)
    domain_bytes = domain_value.encode("utf-8")
    message = (
        TON_PROOF_MESSAGE_PREFIX
        + struct.pack(">i", workchain)
        + address_hash
        + struct.pack("<I", len(domain_bytes))
        + domain_bytes
        + struct.pack("<Q", timestamp)
        + payload.encode("utf-8")
    )

    message_hash = hashlib.sha256(message).digest()
    return hashlib.sha256(TON_CONNECT_PREFIX + message_hash).digest()


def verify_ton_proof(
    *,
    account_address: str,
    account_public_key: str | None,
    proof_domain_value: str,
    proof_domain_length_bytes: int,
    proof_timestamp: int,
    proof_payload: str,
    proof_signature: str,
    expected_domain: str,
    expected_payload: str,
    max_age_seconds: int,
    now: datetime | None = None,
) -> None:
    if proof_payload != expected_payload:
        raise TonProofVerificationError("Proof payload does not match challenge")

    normalized_domain = proof_domain_value.strip().lower()
    if normalized_domain != expected_domain.strip().lower():
        raise TonProofVerificationError("Proof domain mismatch")

    actual_domain_length = len(proof_domain_value.encode("utf-8"))
    if proof_domain_length_bytes != actual_domain_length:
        raise TonProofVerificationError("Invalid proof domain length")

    current_ts = int((now or datetime.now(timezone.utc)).timestamp())
    if proof_timestamp > current_ts + MAX_PROOF_CLOCK_SKEW_SECONDS:
        raise TonProofVerificationError("Proof timestamp is in the future")
    if current_ts - proof_timestamp > max_age_seconds:
        raise TonProofVerificationError("Proof timestamp is too old")

    signature = _decode_base64(proof_signature)
    if len(signature) != 64:
        raise TonProofVerificationError("Invalid proof signature format")

    public_key_bytes = _decode_public_key(account_public_key)
    digest = build_ton_proof_digest(
        address=account_address,
        domain_value=proof_domain_value,
        timestamp=proof_timestamp,
        payload=proof_payload,
    )

    try:
        verifier = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        verifier.verify(signature, digest)
    except Exception as exc:  # pragma: no cover - maps crypto errors to public API errors.
        raise TonProofVerificationError("Invalid TonConnect proof signature") from exc


def parse_ton_address(value: str) -> tuple[int, bytes]:
    address = value.strip()
    if not address:
        raise TonProofVerificationError("Wallet address is required")

    if ":" in address:
        return _parse_raw_address(address)
    return _parse_friendly_address(address)


def _parse_raw_address(value: str) -> tuple[int, bytes]:
    parts = value.split(":", 1)
    if len(parts) != 2:
        raise TonProofVerificationError("Invalid wallet address format")

    workchain_text, hash_text = parts
    try:
        workchain = int(workchain_text)
    except ValueError as exc:
        raise TonProofVerificationError("Invalid wallet workchain") from exc

    if workchain < -2_147_483_648 or workchain > 2_147_483_647:
        raise TonProofVerificationError("Invalid wallet workchain")

    if len(hash_text) != 64:
        raise TonProofVerificationError("Invalid wallet address hash")

    try:
        address_hash = bytes.fromhex(hash_text)
    except ValueError as exc:
        raise TonProofVerificationError("Invalid wallet address hash") from exc

    return workchain, address_hash


def _parse_friendly_address(value: str) -> tuple[int, bytes]:
    decoded = _decode_base64(value)
    if len(decoded) != 36:
        raise TonProofVerificationError("Invalid friendly wallet address")

    body = decoded[:34]
    checksum = decoded[34:]
    if _crc16_xmodem(body) != checksum:
        raise TonProofVerificationError("Invalid wallet address checksum")

    workchain_byte = body[1]
    workchain = workchain_byte if workchain_byte < 128 else workchain_byte - 256
    address_hash = body[2:34]
    return workchain, address_hash


def _decode_public_key(value: str | None) -> bytes:
    if not value:
        raise TonProofVerificationError("Wallet public key is required")

    normalized = value.strip().lower()
    if normalized.startswith("0x"):
        normalized = normalized[2:]

    if len(normalized) != 64:
        raise TonProofVerificationError("Wallet public key must be 32-byte hex")

    try:
        return bytes.fromhex(normalized)
    except ValueError as exc:
        raise TonProofVerificationError("Wallet public key must be 32-byte hex") from exc


def _decode_base64(value: str) -> bytes:
    normalized = value.strip()
    if not normalized:
        raise TonProofVerificationError("Invalid base64 value")

    padding = "=" * (-len(normalized) % 4)
    candidate = normalized + padding

    try:
        return base64.b64decode(candidate, validate=True)
    except binascii.Error:
        try:
            return base64.urlsafe_b64decode(candidate)
        except binascii.Error as exc:
            raise TonProofVerificationError("Invalid base64 value") from exc


def _crc16_xmodem(data: bytes) -> bytes:
    crc = 0
    for item in data:
        crc ^= item << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc.to_bytes(2, "big")
