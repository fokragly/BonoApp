from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def _arg_fmt(value, decimals: int) -> str:
    if value is None:
        return "-"
    try:
        formatted = f"{float(value):,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "-"


def _arg_price(value, currency: str = "USD") -> str:
    return _arg_fmt(value, 2)


def _arg_dec(value, decimals: int = 2) -> str:
    return _arg_fmt(value, decimals)


def _arg_pct(value) -> str:
    if value is None:
        return "-"
    try:
        sign = "+" if float(value) >= 0 else ""
        return sign + _arg_fmt(value, 2) + "%"
    except (TypeError, ValueError):
        return "-"


def _arg_vol(value) -> str:
    if value is None:
        return "-"
    try:
        v = float(value)
        if v >= 1_000_000_000:
            return _arg_fmt(v / 1_000_000_000, 2) + " MM"
        if v >= 1_000_000:
            return _arg_fmt(v / 1_000_000, 2) + " M"
        return _arg_fmt(v, 0)
    except (TypeError, ValueError):
        return "-"


templates.env.filters["arg_price"] = _arg_price
templates.env.filters["arg_dec"] = _arg_dec
templates.env.filters["arg_pct"] = _arg_pct
templates.env.filters["arg_vol"] = _arg_vol
