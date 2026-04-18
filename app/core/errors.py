class ServiceError(Exception):
    """Base service-layer error."""


class NotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""


class DomainValidationError(ServiceError):
    """Raised when a request is structurally valid but violates business rules."""
