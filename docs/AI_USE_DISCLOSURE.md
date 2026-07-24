# AI-Use Disclosure — DRAFT

**Status:** Draft requiring author approval before submission.

---

## General Disclosure (for repository documentation)

AI tools (Claude, Anthropic) were used during the development and documentation of this project in the following capacities:

1. **Software development assistance:** AI assisted with code review, debugging, test design, and engineering iteration during the Validex 0.2.0 development cycle.

2. **Corpus screening assistance:** The real-world corpus feasibility study used an AI-assisted screening workflow to assess structural eligibility of candidate metabolomics tables. This AI screening was not equivalent to independent domain-expert validation and is explicitly documented as such.

3. **Manuscript and documentation drafting:** AI assisted with drafting the manuscript text, tables, figures, supplementary materials, and technical documentation. All scientific claims, numerical results, and interpretive conclusions are derived from frozen repository artifacts and deterministic analysis scripts, not from AI generation.

4. **Post hoc analytical classification:** AI assisted with the systematic adjudication of the 13 non-exact held-out cases, including evidence collection, data-flow tracing, and interpretation evaluation. The adjudication methodology and conclusions are documented in the probability-contract adjudication package with full evidence trails.

5. **Human responsibility:** The repository owner bears responsibility for all scientific claims, methodological decisions, and publication judgments. AI assistance did not substitute for independent domain-expert validation, which has not been conducted.

6. **No fabricated expert labels:** No AI-generated content was presented as independent expert validation. The AI-assisted corpus screening is explicitly labeled as structural pre-screening, not expert assessment.

---

## Concise Manuscript Disclosure

> AI tools (Claude, Anthropic) assisted with software development, manuscript drafting, corpus screening, and post hoc analytical classification. All scientific claims derive from frozen deterministic artifacts. AI-assisted corpus screening was structural and is not equivalent to independent expert validation. The repository owner is responsible for all scientific conclusions.

---

## Detailed Supplementary Disclosure

### Software Development

AI tools assisted with iterative development of the Validex 0.2.0 release candidate, including alias registry design, probability-field usability gating implementation, XLSX ingestion, test development, and code review. The final product behavior is deterministic and verified by 350 automated tests at the locked commit.

### Corpus Feasibility Screening

The real-world corpus feasibility study used AI-assisted workflows for:
- Candidate identification from public repository metadata
- Structural eligibility screening (format, field presence, row structure)
- Contamination detection (identifying prior Validex outputs)
- Eligibility reconciliation across multiple screening passes

These workflows operated under frozen rules and did not execute Validex on any candidate table. The screening outcome (zero eligible tables) reflects the frozen criteria and search environment. The AI screening is explicitly documented as not equivalent to independent expert eligibility assessment.

### Manuscript Preparation

AI tools assisted with:
- Drafting manuscript sections from frozen evidence
- Generating tables and figures from frozen data
- Constructing the post hoc adjudication framework
- Creating supplementary methods and reproducibility documentation
- Systematic claim auditing against evidence boundaries

### Limitations of AI Involvement

- AI tools cannot substitute for independent domain-expert scientific review
- AI-generated text was not independently verified by a metabolomics domain expert
- The corpus screening workflow has not been validated against expert screening outcomes
- AI assistance in the adjudication phase does not constitute independent expert adjudication

### Transparency

All AI-assisted analysis is documented with evidence trails, verification scripts, and hash-governed artifact chains. The adjudication methodology is reproducible from the repository evidence without AI tools.
