"""Late-disclosure recovery benchmark and the RECHECK agent.

Module map (see recheck/README.md for the full contract of each one):
    records     patient records, medication classes, fact lookup
    rules       record rules: is this symptom urgent for this patient?
    policy      clinic policy passages and keyword search over them
    scenarios   scenario and episode definitions, loading from JSON
    backend     the mock clinic backend (slots, bookings, escalations, faults)
    tools       per-conversation tool harness: allow-list, authority, ledger, logs
    simulator   rule-based, event-triggered patient
    runner      runs one episode or a whole suite
    grader      end-state classification, outcome schemes, unsafe actions, stages
    analysis    scenario-clustered bootstrap, paired differences, tables
    detectors   keyword, TF-IDF, oracle (and later LoRA) symptom detectors
    controllers scripted pilot controllers and the deterministic DSC
    agents      LLM agents: Plain, Safety prompt, Plain+Label, RECHECK, Hybrid
"""

__version__ = "0.1.0"
