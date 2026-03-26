class WalletError(Exception):
    """Base domain error for wallet operations."""


class WalletNotFoundError(WalletError):
    """Raised when a wallet does not exist."""


class InsufficientFundsError(WalletError):
    """Raised when a withdrawal would make the balance negative."""

