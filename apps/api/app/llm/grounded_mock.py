"""Case-grounded mock LLM — extracts from the user's text instead of pasting templates."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Type, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
AMOUNT_RE = re.compile(r"(?:₹|Rs\.?\s*|INR\s*)[\d,]+(?:\.\d{1,2})?", re.I)
DATE_RE = re.compile(rf"\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}", re.I)
ID_RE = re.compile(
    r"\[ID: ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]",
    re.I,
)
SOURCE_RE = re.compile(
    r"\[ID: ([0-9a-f-]{36})\]\s*(.+?)\s+[—-]\s*(.+?)\n(.*?)(?=\n\[ID:|\Z)",
    re.I | re.S,
)
LABELED_RE = re.compile(
    r"^(Parties involved|Amount involved|Evidence available|Additional context|Location|When):\s*(.+)$",
    re.I | re.M,
)
NAME_ROLE_RE = re.compile(r"([A-Za-z][A-Za-z0-9.&'’ -]{1,70}?)\s*\(([^)]+)\)")
GOOD_RE = re.compile(
    r"(?:bought|purchased|ordered)\s+(?:a|an|the)\s+([A-Za-z0-9][\w .&-]{2,50}?)(?:\s+from|\s+online|\s+for|,|\.)",
    re.I,
)
EVIDENCE_TERMS = (
    "invoice",
    "credit-card",
    "credit card",
    "upi",
    "whatsapp",
    "chat",
    "screenshot",
    "service report",
    "photos",
    "video",
    "rental agreement",
    "salary slip",
    "call log",
    "sms",
    "email",
)

ROLE_MAP = {
    "buyer": "claimant",
    "purchaser": "claimant",
    "consumer": "claimant",
    "tenant": "claimant",
    "employee": "claimant",
    "complainant": "claimant",
    "lender": "claimant",
    "seller": "respondent",
    "landlord": "respondent",
    "employer": "respondent",
    "borrower": "respondent",
    "marketplace": "third_party",
    "platform": "third_party",
    "manufacturer": "third_party",
    "brand": "third_party",
}


@dataclass
class ExtractedCase:
    category: str
    text: str
    amounts: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    goods: list[str] = field(default_factory=list)
    labeled: dict[str, str] = field(default_factory=dict)
    sentences: list[str] = field(default_factory=list)
    parties: list[tuple[str, str, str]] = field(default_factory=list)


def _section_after(prompt: str, marker: str) -> str:
    if marker not in prompt:
        return ""
    chunk = prompt.split(marker, 1)[1]
    for stop in (
        "\nCASE TYPE",
        "\nEXTRACTED FACTS",
        "\nFACTS:",
        "\nISSUES:",
        "\nRETRIEVED",
        "\nLEGAL ANALYSIS",
        "\nRELEVANT LAW",
        "\nKNOWN MISSING",
        "\nRECENT CONVERSATION",
        "\nUSER QUESTION",
        "\nMISSING INFORMATION",
    ):
        if stop in chunk:
            chunk = chunk.split(stop, 1)[0]
    return chunk.strip()


def case_text(prompt: str) -> str:
    for marker in ("CASE DESCRIPTION:", "CASE:", "CASE TYPE HINT:"):
        body = _section_after(prompt, marker)
        if len(body) > 40:
            return body
    return prompt


def case_category(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["landlord", "tenant", "deposit", "rent", "moved out", "lease"]):
        return "tenancy"
    if any(w in lower for w in ["otp", "phishing", "upi fraud", "personation", "harassment", "cyber"]):
        return "cyber"
    if any(
        w in lower
        for w in [
            "consumer",
            "laptop",
            "refrigerator",
            "fridge",
            "defective",
            "refund",
            "seller",
            "warranty",
            "amazon",
            "marketplace",
            "compressor",
        ]
    ):
        return "consumer"
    if any(w in lower for w in ["employment", "salary", "terminated", "worked", "settlement", "wages"]):
        return "employment"
    if any(w in lower for w in ["lent", "loan", "repay", "borrow"]):
        return "loan"
    return "other"


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = re.sub(r"\s+", " ", item).strip(" .,;:")
        if not key or key.lower() in seen:
            continue
        seen.add(key.lower())
        out.append(key)
    return out


def extract(prompt: str) -> ExtractedCase:
    text = case_text(prompt)
    labeled = {m.group(1).lower(): m.group(2).strip() for m in LABELED_RE.finditer(text)}
    amounts = _unique(AMOUNT_RE.findall(text) + ([labeled["amount involved"]] if "amount involved" in labeled else []))
    dates = _unique(DATE_RE.findall(text))
    evidence = [term for term in EVIDENCE_TERMS if term in text.lower()]
    if "evidence available" in labeled:
        evidence = _unique(evidence + [p.strip() for p in re.split(r"[,/]", labeled["evidence available"]) if p.strip()])
    goods = _unique([m.group(1).strip() for m in GOOD_RE.finditer(text)])
    locations: list[str] = []
    if "location" in labeled:
        locations.append(labeled["location"])
    for match in re.finditer(r"\bin ([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?)", text):
        locations.append(match.group(1))
    locations = _unique(locations)

    parties: list[tuple[str, str, str]] = []
    if "parties involved" in labeled:
        for name, role_raw in NAME_ROLE_RE.findall(labeled["parties involved"]):
            role = ROLE_MAP.get(role_raw.strip().lower(), "unknown")
            parties.append((name.strip(), role, role_raw.strip()))
    if not parties:
        for name, role_raw in NAME_ROLE_RE.findall(text):
            role = ROLE_MAP.get(role_raw.strip().lower(), "unknown")
            parties.append((name.strip(), role, role_raw.strip()))

    lower = text.lower()
    extras = [
        ("Amazon", "third_party", "marketplace") if "amazon" in lower else None,
        ("Samsung", "third_party", "brand") if "samsung" in lower else None,
    ]
    existing = {p[0].lower() for p in parties}
    for extra in extras:
        if extra and extra[0].lower() not in existing:
            parties.append(extra)

    sentences = []
    for raw in re.split(r"(?<=[.!?])\s+", text):
        line = raw.strip()
        if len(line) < 28:
            continue
        if line.lower().startswith(("parties involved", "amount involved", "evidence available", "additional context")):
            continue
        sentences.append(line[:320])

    return ExtractedCase(
        category=case_category(text),
        text=text,
        amounts=amounts,
        dates=dates,
        locations=locations,
        evidence=evidence,
        goods=goods,
        labeled=labeled,
        sentences=sentences[:10],
        parties=parties[:6],
    )


def _snippet(ex: ExtractedCase, *needles: str, fallback: str = "") -> str:
    for sentence in ex.sentences:
        lower = sentence.lower()
        if any(n.lower() in lower for n in needles):
            return sentence
    return fallback or (ex.sentences[0] if ex.sentences else ex.text[:240])


def _amount(ex: ExtractedCase) -> str:
    return ex.amounts[0] if ex.amounts else "the amount stated"


def _good(ex: ExtractedCase) -> str:
    return ex.goods[0] if ex.goods else "the goods"


def _place(ex: ExtractedCase) -> str:
    return ex.locations[0] if ex.locations else "the place stated"


def _party_by_role(ex: ExtractedCase, role: str, default: str) -> str:
    for name, mapped, _hint in ex.parties:
        if mapped == role:
            return name
    return default


def _claimant_name(ex: ExtractedCase) -> str:
    return _party_by_role(ex, "claimant", "the buyer/user")


def _respondent_name(ex: ExtractedCase) -> str:
    return _party_by_role(ex, "respondent", "the other party")


def _extract_ids(prompt: str) -> list[UUID]:
    ids: list[UUID] = []
    for match in ID_RE.findall(prompt):
        try:
            ids.append(UUID(match))
        except ValueError:
            continue
    return ids


def _parse_sources(prompt: str) -> list[tuple[UUID, str, str, str]]:
    rows = []
    for match in SOURCE_RE.finditer(prompt):
        try:
            rows.append((UUID(match.group(1)), match.group(2).strip(), match.group(3).strip(), match.group(4).strip()))
        except ValueError:
            continue
    return rows


def _default_parties(ex: ExtractedCase) -> list[dict]:
    if ex.parties:
        return [
            {"name": name, "role": role, "description": hint.capitalize() if hint else None}
            for name, role, hint in ex.parties
        ]
    if ex.category == "tenancy":
        return [
            {"name": "Tenant", "role": "claimant", "description": "Occupant seeking deposit return"},
            {"name": "Landlord", "role": "respondent", "description": "Person alleged to be withholding the deposit"},
        ]
    if ex.category == "cyber":
        return [
            {"name": "Complainant", "role": "claimant", "description": "Person alleging online fraud or harassment"},
            {"name": "Unknown actor", "role": "respondent", "description": "Person or account alleged to have caused the harm"},
        ]
    if ex.category == "employment":
        return [
            {"name": "Employee", "role": "claimant", "description": "Worker alleging unpaid dues or unfair termination"},
            {"name": "Employer", "role": "respondent", "description": "Organisation alleged to owe wages or to have terminated employment"},
        ]
    if ex.category == "loan":
        return [
            {"name": "Lender", "role": "claimant", "description": "Person who says money was advanced"},
            {"name": "Borrower", "role": "respondent", "description": "Person alleged not to have repaid"},
        ]
    return [
        {"name": _claimant_name(ex) if _claimant_name(ex) != "the buyer/user" else "Buyer", "role": "claimant", "description": "Purchaser of goods or services"},
        {"name": _respondent_name(ex) if _respondent_name(ex) != "the other party" else "Seller", "role": "respondent", "description": "Person or business that supplied the goods or services"},
    ]


def _facts(ex: ExtractedCase) -> list[dict]:
    facts: list[dict] = []
    for sentence in ex.sentences[:6]:
        disputed = any(w in sentence.lower() for w in ["refus", "deny", "dispute", "withhold", "expired"])
        facts.append(
            {
                "description": sentence,
                "fact_type": "disputed" if disputed else "alleged",
                "date": next((d for d in ex.dates if d.lower() in sentence.lower()), None),
                "location": next((loc for loc in ex.locations if loc.lower() in sentence.lower()), None),
                "amount": next((a for a in ex.amounts if a.replace(" ", "") in sentence.replace(" ", "")), None),
            }
        )
    if not facts:
        facts = [{"description": ex.text[:280], "fact_type": "alleged"}]
    return facts


def _unknown(ex: ExtractedCase) -> list[str]:
    if ex.category == "consumer":
        items = [
            "Exact return / refund policy text of the seller and marketplace",
            "Whether repair or replacement was offered or attempted after the service inspection",
            "Written warranty terms and whether the manufacturer accepted a manufacturing defect",
        ]
        if any("amazon" in p[0].lower() or p[2] == "marketplace" for p in ex.parties) or "amazon" in ex.text.lower():
            items.append("Whether the marketplace is only an intermediary or also an opposite party on these facts")
        return items
    if ex.category == "tenancy":
        return [
            "Whether there is a written rental agreement and what it says about the deposit",
            "Whether a move-out inspection was done and any damage was recorded",
            "Whether rent or utility dues are claimed as a set-off",
        ]
    if ex.category == "cyber":
        return [
            "Whether a police or cyber-crime complaint has already been filed",
            "Account numbers, UTR/UPI references, and the exact handles used",
            "Whether the bank or platform froze the transaction or reversed any amount",
        ]
    if ex.category == "employment":
        return [
            "Whether a written appointment letter or contract exists",
            "Exact unpaid salary / settlement figures and wage period",
            "Whether termination was in writing and on what stated ground",
        ]
    if ex.category == "loan":
        return [
            "Whether repayment was agreed in writing and by which date",
            "Whether the transfer was described as a loan, gift, or something else at the time",
            "Whether any part payment or settlement already occurred",
        ]
    return ["Further documents that corroborate dates, amounts, and the other party's position"]


def _issues(ex: ExtractedCase) -> list[dict]:
    facts = [f["description"] for f in _facts(ex)[:3]]
    missing = _unknown(ex)
    good = _good(ex)
    amount = _amount(ex)
    seller = _respondent_name(ex)
    buyer = _claimant_name(ex)
    place = _place(ex)

    if ex.category == "consumer":
        return [
            {
                "issue": f"Whether {seller} may be liable for a defective {good} sold for {amount}",
                "why_it_matters": "Consumer remedies usually turn on proving a defect or deficiency in goods or services, not merely that a return window on a platform expired.",
                "supporting_fact_descriptions": facts[:2],
                "missing_fact_descriptions": missing[:1],
                "priority": "high",
            },
            {
                "issue": "Whether a short marketplace return window can defeat statutory consumer remedies after a later manufacturing-defect finding",
                "why_it_matters": "Sellers often rely on platform policy; that is a defence to test against the Consumer Protection Act, 2019, not an automatic bar.",
                "supporting_fact_descriptions": facts[1:3] or facts,
                "missing_fact_descriptions": missing[:2],
                "priority": "high",
            },
            {
                "issue": f"What remedies (repair, replacement, refund of {amount}, or compensation) may be available, and in which forum connected with {place}",
                "why_it_matters": "Section 38-type relief depends on proof and on territorial/pecuniary jurisdiction; this tool cannot choose the forum for you.",
                "missing_fact_descriptions": missing[1:3],
                "priority": "medium",
            },
        ]
    if ex.category == "tenancy":
        return [
            {
                "issue": f"Whether withholding {amount} as a security deposit is legally supportable on the stated facts",
                "why_it_matters": "Deposit refund usually depends on the agreement, lawful deductions, and the condition of the premises at handover.",
                "supporting_fact_descriptions": facts[:2],
                "missing_fact_descriptions": missing[:2],
                "priority": "high",
            },
            {
                "issue": "What process (notice, consumer/tenancy/civil route) may be appropriate to seek return of the deposit",
                "why_it_matters": "The available forum depends on the contract, local tenancy law, and whether the occupancy was residential.",
                "priority": "medium",
            },
        ]
    if ex.category == "cyber":
        return [
            {
                "issue": "Whether the alleged conduct may engage cheating-by-personation, password/OTP misuse, or related cyber provisions",
                "why_it_matters": "The legal characterisation affects evidence, urgency, and whether the police/cyber cell is the first step.",
                "supporting_fact_descriptions": facts[:2],
                "missing_fact_descriptions": missing[:2],
                "priority": "high",
            },
            {
                "issue": "What electronic records should be preserved and how they may be proved",
                "why_it_matters": "Screenshots and SMS often matter only if authenticity and the transaction trail can be shown.",
                "priority": "medium",
            },
        ]
    if ex.category == "employment":
        return [
            {
                "issue": f"Whether unpaid wages or terminal dues of about {amount} are owed on the stated employment facts",
                "why_it_matters": "Wage statutes and the contract (if any) control timing of payment after termination.",
                "supporting_fact_descriptions": facts[:2],
                "missing_fact_descriptions": missing[:2],
                "priority": "high",
            },
            {
                "issue": "Whether termination without notice, if proved, has consequences under applicable labour law",
                "why_it_matters": "Notice, wage timelines, and whether the person is a 'workman' can change the analysis.",
                "priority": "medium",
            },
        ]
    if ex.category == "loan":
        return [
            {
                "issue": f"Whether a legally enforceable obligation to repay {amount} arose, or whether the transfer may be characterised as a gift or something else",
                "why_it_matters": "A UPI credit alone does not prove a loan; contemporaneous messages and the parties' words at the time matter.",
                "supporting_fact_descriptions": facts[:2],
                "missing_fact_descriptions": missing[:2],
                "priority": "high",
            },
            {
                "issue": "Whether limitation or lack of written terms may affect recovery",
                "why_it_matters": "Delay and missing terms can change both liability and the practical value of a claim.",
                "priority": "medium",
            },
        ]
    return [
        {
            "issue": f"What legal characterisation best fits the dispute described by {buyer}",
            "why_it_matters": "The available rights and forums depend on facts that are still only one side's account.",
            "supporting_fact_descriptions": facts[:2],
            "priority": "medium",
        }
    ]


def _summary(ex: ExtractedCase) -> str:
    good = _good(ex)
    amount = _amount(ex)
    seller = _respondent_name(ex)
    buyer = _claimant_name(ex)
    if ex.category == "consumer":
        defect = _snippet(ex, "defect", "fail", "leak", "flicker", fallback="a defect is alleged shortly after delivery")
        return (
            f"This may be a consumer-goods dispute: {buyer} describes buying {good} for {amount} from {seller}. "
            f"Key alleged sequence: {defect} A platform return window and a brand-warranty diversion are in issue. "
            "This is one side's account; liability is not decided here."
        )
    if ex.category == "tenancy":
        return (
            f"This may be a tenancy / deposit dispute involving about {amount}. "
            f"{_snippet(ex, 'deposit', 'moved out', 'landlord')} "
            "Whether deductions for damage or dues are justified is not established on this record."
        )
    if ex.category == "cyber":
        return (
            f"This may involve online fraud, OTP/identity misuse, or electronic harassment. "
            f"{_snippet(ex, 'otp', 'upi', 'transfer', 'message')} "
            "Criminal characterisation, if any, depends on evidence and investigation — not on this summary."
        )
    if ex.category == "employment":
        return (
            f"This may be an employment / wages dispute involving about {amount}. "
            f"{_snippet(ex, 'terminated', 'salary', 'settlement')} "
            "Contract terms and whether labour statutes apply remain to be checked."
        )
    if ex.category == "loan":
        return (
            f"This may be a money-recovery / contract dispute about {amount}. "
            f"{_snippet(ex, 'lent', 'upi', 'repay')} "
            "Whether the transfer was a loan is a fact to be proved, not assumed."
        )
    return "Based on the information provided, this may be a civil dispute. Further facts are required before any reliable conclusion can be drawn."


def _explain_source(title: str, section: str, law_text: str, ex: ExtractedCase) -> tuple[str, str, str, list[str]]:
    blob = f"{title} {section} {law_text}".lower()
    amount = _amount(ex)
    good = _good(ex)
    seller = _respondent_name(ex)
    buyer = _claimant_name(ex)
    quote = law_text.strip()[:220]

    if ("2(7)" in blob and "consumer" in blob) or "consumer means" in blob:
        extra = _snippet(ex, "home", "not for business", "household", fallback="personal use is alleged")
        return (
            f"FACT: {buyer} says the {good} was bought for {amount}. {extra} "
            f"LAW: {title} {section} defines who is a 'consumer' (consideration for goods/services, typically not for commercial resale). "
            "ANALYSIS: If personal/household use and payment are proved, this definition may be satisfied. It does not by itself prove a defect.",
            "May apply if the purchase was for consideration and not mainly for commercial resale — still a proof question.",
            "If the goods were bought for business, the consumer forum route may be contested.",
            ["The opposite party may argue the purchase was commercial or that the complainant is not a 'consumer' on these facts."],
        )
    if "deficiency" in blob or "2(11)" in blob:
        return (
            f"FACT: {_snippet(ex, 'refus', 'warranty', 'seller to resolve', 'service')} "
            f"LAW: {title} {section} concerns deficiency in service (fault, shortcoming, or inadequacy in performance). "
            f"ANALYSIS: Directing {buyer} only to brand warranty, or leaving the ticket as 'seller to resolve' without a remedy, might be argued as deficiency — if a service obligation existed. That is contested.",
            "Potentially relevant to after-sales handling, not automatically to a goods defect.",
            "A seller may say the only obligation was to pass on manufacturer warranty.",
            ["Respondent may deny any service contract with the buyer beyond supply of goods."],
        )
    if "section 38" in blob or "district commission" in blob:
        report = _snippet(ex, "service", "manufacturing", "compressor", "defect")
        return (
            f"FACT: {report} Refund/replacement of {amount} is sought from {seller}. "
            f"LAW: {title} {section} lists possible District Commission directions: remove defect, replace, refund price, or compensation — if allegations are proved. "
            "ANALYSIS: This is a remedies provision. It does not decide the complaint. A 7-day platform window, if proved, is a defence to weigh; it is not in this section as an automatic bar.",
            f"May support asking for repair, replacement, or refund of {amount} if defect/deficiency is later proved.",
            "Relief is discretionary and fact-dependent; jurisdiction (Pecuniary/territorial) is not determined here.",
            ["Seller may argue the return window expired and only warranty repair is due.", "Marketplace may argue it is not the seller."],
        )
    if "section 10" in blob and "contract" in blob:
        return (
            f"FACT: Payment of {amount} for {good} is alleged, with invoice/payment records mentioned. "
            f"LAW: {title} {section} — agreements become contracts if made with free consent, competent parties, lawful consideration and object. "
            "ANALYSIS: A paid retail sale may be a contract of sale. That still leaves quality, warranty, and statutory consumer rights as separate questions.",
            "May apply to show a contract arose from the paid purchase, if those elements are proved.",
            "Formation of a contract is not the same as proving a defect.",
            ["Respondent may admit a sale but deny breach or defect at the time of supply."],
        )
    if "section 73" in blob:
        return (
            f"FACT: {_snippet(ex, 'leak', 'fail', 'refus', 'loss')} "
            f"LAW: {title} {section} allows compensation for loss naturally arising from breach, not remote loss. "
            "ANALYSIS: Even if a contract is proved, damages still require proof of breach and of loss. Consumer-forum refund is a different statutory route.",
            "May be relevant if a contractual breach is later established.",
            "Remote losses (for example unexplained consequential claims) may be excluded.",
            ["Respondent may deny breach or say any loss is too remote."],
        )
    if "65b" in blob or "electronic record" in blob:
        ev = ", ".join(ex.evidence[:4]) or "chats, invoices, or photos"
        return (
            f"FACT: The user lists electronic material ({ev}). "
            f"LAW: {title} {section} deals with admissibility of electronic records when statutory conditions are met. "
            "ANALYSIS: Keeping originals/exports helps; this section does not make every screenshot automatically conclusive.",
            f"May matter if {ev} are later used in any proceeding.",
            "Conditions of s.65B (where applicable) and authenticity can still be disputed.",
            ["The other side may challenge authenticity or completeness of chats/screenshots."],
        )
    if "security deposit" in blob or "model tenancy" in blob:
        return (
            f"FACT: {_snippet(ex, 'deposit', 'moved out', 'refund')} involving about {amount}. "
            f"LAW: {quote} "
            "ANALYSIS: Model tenancy rules are not automatically in force in every State. Local rent/tenancy law and the written agreement control.",
            "May be analogous if a comparable State tenancy law or the agreement has similar deposit-refund terms.",
            "Applicability depends on whether that statute is in force for this premises.",
            ["Landlord may claim lawful deductions for damage or dues."],
        )
    if "66d" in blob or "66c" in blob or "personation" in blob or "password" in blob:
        return (
            f"FACT: {_snippet(ex, 'otp', 'upi', 'called', 'password')} "
            f"LAW: {title} {section}: {quote} "
            "ANALYSIS: These are penal provisions. Whether they are attracted is for investigation/court, and only if the statutory ingredients are made out. This tool does not charge anyone.",
            "May be relevant to discuss with an advocate or cyber cell if the facts match the ingredients — that is not decided here.",
            "Identity of the actor and dishonest intent are typically the hard parts.",
            ["The unknown actor's identity may never be proved on the current record."],
        )
    if "wages" in blob or "industrial disputes" in blob or "section 5" in blob:
        return (
            f"FACT: {_snippet(ex, 'salary', 'terminated', 'settlement')} about {amount}. "
            f"LAW: {title} {section}: {quote} "
            "ANALYSIS: Wage/termination statutes often depend on establishment size, whether the person is a 'workman', and written terms. Those filters are not in the user's story yet.",
            "May apply if the employment relationship and statutory coverage are proved.",
            "Startups/contracting labels are often disputed.",
            ["Employer may deny the relationship or the amount claimed."],
        )
    return (
        f"FACT: {_snippet(ex, good, amount)} "
        f"LAW: {title} {section}: {quote} "
        "ANALYSIS: This retrieved provision is only potentially relevant. It applies if its factual ingredients are later proved; NyayaLens does not treat retrieval as a conclusion.",
        "Potentially applicable if the required facts and legal conditions are established.",
        "Outcome depends on evidence, the other side's account, and the actual in-force text.",
        ["The other party may argue different facts or that this provision's ingredients are not met."],
    )


def _arguments(ex: ExtractedCase) -> dict:
    amount = _amount(ex)
    good = _good(ex)
    seller = _respondent_name(ex)
    buyer = _claimant_name(ex)
    ev = ", ".join(ex.evidence[:5]) or "the documents mentioned"
    defect = _snippet(ex, "defect", "fail", "leak", "service report", "compressor")
    refused = _snippet(ex, "refus", "expired", "warranty")

    if ex.category == "consumer":
        return {
            "claimant": {
                "position": f"{buyer}'s consumer / buyer position",
                "strongest_arguments": [
                    f"Invoice / payment records for {amount} may show a purchase of {good} for consideration.",
                    defect,
                    f"A service finding of manufacturing defect, if authentic, is stronger than a bare complaint that the product 'did not work'.",
                    f"A 7-day platform return policy, even if it exists, may not automatically cancel statutory consumer remedies — that is a legal argument, not a proved bar.",
                ],
                "weaknesses": [
                    "Only one side's account is on this record; {seller} has not been heard.".format(seller=seller),
                    "Without the actual policy/warranty text, the 7-day vs statutory-rights point cannot be decided.",
                    "If repair was never attempted, a forum might be asked why replacement/refund is the first ask.",
                ],
                "confidence": "medium",
            },
            "respondent": {
                "position": f"{seller}'s / marketplace defence position",
                "strongest_arguments": [
                    refused or f"{seller} may say the platform return window had closed and only manufacturer warranty remains.",
                    "They may dispute that the defect existed at sale, or allege misuse, installation error, or later damage.",
                    "A marketplace may argue it is an intermediary and that the contract of sale is only with the listed seller.",
                    "They may say the appropriate first remedy is repair under warranty, not an immediate refund of " + amount + ".",
                ],
                "possible_defenses": [
                    "Return window expired under platform terms.",
                    "Direct the buyer to brand warranty / authorised service.",
                    "Deny manufacturing defect or challenge the service report.",
                    "Marketplace intermediary defence (if Amazon or similar is joined).",
                ],
                "weaknesses": [
                    f"A contemporaneous service report of a manufacturing defect, plus {ev}, may be hard to dismiss as a mere afterthought.",
                    "Sending the buyer in circles ('seller to resolve' vs 'use warranty') can itself be characterised as poor after-sales handling.",
                ],
                "confidence": "medium",
            },
        }
    if ex.category == "loan":
        return {
            "claimant": {
                "position": "Person claiming repayment",
                "strongest_arguments": [
                    f"A transfer of about {amount} is alleged, with {ev} as possible corroboration.",
                    _snippet(ex, "promised", "repay", "three months", "lent"),
                ],
                "weaknesses": [
                    "If messages never used the word loan, the other side may call it a gift or informal help.",
                    "Missing a written due date weakens a clean breach narrative.",
                ],
                "confidence": "medium",
            },
            "respondent": {
                "position": "Person resisting repayment",
                "strongest_arguments": [
                    "They may deny any enforceable repayment promise and say the transfer was a gift, reimbursement, or already settled.",
                    "They may attack the completeness of chats or say context is missing.",
                ],
                "possible_defenses": [
                    "Denial of promise or agreement.",
                    "Claim that the transfer was a gift or settled account.",
                    "Limitation or lack of proof.",
                ],
                "weaknesses": [
                    f"Contemporaneous {ev} can undermine a bare denial if they discuss repayment.",
                ],
                "confidence": "medium",
            },
        }
    if ex.category == "tenancy":
        return {
            "claimant": {
                "position": "Tenant / deposit-holder position",
                "strongest_arguments": [
                    f"Payment of a deposit of about {amount} is alleged, with {_snippet(ex, 'deposit', 'moved out')}",
                    "Vacating without recorded damage, if true, undercuts a withholding justification.",
                ],
                "weaknesses": [
                    "Without the written agreement and inspection notes, lawful deductions cannot be ruled in or out.",
                ],
                "confidence": "medium",
            },
            "respondent": {
                "position": "Landlord position",
                "strongest_arguments": [
                    "They may claim unpaid rent, utilities, or damage exceeding wear and tear.",
                    "They may dispute the date of handover or that vacant possession was given.",
                ],
                "possible_defenses": [
                    "Set-off for dues or damage.",
                    "No written tenancy / different terms.",
                    "Deposit already adjusted.",
                ],
                "weaknesses": [
                    "If they cannot produce an inspection inventory, a blanket withholding of the full deposit is harder to justify.",
                ],
                "confidence": "medium",
            },
        }
    if ex.category == "employment":
        return {
            "claimant": {
                "position": "Worker's position",
                "strongest_arguments": [
                    _snippet(ex, "worked", "salary", "terminated"),
                    f"Unpaid wages/settlement of about {amount} are alleged, with {ev} as possible support.",
                ],
                "weaknesses": [
                    "No written contract makes status (employee vs contractor) and notice terms harder to prove.",
                ],
                "confidence": "medium",
            },
            "respondent": {
                "position": "Employer's position",
                "strongest_arguments": [
                    "They may deny the relationship, the period, or the amount.",
                    "They may allege performance issues or that dues were paid.",
                ],
                "possible_defenses": [
                    "Contractor / consultant label.",
                    "Payment already made.",
                    "Misconduct justifying termination.",
                ],
                "weaknesses": [
                    "Salary slips and email trails, if genuine, often cut against a total denial.",
                ],
                "confidence": "medium",
            },
        }
    if ex.category == "cyber":
        return {
            "claimant": {
                "position": "Complainant's position",
                "strongest_arguments": [
                    _snippet(ex, "otp", "upi", "transfer", "message"),
                    f"Electronic traces ({ev}) should be preserved immediately.",
                ],
                "weaknesses": [
                    "The actor may be unidentified; civil recovery then depends on tracing the money.",
                ],
                "confidence": "medium",
            },
            "respondent": {
                "position": "Unknown actor / platform position",
                "strongest_arguments": [
                    "Identity and dishonest intent may be denied or never proved.",
                    "A platform may argue it is an intermediary once due diligence steps are shown.",
                ],
                "possible_defenses": [
                    "Wrong person / identity not proved.",
                    "Consent or authorised transaction.",
                    "Intermediary safe-harbour arguments.",
                ],
                "weaknesses": [
                    "Call logs plus an OTP plus an immediate debit can be a strong circumstantial cluster if authenticated.",
                ],
                "confidence": "medium",
            },
        }
    return {
        "claimant": {
            "position": "User position",
            "strongest_arguments": [ex.sentences[0] if ex.sentences else "The stated facts may support a claim if proved."],
            "weaknesses": ["Key documents and the other side's account are missing."],
            "confidence": "low",
        },
        "respondent": {
            "position": "Opposing position",
            "strongest_arguments": ["They may dispute the characterisation of events."],
            "possible_defenses": ["Denial and lack of proof."],
            "weaknesses": ["Documents listed by the user, if genuine, may narrow the denial."],
            "confidence": "low",
        },
    }


def _recommendations_json(ex: ExtractedCase) -> str:
    ev = ", ".join(ex.evidence[:5]) or "messages, receipts, contracts, and transaction records"
    amount = _amount(ex)
    place = _place(ex)
    seller = _respondent_name(ex)
    items: list[dict] = [
        {
            "action": f"Preserve {ev} in original form (export chats, keep invoice PDFs, do not edit screenshots).",
            "rationale": "Later disputes often turn on whether the record is complete and authentic.",
            "priority": "high",
        }
    ]
    if ex.category == "consumer":
        items.extend(
            [
                {
                    "action": f"Send {seller} and the marketplace a dated written complaint attaching the service report and stating whether you seek repair, replacement, or refund of {amount}.",
                    "rationale": "A clear demand record may matter if the dispute is later taken to a consumer commission.",
                    "priority": "high",
                },
                {
                    "action": f"Note territorial connection with {place} and do not assume the 7-day platform window is the last word — ask an advocate about Consumer Protection Act remedies and limitation.",
                    "rationale": "Platform policy and statutory rights can diverge; this tool cannot file or choose a forum.",
                    "priority": "medium",
                },
            ]
        )
    elif ex.category == "tenancy":
        items.append(
            {
                "action": "Ask in writing for an itemised statement of any proposed deposit deductions and copies of the agreement/inspection notes.",
                "rationale": "A blanket refusal to refund is harder to justify without particulars.",
                "priority": "high",
            }
        )
    elif ex.category == "cyber":
        items.append(
            {
                "action": "Preserve UTR/UPI references, call recordings if lawful, and consider a cyber-crime / police complaint if advised — do not pay further 'recovery' agents.",
                "rationale": "Speed and unaltered electronic records matter; further OTP sharing usually worsens the position.",
                "priority": "high",
            }
        )
    elif ex.category == "employment":
        items.append(
            {
                "action": f"Write to the employer seeking an itemised final settlement for about {amount} and copies of appointment/termination documents.",
                "rationale": "A paper trail of demand helps if wages or termination later go to a labour or civil forum.",
                "priority": "high",
            }
        )
    elif ex.category == "loan":
        items.append(
            {
                "action": f"Send a dated written reminder stating the amount ({amount}), the alleged due date, and attaching the UPI/chat record.",
                "rationale": "A documented demand may support a later recovery attempt; it is not itself a court filing.",
                "priority": "medium",
            }
        )
    items.append(
        {
            "action": "Consult a qualified advocate with this evidence before filing anything.",
            "rationale": "NyayaLens is general information. Strategy, limitation, and forum choice need professional advice.",
            "priority": "high",
        }
    )
    return json.dumps(items[:5])


def _chat_answer(prompt: str) -> str:
    ex = extract(prompt)
    question = _section_after(prompt, "USER QUESTION:") or prompt[-400:]
    sources = _parse_sources(prompt) or []
    law_line = ""
    if sources:
        _sid, title, section, text = sources[0]
        law_line = f"LAW: Retrieved {title} {section}: {text.strip()[:280]}"
    else:
        law_line = "LAW: No sufficiently specific provision was retrieved for this follow-up. Do not treat that as a finding that no law exists."

    q = question.lower()
    if any(w in q for w in ["amazon", "marketplace", "platform", "flipkart"]):
        analysis = (
            f"ANALYSIS: Joining a marketplace as an opposite party depends on its role in the sale of {_good(ex)}, "
            "the contract terms, and Consumer Protection Act concepts — not on the ticket status 'seller to resolve' alone."
        )
    elif any(w in q for w in ["7-day", "seven day", "return window", "return policy"]):
        analysis = (
            "ANALYSIS: A short platform return window may be a contractual term the seller relies on. "
            "Whether it can defeat statutory consumer remedies after a recorded manufacturing defect is a legal question; this tool cannot decide it."
        )
    elif any(w in q for w in ["forum", "commission", "where to file", "district"]):
        analysis = (
            f"ANALYSIS: Consumer complaints are often discussed in terms of a District Commission with territorial links "
            f"(for example {_place(ex)}) and pecuniary limits tied to {_amount(ex)}. An advocate must confirm forum and limitation."
        )
    elif any(w in q for w in ["evidence", "screenshot", "invoice", "prove"]):
        analysis = (
            f"ANALYSIS: {', '.join(ex.evidence[:4]) or 'The listed documents'} may help, especially if kept unedited. "
            "Electronic records can still be challenged on authenticity."
        )
    else:
        analysis = (
            f"ANALYSIS: On the stated facts, {_snippet(ex, 'defect', 'deposit', 'otp', 'salary', 'lent')} "
            "The other side has not been heard. Retrieved law is only a starting point."
        )

    return (
        f"FACT: {_snippet(ex, 'bought', 'deposit', 'otp', 'lent', 'terminated')}\n"
        f"{law_line}\n"
        f"{analysis}\n"
        "RECOMMENDATION: Preserve the original files and take this record to a qualified advocate. "
        "This is general information, not legal advice."
    )


def generate_text(prompt: str, system_prompt: str | None = None) -> str:
    if "USER QUESTION:" in prompt or (system_prompt and "follow-up" in system_prompt.lower()):
        return _chat_answer(prompt)
    if "JSON" in prompt or "next steps" in prompt.lower():
        return _recommendations_json(extract(prompt))
    return _chat_answer(prompt)


def build_structured(model: Type[T], prompt: str) -> T:
    from nyayalens_schemas.enums import ConfidenceLevel, LegalDomain

    from app.services.argument_analyzer_models import ArgumentAnalysisResult
    from app.services.case_parser_models import CaseParseResult
    from app.services.classification import ClassificationResult
    from app.services.issue_identifier_models import IdentifiedIssue, IssueIdentificationResult
    from app.services.legal_analyzer_models import AnalyzedProvision, IssueLegalAnalysis, LegalAnalysisResult

    ex = extract(prompt)
    name = model.__name__

    if name == "ClassificationResult":
        domain_map = {
            "tenancy": [LegalDomain.TENANCY, LegalDomain.PROPERTY, LegalDomain.CONSUMER],
            "cyber": [LegalDomain.CYBER, LegalDomain.CRIMINAL],
            "consumer": [LegalDomain.CONSUMER, LegalDomain.CONTRACT],
            "employment": [LegalDomain.EMPLOYMENT],
            "loan": [LegalDomain.CONTRACT, LegalDomain.CIVIL_PROCEDURE],
            "other": [LegalDomain.OTHER],
        }
        inferences = [
            "The other party's account is not in this record.",
        ]
        if ex.category == "consumer" and ("7-day" in ex.text.lower() or "7 day" in ex.text.lower()):
            inferences.append(
                "INFERENCE (not a finding): a platform return window, if it exists, may not automatically extinguish statutory consumer remedies."
            )
        return ClassificationResult(
            domains=domain_map.get(ex.category, [LegalDomain.OTHER]),
            rationale="Domains are indicated by the described transaction and complaints, not by a court finding.",
            summary=_summary(ex),
            inferred_facts=inferences,
        )

    if name == "CaseParseResult":
        return model(
            case_type={
                "tenancy": "Potential tenancy / security deposit dispute",
                "cyber": "Potential cyber / online fraud or harassment dispute",
                "consumer": "Potential consumer dispute",
                "employment": "Potential employment / wages dispute",
                "loan": "Potential contractual / money-recovery dispute",
            }.get(ex.category, "Potential civil dispute"),
            parties=_default_parties(ex),
            facts=_facts(ex),
            evidence_mentioned=ex.evidence or ["documents mentioned in the description"],
            disputed_facts=[s for s in ex.sentences if any(w in s.lower() for w in ["refus", "deny", "expired", "withhold"])][:3],
            unknown_facts=_unknown(ex),
        )

    if name == "IssueIdentificationResult":
        issues = [IdentifiedIssue(**item) if not isinstance(item, IdentifiedIssue) else item for item in _issues(ex)]
        return model(issues=issues)

    if name == "LegalAnalysisResult":
        issue_ids = _extract_ids(_section_after(prompt, "ISSUES:") or prompt) or [uuid4()]
        sources = _parse_sources(prompt)
        if not sources:
            sources = [(sid, "Retrieved source", "N/A", "") for sid in (_extract_ids(_section_after(prompt, "RETRIEVED SOURCES") or prompt) or [uuid4()])]
        analyses = []
        for issue_id in issue_ids[:3]:
            provisions = []
            for sid, title, section, text in sources[:4]:
                explanation, applicability, uncertainty, counters = _explain_source(title, section, text, ex)
                provisions.append(
                    AnalyzedProvision(
                        legal_source_id=sid,
                        explanation=explanation,
                        applicability=applicability,
                        uncertainty=uncertainty,
                        counterarguments=counters,
                        confidence=ConfidenceLevel.MEDIUM,
                        claim=f"{title} {section} may be relevant if its ingredients are proved on these facts.",
                    )
                )
            analyses.append(
                IssueLegalAnalysis(
                    issue_id=issue_id,
                    summary=_summary(ex),
                    provisions=provisions,
                    overall_confidence=ConfidenceLevel.MEDIUM,
                )
            )
        return model(analyses=analyses)

    if name == "ArgumentAnalysisResult":
        payload = _arguments(ex)
        return ArgumentAnalysisResult.model_validate(payload)

    try:
        return model()
    except Exception:
        fields = {}
        for field_name, field_info in model.model_fields.items():
            if field_info.default is not None:
                fields[field_name] = field_info.default
            elif field_info.default_factory is not None:
                fields[field_name] = field_info.default_factory()
        return model(**fields)
