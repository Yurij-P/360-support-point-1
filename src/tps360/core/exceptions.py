class DomainRuleViolation(ValueError):
    """Raised when a domain invariant or lifecycle rule is violated."""


class NotFoundError(LookupError):
    """Raised when an in-memory aggregate cannot be found."""
