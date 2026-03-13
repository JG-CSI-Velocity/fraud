from .base import Rule, Finding
from .self_referral import SelfReferralRule
from .cross_referral import CrossReferralRule
from .batch_referral import BatchReferralRule
from .surname_match import SurnameMatchRule
from .duplicate_account import DuplicateAccountRule
from .missing_code import MissingCodeRule
from .name_variant import NameVariantRule
from .reciprocal_pair import ReciprocalPairRule
from .employee_as_account import EmployeeAsAccountRule
from .data_quality import DataQualityRule
from .ring_detection import RingDetectionRule

ALL_RULES = [
    SelfReferralRule,
    CrossReferralRule,
    BatchReferralRule,
    SurnameMatchRule,
    DuplicateAccountRule,
    MissingCodeRule,
    NameVariantRule,
    ReciprocalPairRule,
    EmployeeAsAccountRule,
    DataQualityRule,
    RingDetectionRule,
]
