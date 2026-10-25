# lmpdf

> The public README, docs, images, and examples for `lmpdf` are MIT under `LICENSE-examples`. Binary releases use `LICENSE`; implementation source and its history are maintained privately in `lmctlhq/lmpdf`.

Generate PDF documents and slide decks from the same typed calls as `lmoffice docx` and `lmoffice pptx`.
The Rust host uses Typst for layout and PDF export. The initial target is tagged
PDF/A-2b plus PDF/UA-1, deterministic output, and a self-contained executable.
See the foundation decision and
release engineering for supported profiles and
verification. Interactive forms, encryption and digital signing are outside v1.

## Install

LMScript resolves the platform release asset through
`install="github:lmctl-ai/lmpdf@latest"`. Releases contain
`lmpdf-linux-x64`, `lmpdf-linux-arm64`, `lmpdf-macos-arm64`,
`lmpdf-macos-x64`, `lmpdf-windows-x64.exe`, and `SHA256SUMS`.

For a direct Linux x64 download:

```sh
gh release download --repo lmctl-ai/lmpdf --pattern lmpdf-linux-x64 --pattern SHA256SUMS
sha256sum --check --ignore-missing SHA256SUMS
chmod +x lmpdf-linux-x64
./lmpdf-linux-x64 --version
```

## Same document calls

```text
output = ARGV.len() > 0 ? ARGV[0] : "hello.pdf";
p = _dsl_ cli="lmpdf docx" install="github:lmctl-ai/lmpdf@latest";
let doc = docx.create(${output});
doc.heading("Hello PDF", 1);
doc.paragraph("The same document calls can target lmoffice docx.");
doc.footer_fields("Page {PAGE} of {NUMPAGES}").save();
end _dsl_
savedsl(p, output + ".dslb");
r = system(concat(dsl_cli(p), ["--dsl", output + ".dslb"]), 120000);
assert(r.code == 0);
```

The schemas are the API source of truth: `lmpdf docx --dsl-signatures` and `lmpdf pptx --dsl-signatures`.
The output path is supplied to `docx.create` or `pptx.create`; `save()` takes no arguments.

## Same script, two outputs

<!-- GALLERY:START -->
Each picture shows page 1 of one lmoffice example script. On the left is the `.docx` written by
`cli="lmoffice docx"` (lmoffice v0.1.23) as LibreOffice renders it; on the right is the `.pdf`
written by the same script with `cli="lmpdf docx"`. Nothing else in the script changes.
42 of 43 examples are within the parity thresholds; see the
parity report for the method, thresholds and worst offenders.

### Legal

| | |
|---|---|
| <img src="docs/gallery/parity/legal-demand-letter.png" width="420" alt="legal-demand-letter: docx render left, pdf right"><br>**legal-demand-letter**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.43 % · within thresholds</sub> | <img src="docs/gallery/parity/legal-lease.png" width="420" alt="legal-lease: docx render left, pdf right"><br>**legal-lease**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.06 % · within thresholds</sub> |
| <img src="docs/gallery/parity/legal-nda.png" width="420" alt="legal-nda: docx render left, pdf right"><br>**legal-nda**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.66 % · within thresholds</sub> | <img src="docs/gallery/parity/legal-power-of-attorney.png" width="420" alt="legal-power-of-attorney: docx render left, pdf right"><br>**legal-power-of-attorney**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.37 % · within thresholds</sub> |
| <img src="docs/gallery/parity/legal-services-agreement.png" width="420" alt="legal-services-agreement: docx render left, pdf right"><br>**legal-services-agreement**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.51 % · within thresholds</sub> | <img src="docs/gallery/parity/legal-terms-of-service.png" width="420" alt="legal-terms-of-service: docx render left, pdf right"><br>**legal-terms-of-service**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.60 % · within thresholds</sub> |

### Resume and career

| | |
|---|---|
| <img src="docs/gallery/parity/resume-academic-cv.png" width="420" alt="resume-academic-cv: docx render left, pdf right"><br>**resume-academic-cv**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.62 % · within thresholds</sub> | <img src="docs/gallery/parity/resume-classic.png" width="420" alt="resume-classic: docx render left, pdf right"><br>**resume-classic**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.08 % · within thresholds</sub> |
| <img src="docs/gallery/parity/resume-cover-letter.png" width="420" alt="resume-cover-letter: docx render left, pdf right"><br>**resume-cover-letter**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.36 % · within thresholds</sub> | <img src="docs/gallery/parity/resume-reference-sheet.png" width="420" alt="resume-reference-sheet: docx render left, pdf right"><br>**resume-reference-sheet**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.40 % · within thresholds</sub> |
| <img src="docs/gallery/parity/resume-two-column.png" width="420" alt="resume-two-column: docx render left, pdf right"><br>**resume-two-column**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.28 % · within thresholds</sub> |  |

### Business

| | |
|---|---|
| <img src="docs/gallery/parity/business-agenda.png" width="420" alt="business-agenda: docx render left, pdf right"><br>**business-agenda**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.66 % · within thresholds</sub> | <img src="docs/gallery/parity/business-job-offer.png" width="420" alt="business-job-offer: docx render left, pdf right"><br>**business-job-offer**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.24 % · within thresholds</sub> |
| <img src="docs/gallery/parity/business-letter.png" width="420" alt="business-letter: docx render left, pdf right"><br>**business-letter**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.93 % · within thresholds</sub> | <img src="docs/gallery/parity/business-memo.png" width="420" alt="business-memo: docx render left, pdf right"><br>**business-memo**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.65 % · within thresholds</sub> |
| <img src="docs/gallery/parity/business-press-release.png" width="420" alt="business-press-release: docx render left, pdf right"><br>**business-press-release**<br><sub>lines 0.909 · ink ≤ 1 pt 100% · pixels 0.74 % · documented difference</sub> | <img src="docs/gallery/parity/business-proposal.png" width="420" alt="business-proposal: docx render left, pdf right"><br>**business-proposal**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.68 % · within thresholds</sub> |
| <img src="docs/gallery/parity/business-purchase-order.png" width="420" alt="business-purchase-order: docx render left, pdf right"><br>**business-purchase-order**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.96 % · within thresholds</sub> | <img src="docs/gallery/parity/business-report-with-toc.png" width="420" alt="business-report-with-toc: docx render left, pdf right"><br>**business-report-with-toc**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.70 % · within thresholds</sub> |

### Markdown bodies

| | |
|---|---|
| <img src="docs/gallery/parity/markdown-business-letter.png" width="420" alt="markdown-business-letter: docx render left, pdf right"><br>**markdown-business-letter** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.18 % · within thresholds</sub> | <img src="docs/gallery/parity/markdown-lesson-plan.png" width="420" alt="markdown-lesson-plan: docx render left, pdf right"><br>**markdown-lesson-plan** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.19 % · within thresholds</sub> |
| <img src="docs/gallery/parity/markdown-meeting-minutes.png" width="420" alt="markdown-meeting-minutes: docx render left, pdf right"><br>**markdown-meeting-minutes** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.58 % · within thresholds</sub> | <img src="docs/gallery/parity/markdown-nda.png" width="420" alt="markdown-nda: docx render left, pdf right"><br>**markdown-nda** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.24 % · within thresholds</sub> |
| <img src="docs/gallery/parity/markdown-report-toc.png" width="420" alt="markdown-report-toc: docx render left, pdf right"><br>**markdown-report-toc** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.21 % · within thresholds</sub> | <img src="docs/gallery/parity/markdown-resume.png" width="420" alt="markdown-resume: docx render left, pdf right"><br>**markdown-resume** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.50 % · within thresholds</sub> |
| <img src="docs/gallery/parity/markdown-review-notes.png" width="420" alt="markdown-review-notes: docx render left, pdf right"><br>**markdown-review-notes** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.60 % · within thresholds</sub> | <img src="docs/gallery/parity/markdown-services-agreement.png" width="420" alt="markdown-services-agreement: docx render left, pdf right"><br>**markdown-services-agreement** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.47 % · within thresholds</sub> |

### HR

| | |
|---|---|
| <img src="docs/gallery/parity/hr-offer-letter.png" width="420" alt="hr-offer-letter: docx render left, pdf right"><br>**hr-offer-letter**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.82 % · within thresholds</sub> | <img src="docs/gallery/parity/hr-onboarding-checklist.png" width="420" alt="hr-onboarding-checklist: docx render left, pdf right"><br>**hr-onboarding-checklist**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.45 % · within thresholds</sub> |
| <img src="docs/gallery/parity/hr-org-chart.png" width="420" alt="hr-org-chart: docx render left, pdf right"><br>**hr-org-chart**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 2.23 % · within thresholds</sub> | <img src="docs/gallery/parity/hr-performance-review.png" width="420" alt="hr-performance-review: docx render left, pdf right"><br>**hr-performance-review**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.06 % · within thresholds</sub> |

### Education

| | |
|---|---|
| <img src="docs/gallery/parity/education-assessment-rubric.png" width="420" alt="education-assessment-rubric: docx render left, pdf right"><br>**education-assessment-rubric**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.33 % · within thresholds</sub> | <img src="docs/gallery/parity/education-certificate.png" width="420" alt="education-certificate: docx render left, pdf right"><br>**education-certificate**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.34 % · within thresholds</sub> |
| <img src="docs/gallery/parity/education-lesson-plan.png" width="420" alt="education-lesson-plan: docx render left, pdf right"><br>**education-lesson-plan**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.15 % · within thresholds</sub> | <img src="docs/gallery/parity/education-syllabus.png" width="420" alt="education-syllabus: docx render left, pdf right"><br>**education-syllabus**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.50 % · within thresholds</sub> |

### Marketing

| | |
|---|---|
| <img src="docs/gallery/parity/marketing-case-study.png" width="420" alt="marketing-case-study: docx render left, pdf right"><br>**marketing-case-study**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 2.80 % · within thresholds</sub> | <img src="docs/gallery/parity/marketing-content-plan.png" width="420" alt="marketing-content-plan: docx render left, pdf right"><br>**marketing-content-plan**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.66 % · within thresholds</sub> |

### Operations

| | |
|---|---|
| <img src="docs/gallery/parity/operations-inspection-checklist.png" width="420" alt="operations-inspection-checklist: docx render left, pdf right"><br>**operations-inspection-checklist**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.50 % · within thresholds</sub> | <img src="docs/gallery/parity/operations-lease-abstract.png" width="420" alt="operations-lease-abstract: docx render left, pdf right"><br>**operations-lease-abstract**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.86 % · within thresholds</sub> |

### Other

| | |
|---|---|
| <img src="docs/gallery/parity/cross-workbook-memo.png" width="420" alt="cross-workbook-memo: docx render left, pdf right"><br>**cross-workbook-memo** · Markdown body<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 1.47 % · within thresholds</sub> | <img src="docs/gallery/parity/invoice.png" width="420" alt="invoice: docx render left, pdf right"><br>**invoice**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.77 % · within thresholds</sub> |
| <img src="docs/gallery/parity/meetingminutes.png" width="420" alt="meetingminutes: docx render left, pdf right"><br>**meetingminutes**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.26 % · within thresholds</sub> | <img src="docs/gallery/parity/report.png" width="420" alt="report: docx render left, pdf right"><br>**report**<br><sub>lines 1.000 · ink ≤ 1 pt 100% · pixels 0.87 % · within thresholds</sub> |

### Slide decks (`lmpdf pptx`)

Each picture shows a slide from an lmoffice presentation script (`1280 × 720 px` / `960 × 540 pt` 16:9 canvas). On the left is the `.pptx` written by `cli="lmoffice pptx"` (lmoffice v0.1.23) as LibreOffice Impress renders it; on the right is the `.pdf` written by the same script with `cli="lmpdf pptx"`. **17 of 17 decks (79 slides)** are within the 2 pt text and 2 px shape box thresholds and pass veraPDF PDF/A-2b and PDF/UA-1.

| | |
|---|---|
| <img src="docs/gallery/parity/5slidedeck.png" width="420" alt="5slidedeck: pptx render left, pdf right"><br>**5slidedeck** (slide 3/5)<br><sub>text ≤ 2 pt 13/13 (max 0.05 pt) · shapes ≤ 2 px 2/2 (max 0.09 px) · within thresholds</sub> | <img src="docs/gallery/parity/annual_report.png" width="420" alt="annual_report: pptx render left, pdf right"><br>**annual_report** (slide 4/5)<br><sub>text ≤ 2 pt 64/64 (max 1.01 pt) · shapes ≤ 2 px 29/29 (max 0.66 px) · within thresholds</sub> |
| <img src="docs/gallery/parity/conference_talk.png" width="420" alt="conference_talk: pptx render left, pdf right"><br>**conference_talk** (slide 4/5)<br><sub>text ≤ 2 pt 56/56 (max 1.00 pt) · shapes ≤ 2 px 22/22 (max 0.49 px) · within thresholds</sub> | <img src="docs/gallery/parity/cross-workbook-briefing.png" width="420" alt="cross-workbook-briefing: pptx render left, pdf right"><br>**cross-workbook-briefing** (slide 2/2) · Markdown deck<br><sub>text ≤ 2 pt 14/14 (max 0.24 pt) · shapes ≤ 2 px 11/11 (max 0.25 px) · within thresholds</sub> |
| <img src="docs/gallery/parity/education-lesson-deck.png" width="420" alt="education-lesson-deck: pptx render left, pdf right"><br>**education-lesson-deck** (slide 5/5)<br><sub>text ≤ 2 pt 69/69 (max 1.09 pt) · shapes ≤ 2 px 38/38 (max 1.96 px) · within thresholds</sub> | <img src="docs/gallery/parity/hr-onboarding-review.png" width="420" alt="hr-onboarding-review: pptx render left, pdf right"><br>**hr-onboarding-review** (slide 2/5)<br><sub>text ≤ 2 pt 72/72 (max 1.09 pt) · shapes ≤ 2 px 43/43 (max 0.54 px) · within thresholds</sub> |
| <img src="docs/gallery/parity/markdown-project-deck.png" width="420" alt="markdown-project-deck: pptx render left, pdf right"><br>**markdown-project-deck** (slide 2/3) · Markdown deck<br><sub>text ≤ 2 pt 21/21 (max 0.24 pt) · shapes ≤ 2 px 11/11 (max 0.25 px) · within thresholds</sub> | <img src="docs/gallery/parity/markdown-training-deck.png" width="420" alt="markdown-training-deck: pptx render left, pdf right"><br>**markdown-training-deck** (slide 2/3) · Markdown deck<br><sub>text ≤ 2 pt 19/19 (max 0.24 pt) · shapes ≤ 2 px 10/10 (max 0.25 px) · within thresholds</sub> |
| <img src="docs/gallery/parity/marketing-brand-guidelines.png" width="420" alt="marketing-brand-guidelines: pptx render left, pdf right"><br>**marketing-brand-guidelines** (slide 2/5)<br><sub>text ≤ 2 pt 82/82 (max 1.87 pt) · shapes ≤ 2 px 44/44 (max 0.93 px) · within thresholds</sub> | <img src="docs/gallery/parity/onboarding.png" width="420" alt="onboarding: pptx render left, pdf right"><br>**onboarding** (slide 3/5)<br><sub>text ≤ 2 pt 77/77 (max 1.74 pt) · shapes ≤ 2 px 20/20 (max 1.53 px) · within thresholds</sub> |
| <img src="docs/gallery/parity/pitch_deck.png" width="420" alt="pitch_deck: pptx render left, pdf right"><br>**pitch_deck** (slide 5/6)<br><sub>text ≤ 2 pt 78/78 (max 0.83 pt) · shapes ≤ 2 px 14/14 (max 1.33 px) · within thresholds</sub> | <img src="docs/gallery/parity/product_launch.png" width="420" alt="product_launch: pptx render left, pdf right"><br>**product_launch** (slide 3/5)<br><sub>text ≤ 2 pt 59/59 (max 1.60 pt) · shapes ≤ 2 px 21/21 (max 0.22 px) · within thresholds</sub> |
| <img src="docs/gallery/parity/project_status.png" width="420" alt="project_status: pptx render left, pdf right"><br>**project_status** (slide 3/5)<br><sub>text ≤ 2 pt 71/71 (max 0.52 pt) · shapes ≤ 2 px 31/31 (max 0.45 px) · within thresholds</sub> | <img src="docs/gallery/parity/quarterly_business_review.png" width="420" alt="quarterly_business_review: pptx render left, pdf right"><br>**quarterly_business_review** (slide 1/5)<br><sub>text ≤ 2 pt 63/63 (max 1.01 pt) · shapes ≤ 2 px 32/32 (max 0.66 px) · within thresholds</sub> |
| <img src="docs/gallery/parity/sales_proposal.png" width="420" alt="sales_proposal: pptx render left, pdf right"><br>**sales_proposal** (slide 3/5)<br><sub>text ≤ 2 pt 63/63 (max 1.89 pt) · shapes ≤ 2 px 20/20 (max 0.22 px) · within thresholds</sub> | <img src="docs/gallery/parity/team_intro.png" width="420" alt="team_intro: pptx render left, pdf right"><br>**team_intro** (slide 4/5)<br><sub>text ≤ 2 pt 57/57 (max 1.81 pt) · shapes ≤ 2 px 20/20 (max 0.34 px) · within thresholds</sub> |
| <img src="docs/gallery/parity/training_workshop.png" width="420" alt="training_workshop: pptx render left, pdf right"><br>**training_workshop** (slide 3/5)<br><sub>text ≤ 2 pt 77/77 (max 0.99 pt) · shapes ≤ 2 px 27/27 (max 1.53 px) · within thresholds</sub> |  |

<!-- GALLERY:END -->

## PDF examples

<!-- EXAMPLES:START -->
PDF-specific examples in `examples/`. Each script is plain lmcode with `cli="lmpdf docx"`;
the caption shows what was checked on the committed build: page count, byte-identical rebuild,
`qpdf --check`, and veraPDF 1.30 for PDF/A-2b and PDF/UA-1 (lmpdf's default output profile).
Rebuild them with `python3 examples/render.py --lmpdf private implementation detail`.

**[bilingual-arabic-cjk](examples/bilingual-arabic-cjk.lms)**: A trilingual notice: English, Arabic (right to left, joined letters) and Japanese, with a three-column glossary table. Fonts are bundled (Noto Naskh Arabic, Kosugi); nothing comes from the system.

<img src="docs/examples/bilingual-arabic-cjk.png" width="760" alt="bilingual-arabic-cjk">

<sub>1 pages · rebuild byte-identical: yes · qpdf --check: ok · veraPDF PDF/A-2b: PASS (144 rules passed, 0 failed) · veraPDF PDF/UA-1: PASS (106 rules passed, 0 failed)</sub>

**[certificate](examples/certificate.lms)**: A landscape certificate: large centred type, a recipient line, two signature blocks.

<img src="docs/examples/certificate.png" width="760" alt="certificate">

<sub>1 pages · rebuild byte-identical: yes · qpdf --check: ok · veraPDF PDF/A-2b: PASS (144 rules passed, 0 failed) · veraPDF PDF/UA-1: PASS (106 rules passed, 0 failed)</sub>

**[contract-pdfa](examples/contract-pdfa.lms)**: A services contract with numbered clauses and two signature blocks. lmpdf writes PDF/A-2b and PDF/UA-1 by default; the gallery caption shows the veraPDF result for this file.

<img src="docs/examples/contract-pdfa.png" width="760" alt="contract-pdfa">

<sub>1 pages · rebuild byte-identical: yes · qpdf --check: ok · veraPDF PDF/A-2b: PASS (144 rules passed, 0 failed) · veraPDF PDF/UA-1: PASS (106 rules passed, 0 failed)</sub>

**[invoice-multipage](examples/invoice-multipage.lms)**: Invoice whose line-item table runs over several pages: the header row repeats on every page and the footer counts pages (Page X of Y). The rows are generated in the outer script as Markdown.

<img src="docs/examples/invoice-multipage.png" width="760" alt="invoice-multipage">

<sub>3 pages · rebuild byte-identical: yes · qpdf --check: ok · veraPDF PDF/A-2b: PASS (144 rules passed, 0 failed) · veraPDF PDF/UA-1: PASS (106 rules passed, 0 failed)</sub>

**[letterhead-footnotes](examples/letterhead-footnotes.lms)**: A letter on a letterhead (running header) with numbered footnotes at the page bottom and a link.

<img src="docs/examples/letterhead-footnotes.png" width="760" alt="letterhead-footnotes">

<sub>1 pages · rebuild byte-identical: yes · qpdf --check: ok · veraPDF PDF/A-2b: PASS (144 rules passed, 0 failed) · veraPDF PDF/UA-1: PASS (106 rules passed, 0 failed)</sub>

**[newsletter-two-column](examples/newsletter-two-column.lms)**: A two-column newsletter: a section with two columns, headings, bullets and an image in the flow.

<img src="docs/examples/newsletter-two-column.png" width="760" alt="newsletter-two-column">

<sub>1 pages · rebuild byte-identical: yes · qpdf --check: ok · veraPDF PDF/A-2b: PASS (144 rules passed, 0 failed) · veraPDF PDF/UA-1: PASS (106 rules passed, 0 failed)</sub>

**[report-40-pages](examples/report-40-pages.lms)**: A 40-page technical report: a generated table of contents with real page numbers, numbered headings, a running header and a "Page X of Y" footer. The body is generated as Markdown.

<img src="docs/examples/report-40-pages.png" width="760" alt="report-40-pages">

<sub>41 pages · rebuild byte-identical: yes · qpdf --check: ok · veraPDF PDF/A-2b: PASS (144 rules passed, 0 failed) · veraPDF PDF/UA-1: PASS (106 rules passed, 0 failed)</sub>

**[resume](examples/resume.lms)**: A one-page resume: centred name, contact line, sections with right-aligned dates (tab stops) and bullets.

<img src="docs/examples/resume.png" width="760" alt="resume">

<sub>1 pages · rebuild byte-identical: yes · qpdf --check: ok · veraPDF PDF/A-2b: PASS (144 rules passed, 0 failed) · veraPDF PDF/UA-1: PASS (106 rules passed, 0 failed)</sub>

<!-- EXAMPLES:END -->

## Build and verification

The host pins Typst and its dependency lock. CI builds five platforms, checks
static/self-contained linkage, audits dependency and font licences, validates
archival/accessibility profiles, compares output hashes on independent runners,
and measures binary size and 200-page tagged/untagged table memory. Generated
notices ship with every release. See the release guide
for commands, budgets, measurements, and upgrade procedure.

## License


Releases up to and including v0.1.62 were published under the MIT License (see the LICENSE asset of that release). Releases after v0.1.62 are published under the Lattice Systems Personal Use License (this file).
The README, docs, images, and `examples/*.lms` are MIT-licensed under `LICENSE-examples`.
Binary releases are licensed under `LICENSE`. Third-party components remain under their own licenses and notices.
