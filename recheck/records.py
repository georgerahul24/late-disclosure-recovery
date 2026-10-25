"""Patient records.

A record is a simplified, Synthea-shaped longitudinal history: conditions,
medications (active and stopped), encounters and observations. Stopped
medications are kept on purpose as distractors (for example a clopidogrel
course that ended two years ago), so any code that asks "is this patient on
an antiplatelet?" must look at *active* medications only.

Every fact has a stable `fact_id`. Scenarios name the decisive fact by id, and
the grader checks whether an agent cited it (stage 2, context).
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

# Medication classes used by the record rules: ingredient (or brand) words
# matched as whole words inside the medication name. This works for plain
# generic names ("clopidogrel") and for Synthea/RxNorm descriptions
# ("clopidogrel 75 MG Oral Tablet", "Humulin 70/30 Injectable Suspension").
# Keep this list in sync with data/README.md.
MED_CLASSES: dict[str, set[str]] = {
    "anticoagulant": {"warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban", "enoxaparin", "heparin",
                      "dalteparin", "fondaparinux", "jantoven", "coumadin", "eliquis", "xarelto", "pradaxa"},
    "antiplatelet": {"clopidogrel", "ticagrelor", "prasugrel", "aspirin", "dipyridamole", "plavix", "brilinta",
                     "effient", "ticlopidine", "cilostazol"},
    "insulin": {"insulin", "humulin", "novolin", "lantus", "levemir", "humalog", "novolog", "glargine", "lispro",
                "aspart", "detemir", "degludec"},
    "sulfonylurea": {"gliclazide", "glipizide", "glimepiride", "glibenclamide", "glyburide"},
    # ADA SOC 2025 sec 6 and JBDS 01 (2023) name meglitinides with sulfonylureas
    # as insulin secretagogues that cause hypoglycaemia (docs/clinical_sources.md A2).
    "meglitinide": {"repaglinide", "nateglinide"},
    "other_diabetes": {"metformin", "sitagliptin", "empagliflozin", "dapagliflozin", "canagliflozin",
                       "liraglutide", "semaglutide", "pioglitazone"},
}
NON_ASPIRIN_ANTIPLATELET = MED_CLASSES["antiplatelet"] - {"aspirin"}
_WORD = re.compile(r"[a-z]+")


def med_classes(name: str) -> set[str]:
    words = set(_WORD.findall(name.lower()))
    return {cls for cls, members in MED_CLASSES.items() if words & members}


def med_class(name: str) -> str | None:
    """The single most safety-relevant class, by priority."""
    cls = med_classes(name)
    for c in ("anticoagulant", "antiplatelet", "insulin", "sulfonylurea", "meglitinide", "other_diabetes"):
        if c in cls:
            return c
    return None


def is_non_aspirin_antiplatelet(name: str) -> bool:
    return bool(set(_WORD.findall(name.lower())) & NON_ASPIRIN_ANTIPLATELET)


@dataclass
class Medication:
    fact_id: str
    name: str
    start: str  # ISO date
    stop: str | None = None  # None means still active

    @property
    def active(self) -> bool:
        return self.stop is None

    @property
    def med_class(self) -> str | None:
        return med_class(self.name)


@dataclass
class Condition:
    fact_id: str
    name: str
    onset: str
    resolved: str | None = None

    @property
    def active(self) -> bool:
        return self.resolved is None


@dataclass
class Encounter:
    fact_id: str
    date: str
    kind: str
    reason: str


@dataclass
class Observation:
    fact_id: str
    date: str
    name: str
    value: str


@dataclass
class PatientRecord:
    patient_id: str
    name: str
    birth_date: str
    sex: str
    conditions: list[Condition] = field(default_factory=list)
    medications: list[Medication] = field(default_factory=list)
    encounters: list[Encounter] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)

    def age(self, on: date | None = None) -> int:
        on = on or REFERENCE_DATE
        b = date.fromisoformat(self.birth_date)
        return on.year - b.year - ((on.month, on.day) < (b.month, b.day))

    def active_meds(self) -> list[Medication]:
        return [m for m in self.medications if m.active]

    def active_med_classes(self) -> set[str]:
        return {m.med_class for m in self.active_meds() if m.med_class}

    def active_conditions(self) -> list[Condition]:
        return [c for c in self.conditions if c.active]

    def has_condition(self, keyword: str) -> bool:
        """Whole-word match on active conditions. "diabetes" does NOT match
        "Prediabetes" (a real Synthea condition)."""
        pat = re.compile(rf"\b{re.escape(keyword.lower())}\b")
        return any(pat.search(c.name.lower()) for c in self.active_conditions())

    def is_diabetic(self) -> bool:
        return any(re.search(r"\bdiabetes\b", c.name.lower()) and "prediabetes" not in c.name.lower()
                   and "gestational" not in c.name.lower() for c in self.active_conditions())

    def facts(self) -> list[dict]:
        """Flatten the record into retrievable text facts (one per item).

        This is what search_record indexes and what the RAG step retrieves.
        """
        out = []
        for m in self.medications:
            status = "active" if m.active else f"stopped {m.stop}"
            out.append({"fact_id": m.fact_id, "type": "medication",
                        "text": f"Medication: {m.name} (started {m.start}, {status})"})
        for c in self.conditions:
            status = "active" if c.active else f"resolved {c.resolved}"
            out.append({"fact_id": c.fact_id, "type": "condition",
                        "text": f"Condition: {c.name} (onset {c.onset}, {status})"})
        for e in self.encounters:
            out.append({"fact_id": e.fact_id, "type": "encounter",
                        "text": f"Encounter {e.date}: {e.kind} for {e.reason}"})
        for o in self.observations:
            out.append({"fact_id": o.fact_id, "type": "observation",
                        "text": f"Observation {o.date}: {o.name} = {o.value}"})
        return out

    def summary(self) -> dict:
        """Short header returned by get_patient_record (not the full history)."""
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age(),
            "sex": self.sex,
            "n_facts": len(self.facts()),
            "note": "Full history is long. Use search_record to look up medications, conditions and visits.",
        }

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PatientRecord":
        return cls(
            patient_id=d["patient_id"],
            name=d["name"],
            birth_date=d["birth_date"],
            sex=d["sex"],
            conditions=[Condition(**c) for c in d.get("conditions", [])],
            medications=[Medication(**m) for m in d.get("medications", [])],
            encounters=[Encounter(**e) for e in d.get("encounters", [])],
            observations=[Observation(**o) for o in d.get("observations", [])],
        )


# All ages and "active" checks are computed relative to this fixed date so
# results do not drift with the wall clock.
REFERENCE_DATE = date(2026, 11, 2)


def load_patients(path: str | Path) -> dict[str, PatientRecord]:
    data = json.loads(Path(path).read_text())
    return {d["patient_id"]: PatientRecord.from_dict(d) for d in data}


def save_patients(patients: list[PatientRecord], path: str | Path) -> None:
    Path(path).write_text(json.dumps([p.to_dict() for p in patients], indent=1))
