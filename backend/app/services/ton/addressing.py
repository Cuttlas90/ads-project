from __future__ import annotations

from app.services.ton.wallet_proof import TonProofVerificationError, parse_ton_address


def to_raw_address(address: str) -> str:
    workchain, address_hash = parse_ton_address(address)
    return f"{workchain}:{address_hash.hex()}"


def try_to_raw_address(address: str | None) -> str | None:
    if address is None:
        return None
    candidate = address.strip()
    if not candidate:
        return None
    try:
        return to_raw_address(candidate)
    except TonProofVerificationError:
        return None
