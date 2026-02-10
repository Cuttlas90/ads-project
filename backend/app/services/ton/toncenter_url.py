from __future__ import annotations

import re

_JSONRPC_SUFFIX = re.compile(r"/jsonrpc/?$", re.IGNORECASE)
_API_V3_SUFFIX = re.compile(r"/api/v3/?$", re.IGNORECASE)


def _strip_known_suffixes(url: str) -> str:
    value = url.strip().rstrip("/")
    value = _JSONRPC_SUFFIX.sub("", value)
    return value


def normalize_toncenter_v3_base_url(url: str) -> str:
    """
    Normalize TONCENTER_API for direct V3 REST calls.

    Examples:
    - https://testnet.toncenter.com -> https://testnet.toncenter.com/api/v3
    - https://testnet.toncenter.com/api/v3 -> unchanged
    - https://testnet.toncenter.com/api/v3/jsonRPC -> /jsonRPC removed
    """
    value = _strip_known_suffixes(url)
    if not _API_V3_SUFFIX.search(value):
        value = f"{value}/api/v3"
    return value


def normalize_toncenter_tonutils_base_url(url: str) -> str:
    """
    Normalize TONCENTER_API for tonutils ToncenterV3Client.

    tonutils appends `/api/v3` internally, so inputs ending with `/api/v3`
    (or `/api/v3/jsonRPC`) must be reduced to provider host root.
    """
    value = _strip_known_suffixes(url)
    return _API_V3_SUFFIX.sub("", value)
