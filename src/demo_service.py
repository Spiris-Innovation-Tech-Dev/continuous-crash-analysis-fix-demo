from __future__ import annotations


def load_customer_profile(customer: dict[str, str | None]) -> str:
    """Return a normalized customer name.

    The synthetic crash report points here because this code assumes the name is
    always present. If the name is None, `.strip()` would fail.
    """

    return customer["name"].strip().title()


def build_account_overview(customer: dict[str, str | None]) -> dict[str, str]:
    return {
        "display_name": load_customer_profile(customer),
        "status": "active",
    }


def calculate_discount_ratio(total: int, discount: int) -> float:
    return discount / total


def build_invoice_preview(total: int, discount: int) -> dict[str, float]:
    return {
        "total": float(total),
        "discount_ratio": calculate_discount_ratio(total, discount),
    }


def synthetic_fail_fast(message: str) -> None:
    raise RuntimeError(message)
