"""Domain enumerations for NyayaLens."""

import sys

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        pass


class PartyRole(StrEnum):
    CLAIMANT = "claimant"
    RESPONDENT = "respondent"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


class FactType(StrEnum):
    ALLEGED = "alleged"
    DISPUTED = "disputed"
    UNDISPUTED = "undisputed"
    UNKNOWN = "unknown"


class EvidenceType(StrEnum):
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    CONTRACT = "contract"
    INVOICE = "invoice"
    SCREENSHOT = "screenshot"
    CONVERSATION_EXPORT = "conversation_export"
    OTHER = "other"


class LegalSourceType(StrEnum):
    CONSTITUTION = "constitution"
    ACT = "act"
    RULE = "rule"
    REGULATION = "regulation"
    JUDGMENT = "judgment"
    GOVERNMENT_NOTIFICATION = "government_notification"
    OFFICIAL_GUIDANCE = "official_guidance"


class Jurisdiction(StrEnum):
    INDIA = "india"
    STATE = "state"
    UNION_TERRITORY = "union_territory"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class IssuePriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationPriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StatementType(StrEnum):
    FACT = "fact"
    INFERENCE = "inference"
    LEGAL_SOURCE = "legal_source"
    MODEL_INTERPRETATION = "model_interpretation"
    RECOMMENDATION = "recommendation"


class LegalDomain(StrEnum):
    CRIMINAL = "criminal_law"
    CONTRACT = "contract_law"
    PROPERTY = "property_law"
    CONSUMER = "consumer_law"
    EMPLOYMENT = "employment_law"
    FAMILY = "family_law"
    CYBER = "cyber_law"
    MOTOR_VEHICLE = "motor_vehicle_law"
    CONSTITUTIONAL = "constitutional_law"
    CIVIL_PROCEDURE = "civil_procedure"
    TENANCY = "tenancy_law"
    OTHER = "other"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
