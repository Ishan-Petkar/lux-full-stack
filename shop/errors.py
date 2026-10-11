"""Exception types shared by the service layer and the UI."""


class ShopError(Exception):
    """Base class; the message is safe to show to an end user."""


class ValidationError(ShopError):
    """User supplied data failed validation."""


class NotFoundError(ShopError):
    """A requested product / user / order does not exist."""


class StockError(ShopError):
    """Requested quantity is not available."""


class DatabaseError(ShopError):
    """The database could not be reached or an operation failed."""


class AuthError(ShopError):
    """Sign-in failed or the action needs a different role."""


class PaymentError(ShopError):
    """The payment could not be completed."""
