from __future__ import annotations


def load_customer_profile(customer: dict[str, str | None]) -> str:
    """Return a normalized customer name.

    Guards against a missing or None ``name`` value that would previously cause
    an ``AttributeError`` (the synthetic EXCEPTION_ACCESS_VIOLATION analogue).
    """

    name = customer.get("name")
    if not name:
        raise ValueError("customer record is missing a valid 'name' field")
    return name.strip().title()


def build_account_overview(customer: dict[str, str | None]) -> dict[str, str]:
    return {
        "display_name": load_customer_profile(customer),
        "status": "active",
    }


def calculate_discount_ratio(total: int, discount: int) -> float:
    if total == 0:
        raise ValueError("total must be non-zero when calculating a discount ratio")
    return discount / total


def build_invoice_preview(total: int, discount: int) -> dict[str, float]:
    return {
        "total": float(total),
        "discount_ratio": calculate_discount_ratio(total, discount),
    }


def synthetic_fail_fast(message: str) -> None:
    raise RuntimeError(message)
