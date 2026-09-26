# SIH26054 submission materials

Prepared for **TwinGuard Aero**, 26 September 2026. The user confirmed **PS54**; the screenshot's student-innovation challenge is not the selected target for these materials.

## Paste-ready fields

- `idea-title.txt` — title only.
- `idea-description.txt` — detailed project description.
- `abstract.txt` — abstract/summary.
- `demo-and-questions.md` — four-minute demonstration, optional fifth minute and evaluator Q&A.
- `evidence-and-roadmap.md` — implementation mapping, architecture, experiments, claim boundaries and slide content.

The source `.txt` files contain only the field content. They intentionally avoid fabricated team details, field metrics, test counts or a claimed selection outcome.

## Portal checks and constraints

The supplied screenshot shows **100 characters** for the title, **50,000** for description, **10,000** for abstract and a **PDF up to 10 MB** for the idea template. These are screenshot-derived constraints, not independently verified limits for the currently selected PS54 form. The files are checked against these limits in `field-validation.json`.

Before final submission, confirm that the portal names **SIH26054** and the DRDO aero-piston digital-twin challenge. A title pasted into the wrong student-innovation form would not change the selected problem statement. The screenshot shows **Save as Draft**; saving a draft is not proof of final submission.

The official listing currently identifies **Software** and **Robotics and Drones** for this PS. The form's **Technology Bucket** is a separate field: select the actual AI/ML or digital-twin option if offered, using the portal's wording. Do not assume that theme and technology bucket have identical options. Leave the optional YouTube field empty unless a real, accessible demo video has been published.

The public PS listing displayed **30 September 2026** on 26 September 2026. Confirm the live portal immediately before submitting because dates and availability can change. [Official SIH 2026 PS listing](https://sih.gov.in/sih2026PS)

## Official template and rubric status

The [official SIH2026 presentation template](https://sih.gov.in/letters/2026/SIH2026-IDEA-Presentation-Format.pptx) was downloaded directly and verified byte-for-byte against the existing Desktop copy. SHA-256: `ce3e5deebec2741f3383cb2dd21269cad8d9930f7c747c9903d7d4b27db14de6`. Its instructions require at most six slides including the title, the supplied template and section pointers, and PDF upload. The removable instruction slide has been excluded from the prepared six-slide draft.

**Template draft:** `TwinGuard-Aero-SIH2026-Template-Draft.pptx` and its PDF preserve the official masters, layout/theme assets, logos, footer and six prescribed sections. All package checks passed against the original and all six rendered slides were inspected. The required **Team ID** is still marked **CONFIRM FROM PORTAL** because existing PS54 materials left it blank. **MINDMESH** is sourced from the existing PS54 PDF, but should match the live registration. This remains a draft until the identifier is filled and the title slide is rechecked. No submission has been made.

Rebuild the deck with `python docs/submission/build_official_deck.py path/to/SIH2026-IDEA-Presentation-Format.pptx` using Python with `defusedxml` installed. The builder accepts the template path as an argument; no machine-specific source path is embedded.

The accessible official college guidelines PDF is labeled **SIH 2024**, including its idea-selection section. Its emphasis on originality, credible implementation, clear presentation, usefulness, usability and future development is useful background, but it is not evidence of a 2026 weighted scoring rubric. [Official older guidelines, PDF page 20](https://sih.gov.in/letters/Guidelines-College-SPOC.pdf)

Search results also surfaced a third-party site explicitly labeled a student redesign concept that asserts percentage weights and a five-slide format. Those claims were not used as official rules. No 2026 score weights or guaranteed shortlist result is asserted in this pack; the six-slide limit is now verified from the official template itself.

## Supporting PDF

`TwinGuard-Aero-Evaluator-Brief.pdf`, when included in the delivered output folder, is a six-page companion brief. It is marked **supporting material, not the official submission template**. It can support a rehearsal or technical discussion; it is not evidence that the prescribed template requirement has been met.

## Sources and provenance

| Source | What was verified / used | Limitation |
|---|---|---|
| [Official SIH PS list](https://sih.gov.in/sih2026PS) | PS54 identity, organization/category/theme, high-level deliverable alignment and displayed deadline | Live listing may change; use the portal's selected record for final identity |
| [Official college guidelines PDF](https://sih.gov.in/letters/Guidelines-College-SPOC.pdf) | General historical selection guidance | Document says SIH2024, not a verified 2026 rubric |
| [Official SIH2026 template](https://sih.gov.in/letters/2026/SIH2026-IDEA-Presentation-Format.pptx) | Byte-verified template, six-slide cap, preserved section pointers and PDF format | Team ID still needs portal confirmation |
| User-supplied screenshot | Character and PDF-size limits; visible draft button | Screenshot shows a different student-innovation challenge |
| Repository source and docs | Implemented architecture, UI paths, model boundaries and validation utilities | Source inspection does not equal a fresh successful test run |

The PS summary is intentionally brief. The description, script, technical rationale and roadmap are original project-specific material grounded in the implementation rather than a reproduction of the official statement.
