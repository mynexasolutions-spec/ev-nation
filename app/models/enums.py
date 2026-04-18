from enum import Enum


class LeadSource(str, Enum):
    WHATSAPP = "whatsapp"
    CALL = "call"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"
