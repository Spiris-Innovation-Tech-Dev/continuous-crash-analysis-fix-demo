from __future__ import annotations


def load_customer_profile(customer: dict[str, str | None]) -> str:
    """Return a normalized customer name.

    Raises ``ValueError`` when the ``name`` key is missing or ``None`` so
    callers get a clear error instead of an ``AttributeError`` on ``None``.
    """

    name = customer.get("name")
    if name is None or not name.strip():
        raise ValueError("Customer record is missing a valid 'name' field.")
    return name.strip().title()


def build_account_overview(customer: dict[str, str | None]) -> dict[str, str]:
    return {
        "display_name": load_customer_profile(customer),
        "status": "active",
    }


def calculate_discount_ratio(total: int, discount: int) -> float:
    """Return the ratio of *discount* to *total*.

    Raises ``ValueError`` when *total* is zero so the caller gets a clear
    error instead of an ``EXCEPTION_INT_DIVIDE_BY_ZERO`` crash.
    """
    if total == 0:
        raise ValueError("Cannot calculate a discount ratio when 'total' is zero.")
    return discount / total


def build_invoice_preview(total: int, discount: int) -> dict[str, float]:
    return {
        "total": float(total),
        "discount_ratio": calculate_discount_ratio(total, discount),
    }


def synthetic_fail_fast(message: str) -> None:
    raise RuntimeError(message)
