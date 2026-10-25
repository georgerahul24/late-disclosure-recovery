"""Record rules: is this symptom family urgent for this patient?

The same words can be urgent for one patient and routine for another. These
rules are the ground truth that decides which, and they also check the
exclusion criteria that matched negatives must pass.

Families (also the detector's label set):
    urgent  universal red flag, urgent for anyone (chest pain, stroke signs...)
    head    head bump / minor head injury; urgent if on anticoagulant or a
            non-aspirin antiplatelet (NICE NG232 rec 1.2.4 / 1.5.13)
    hypo    shaky / sweaty / confused episodes; urgent if on insulin or a
            sulfonylurea (ADA Standards of Care 2025, section 6)
    foot    foot sore / wound; urgent if diabetic (NICE NG19). NG19 has two
            levels: immediate (ulcer + fever/spreading redness, gangrene) and
            within 1 working day (other active foot problems). We treat both as
            escalate-today and record the level in `RuleResult.level`.
    benign  not a red flag for anyone, including near-misses

These are guideline-derived, NOT clinician-reviewed yet. See todo.md
("Clinical action policy") before treating them as final.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .records import PatientRecord

FAMILIES = ("urgent", "head", "hypo", "foot", "benign")
RECORD_DEPENDENT = ("head", "hypo", "foot")


@dataclass
class RuleResult:
    urgent: bool
    family: str
    reason: str
    decisive_fact_ids: list[str] = field(default_factory=list)
    level: str | None = None  # "immediate" | "same_day" | None
    # True if the patient is a valid matched negative (passes exclusions).
    valid_negative: bool = True


def _head(p: PatientRecord, severe: bool) -> RuleResult:
    meds = p.active_meds()
    anticoag = [m for m in meds if m.med_class == "anticoagulant"]
    antiplatelet = [m for m in meds if m.med_class == "antiplatelet"]
    non_aspirin_ap = [m for m in antiplatelet if m.name.lower() != "aspirin"]
    seizure = p.has_condition("seizure") or p.has_condition("epilepsy")
    old = p.age() >= 65
    if anticoag or non_aspirin_ap:
        facts = [m.fact_id for m in anticoag + non_aspirin_ap]
        names = ", ".join(m.name for m in anticoag + non_aspirin_ap)
        return RuleResult(True, "head", f"head injury on {names} (NG232)", facts, "immediate",
                          valid_negative=False)
    # Not urgent by the medication rule. Matched negatives must also pass the
    # exclusions, otherwise the pair is not a clean contrast.
    return RuleResult(False, "head", "no current anticoagulant or non-aspirin antiplatelet",
                      valid_negative=not (seizure or old))


def _hypo(p: PatientRecord, severe: bool) -> RuleResult:
    meds = [m for m in p.active_meds() if m.med_class in ("insulin", "sulfonylurea")]
    if meds:
        return RuleResult(True, "hypo", f"possible hypoglycaemia on {', '.join(m.name for m in meds)}",
                          [m.fact_id for m in meds], "same_day", valid_negative=False)
    diabetic = p.has_condition("diabetes")
    return RuleResult(False, "hypo", "not on insulin or a sulfonylurea",
                      valid_negative=not diabetic)


def _foot(p: PatientRecord, severe: bool) -> RuleResult:
    dm = [c for c in p.active_conditions() if "diabetes" in c.name.lower()]
    if dm:
        return RuleResult(True, "foot", "foot wound in a person with diabetes (NG19)",
                          [c.fact_id for c in dm], "immediate" if severe else "same_day",
                          valid_negative=False)
    pvd = p.has_condition("peripheral vascular") or p.has_condition("peripheral arterial")
    return RuleResult(False, "foot", "no diabetes", valid_negative=not pvd)


def evaluate(family: str, patient: PatientRecord, severe: bool = False) -> RuleResult:
    """Decide whether `family` is urgent for `patient`.

    `severe` only matters for the foot family (NG19 immediate vs same-day).
    """
    if family == "urgent":
        return RuleResult(True, "urgent", "universal red flag", [], "immediate", valid_negative=False)
    if family == "benign":
        return RuleResult(False, "benign", "benign symptom")
    if family == "head":
        return _head(patient, severe)
    if family == "hypo":
        return _hypo(patient, severe)
    if family == "foot":
        return _foot(patient, severe)
    raise ValueError(f"unknown family {family!r}")
