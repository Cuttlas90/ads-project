from __future__ import annotations

from decimal import Decimal

from app.services.ton.chain_scan import TonCenterAdapter
from app.settings import Settings


def test_find_incoming_tx_matches_address_variants(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        TON_ENABLED=True,
        TONCENTER_API="https://testnet.toncenter.com/api/v3/jsonRPC",
    )
    adapter = TonCenterAdapter(settings)

    target_address = "0QC3CK09jJSQNrMvUlFia7HTCUWcJ5wIFgPolR6wSbb7krv1"
    destination_variant = "EQC3CK09jJSQNrMvUlFia7HTCUWcJ5wIFgPolR6wSbb7kl26"

    monkeypatch.setattr(
        adapter,
        "_get",
        lambda path, params=None: {
            "transactions": [
                {
                    "hash": "tx1",
                    "lt": "100",
                    "mc_block_seqno": 10,
                    "in_msg": {
                        "destination": destination_variant,
                        "value": "1000000000",
                    },
                }
            ]
        },
    )

    tx = adapter.find_incoming_tx(target_address, Decimal("0"), None)
    assert tx is not None
    assert tx["hash"] == "tx1"


def test_find_incoming_tx_ignores_other_destinations(monkeypatch) -> None:
    settings = Settings(
        _env_file=None,
        TON_ENABLED=True,
        TONCENTER_API="https://testnet.toncenter.com/api/v3/jsonRPC",
    )
    adapter = TonCenterAdapter(settings)

    monkeypatch.setattr(
        adapter,
        "_get",
        lambda path, params=None: {
            "transactions": [
                {
                    "hash": "tx1",
                    "lt": "100",
                    "mc_block_seqno": 10,
                    "in_msg": {
                        "destination": "EQAAcFNNhAvs_xf28FGk9u1BWiWzCl-fjtDqClpJtRXegOrt",
                        "value": "1000000000",
                    },
                }
            ]
        },
    )

    tx = adapter.find_incoming_tx(
        "0QC3CK09jJSQNrMvUlFia7HTCUWcJ5wIFgPolR6wSbb7krv1",
        Decimal("0"),
        None,
    )
    assert tx is None
