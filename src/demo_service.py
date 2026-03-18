from __future__ import annotations


def load_customer_profile(customer: dict[str, str | None]) -> str:
    """Return a normalized customer name.

    Raises ValueError when the name field is absent or None so callers receive
    a clear error instead of an AttributeError from a None.strip() call.
    """
    name = customer.get("name")
    if name is None:
        raise ValueError("Customer name must not be None")
    return name.strip().title()


def build_account_overview(customer: dict[str, str | None]) -> dict[str, str]:
    return {
        "display_name": load_customer_profile(customer),
        "status": "active",
    }


def calculate_discount_ratio(total: int, discount: int) -> float:
    if total == 0:
        raise ValueError("Cannot calculate discount ratio when total is zero")
    return discount / total


def build_invoice_preview(total: int, discount: int) -> dict[str, float]:
    return {
        "total": float(total),
        "discount_ratio": calculate_discount_ratio(total, discount),
    }


def save_invoice(invoice: dict[str, object]) -> None:
    """Persist an invoice record after validating required fields.

    Calls synthetic_fail_fast when required fields are absent, mirroring the
    fail-fast pattern referenced in crash report 02f3d8047cf0 (EXCEPTION_BREAKPOINT).
    Replace or extend this guard with your real validation logic.
    """
    required = {"customer_id", "total", "line_items"}
    missing = required - invoice.keys()
    if missing:
        synthetic_fail_fast(f"Invoice missing required fields: {sorted(missing)}")


def synthetic_fail_fast(message: str) -> None:
    raise RuntimeError(message)
