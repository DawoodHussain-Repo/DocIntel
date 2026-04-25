"""Static retrieval catalogs for contract analysis."""

from __future__ import annotations

from typing import Dict, List, Tuple


SUMMARY_QUERIES: List[str] = [
    "purpose of this agreement",
    "term and termination",
    "payment terms fees invoice",
    "confidentiality",
    "limitation of liability",
    "indemnification",
    "governing law jurisdiction venue",
    "deliverables services scope of work",
    "renewal",
    "assignment",
]

CLASSIFICATION_QUERIES: List[str] = [
    "confidential information non-disclosure",
    "landlord tenant rent premises lease",
    "independent contractor services deliverables invoice",
    "ownership of work product intellectual property",
]

FIELD_SPECS: List[Tuple[str, str, str]] = [
    ("parties", "Parties", "parties to this agreement"),
    ("effective_date", "Effective Date", "effective date"),
    ("term", "Term / Duration", "term of this agreement duration"),
    ("renewal", "Renewal", "renewal automatic renew"),
    ("termination_for_convenience", "Termination (Convenience)", "terminate for convenience without cause"),
    ("termination_for_cause", "Termination (Cause)", "terminate for cause breach"),
    ("notice_period", "Notice Period", "notice period days written notice"),
    ("payment_amount", "Payment Amount", "fees payment amount"),
    ("payment_schedule", "Payment Schedule", "payment schedule milestones monthly"),
    ("late_fees", "Late Fees / Interest", "late fee interest overdue"),
    ("currency", "Currency", "USD PKR currency"),
    ("governing_law", "Governing Law", "governing law"),
    ("jurisdiction", "Jurisdiction / Venue", "jurisdiction venue courts"),
    ("arbitration", "Arbitration", "arbitration dispute resolution"),
    ("confidentiality", "Confidentiality", "confidentiality confidential information"),
    ("non_disparagement", "Non-disparagement", "non-disparagement"),
    ("non_compete", "Non-compete / Non-solicit", "non-compete non-solicit"),
    ("ip_ownership", "IP Ownership", "intellectual property ownership work product"),
    ("license_grant", "License Grant", "license grant"),
    ("assignment", "Assignment", "assignment assign this agreement"),
    ("subcontracting", "Subcontracting", "subcontracting subcontractors"),
    ("indemnification", "Indemnification", "indemnify indemnification"),
    ("limitation_of_liability", "Limitation of Liability", "limitation of liability cap"),
    ("warranties", "Warranties / Disclaimers", "warranty warranties disclaimer"),
    ("insurance", "Insurance", "insurance coverage"),
    ("force_majeure", "Force Majeure", "force majeure"),
    ("data_protection", "Data Protection", "data protection privacy security"),
    ("audit_rights", "Audit Rights", "audit inspection records"),
    ("change_control", "Change Control", "change control amendments"),
    ("signature_block", "Signatures", "IN WITNESS WHEREOF signatures"),
]

RISK_QUERIES: List[str] = [
    "limitation of liability cap exclusion",
    "indemnification defend hold harmless",
    "termination for convenience",
    "payment late fee interest",
    "warranty disclaimer as-is",
    "assignment change of control",
    "non-compete non-solicit",
    "confidentiality remedies injunctive relief",
    "governing law jurisdiction venue",
    "audit inspection records",
]

PLAYBOOK: Dict[str, List[Tuple[str, str]]] = {
    "NDA": [
        ("Mutuality", "mutual confidentiality obligations"),
        ("Permitted disclosures", "compelled disclosure required by law notice"),
        ("Return/destruction", "return or destroy confidential information"),
        ("Survival", "confidentiality survives termination"),
        ("No license", "no license to intellectual property"),
        ("Injunctive relief", "injunctive relief equitable remedies"),
    ],
    "Lease": [
        ("Rent", "rent base rent payment due date"),
        ("Security deposit", "security deposit"),
        ("Maintenance/repairs", "maintenance repairs landlord tenant responsibilities"),
        ("Late fees", "late fee interest overdue rent"),
        ("Utilities", "utilities electricity water"),
        ("Early termination", "early termination break clause"),
    ],
    "Freelance Agreement": [
        ("Scope", "scope of work deliverables services"),
        ("Acceptance", "acceptance criteria review revisions"),
        ("Kill fee", "kill fee cancellation fee"),
        ("IP assignment", "assignment of intellectual property work product"),
        ("Payment terms", "invoice net 15 net 30 payment schedule"),
        ("Indemnity/limits", "indemnification limitation of liability"),
    ],
    "Other": [
        ("Termination", "termination written notice"),
        ("Payment terms", "fees payment invoice"),
        ("Governing law", "governing law jurisdiction"),
    ],
}
