from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from app.models.channel import Channel
from app.models.channel_stats_snapshot import ChannelStatsSnapshot
from app.models.listing import Listing
from app.models.listing_format import ListingFormat
from app.models.user import User
from app.repositories.marketplace_repo import fetch_marketplace_listings
from shared.db.base import SQLModel


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


def _seed_listing(
    session: Session,
    *,
    telegram_user_id: int,
    username: str,
    title: str,
    subscribers: int | None,
    avg_views: int | None,
    language_stats: dict | None,
    premium_stats: dict | None,
    formats: list[tuple[str, int, int, str]],
    created_at: datetime,
) -> Listing:
    user = User(telegram_user_id=telegram_user_id, username="user")
    channel = Channel(
        username=username,
        title=title,
        is_verified=True,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(user)
    session.add(channel)
    session.flush()

    listing = Listing(
        channel_id=channel.id,
        owner_id=user.id,
        is_active=True,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(listing)
    session.flush()

    for placement_type, exclusive_hours, retention_hours, price in formats:
        session.add(
            ListingFormat(
                listing_id=listing.id,
                placement_type=placement_type,
                exclusive_hours=exclusive_hours,
                retention_hours=retention_hours,
                price=Decimal(price),
            )
        )

    session.add(
        ChannelStatsSnapshot(
            channel_id=channel.id,
            subscribers=subscribers,
            avg_views=avg_views,
            language_stats=language_stats,
            premium_stats=premium_stats,
            created_at=created_at,
        )
    )
    session.commit()
    return listing


def test_repo_filters_combined(db_engine) -> None:
    created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with Session(db_engine) as session:
        _seed_listing(
            session,
            telegram_user_id=1,
            username="alpha",
            title="Alpha",
            subscribers=1000,
            avg_views=200,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.3},
            formats=[("post", 2, 24, "10.00"), ("story", 0, 24, "100.00")],
            created_at=created_at,
        )
        _seed_listing(
            session,
            telegram_user_id=2,
            username="beta",
            title="Beta",
            subscribers=5000,
            avg_views=800,
            language_stats={"fa": 0.2},
            premium_stats={"premium_ratio": 0.05},
            formats=[("post", 1, 12, "50.00")],
            created_at=created_at,
        )

        result = fetch_marketplace_listings(
            session,
            min_price=Decimal("5"),
            max_price=Decimal("20"),
            placement_type="post",
            min_exclusive_hours=2,
            max_exclusive_hours=None,
            min_retention_hours=24,
            max_retention_hours=None,
            min_subscribers=500,
            max_subscribers=None,
            min_avg_views=None,
            max_avg_views=None,
            language="en",
            min_premium_pct=0.2,
            search=None,
            sort=None,
            page=1,
            page_size=20,
        )

    assert result.total == 1
    assert result.items[0].channel_username == "alpha"
    assert result.items[0].formats[0].placement_type in {"post", "story"}


def test_repo_search_and_filter_and_logic(db_engine) -> None:
    created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with Session(db_engine) as session:
        _seed_listing(
            session,
            telegram_user_id=1,
            username="alpha",
            title="Alpha",
            subscribers=1000,
            avg_views=200,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.3},
            formats=[("post", 1, 24, "10.00")],
            created_at=created_at,
        )
        _seed_listing(
            session,
            telegram_user_id=2,
            username="beta",
            title="Beta",
            subscribers=3000,
            avg_views=500,
            language_stats={"en": 0.7},
            premium_stats={"premium_ratio": 0.2},
            formats=[("post", 4, 48, "20.00")],
            created_at=created_at,
        )

        result = fetch_marketplace_listings(
            session,
            min_price=None,
            max_price=None,
            placement_type="post",
            min_exclusive_hours=4,
            max_exclusive_hours=None,
            min_retention_hours=48,
            max_retention_hours=None,
            min_subscribers=2000,
            max_subscribers=None,
            min_avg_views=None,
            max_avg_views=None,
            language=None,
            min_premium_pct=None,
            search="beta",
            sort=None,
            page=1,
            page_size=20,
        )
        assert result.total == 1
        assert result.items[0].channel_username == "beta"

        result = fetch_marketplace_listings(
            session,
            min_price=None,
            max_price=None,
            placement_type="story",
            min_exclusive_hours=None,
            max_exclusive_hours=None,
            min_retention_hours=None,
            max_retention_hours=None,
            min_subscribers=2000,
            max_subscribers=None,
            min_avg_views=None,
            max_avg_views=None,
            language=None,
            min_premium_pct=None,
            search="beta",
            sort=None,
            page=1,
            page_size=20,
        )

        assert result.total == 0


def test_repo_pagination_consistency(db_engine) -> None:
    with Session(db_engine) as session:
        listing_a = _seed_listing(
            session,
            telegram_user_id=1,
            username="alpha",
            title="Alpha",
            subscribers=100,
            avg_views=10,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.1},
            formats=[("post", 1, 24, "5.00")],
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        listing_b = _seed_listing(
            session,
            telegram_user_id=2,
            username="beta",
            title="Beta",
            subscribers=200,
            avg_views=20,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.1},
            formats=[("post", 1, 24, "10.00")],
            created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
        )
        _seed_listing(
            session,
            telegram_user_id=3,
            username="gamma",
            title="Gamma",
            subscribers=300,
            avg_views=30,
            language_stats={"en": 0.8},
            premium_stats={"premium_ratio": 0.1},
            formats=[("post", 1, 24, "15.00")],
            created_at=datetime(2025, 1, 3, tzinfo=timezone.utc),
        )

        listing_a_id = listing_a.id
        listing_b_id = listing_b.id

        first_page = fetch_marketplace_listings(
            session,
            min_price=None,
            max_price=None,
            placement_type=None,
            min_exclusive_hours=None,
            max_exclusive_hours=None,
            min_retention_hours=None,
            max_retention_hours=None,
            min_subscribers=None,
            max_subscribers=None,
            min_avg_views=None,
            max_avg_views=None,
            language=None,
            min_premium_pct=None,
            search=None,
            sort=None,
            page=1,
            page_size=1,
        )
        second_page = fetch_marketplace_listings(
            session,
            min_price=None,
            max_price=None,
            placement_type=None,
            min_exclusive_hours=None,
            max_exclusive_hours=None,
            min_retention_hours=None,
            max_retention_hours=None,
            min_subscribers=None,
            max_subscribers=None,
            min_avg_views=None,
            max_avg_views=None,
            language=None,
            min_premium_pct=None,
            search=None,
            sort=None,
            page=2,
            page_size=1,
        )

    assert first_page.items[0].listing_id == listing_a_id
    assert second_page.items[0].listing_id == listing_b_id


def test_repo_missing_premium_ratio_defaults_to_zero(db_engine) -> None:
    with Session(db_engine) as session:
        _seed_listing(
            session,
            telegram_user_id=1,
            username="alpha",
            title="Alpha",
            subscribers=100,
            avg_views=10,
            language_stats={"en": 0.8},
            premium_stats=None,
            formats=[("post", 1, 24, "5.00")],
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )

        result = fetch_marketplace_listings(
            session,
            min_price=None,
            max_price=None,
            placement_type=None,
            min_exclusive_hours=None,
            max_exclusive_hours=None,
            min_retention_hours=None,
            max_retention_hours=None,
            min_subscribers=None,
            max_subscribers=None,
            min_avg_views=None,
            max_avg_views=None,
            language=None,
            min_premium_pct=None,
            search=None,
            sort=None,
            page=1,
            page_size=20,
        )

    assert result.items[0].premium_ratio == 0.0


def test_repo_excludes_active_listing_with_zero_formats(db_engine) -> None:
    created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with Session(db_engine) as session:
        user = User(telegram_user_id=999, username="owner")
        channel = Channel(
            username="empty",
            title="Empty",
            is_verified=True,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(user)
        session.add(channel)
        session.flush()

        listing = Listing(
            channel_id=channel.id,
            owner_id=user.id,
            is_active=True,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(listing)
        session.add(
            ChannelStatsSnapshot(
                channel_id=channel.id,
                subscribers=100,
                avg_views=20,
                language_stats={"en": 0.8},
                premium_stats={"premium_ratio": 0.2},
                created_at=created_at,
            )
        )
        session.commit()

        result = fetch_marketplace_listings(
            session,
            min_price=None,
            max_price=None,
            placement_type=None,
            min_exclusive_hours=None,
            max_exclusive_hours=None,
            min_retention_hours=None,
            max_retention_hours=None,
            min_subscribers=None,
            max_subscribers=None,
            min_avg_views=None,
            max_avg_views=None,
            language=None,
            min_premium_pct=None,
            search=None,
            sort=None,
            page=1,
            page_size=20,
        )

    assert result.total == 0
