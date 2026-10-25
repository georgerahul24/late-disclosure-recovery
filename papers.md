# Literature Review: Late-Disclosure Recovery in Stateful Clinical Agents

Last updated: 2026-10-26. Built from three parallel searches: (A) patient-facing health agents and triage, (B) agent recovery, reversibility and state-based grading, (C) method parts and evaluation methods. Each search checked the papers the proposal cites and looked for new ones. About 95 items were looked at. About 85 are listed here after removing duplicates.

**Verification tags.**
- **[V]**: the searcher opened the arXiv, ACL, journal or official page.
- **[P]**: partly verified (title or venue seen only in a snippet or a secondary page).
- **[U]**: not verified. Check by hand before citing.

Never cite a [U] item as is.

---

## 1. Bottom line

1. **The core gap is real, but narrow.** No paper we found tests this exact case: a patient reveals a safety fact late, without being asked, and that fact makes the agent's *own already-committed backend action* wrong. The fact depends on the patient's record. The disclosure time is controlled. Grading uses the final backend state. Every part of this has been studied somewhere. The combination has not.
2. **The benchmark is the contribution. RECHECK is not.** Every RECHECK part already exists in general-agent work: the action ledger and re-check, compensating repair, read-back checks, and a small per-turn guard model. RECHECK should be presented as a targeted baseline method. This matches the reviewer pointers in `docs/pointers.txt`.
3. **Two 2026 papers are now the closest threats, and the proposal does not cite either.**
   - **Zheng et al. 2610.21270** is a healthcare escalation benchmark with "late" and "stale" evidence. It labels actions only. It has no tools, no backend and no repair.
   - **REVISE 2609.00643** finds which completed work a later user message makes invalid, and redoes that work. The message there is an explicit revision, not an implied safety fact. It also does not undo effects that already left the system.
4. **Three other uncited papers weaken sub-claims.**
   - **MedPIC-Bench 2608.03028:** counterfactual patient-info pairs for medication safety, in static question-answer form.
   - **PMR-Bench 2601.13178:** message urgency judged using the patient's EHR, with small fine-tuned models.
   - **AgentAbstain 2607.10059:** names "post-hoc abstention", where the agent acts first and notices later. It explicitly leaves repair out of scope.
5. **Safe novelty sentence:** "No prior benchmark tests an implicit, safety-relevant user disclosure, placed at a controlled point relative to the agent's own committed backend actions, whose urgency depends on the patient record, and grades recovery by final backend state."
6. **Citation fixes are minor.** No cited paper is made up. A few titles, IDs and venues need fixing (section 9).

---

## 2. Feature matrix: who covers what

Legend: Y = yes, P = partly, - = no.

| Work | Patient-facing | Tools + stateful backend | Disclosure timing controlled | Disclosure after a committed action | Record decides urgency | Final-state grading | Repair of past action | Read-back / tool faults | Stage-level failure analysis |
|---|---|---|---|---|---|---|---|---|---|
| **Ours** | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| PatientAgentBench 2607.25485 | Y | Y | - | - | P | - (LLM jury) | - | - | - |
| CareConnect 2607.05055 | Y | Y | - | - | - | P (tool sequence) | - | - | - |
| CARE-Bench 2608.03731 | Y | - | Y (prefixes) | - | - | - | - | - | - |
| Zheng et al. 2610.21270 | P | - | P (late/stale variants) | - | - | - (action labels) | - | - | P |
| Yao et al. 2609.00296 (protocol) | P | P | P | - | - | P (proposed) | - | - | - |
| ELICITED 2608.09024 | Y | - | Y | - | P (EHR-grounded) | - | - | - | - |
| Srirag et al. 2609.22904 | Y | - | Y (checkpoints) | - | - | - | - | - | - |
| MedPIC-Bench 2608.03028 | - | - | - | - | Y (static QA) | - | - | - | - |
| PMR-Bench 2601.13178 | Y | - | - | - | Y | - | - | - | - |
| MedAgentBench 2501.14654 | - | Y (FHIR) | - | - | - | Y | - | - | - |
| τ-bench / τ²-bench | - | Y | - | - | - | Y | - | - | - |
| AgentChangeBench 2510.18170 | - | Y | P (goal shift) | P (explicit goal change) | - | Y | P | - | - |
| InterventionBench (EMNLP-F 2026) | - | Y | Y | P (explicit) | - | Y | ? | - | - |
| REVISE 2609.00643 | - | Y | P | P (explicit revision) | - | P | Y (recompute) | P | - |
| Zhai et al. 2604.23283 | - | Y | P | P (explicit) | - | P | Y (compensate) | - | - |
| AgentAbstain 2607.10059 | - | Y | P (emergent risk) | P (names it, no repair) | - | - (LLM judge) | - | - | - |
| SABER 2512.07850 | - | Y | - | - | - | Y | - (guards next step) | - | P |
| Verified Tool Calls 2608.02645 | - | Y | - | - | - | Y | - | Y | - |

**How to read this.** The healthcare papers (top block) have the patient and urgency columns but miss the committed-action columns. The general agent papers (bottom block) have the committed-action and repair columns, but the trigger there is an explicit user change, not a fact the agent has to infer, and none are clinical. Our work sits where the two blocks meet.

---

## 3. Patient-facing health agents and triage

### 3.1 Closest competitors (must cite and contrast)

**PatientAgentBench** [V]. Vatanparvar, Joshi, Xenochristou, ... Hakkani-Tur, Schulz-Mahlendorf. arXiv:2607.25485, 2026. *Cited.*
- **What it does:** A simulated patient talks to an agent with 15 stateful tools, including schedule_appointment, cancel_appointment, list_appointments and message_pcp. It has 1,200 scenarios, 10 models and an LLM jury scoring 6 dimensions. Triage separates models best (32-88% pass). Weak models claim actions they never took. It reports that agents "processed administrative requests transactionally, without asking clinical questions."
- **Overlap:** Very high on setup. Its tool design could be reused.
- **Gap:** No control over when the disclosure comes. No scenario where the patient reveals a red flag after booking. No record-matched pairs. Grading is by LLM jury, not final state. No stage analysis. No tool faults.
- **Threat:** We cannot claim to be "first patient-facing stateful benchmark" or "first to show agents book without screening." Use its finding as motivation.
- **To do:** About 38k of its 238k characters were not read. Check the rest for any post-booking disclosure scenario.

**CareConnect: "Toward Trustworthy Large Language Model Agents in Healthcare"** [V]. Hasan, Salman, Abou Dargham, Mohanna, Chehab. arXiv:2607.05055, 2026. *Cited.*
- **What it does:** A booking agent with 8 tools. A deterministic rule-based intent filter (English and Arabic) runs before the LLM and short-circuits to an emergency message or a refusal. It reaches 91.8% task completion and 96.0% safety compliance on 680 scenarios (150 safety).
- **Overlap:** Same tool family. This is our Rule gate baseline.
- **Gap:** Safety cases are single-shot emergency phrases. No late or post-booking disclosure. Urgency does not use the record. Grading is by expected tool sequence. The paper does not say the gate runs on every turn.

**CARE-Bench** [V]. Hua, Na, Ayubcha. arXiv:2608.03731, 2026. *Cited.*
- **What it does:** 500 cases with 1,059 patient-disclosure prefixes, each scored with a 4-label next-action label, across 11 models. Macro-F1 is 31-50 unprompted. Models recommend care before asking the key questions.
- **Overlap:** The timing of disclosure matters.
- **Gap:** No tools, state, record or earlier action.
- **Threat:** "Disclosure timing" alone is not new. Our new part is timing *relative to committed actions*.

**Zheng, Yao, Li, Long. "Auditing Escalation Reliability in Healthcare LLM Agents: A Perturbation-Controlled Benchmark of Workflow-State Failures"** [V]. arXiv:2610.21270, Oct 2026. **Not cited. Must add.**
- **What it does:** 400 synthetic healthcare workflow episodes, built from 40 seeds with 5 variants: missing, stale, conflicting and *late* evidence. Each response is labelled Answer / Ask / Abstain / Escalate, and a missed escalation costs 5x. A workflow-aware controller reduces missed escalations. A rule detector falls from 1.00 recall on trigger phrases to 0.00 on unseen paraphrases.
- **Overlap:** Very high: healthcare, late evidence, escalation, a controller baseline, keyword brittleness.
- **Gap:** Grades action labels only. No tools, backend, executed booking or repair. Labels come from a single author.
- **Use:** The closest competitor. Its paraphrase result directly supports our keyword-gate baseline.

**"Toward Workflow-Aware Benchmarking for Healthcare NLP Agents"** [V]. Junyi Yao, Baichuan Li, Zihao Zheng, Jiayu Long. arXiv:2609.00296, 2026. *Cited.*
- **What it does:** A protocol paper. It proposes episode-level scores for state continuity, evidence traceability and escalation, with missed escalations weighted more. It reports no clinical results.
- **Threat:** Mild. Asymmetric escalation scoring and state continuity are already proposed here. Present ours as the first concrete benchmark plus a method. Note it shares authors with Zheng et al. 2610.21270.

### 3.2 Sequential disclosure and anchoring

| Paper | What it does | Relation to us |
|---|---|---|
| **Srirag et al. "LLMs Anchor on Chief Complaint and Fail to Integrate Evidence in Sequential Clinical Triage"** [V] arXiv:2609.22904, 2026. *Cited.* | 6 LLMs give ESI at 5 checkpoints in 475 conversations. Predictions stay anchored to the first complaint. Best QWK 0.295, against 0.89-0.93 for clinicians. Prompting does not help. | Direct evidence for stage-1/stage-3 failure. No tools. |
| **ELICITED / EHR2Dial-Triage** [V] Zhu, Shi, Zhou. arXiv:2608.09024, 2026. *Cited.* | ED triage dialogues from MIMIC-IV-ED. Each disclosure is tied to an EHR event and the turn it appears. | EHR-grounded timing. Predicts acuity, not actions. Cite under both names. |
| **Laban, Hayashi, Zhou, Neville. "LLMs Get Lost In Multi-Turn Conversation"** [V] arXiv:2505.06120, 2025 (ICLR 2026 per a secondary source). **Not cited.** | A 39% average drop when information is split across turns. Models commit early and do not recover. | The strongest general motivation for late disclosure. We test it in a stateful clinical setting. |
| **Tack, Laban, Neville. "LLMs Get Lost in Evolving User Intent"** [V] arXiv:2607.20734, 2026. **Not cited.** | Users reveal, revise or redirect intent. Large drops. | General, not stateful. |
| **Hua et al. "LLMs for Medical Consultation Are Evaluated Too Late: The Preformulation Gap"** [V] arXiv:2608.17330, 2026. | Models give self-care advice before asking questions. An "entry-to-care" prompt fixes the order, not the eliciting. | Supports the claim that a safety prompt alone is not enough. Supports our Safety-prompt baseline. |
| **MediQ** [V] Li et al. NeurIPS 2024, arXiv:2406.00922. | Partial info at the start. The model decides whether to ask or answer. | Information gathering, no actions. |
| **AgentClinic** [V] Schmidgall et al. arXiv:2405.07960. | Doctor agent with a simulated patient. Accuracy drops in sequential form and with biases. | Clinician-side diagnosis. Precedent for a patient simulator. |
| **CRAFT-MD** [P] Johri et al. "An evaluation framework for clinical use of large language models in patient interaction tasks." Nature Medicine, Jan 2025. | LLM patient plus LLM grader, audited by experts. Accuracy drops in conversation compared with vignettes. | Simulator and judge precedent. Confirm the title. |
| **"When Patients Cut In"** [V] Ellis et al. Findings EMNLP 2026, arXiv:2608.29241. | Interruptions make voice agents drop safety-netting. | Another disruption of turn order. Low relevance. |
| **MTDiag** [V] SIGDIAL 2026, arXiv:2608.25085. | Multi-turn diagnostic dialogues. | Low relevance. |

### 3.3 Under-triage and real-world safety evidence (motivation)

| Paper | Key finding |
|---|---|
| **Ramaswamy et al. "ChatGPT Health performance in a structured test of triage recommendations"** [V] Nature Medicine 32:1671-1675, 2026. doi:10.1038/s41591-026-04297-7 | About 48-52% of emergencies were under-triaged. When family members downplayed symptoms, triage shifted (OR 11.7). Strong motivation. |
| **Bean et al. "Reliability of LLMs as medical assistants for the general public"** [V] Nature Medicine 32:609-615, 2026. doi:10.1038/s41591-025-04074-y (arXiv 2504.18919, different title) | Models alone get 94.9% of conditions right. Users helped by the models get under 34.5%. Knowledge does not carry over into the interaction. |
| **HealthBench** [V] Arora et al. arXiv:2505.08775, 2025. *Cited.* | 5,000 conversations with 48.5k physician rubric items and an emergency-referral theme. Grades text only. |
| **MATRIX** [V] Lim et al. arXiv:2508.19163, 2025. | Clinical hazard taxonomy, the BehvJudge evaluator validated against clinicians, and the PatBot simulator. Useful for validating our simulator and safety labels. |

### 3.4 Other healthcare agent benchmarks (background)

| Paper | Notes |
|---|---|
| **MedAgentBench** [V] Jiang et al. arXiv:2501.14654, 2025 (possibly NEJM AI, doi 10.1056/AIdbp2500144 [U]). *Cited.* | FHIR virtual EHR with 300 clinician tasks and 100 patients. Best 69.7%. Clinician-facing. A later audit (arXiv:2609.37315 [U]) says it grades writes from the request sent, not by reading the record back. That supports our read-back grading. |
| **GPAgentBench-2K** [V] Boqi Chen et al. arXiv:2608.30188, 2026. *Cited.* | GP encounters framed as a constrained MDP. Accurate models break safety constraints in more than half of high-risk cases. Clinician-side. |
| **CHI-Bench** (cited as "χ-Bench") [V] Haolin Chen et al. (33 authors). arXiv:2605.16679, 2026. *Cited.* | Payer and operations workflows with 87 tools and a 1,290-document handbook. Best 28%. Note the title spelling. |
| **MediEval** [V] Qu, Färber. ACL 2026 long, doi:10.18653/v1/2026.acl-long.734, arXiv:2512.20822. *Cited.* | MIMIC-IV plus UMLS. Checks claims against the patient record and medical knowledge. Static. |
| **HealthAdminBench** [V] Bedi et al. arXiv:2604.09937, 2026. | Computer-use agents for prior authorization and appeals. Admin, but not patient-facing. |
| **PhysicianBench** [V] Ruoqi Liu et al. arXiv:2605.02240, 2026. | 100 EHR tasks with 670 checkpoints verified in the environment. A precedent for state verification. |
| **PhysAssistBench** [V] Du et al. arXiv:2606.18613, 2026. | Agentic patients built from MIMIC-IV. |
| **FHIR-AgentBench** [V] Gyubok Lee et al. ML4H 2025, arXiv:2509.19319. | 2,931 FHIR QA questions. Separates retrieval failures from reasoning failures. |
| **AMIE** [V] Tu et al. Nature 642:442-450, 2025. | Diagnostic dialogue. Background only. |
| **Gupta, Kumar, Dang. "Agentic AI for Clinical Urgency Mapping..."** [V] arXiv:2604.00215, 2026. | Outpatient queue re-prioritized as urgency drifts. Simulation only. |

---

## 4. Message urgency detection and guard models

| Paper | What it does | Relation to us |
|---|---|---|
| **Liu S. et al. "Detecting emergencies in patient portal messages using LLMs and KG-RAG"** [V] JAMIA 32(6):1032-1039, 2025. doi:10.1093/jamia/ocaf059. *Cited.* | 1,020 messages with only 41 emergencies. KG-RAG over a nurse triage book reaches sensitivity 0.98 and precision 0.80. Prompt-only reaches 0.73 sensitivity. | Single-turn and does not use the record. The few positives give wide confidence intervals; say so if we compare. |
| **PMR-Bench. Gatto et al. "Medical Triage as Pairwise Ranking"** [V] arXiv:2601.13178, 2026. **Not cited. Add.** | 1,569 messages, some paired with EHR data. Fine-tuned 8B models (UrgentSFT, UrgentReward) beat off-the-shelf models by 15-16 points. | The closest record-conditioned urgency work, but static inbox ranking. Supports small fine-tuned models. We must argue why we split text detection from record grounding. |
| **Noora Health. Jagga et al. "Auditable Emergency Triage for Maternal and Newborn Care in India"** [V] arXiv:2609.09356, 2026. | The LLM extracts symptoms and context. A deterministic clinician rule engine decides. Recall rises from 0.565 to 0.810. Deployed on about 152k queries. States that the same symptom has different urgency in different patient contexts. | A deployed precedent for our DSC and Hybrid design. Cite in Baselines. |
| **Zhou, Li. "Few-Shot LLMs for Actionable Triage Categorization of Online Patient Inquiries"** [V] arXiv:2605.15680, 2026. | 4-level routing, best macro-F1 0.475. | Detector baseline context. |
| **Llama Guard** [V] Inan et al. arXiv:2312.06674, 2023. **Add.** | A small model that classifies each turn against a risk taxonomy. | Our detector follows the same "guard model" pattern. Frame the detector as a clinical guard. |
| **Llama Guard 3-1B-INT4** [V] Fedorov et al. arXiv:2411.17713, 2024. | A 440MB guard that runs on a phone CPU. | Supports the claim that a 0.5-1.5B monitor is enough. |
| **ShieldGemma** [U] Zeng et al. 2024. | Guard model. | Low priority. |
| **Bucher, Martini. "Fine-Tuned 'Small' LLMs (Still) Significantly Outperform Zero-Shot Generative AI Models in Text Classification"** [V] arXiv:2406.08660, 2024. | Fine-tuned encoders beat zero-shot GPT-4 and Claude. | Supports LoRA against the prompted large model. Not clinical. |
| **Edwards, Camacho-Collados. "Language Models for Text Classification: Is In-Context Learning Enough?"** [P] arXiv:2403.17661, 2024. | Same direction. | Low priority. |
| **Edinburgh Clinical NLP at SemEval-2024 Task 2** [V] arXiv:2404.00484. | LoRA helps 7B models, but GPT-4 stays strong. | A prompted frontier model may match LoRA. Frame the comparison as cost and latency per turn. |
| **LoRA** [V] Hu et al. ICLR 2022, arXiv:2106.09685. *Cited.* | Low-rank adapters. | Method citation. |

### Robustness of detectors to wording and context

| Paper | What it does | Relation to us |
|---|---|---|
| **Gourabathina, Gerych, Pan, Ghassemi. "The Medium is the Message"** [V] FAccT 2025. **Add.** | Typos, whitespace, tone and gender markers change LLM clinical decisions. | Explains the pilot's 94% to 82% recall drop when the symptom sits inside a booking message. Add these perturbations as invariance tests. |
| **MedPerturb** [V] Gourabathina et al. arXiv:2506.17163, 2025. | 800 contexts with gender, style and format perturbations, 4 LLMs and 3 human raters. | The mirror image of our design: they keep the content and change the surface; we keep the words and change the record. |
| **CheckList** [V] Ribeiro et al. ACL 2020. | Behaviour tests: invariance and directional. | The booking wrapper should not change the label (invariance). A record change should change it (directional). |
| **Contrast sets** [V] Gardner et al. Findings EMNLP 2020, arXiv:2004.02709. **Add.** | Expert edits that flip the label. Up to a 25% drop. | The method ancestor of our record-matched pairs. Use its "contrast consistency" metric: a pair counts as correct only if both sides are. |

---

## 5. Record-conditioned reasoning, EHR retrieval and long context

| Paper | What it does | Relation to us |
|---|---|---|
| **MedPIC-Bench. Hou et al. "Evaluating Counterfactual Sensitivity to Patient Information in Medication-Safety Reasoning"** [V] arXiv:2608.03028, 2026. **Not cited. Must add.** | 467 guideline questions, each with a counterfactual where patient info changes whether a rule applies. Accuracy drops from 63.6% to 45.1%. Explanations notice the change, but answers keep the old judgment. | The closest precedent for record-matched pairs, in static QA. Its "notices but does not act" finding predicts our stage-3 failure. Our claim must be limited to *agentic, tool-retrieved, action-consequential* pairs. |
| **Zack et al.** [V] Lancet Digital Health 6(1):e12-e22, 2024. | Swaps demographics in vignettes and finds bias. | A counterfactual-vignette precedent. We swap clinical record facts, not demographics. |
| **Pfohl et al. "A Toolbox for Surfacing Health Equity Harms and Biases in LLMs"** [V] Nature Medicine 2024, arXiv:2403.12025. | EquityMedQA counterfactual pairs. | Pair design with several rater types. |
| **MedAlign** [V] Fleming et al. AAAI 2024, arXiv:2308.14089. | 983 clinician instructions over 276 long EHRs. GPT-4 has a 35% error rate, and accuracy drops 8.3% when context is cut from 32k to 2k. | Supports the full-record-in-context ablation. Truncation hurts. |
| **LongHealth** [V] Adams et al. arXiv:2401.14490 (J Healthc Inform Res 2025 [P]). | 20 fictional long patient files. Models are worst at spotting *missing* information. | Our aspirin-only and stopped-clopidogrel negatives are tests of absence and status. |
| **Myers, Dligach, Miller et al. "Evaluating RAG vs. Long-Context Input for Clinical Reasoning over EHRs"** [V] arXiv:2508.14817, 2025 (possibly JAMIA doi 10.1093/jamia/ocag139 [U]). | RAG under 8k tokens matched or beat long context on finding imaging and antibiotic timelines. | The closest precedent for our retrieval vs full-record ablation. The antibiotic-timeline task resembles our active vs stopped medication case. |
| **Li et al. "RAG or Long-Context LLMs?"** [V] EMNLP 2024 Industry, arXiv:2407.16833. | Long context wins on average but costs more. Self-Route picks one per query. | Predict that full-record may win on accuracy. Report cost too. |
| **Lost in the Middle** [V] N. F. Liu et al. TACL 2024, arXiv:2307.03172. | U-shaped accuracy depending on where the key fact sits. | Control or randomize where the decisive fact sits in the full-record arm. |
| **Medication discontinuation extraction** [P] arXiv:2506.11137, 2025. | 12 LLMs. GPT-4o zero-shot gets F1 78.1% on whether a drug was stopped. | Evidence that active vs stopped status is hard. Check title and authors before citing. |
| **EHRNoteQA** [V] Kweon et al. NeurIPS 2024 D&B, arXiv:2402.16040. | Discharge-summary QA. Scores correlate with clinicians (Spearman 0.78). | Precedent for checking an evaluation against clinicians. |
| **EHRSHOT** [V] Wornow et al. NeurIPS 2023 D&B. | Few-shot EHR prediction. | Background, low relevance. |
| **RAG** [V] Lewis et al. NeurIPS 2020. *Cited.* | Method citation. | |

---

## 6. Agent recovery, reversibility and changing user input

### 6.1 Closest general-agent work

**REVISE. Qi, Wu, Liu, Chen, Liu. "Validity-Guided Recovery for Online Revisions in Agent Workflows"** [V]. arXiv:2609.00643, 2026. **Not cited. Must add.**
- **What it does:** When a revision arrives mid-workflow, it maps it onto recorded data and control dependencies. It stops invalid work, keeps valid work and re-checks reused results.
- **Overlap:** Close to our ledger re-check.
- **Gap:** The revision is explicit, not inferred. The abstract does not cover effects already committed outside the system. Tested on coding and LangGraph traces, not safety.

**Zhai, Li, Wang. "Revisable by Design: A Theory of Streaming LLM Agent Execution"** [V]. arXiv:2604.23283, 2026. *Cited (shortened title).*
- **What it does:** Sorts actions into idempotent, reversible, compensable and irreversible. Its Revision Absorber rolls back when the user steps in.
- **Threat:** The idea of compensating executed actions after a revision is not new.
- **Gap:** Explicit user revision, no detection, not clinical, no read-back.

**AgentChangeBench** [V]. Rana, Man, Msiiwa, Paine, Zhu, Dev, Sharma, M R. arXiv:2510.18170, 2025. *Cited.*
- **What it does:** 2,835 task sequences with goal shifts mid-conversation in airline, retail and banking.
- **Gap:** The user states the change. No hidden fact, no compensating repair, no read-back.
- **Note:** The proposal's author list has "Anotida Expected". The arXiv page says "Msiiwa". Check and fix.

**InterventionBench. Lee, Bae, Lee, Choi, Lee. "Can LLM Agents Adapt to Mid-task User Interventions?"** [V]. Findings of EMNLP 2026, pp. 14646-14666. **Add.**
- **What it does:** Goal-revising messages inserted into AppWorld and WebArena tasks. 9 types, 2,250 instances. All of them hurt.
- **Gap:** Explicit revision. Check whether completed steps had to be undone.

**AgentAbstain. Liu et al. "Do LLM Agents Know When Not to Act?"** [V]. arXiv:2607.10059, 2026. **Add.**
- **What it does:** 263 paired tasks, including "Emergent Risk Discovery" at runtime. Names "post-hoc abstention": the agent acts irreversibly, then claims it refused.
- **Use:** It documents the act-first, notice-later failure. It says verbal correction cannot fix it and does not test repair. That is exactly our gap.

**STALE. Chao et al. "Can LLM Agents Know When Their Memories Are No Longer Valid?"** [V]. arXiv:2605.06527, 2026.
- **What it does:** A later observation silently makes an earlier belief invalid. The best model scores 55.2%.
- **Use:** The same mental step as our stages 1-3, but for memory and answers, not executed actions.

**Li, Oh, Choi, Wang, Li. "Thinking Is Not Telling: Information Disclosure in User-Service LLM Agents"** [V]. arXiv:2602.07796, 2026.
- **What it does:** Inserts decision-relevant info at a chosen agent turn, with counterfactual controls. Measures a "First Edit Correction Rate".
- **Use:** The closest precedent for manipulating *where* information appears. They compare against missing info, not early vs late.

**Wang et al. "From Faulty Memories to Corrected Actions: Dependency-Guided Rollback Repair for Memory-Augmented Agents"** [V]. arXiv:2608.10502, 2026.
- **What it does:** A memory-to-action dependency graph. Replays only the affected work. 85.3% recovery.
- **Use:** A ledger plus targeted repair. The trigger is a faulty memory, not a user disclosure.

**Recovery-Bench** [V]. Letta blog, 2025, plus a NeurIPS 2025 listing (neurips.cc/virtual/2025/122490). *Cited.*
- **What it does:** Agents start from failed Terminal-Bench states. 11.2% recovery.
- **Use:** Shows recovery is a separate skill. Coding domain.

**AgentRewind** [V]. Zhuang et al. arXiv:2608.14380, 2026. *Cited.*
- **What it does:** Matched checkpoints of context and environment.
- **Gap:** Needs environment snapshots, which you cannot take of a clinic backend. That is why we use compensation.

**Gaia2** [V]. Froger et al. ICLR 2026 oral, arXiv:2602.11964.
- **What it does:** Environments that change on their own, with a check on each write.
- **Use:** Write-level grading.

### 6.2 State-based grading and procedure-aware evaluation

| Paper | Notes |
|---|---|
| **τ-bench** [V] Yao, Shinn, Razavi, Narasimhan. arXiv:2406.12045, 2024. *Cited.* | Final DB state compared with a goal state, plus a policy document. Introduces **pass^k**. We should report pass^k across seeds. |
| **τ²-bench** [V] Barres et al. arXiv:2506.07982, 2025. *Cited.* | Dual control and compositional task generation. Ablations split reasoning from communication errors, a precedent for our stage attribution. |
| **ToolSandbox** [V] Lu et al. arXiv:2408.04682, 2024. *Cited.* | Stateful tools and milestone grading. The arXiv page lists no venue, so do not name one. |
| **Cao, Driouich, Thomas. "Beyond Task Completion: Revealing Corrupt Success in LLM Agents through Procedure-Aware Evaluation"** [V] arXiv:2603.03116, 2026. *Cited (shortened title).* | 27-78% of τ-bench successes are "corrupt". Supports our separate unsafe-action metric. |
| **Cartagena, Teixeira. "Mind the GAP: Text Safety Does Not Transfer to Tool-Call Safety in LLM Agents"** [V] arXiv:2602.16943, 2026. *Cited.* | The agent's text refuses, but its tool calls still act. Supports grading the backend, not the text. |

### 6.3 Pre-execution guardrails (all check the next action only, never look back)

| Paper | Notes |
|---|---|
| **SABER** [V] Cuadron, Yu, Liu, Gupta. arXiv:2512.07850, 2025. *Cited.* | Mutating steps drive failure. Agents "act on outdated constraints". Guards the *next* mutating step. Like our gate baseline, but stronger. |
| **AgentSpec** [V] Haoyu Wang, Poskitt, Sun. ICSE 2026, arXiv:2503.18666. *Cited (add the ID).* | A rule language for runtime constraints. |
| **Wu, Gong. "Policy-Invisible Violations in LLM-Based Agents"** [V] arXiv:2604.12177, 2026. *Cited.* | The deciding fact is not visible. Sentinel checks before running. |
| **InferAct** [V] Fang, Zhu, Gurevych. EMNLP 2025, arXiv:2407.11843. | Detects misaligned actions before they run. |
| **ToolEmu** [V] Ruan et al. arXiv:2309.15817 (ICLR 2024 [U]). | LM-emulated sandbox for risky actions. |
| **R-Judge** [V] Yuan et al. Findings EMNLP 2024, arXiv:2401.10019. | Judges risk from agent records. |
| **GuardAgent** [V] Xiang et al. ICML 2025, arXiv:2406.09187. | Includes an EHR access-control benchmark. |
| **ShieldAgent** [V] Chen, Kang, Li. arXiv:2503.22738. | Policy-based shield. |
| **AgentHarm** [V] Andriushchenko et al. ICLR 2025, arXiv:2410.09024. | Harmful-task benchmark. Low relevance. |
| **AgentDojo** [V] Debenedetti et al. arXiv:2406.13352 (NeurIPS 2024 D&B [U]). | Template for an extensible tool environment. |

### 6.4 Tool failures and read-back

| Paper | Notes |
|---|---|
| **Mansoor, Phadke, Rana. "Verified Tool Calls Improve LLM Agent Reliability Under Non-Atomic Failures"** [V] arXiv:2608.02645, 2026. **Add.** | Postcondition checks, verify-before-retry and idempotency keys under injected timeouts. **Prior art for our read-back step.** |
| **Bench2Robust** [V] Chen et al. arXiv:2608.11977, 2026. | Injects retry, switch or abstain failures. 69 of 70 setups get worse. **Warning:** transient faults that clear on retry make blind retrying look robust. We must include a lost-response ("silent success") fault where a blind retry is wrong. |
| **ToolMaze. Zhu et al. "When Tools Fail"** [V] arXiv:2606.05806, 2026. | Explicit or implicit, transient or permanent faults. Agents trust corrupted outputs. |
| **Kaynar, Yan, Kingsford. "When Tools Fail, Agents Fabricate"** [V] NeurIPS 2026 workshop. | Silent ingestion of bad tool data. A verify-first monitor helps. |
| **Trofimov, Novikov. "When Tool Calls Succeed but Workflows Fail"** [V] arXiv:2609.15397, 2026. | Separates what happened in the world from what the runtime saw. MCP annotations cannot express whether an action is compensable. |
| **Mittal. "When Tool Outputs Go Wrong: Belief Revision in Tool-Using Agents"** [V] ICML 2026. | Recovers 87.5% of the time, but only 54.8% explicitly retract the old evidence. |
| **"Failing Tools: Benchmarking LLM Agent Recovery Under Runtime Tool Failures"** [U] OpenReview j7YsSnA64D. | Reportedly uses "confirmation functions". Check by hand. |
| **"Did It Happen? Counterfactual Evaluation of LLM Agent Recovery from Ambiguous Tool Outcomes"** [U] Research Square rs-10730245. | Paired hidden commit states behind identical timeouts. Check by hand. Very relevant to read-back. |

### 6.5 Transactions, sagas and undo (prior art for compensation)

| Paper | Notes |
|---|---|
| **GoEX** [V] Patil et al. (Gonzalez, Popa, Stoica). arXiv:2404.06921, 2024. | Post-facto validation plus undo plus damage confinement. The conceptual origin of "undo, then verify". |
| **SagaLLM** [V] Chang, Geng. arXiv:2503.11951, 2025 (VLDB 2025 [U]). | Saga pattern: transaction memory plus automatic compensation plus validators. |
| **Atomix** [V] Mohammadi et al. arXiv:2602.14849, 2026. | Logs effects and compensates reversible external effects on abort. Tested with faults. |
| **Cordon** [V] Chen et al. arXiv:2606.17573, 2026. | Holds irreversible effects in an outbox and checks before commit. |

### 6.6 Self-correction (background)

| Paper | Notes |
|---|---|
| **ReAct** [V] Yao et al. ICLR 2023, arXiv:2210.03629. *Cited.* | Our orchestrator loop. |
| **Reflexion** [V] Shinn et al. arXiv:2303.11366 (NeurIPS 2023 [U]). | Verbal self-reflection. |
| **CRITIC** [V] Gou et al. ICLR 2024, arXiv:2305.11738. | Self-correction checked with tools. |

---

## 7. Evaluation method: simulators, judges, citations, statistics, leakage

| Paper | Use for us |
|---|---|
| **PatientSim** [V] Kyung et al. NeurIPS 2025 D&B. | Persona simulator validated by clinicians. Check that our simulator stays consistent with the facts. |
| **Synthea** [V] Walonoski et al. JAMIA 25(3):230-238, 2018. *Cited.* | Source of our records. |
| **Chen et al. "The validity of synthetic clinical data: Synthea"** [V] BMC Med Inform Decis Mak 19:44, 2019. **Add.** | Synthea's quality-measure rates differ from real data. Put this in the limitations section. |
| **Zheng L. et al. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"** [V] NeurIPS 2023 D&B. | Biases in judges: position, verbosity, self-preference. Use a judge from a different model family than the agent. |
| **DeLucia et al. "Same Verdict, Different Reasons"** [V] arXiv:2604.16383, 2026. **Add.** | Medical LLM judges detect incompleteness at only AUC 0.49-0.66. Our advice judge needs per-class sensitivity and specificity, a pre-set threshold and a check of its reasons, not just raw agreement. |
| **SourceCheckup** [V] Wu et al. Nature Communications 16:3615, 2025. | Automatic citation-support checking (88% agreement with physicians). A model for our "citation support" metric. |
| **ALCE** [V] Gao et al. EMNLP 2023, arXiv:2305.14627. | Citation recall and precision checked with NLI. Borrow its definitions. |
| **Miller. "Adding Error Bars to Evals"** [V] arXiv:2411.00640, 2024. **Add.** | Clustered standard errors and paired differences. Justifies our scenario-level analysis. |
| **Card et al. "With Little Power Comes Great Responsibility"** [V] EMNLP 2020. | Do a power analysis by simulation, especially for TOST. |
| **Lakens. "Equivalence Tests"** [V] SPPS 8(4):355-362, 2017. **Add.** | The TOST citation. The margin must be set in advance and have clinical meaning. |
| **Elangovan, He, Verspoor. "Memorization vs. Generalization"** [V] EACL 2021. **Add.** | Train/test overlap inflates scores. Split by seed and report n-gram overlap. |
| **Xu et al. "Benchmark Data Contamination of LLMs: A Survey"** [V] arXiv:2406.04244, 2024. | n-gram contamination rules (13-gram, 50-char). |

---

## 8. Clinical grounding for the record rules

| Source | What it says | Effect on our rules |
|---|---|---|
| **NICE NG232 "Head injury: assessment and early management"** [P] 2023. *Cited.* Wording checked through the RCEM/AACE/BGS/SBNS position statement, Oct 2023. | Rec 1.2.4: community services should refer to the ED if the patient is on current anticoagulant or antiplatelet treatment. Rec 1.5.13: *consider* CT within 8 h for people on anticoagulants or antiplatelets, **excluding aspirin monotherapy**. | (1) Aspirin alone is **not** a positive. It makes a clean routine twin. (2) Write "guideline-based referral", not "mandatory CT". (3) Only *current* treatment counts, so stopped clopidogrel is a correct distractor. Already in `recheck/rules.py`. |
| **NICE NG19 "Diabetic foot problems"** [P] 2015, updated 2019. | Limb- or life-threatening problems (ulcer with fever or sepsis, ischaemia, gangrene) need **immediate** referral. Other active foot problems need referral **within 1 working day**. | The foot family has two levels. Do not merge them into one "urgent". `rules.py` records `level`. |
| **ADA Standards of Care 2025, Section 6** [V citation] Diabetes Care 48(Suppl 1):S128-S145. doi:10.2337/dc25-S006 | Hypoglycaemia levels: Level 1 under 70 mg/dL, Level 2 under 54, Level 3 severe (thresholds from memory). Insulin and sulfonylureas are the main risk drugs. | The hypo rule is "on insulin or a sulfonylurea". For a UK setting, check NICE NG17/NG28 [U] as well. |

---

## 9. Citation fixes for the proposal

| Item | Fix |
|---|---|
| χ-Bench | The arXiv title spells it **"CHI-Bench: Can AI Agents Automate End-to-End, Long-Horizon, Policy-Rich Healthcare Workflows?"** 33 authors. v3, Sept 2026. |
| ELICITED | Also called **EHR2Dial-Triage** in the abstract. Give both names. |
| Zhai et al. | Full title: "Revisable by Design: A Theory of Streaming LLM Agent Execution." |
| Cao et al. | Full title: "Beyond Task Completion: Revealing Corrupt Success in LLM Agents through Procedure-Aware Evaluation." |
| AgentSpec | Add arXiv:2503.18666. |
| Recovery-Bench | Add the NeurIPS 2025 listing next to the blog. |
| ReAct | ICLR 2023, arXiv:2210.03629. |
| ToolSandbox | The arXiv page lists no venue. Keep it as arXiv only. |
| AgentChangeBench | Check the author list: the proposal says "Anotida Expected", arXiv says "Msiiwa". |
| MediEval | Add doi:10.18653/v1/2026.acl-long.734. |
| MedAgentBench | Possibly NEJM AI 2025 (doi 10.1056/AIdbp2500144). Confirm before switching. |
| Liu et al. JAMIA | Pages 1032-1039, doi:10.1093/jamia/ocaf059. First author is Siru Liu. |
| NICE NG232 | Cite recommendation numbers 1.2.4 and 1.5.13. Note the aspirin-monotherapy exclusion. Do not call CT mandatory. |
| The rest | IDs, years and first authors match. No made-up references. |

---

## 10. What the literature means for our design (action items)

These are copied into `todo.md` as tasks.

**Framing and novelty**
1. Lead with the benchmark. Use the safe novelty sentence from section 1. Remove any unqualified "first".
2. Add these to Related Work: Zheng 2610.21270, REVISE, MedPIC-Bench, PMR-Bench, AgentAbstain, InterventionBench, Laban 2025, Noora 2609.09356, Verified Tool Calls, SagaLLM/GoEX/Atomix, and Gardner contrast sets.
3. Present RECHECK's parts as known: ledger (REVISE, Atomix), compensation (SagaLLM, Zhai), read-back (Verified Tool Calls, GoEX), guard model (Llama Guard). The contribution is that the user's disclosure triggers them, and the clinical evaluation.

**Benchmark design**

4. Make clinician-policy grading primary, with strict as a stress test (reviewer pointer). The code already does this.
5. Use **aspirin monotherapy** as a head-bump matched negative.
6. Split the foot family into immediate and same-day levels.
7. Add a **lost-response / silent-success** tool fault, where the write happened but the call errored. Then blind retry is wrong and read-back is needed. This answers the Bench2Robust warning. The backend supports it (`FaultPlan.silent_success`).
8. Report **contrast consistency** on matched pairs (both sides right).
9. Report **pass^k** across seeds.
10. Add surface perturbations (typos, tone, family downplaying the symptom) as robustness variants.
11. Control or randomize the position of the decisive fact in the full-record arm.
12. Add a "status-correct use" retrieval metric: did the agent treat a stopped medication as stopped?

**Detector**

13. Split by seed (already planned) and report n-gram overlap. Also test on clinician- or teammate-written messages that do not come from any seed.
14. Report sensitivity at fixed high recall, PPV and alert burden, not only macro-F1.
15. Explain why detection (text) is kept separate from grounding (record). PMR-Bench merges them.

**Judge and statistics**

16. Advice judge: a different model family from the agent, per-class sensitivity and specificity on about 60 human labels, a pre-set threshold, and a check of its reasons (DeLucia 2026).
17. Run a power analysis by simulation for TOST. Justify the ±10-point margin clinically (Lakens).
18. Note Synthea's realism limits in the limitations section (Chen 2019).

**Still to verify by hand**

19. The rest of PatientAgentBench (about 38k characters unread). Look for any post-booking disclosure.
20. The full text of InterventionBench: are completed steps undone?
21. The [U] items: Failing Tools (OpenReview), Did It Happen? (Research Square), ShieldGemma, the arXiv:2506.11137 title and authors, and the MedAgentBench NEJM AI version.
