# Priority — Problem Statement

## The Problem

College students (18–25) live fragmented, irregular lifestyles: inconsistent sleep schedules driven by coursework and socialising, stress spikes around exams, sporadic exercise, budget-constrained nutrition, and low motivation to engage with complex health tracking tools. Existing health apps present **dashboards of metrics** — step counts, sleep stages, calorie breakdowns — that require the user to synthesise meaning from raw numbers. Most students open these apps once, feel overwhelmed or indifferent, and never return.

The result: students know they *should* sleep more, drink water, move their bodies — but they don't know **what matters most right now**, and they lack the bandwidth to figure it out every day.

## The Opportunity

Instead of showing students everything about their health, **tell them the ONE most important thing they can do today**, explained in plain language, with 2–3 concrete micro-actions they can actually fit into their day.

**Priority** is a daily health coach that:

1. Collects a lightweight daily check-in (≤30 seconds, 5–6 inputs).
2. Runs a transparent, rule-based scoring engine against the student's personal baseline.
3. Identifies the single highest-priority health dimension (sleep, activity, hydration, stress, nutrition, recovery).
4. Suggests 2–3 small, actionable steps.
5. Uses an LLM to rephrase the recommendation in friendly, non-judgmental language.
6. Collects simple feedback (did you do it? did it help?) to personalise over time.

## What This Is NOT

- **Not a medical device or diagnostic tool.** Priority does not diagnose conditions, prescribe treatments, or replace professional advice.
- **Not a fitness tracker replacement.** It does not aim to measure biometrics precisely.
- **Not a gamification engine.** No streaks, badges, leaderboards, or shame-based nudges.
- **Not an AI that makes medical decisions.** The LLM explains; deterministic rules decide.

## Core Design Principles

| Principle | Meaning |
|---|---|
| **One thing, not everything** | Every day surfaces exactly one priority, not a dashboard. |
| **Honesty over engagement** | Never fabricate scores, percentages, or confidence numbers. If data is insufficient, say so. |
| **Safety first** | Red-flag inputs (self-harm mentions, extreme patterns) bypass normal logic and direct toward support resources. |
| **Low friction** | Check-in < 30 seconds. No long onboarding questionnaire. |
| **Personal baseline, not population norms** | Compare the student to *their own* rolling average, not abstract "healthy adult" benchmarks. |
| **Plain language** | No medical jargon, no fear-based copy, no "you are deficient in X." |

## Unvalidated Assumptions

> ⚠️ **The following assumptions have NOT been validated with real users. Before any launch decision, 20–30 structured student interviews are required.**

| # | Assumption | Why It Matters | How to Validate |
|---|---|---|---|
| A1 | Students will complete a daily check-in consistently if it takes ≤30 seconds. | Core loop depends on daily data. If they skip, the system breaks. | Diary study / prototype test with 20+ students over 2 weeks. |
| A2 | One prioritised recommendation is more motivating than a full dashboard. | This is the entire product thesis. | A/B test: dashboard vs. single-priority in prototype. |
| A3 | Students trust a rule-based system enough to follow its advice. | If perceived as "dumb" or "random," they'll ignore it. | Interviews: show sample recommendations, measure trust. |
| A4 | Self-reported data (sleep hours, stress level, meals) is accurate enough to be useful. | Garbage in → garbage out. | Compare self-reports vs. wearable data in a small cohort. |
| A5 | Students care about health enough to install and keep a dedicated app. | Competes with zero-effort alternatives (doing nothing). | Landing page test / intent survey. |
| A6 | An LLM-rewritten explanation adds value over a templated message. | LLM integration has cost, latency, and safety implications. | Show LLM vs. template versions; measure preference. |
| A7 | 5–6 input fields capture enough signal to prioritise correctly. | Too few → bad recommendations; too many → drop-off. | Iterate field count in usability testing. |
| A8 | The safety-layer keyword/threshold approach catches genuine red flags without excessive false positives. | False negatives are dangerous; false positives erode trust. | Expert review + user testing with edge-case scenarios. |

## Success Metrics (future, post-validation)

| Metric | Target | Rationale |
|---|---|---|
| Daily check-in completion rate | ≥60% of active days | Core loop viability |
| Action completion rate | ≥40% of recommended actions marked done | Recommendations are actionable |
| 7-day retention | ≥50% | Students find ongoing value |
| "Did it help?" positive rate | ≥55% | Recommendations are perceived as useful |
| Safety-layer trigger → support resource click-through | Track, no target | Measure if safety layer leads to help-seeking |

---

*This document was created as a design artifact. It does not constitute validated product-market fit.*
