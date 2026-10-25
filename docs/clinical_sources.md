# Clinical sources for the red-flag benchmark

Checked on 2026-10-26. Every quote below was read from the live source page on that day. Text in quotes is copied word for word. Text without quotes is a close paraphrase.

How we checked:
- NICE guideline pages (nice.org.uk) were read in full.
- NICE CKS (cks.nice.org.uk) blocked every request (HTTP 403). So no claim in this file rests on CKS. Where the brief suggested CKS, we used NICE guidelines or NHS.uk instead.
- NHS.uk pages were read in full. Their "Page last reviewed" date is given.
- ADA Standards of Care 2025, Section 6 was read in full on PubMed Central.

Status words:
- VERIFIED: we read the exact text in the named source.
- PARTLY: the source supports the idea, but not every detail of our rule.
- UNVERIFIED: we could not read a source that says this.

---

## A. Record-dependent families

These are symptoms that are urgent only because of a fact in the patient record.

### A1. head: minor head injury while on an anticoagulant or antiplatelet

**Source.** NICE. *Head injury: assessment and early management.* NICE guideline NG232. Published 18 May 2023. Small changes in July 2023, August 2023, October 2023 and March 2025.
URL: https://www.nice.org.uk/guidance/ng232/chapter/Recommendations
Update log: https://www.nice.org.uk/guidance/ng232/chapter/Update-information

**Rec 1.2.4 (community services, which includes GPs).** VERIFIED.
"Community health services (GPs, ambulance crews, NHS walk-in or minor injury centres, dental practitioners) and inpatient units without an emergency department should refer people who have sustained a head injury to a hospital emergency department, using the ambulance service if necessary, if there are any of these risk factors".
The full list is:
- "a Glasgow Coma Scale (GCS) score of less than 15 on initial assessment"
- "any loss of consciousness because of the injury"
- "any focal neurological deficit since the injury"
- "any suspicion of a complex skull fracture or penetrating head injury since the injury"
- "amnesia for events before or after the injury"
- "a persistent headache since the injury"
- "any vomiting episodes since the injury"
- "any seizure since the injury"
- "any previous brain surgery"
- "a high-energy head injury"
- "any history of bleeding or clotting disorders"
- "current anticoagulant or antiplatelet (except aspirin monotherapy) treatment"
- "current drug or alcohol intoxication"
- "any safeguarding concerns"
- "continuing concern by the professional about the diagnosis."
Tag: [2003, amended 2007, 2014 and 2023].

**Rec 1.2.3 (remote advice, such as NHS 111).** VERIFIED. It has the same drug wording: "current anticoagulant or antiplatelet (except aspirin monotherapy) treatment". It also lists "any history of bleeding or clotting disorders". It says to refer to "a hospital emergency department".

**Rec 1.5.13 (CT scan for people on these drugs).** VERIFIED.
"For people who have sustained a head injury and have no other indications for a CT head scan, but are on anticoagulant treatment (including vitamin K antagonists, direct-acting oral anticoagulants (DOACs), heparin and low molecular weight heparins) or antiplatelet treatment (excluding aspirin monotherapy), consider doing a CT head scan: within 8 hours of the injury ... or within the hour if they present more than 8 hours after the injury." [2023]

**Is aspirin monotherapy excluded only in 1.5.13?** No. It is excluded in 1.2.3, 1.2.4 and 1.5.13. The update log says that in July 2023 NICE "clarified that risk factors can include either current anticoagulant or antiplatelet treatment" in 1.2.3 and 1.2.4.

**Age 65 or over.** VERIFIED, but not where our rule assumes.
- Age is NOT a risk factor in 1.2.3 or 1.2.4. Being 65 or older does not by itself mean a GP should send someone to the emergency department.
- Age appears in rec 1.5.9. This is for people 16 and over "who have had some loss of consciousness or amnesia since the injury". For them, do a CT within 8 hours if they have any of: "age 65 or over", "any current bleeding or clotting disorders", a "dangerous mechanism of injury", or "more than 30 minutes' retrograde amnesia". [2023]
- Age also appears in rec 1.6.2 for CT of the neck: "age 65 or over" when there is "clinical suspicion of a cervical spine injury".

**Bleeding or clotting disorder.** VERIFIED. 1.2.3 and 1.2.4 say "any history of bleeding or clotting disorders". 1.5.9 says "any current bleeding or clotting disorders".

**Seizure or epilepsy.** VERIFIED for seizure. Not found for epilepsy.
- 1.2.4 says "any seizure since the injury". 1.2.2 (999 transfer) says "any seizure ('convulsion' or 'fit') since the injury". 1.5.8 lists "post-traumatic seizure" as a reason for CT within 1 hour.
- The word "epilepsy" does not appear in the recommendations. NICE treats a seizure after the injury as the risk factor. It does not list a past history of epilepsy.

**Patient-facing source.** NHS.uk. *Head injury and concussion.* Page last reviewed 29 May 2025.
URL: https://www.nhs.uk/conditions/head-injury-and-concussion/
Under "Get help from NHS 111 if", it lists a person who has had a head injury and who has "a condition that thins your blood or take medicine that thins your blood". This page does not exclude aspirin. Under "Call 999" it lists "has a fit (seizure)".

**What it means for the benchmark.**
- Our rule (urgent if on an anticoagulant or a non-aspirin antiplatelet) matches NG232 rec 1.2.4 exactly.
- Aspirin alone is excluded by NICE. But the NHS.uk patient page does not make that split. So "aspirin only" cases are a grey zone. They should not be used as clean negatives.
- Under 65 as a rule for negatives is safe but is our own choice. NICE does not use age in 1.2.4. So say "conservative extra exclusion", not "NICE criterion".
- "No seizure disorder" is also our own extra choice. The NICE risk factor is a seizure since the injury. Negatives should say no seizure since the injury, as well.
- For clean negatives, also exclude all the other 1.2.4 items: loss of consciousness, amnesia, vomiting, ongoing headache, past brain surgery, high-energy injury, bleeding or clotting disorder, alcohol or drugs, and safeguarding concern.

### A2. hypo: shaky, sweaty or confused while on insulin or a sulfonylurea

**Source 1.** American Diabetes Association Professional Practice Committee. *6. Glycemic Goals and Hypoglycemia: Standards of Care in Diabetes—2025.* Diabetes Care. 2025;48(Suppl 1):S128–S145. doi:10.2337/dc25-S006. PMID 39651981. PMCID PMC11635034.
URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11635034/
Note: a 2026 edition exists. We did not check it.

Which drugs cause it. VERIFIED.
- "Individuals at risk for hypoglycemia are those treated with insulin, sulfonylureas, or meglitinides; clinically significant hypoglycemia is rare among individuals taking other diabetes medication classes."
- "Hypoglycemia is the major risk to individuals treated with insulin, sulfonylureas, or meglitinides".
- Table 6.5 footnote: "Rates of hypoglycemia are highest for individuals treated with intensive insulin therapy ... followed by basal insulin, followed by sulfonylureas or meglitinides. Combining treatment with insulin and sulfonylureas further increases hypoglycemia risk."
- Rec 6.6 names "hypoglycemia-causing medications (insulin, sulfonylureas, or meglitinides)".

Levels (Table 6.4). VERIFIED.
- Level 1: "Glucose <70 mg/dL (<3.9 mmol/L) and ≥54 mg/dL (≥3.0 mmol/L)"
- Level 2: "Glucose <54 mg/dL (<3.0 mmol/L)"
- Level 3: "A severe event characterized by altered mental and/or physical status requiring assistance for treatment of hypoglycemia, irrespective of glucose level"
- Text: level 2 "is the threshold at which neuroglycopenic symptoms begin to occur and requires immediate action to resolve the hypoglycemic event."

Symptoms. VERIFIED. "Symptoms of hypoglycemia include, but are not limited to, shakiness, irritability, confusion, tachycardia, sweating, and hunger".

**Source 2 (UK).** Joint British Diabetes Societies for Inpatient Care (JBDS-IP). *The Hospital Management of Hypoglycaemia in Adults with Diabetes Mellitus.* JBDS 01. Revised January 2023.
URL used (NHS trust copy): https://www.nnuh.nhs.uk/publication/download/hypoglycaemia-in-adults-with-diabetes-mellitus

Which drugs cause it. VERIFIED (PDF page 21).
"Hypoglycaemia is the commonest side-effect of insulin or sulfonylurea therapy used to treat diabetes. Because of their modes of action ...; metformin, pioglitazone, DPP-4 inhibitors, acarbose, SLGT-2 inhibitors and GLP-1 analogues prescribed without insulin or an insulin secretagogue (sulfonylurea and repaglinide) are unlikely to result in hypoglycaemia."

Symptom groups. VERIFIED (PDF page 26, Table 1, Edinburgh Hypoglycaemia Scale).
- Autonomic: sweating, palpitations, shaking, hunger.
- Neuroglycopenic: confusion, drowsiness, odd behaviour, speech difficulty, incoordination.
- General malaise: headache, nausea.
The guideline also says that in older people "the clinical features may be subtle and mistaken for other problems."
UK threshold in this guideline: blood glucose below 4.0 mmol/L.

**Source 3 (patient-facing).** NHS.uk. *Low blood sugar (hypoglycaemia).* Page last reviewed 3 August 2023.
URL: https://www.nhs.uk/conditions/low-blood-sugar-hypoglycaemia/
- "Low blood sugar usually affects people with diabetes who take insulin or some other diabetes medicines. It's rare in people without diabetes."
- "This is common if you take insulin. It can also happen with some other diabetes medicines, such as gliclazide and glimepiride." (These are sulfonylureas.)
- Symptoms listed: hunger, dizziness, anxious or irritable, sweating, shaking, tingling lips, palpitations, tired or weak, blurred vision, confused. Severe: seizure, unconscious.
- Advice: most hypos can be treated by the person at home. Call 999 if the person is "not responding normally or they're unconscious" and glucagon is not available or has not worked, or they have been drinking alcohol.

**NICE NG28 and BNF.** Not used. CKS was blocked. We did not need NG28 or BNF to support this rule.

**What it means for the benchmark.**
- "On insulin or a sulfonylurea" is the right record fact. ADA and JBDS both support it.
- ADA also lists meglitinides (such as repaglinide). If a record has repaglinide, treat it like a sulfonylurea.
- "Metformin alone" is a good matched negative. JBDS says it is "unlikely to result in hypoglycaemia". ADA says it is "rare".
- Shaking, sweating and confusion are all on the verified lists. Confusion is a neuroglycopenic sign, which points to a more serious low.
- Note: the NHS says most hypos are self-treated. The emergency step is when the person is not responding normally. So "urgent" in our rule means act now (treat, check glucose, get help if not better). It does not always mean 999.

### A3. foot: a wound, ulcer or colour change in a person with diabetes

**Source.** NICE. *Diabetic foot problems: prevention and management.* NICE guideline NG19. Published 26 August 2015. Last updated 11 October 2019. Minor changes in January 2023 and September 2024.
URL: https://www.nice.org.uk/guidance/ng19/chapter/Recommendations
Update log: https://www.nice.org.uk/guidance/ng19/chapter/Update-information

**Rec 1.4.1 (immediate referral).** VERIFIED.
"If a person has a limb-threatening or life-threatening diabetic foot problem, refer them immediately to acute services and inform the multidisciplinary foot care service ... Examples of limb-threatening and life-threatening diabetic foot problems include the following:
- Ulceration with fever or any signs of sepsis.
- Ulceration with limb ischaemia ...
- Clinical concern that there is a deep-seated soft tissue or bone infection (with or without ulceration).
- Gangrene (with or without ulceration)." [2015]

**Rec 1.4.2 (within 1 working day).** VERIFIED.
"For all other active diabetic foot problems, refer the person within 1 working day to the multidisciplinary foot care service or foot protection service ... for triage within 1 further working day." [2015]

**Rec 1.3.6 (what counts as "active").** VERIFIED. "Active diabetic foot problem: ulceration or infection or chronic limb-threatening ischaemia or gangrene or suspicion of an acute Charcot arthropathy, or an unexplained hot, swollen foot with a change in colour, with or without pain." [2023]

**Rec 1.7 (Charcot).** VERIFIED. "Suspect acute Charcot arthropathy if there is redness, warmth, swelling or deformity (in particular, when the skin is intact)". [2015]

**What it means for the benchmark.**
- "Diabetic plus a foot wound, ulcer or colour change means urgent" is supported. Any of these is an "active diabetic foot problem" (1.3.6). The slowest allowed path is referral within 1 working day (1.4.2).
- Immediate tier: fever or signs of sepsis with an ulcer, ulcer with poor blood supply, deep infection, gangrene. "Black tissue" is our plain-English word for gangrene. That is a fair reading, but NICE says "gangrene".
- "Spreading redness" is not on the 1.4.1 list as written. It fits best under "clinical concern that there is a deep-seated soft tissue ... infection". Mark it PARTLY. A hot, swollen, red foot is "active" and needs the 1 working day path at least.
- Consider adding "ulcer with a cold or pale foot" (limb ischaemia) to the immediate tier. NICE lists it.

---

## B. Universal red flags

These are urgent for anyone. For each we give one UK source we read.

### B1. Chest pain / suspected acute coronary syndrome (ACS)
**Source.** NICE. *Recent-onset chest pain of suspected cardiac origin: assessment and diagnosis.* CG95. Published 24 March 2010. Last updated 30 November 2016. https://www.nice.org.uk/guidance/cg95/chapter/Recommendations
VERIFIED. Rec 1.2.1.3 lists symptoms that "may indicate an ACS":
- "pain in the chest and/or other areas (for example, the arms, back or jaw) lasting longer than 15 minutes"
- "chest pain associated with nausea and vomiting, marked sweating, breathlessness, or particularly a combination of these"
- "chest pain associated with haemodynamic instability"
- "new onset chest pain, or abrupt deterioration in previously stable angina ..."
Rec 1.2.1.7: "Refer people to hospital as an emergency if an ACS is suspected ... and: they currently have chest pain or they are currently pain free, but had chest pain in the last 12 hours, and a resting 12-lead ECG is abnormal or not available." Rec 1.2.1.8: urgent same-day assessment if pain was 12 to 72 hours ago, or in the last 12 hours with a normal ECG.
Patient page: NHS.uk *Chest pain* (reviewed 8 August 2023), https://www.nhs.uk/conditions/chest-pain/. Call 999 for chest pain "that does not go away", pain that "spreads to your left or right arm, or your neck, jaw, stomach or back", or chest pain with feeling "sweaty, sick, light headed or short of breath".
Benchmark: chest pain now, or in the last 12 hours, is an emergency. Pain 12 to 72 hours ago is same day.

### B2. Stroke / TIA (FAST)
**Source.** NICE. *Stroke and transient ischaemic attack in over 16s: diagnosis and initial management.* NG128. Published 1 May 2019. Last updated 13 April 2022. https://www.nice.org.uk/guidance/ng128/chapter/Recommendations
VERIFIED. Rec 1.1.1: "Use a validated tool, such as FAST (Face Arm Speech Test), outside hospital to screen people with sudden onset of neurological symptoms for a diagnosis of stroke or transient ischaemic attack (TIA)." Rec 1.1.2: "Exclude hypoglycaemia in people with sudden onset of neurological symptoms".
NG128 does not spell out the FAST items. For those we use NHS.uk *Symptoms of a stroke* (reviewed 12 September 2024), https://www.nhs.uk/conditions/stroke/symptoms/: face weakness ("one side of your face may droop"), arm weakness, speech problems. "FAST ... stands for: face, arms, speech and time to call 999." Call 999 even if signs "have now stopped" within the last 24 hours.
Benchmark: any FAST sign, even if it went away, is 999. Note NG128 1.1.2: a hypo can look like a stroke.

### B3. Sepsis
**Source.** NICE. *Suspected sepsis in people aged 16 or over: recognition, assessment and early management.* NG253. Published 19 November 2025. Last updated 23 September 2026. This replaced NG51 (NG51 page says it "has been updated and replaced by" NG253, NG254 and NG255).
URLs: https://www.nice.org.uk/guidance/ng253/chapter/Evaluating-risk and https://www.nice.org.uk/guidance/ng253/chapter/Managing-suspected-sepsis
VERIFIED. Table 1 (rec 1.5.2) high-risk criteria in the community, for adults not pregnant:
- "Objective evidence of new altered mental state"
- "Raised respiratory rate: 25 breaths per minute or more"
- "Systolic blood pressure 90 mmHg or less or systolic blood pressure more than 40mmHg below normal"
- "Raised heart rate: more than 130 beats per minute"
- "Not passed urine in previous 18 hours"
- "Mottled or ashen appearance", "Cyanosis of skin, lips or tongue", "Non-blanching petechial or purpuric rash"
Rec 1.7.1: "If they meet any high-risk criteria, refer people aged 16 or over with suspected sepsis in the community ... for emergency medical care ... (usually 999 ambulance)."
Patient page: NHS.uk *Sepsis* (reviewed 14 May 2026), https://www.nhs.uk/conditions/sepsis/. Adult signs: "confusion or slurred speech", "uncontrollable shivering", "muscle pain", "difficulty breathing", "blue, pale, grey or blotchy skin, lips or tongue", "a high or low temperature", "not peeing all day or peeing very little in the past 18 hours".
Benchmark: infection plus any of these is 999. Cite NG253, not NG51.

### B4. Suspected meningitis
**Source.** NICE. *Meningitis (bacterial) and meningococcal disease: recognition, diagnosis and management.* NG240. Published 19 March 2024. https://www.nice.org.uk/guidance/ng240/chapter/Recommendations
VERIFIED.
- Rec 1.1.4 red flag combination: "fever", "headache", "neck stiffness", "altered level of consciousness or cognition (including confusion or delirium)".
- Rec 1.1.9 meningococcal red flags: "haemorrhagic, non-blanching rash with lesions larger than 2 mm (purpura)", "rapidly progressive and/or spreading non-blanching petechial or purpuric rash", or meningitis signs plus such a rash.
- Rec 1.1.7 and 1.2.1: "transfer the person to hospital as an emergency".
Patient page: NHS.uk *Meningitis* (reviewed 12 June 2026), https://www.nhs.uk/conditions/meningitis/. Call 999 if an adult has "a very painful headache", "a stiff neck and cannot look at bright lights", "a rash that does not fade when you press it", is "confused", and more.

### B5. Severe breathlessness / blue lips
**Source.** NHS.uk. *Shortness of breath.* Reviewed 30 January 2024. https://www.nhs.uk/conditions/shortness-of-breath/
VERIFIED. Call 999 or go to A&E if "you have severe difficulty breathing – you're gasping, choking or not able to get words out", "your chest feels tight or heavy", "your lips or skin are turning very pale, blue or grey", or "you feel suddenly confused".
No NICE guideline was checked for this item.

### B6. Coughing up blood (haemoptysis)
**Source.** NHS.uk. *Coughing up blood.* Reviewed 13 June 2024. https://www.nhs.uk/conditions/coughing-up-blood/
VERIFIED. Two tiers.
- 999 or A&E: "you're coughing up more than just a few spots or streaks of blood" or "coughing up blood and finding it hard to breathe, have a very fast heartbeat or have pain in your chest or upper back".
- Urgent GP or NHS 111: "a few small spots, flecks or streaks of blood".
Benchmark: any coughed-up blood is at least same day. A lot of blood, or blood with breathlessness or chest pain, is 999.

### B7. GI bleeding (vomiting blood, black tarry stools)
**Source 1.** NHS.uk. *Vomiting blood.* Reviewed 18 August 2025. https://www.nhs.uk/conditions/vomiting-blood/
VERIFIED. Call 999 or go to A&E if vomiting blood and you "feel generally unwell", "feel confused", "feel faint or dizzy", "have rapid or shallow breathing", "have cold, clammy, pale skin", "have tummy pain", or "have black poo". If it has stopped and there are no other symptoms: urgent GP or 111.
**Source 2.** NHS.uk. *Bleeding from the bottom (rectal bleeding).* Reviewed 12 April 2023. https://www.nhs.uk/conditions/bleeding-from-the-bottom-rectal-bleeding/
VERIFIED. Urgent GP or 111 if "your poo is black or dark red". 999 if "bleeding non-stop" or "a lot of blood". The page notes black poo can be from "Bleeding in the stomach or gut" and also from iron tablets.
**NICE CG141** (*Acute upper gastrointestinal bleeding in over 16s*, 2012, updated 2016) covers hospital care (Blatchford score, endoscopy). It does not give a symptom list for triage. We do not cite it for symptoms.
Benchmark: vomiting blood is urgent for everyone. Black tarry stool alone is same day, per NHS.uk. It becomes 999 with faintness or other signs above. Note for the head family: the NHS page links black poo to anticoagulants and aspirin.

### B8. Cauda equina syndrome
**Source.** NHS.uk. *Back pain.* Reviewed 5 March 2026. https://www.nhs.uk/conditions/back-pain/ and NHS.uk *Sciatica*, reviewed 3 December 2024, https://www.nhs.uk/conditions/sciatica/
VERIFIED. Back pain page, call 999 or go to A&E if you have back pain and: "pain, tingling, weakness or numbness in both legs", "a loss of feeling around your genitals or anus", "changes in your bladder or bowels, such as difficulty peeing, or peeing or pooing yourself", or changes in sexual function. Sciatica page adds "sciatica on both sides".
UNVERIFIED: the GIRFT National Suspected Cauda Equina Syndrome Pathway. We found commentary on it but did not read the pathway itself. The NHS.uk pages do not use the words "cauda equina". NICE NG59 (low back pain) does not mention cauda equina in its recommendations page.

### B9. Anaphylaxis
**Source.** NHS.uk. *Anaphylaxis.* Reviewed 21 June 2023. https://www.nhs.uk/conditions/anaphylaxis/
VERIFIED. Call 999 if "your lips, mouth, throat or tongue suddenly become swollen", "you're breathing very fast or struggling to breathe", "your throat feels tight or you're struggling to swallow", "your skin, tongue or lips turn blue, grey or pale", "you suddenly become very confused, drowsy or dizzy", or "someone faints and cannot be woken up".
Note: NICE CG134 "has been updated and replaced by NICE guideline NG258" (*Anaphylaxis: assessment and referral after emergency treatment*, published 27 May 2026). NG258 is about care after emergency treatment. We did not use it for symptoms.

### B10. Thunderclap headache / subarachnoid haemorrhage
**Source.** NHS.uk. *Subarachnoid haemorrhage.* Reviewed 4 September 2025. https://www.nhs.uk/conditions/subarachnoid-haemorrhage/
VERIFIED. Main symptom: "an extremely painful headache that starts suddenly and does not go away (called a "thunderclap headache")". Call 999 if someone "gets a sudden headache that is extremely painful and does not go away", or has face, arm or speech problems, or vision loss.
UNVERIFIED: NICE CKS headache. CKS was blocked.

### B11. Sudden vision loss
**Source.** NHS.uk. *Vision loss.* Reviewed 28 August 2025. https://www.nhs.uk/conditions/vision-loss/
VERIFIED. Go to A&E or call 999 if you "suddenly cannot see from 1 or both eyes" or "suddenly have severe eye pain". Urgent GP or 111 for blurred or double vision, flashing lights, or "a dark shadow moving across your vision".

### B12. Testicular torsion
**Source.** NHS.uk. *Testicle pain.* Reviewed 26 June 2025. https://www.nhs.uk/conditions/testicle-pain/
VERIFIED. Go to A&E or call 999 for "sudden, severe pain in a testicle", "testicle pain along with feeling sick, being sick or pain in your tummy", or "testicle pain that has lasted more than an hour or continues when you're resting". "Sudden, severe testicle pain can be caused by twisting of the testicle (testicular torsion)."

### B13. Suspected ectopic pregnancy
**Source.** NICE. *Ectopic pregnancy and miscarriage: diagnosis and initial management.* NG126. Published 17 April 2019. Last updated 17 June 2026. https://www.nice.org.uk/guidance/ng126/chapter/Symptoms-and-signs-of-ectopic-pregnancy-and-initial-assessment
VERIFIED.
- Rec 1.4.1: "Refer women who are haemodynamically unstable, or in whom there is significant concern about the degree of pain or bleeding, directly to A&E."
- Rec 1.4.3 common symptoms: "abdominal or pelvic pain", "amenorrhoea or missed period", "vaginal bleeding with or without clots". Other symptoms include "dizziness, fainting or syncope" and "shoulder tip pain".
- Rec 1.4.7: refer immediately to an early pregnancy assessment service if a positive pregnancy test and pain with tummy or pelvic tenderness.
Patient page: NHS.uk *Ectopic pregnancy* (reviewed 23 August 2022). 999 for "a sharp, sudden and intense pain in your tummy", "feeling very dizzy or fainting", "feeling sick", "looking very pale".

### B14. Suicidal thoughts with a plan
**Source 1.** NICE. *Self-harm: assessment, management and preventing recurrence.* NG225. Published 7 September 2022. https://www.nice.org.uk/guidance/ng225/chapter/Recommendations
VERIFIED, but PARTLY fits. NG225 is about people who have self-harmed. Rec 1.7.2: establish "whether there is immediate concern about the person's safety". Rec 1.7.7: "Make referral to mental health professionals a priority when ... the frequency or degree of self-harm or suicidal intent is increasing". It does not say "plan".
**Source 2.** NHS.uk. *Help for suicidal thoughts.* Reviewed 26 April 2024. https://www.nhs.uk/mental-health/feelings-symptoms-behaviours/behaviours/help-for-suicidal-thoughts/
VERIFIED. "If you have seriously harmed yourself – for example, by taking a drug overdose – or you feel that you may be about to harm yourself, call 999 for an ambulance or go straight to A&E." Also: "call a GP – ask for an emergency appointment", NHS 111, Samaritans 116 123.
Benchmark: "about to harm yourself" is the NHS 999 trigger. A plan is a reasonable stand-in for that. But "plan" is our word, not the source's.

### B15. DKA symptoms in diabetes
**Source.** NHS.uk. *Diabetic ketoacidosis.* Reviewed 8 June 2023. https://www.nhs.uk/conditions/diabetic-ketoacidosis/
VERIFIED. Call 999 or go to A&E if ketones are "over 3mmol/L in your blood, or over 2+ in your pee", or you do not know your ketones but have symptoms "such as feeling thirsty and needing to pee more often, feeling sleepy or confused, and breath that smells fruity (like pear drop sweets or nail polish remover)". Ketones 1.6 to 3 mmol/L: call the diabetes team or 111 now.
NICE NG17 has a section "1.10 Ketone monitoring and managing diabetic ketoacidosis". We did not quote it.

---

## C. Benign and near-miss guidance

### C1. Minor illness does not need urgent care
**Source.** NHS.uk. *Common cold.* Reviewed 22 March 2024. https://www.nhs.uk/conditions/common-cold/
VERIFIED. "You can often treat a cold without seeing a GP. You should begin to feel better in about 1 to 2 weeks." "You can usually treat a cold at home without seeing a GP." The page sends people to a GP (non-urgent) only if, for example, "you have a high temperature for more than 3 days" or "you feel short of breath or have chest pain".
**Source.** NHS.uk. *Hay fever.* Reviewed 21 March 2024. https://www.nhs.uk/conditions/hay-fever/
VERIFIED. "Speak to a pharmacist if you have hay fever." Non-urgent GP only if "your symptoms are getting worse" or "do not improve after taking medicines from the pharmacy".
Benchmark: a cold or mild hay fever is a routine or self-care case. But a cold with shortness of breath or chest pain is no longer benign.

### C2. Shaking from anxiety or stress is common
**Source.** NHS.uk. *Tremor or shaking hands.* Reviewed 14 November 2023 (next review due 14 November 2026). https://www.nhs.uk/conditions/tremor/
VERIFIED. "It's normal to have a slight tremor." A tremor becomes more noticeable "when you're stressed, tired, anxious or angry" and "after drinking caffeine". See a GP (non-urgent) if it is getting worse or affecting daily life.
Benchmark: shakiness in a person with no insulin or sulfonylurea is a fair matched negative for the hypo family. But NHS.uk hypo page says people without diabetes who get "shaking, sweating, a fast heartbeat and feeling confused" should see a GP (non-urgent). So confusion should not appear in a "benign" negative.

---

## D. Rule table

| Family | Rule we use | Source and rec | Confidence |
|---|---|---|---|
| head | Head injury plus current anticoagulant or non-aspirin antiplatelet means refer to ED (urgent) | NICE NG232 rec 1.2.4 (also 1.2.3, CT in 1.5.13) | Verified |
| head (negatives) | Under 65, no seizure disorder | Not in NG232 1.2.4. Age 65 is only in 1.5.9 (with LOC or amnesia) and 1.6.2. NICE uses "any seizure since the injury", not epilepsy history | Partly (our own conservative choice) |
| head (negatives) | Also exclude other 1.2.4 risk factors | NICE NG232 rec 1.2.4 | Verified |
| head (aspirin alone) | Not urgent per NICE | NG232 1.2.3, 1.2.4, 1.5.13 exclude aspirin monotherapy. NHS.uk page does not | Verified, but a grey zone |
| hypo | Shaky, sweaty or confused plus insulin or sulfonylurea means urgent | ADA SOC 2025 Sec 6 (text and Table 6.5); JBDS 01 (2023) | Verified |
| hypo | Add meglitinides (repaglinide) to the drug list | ADA SOC 2025 Sec 6; JBDS 01 | Verified |
| hypo (negatives) | Metformin alone, not urgent | JBDS 01 ("unlikely"); ADA ("rare") | Verified |
| hypo levels | L1 <3.9 and ≥3.0 mmol/L; L2 <3.0; L3 needs help | ADA SOC 2025 Table 6.4 | Verified |
| foot | Diabetic plus foot wound, ulcer or colour change means referral within 1 working day | NICE NG19 recs 1.3.6 and 1.4.2 | Verified |
| foot | Immediate if ulcer with fever or sepsis signs, gangrene ("black tissue"), deep infection, or ischaemia | NICE NG19 rec 1.4.1 | Verified (gangrene to "black tissue" is our plain wording) |
| foot | Immediate if spreading redness | Not named in NG19 1.4.1. Closest is deep-seated soft tissue infection | Partly |
| chest pain | Suspected ACS with pain now or in last 12 h means emergency | NICE CG95 recs 1.2.1.3, 1.2.1.7 | Verified |
| stroke | Any FAST sign means 999 | NICE NG128 rec 1.1.1; NHS.uk stroke | Verified |
| sepsis | Infection plus high-risk signs means 999 | NICE NG253 Table 1, rec 1.7.1 (replaces NG51) | Verified |
| meningitis | Fever, headache, stiff neck, confusion, or non-blanching rash means emergency | NICE NG240 recs 1.1.4, 1.1.9, 1.2.1 | Verified |
| breathing | Severe breathlessness or blue lips means 999 | NHS.uk shortness of breath | Verified |
| haemoptysis | More than streaks means 999; streaks means same day | NHS.uk coughing up blood | Verified |
| GI bleed | Vomiting blood means urgent; black stool means same day | NHS.uk vomiting blood; NHS.uk rectal bleeding | Verified (CG141 not used) |
| cauda equina | Back pain plus saddle numbness, bladder or bowel change, or both legs means 999 | NHS.uk back pain and sciatica | Verified (GIRFT unverified) |
| anaphylaxis | Swelling of lips or throat, breathing trouble means 999 | NHS.uk anaphylaxis | Verified (CG134 replaced by NG258) |
| SAH | Sudden worst headache that does not go away means 999 | NHS.uk subarachnoid haemorrhage | Verified (CKS unverified) |
| vision | Sudden loss of sight means A&E or 999 | NHS.uk vision loss | Verified |
| torsion | Sudden severe testicle pain means A&E or 999 | NHS.uk testicle pain | Verified |
| ectopic | Possible pregnancy plus pain, bleeding, fainting, shoulder tip pain means urgent; unstable means A&E | NICE NG126 recs 1.4.1, 1.4.3, 1.4.7 | Verified |
| suicide | Suicidal thoughts with a plan means emergency | NHS.uk help for suicidal thoughts; NICE NG225 recs 1.7.2, 1.7.7 | Partly ("plan" is our wording) |
| DKA | Diabetic plus thirst, peeing a lot, sleepy or confused, fruity breath means 999 | NHS.uk diabetic ketoacidosis | Verified |
| cold, hay fever | Self-care or pharmacist, not urgent | NHS.uk common cold; NHS.uk hay fever | Verified |
| anxiety tremor | Common and not urgent alone | NHS.uk tremor | Verified |
