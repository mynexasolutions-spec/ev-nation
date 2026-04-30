from enum import Enum


class LeadSource(str, Enum):
    WHATSAPP = "whatsapp"
    CALL = "call"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"


class OrderStatus(str, Enum):
    PENDING = "pending"        # Order placed, awaiting payment
    PAID = "paid"              # Payment received
    CONFIRMED = "confirmed"    # Admin confirmed the order
    READY = "ready"            # Ready for showroom pickup
    COMPLETED = "completed"    # Customer picked up
    CANCELLED = "cancelled"    # Order cancelled


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
