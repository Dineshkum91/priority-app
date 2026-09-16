# Priority — Risk Register

> Last updated: 2026-09-15
> Status values: **Open** | Mitigating | Accepted | Closed

## Risk Table

| # | Risk | Probability | Impact | Mitigation | Status |
|---|---|---|---|---|---|
| R1 | **No user demand** — Students may not want another health app, or may not value a "one priority" approach over existing tools or doing nothing. | High | Critical | Conduct 20–30 structured student interviews before any launch. Build a landing-page smoke test to measure intent. Do not invest in scaling until retention data from a real cohort exists. | **Open** |
| R2 | **Cold-start personalization** — The system has no data on a new user, so early recommendations may feel generic or irrelevant, causing immediate drop-off. | High | High | Use onboarding inputs (sleep goal, activity level, schedule) to set initial baselines. Be transparent: "Your recommendations will improve after a few days of check-ins." Avoid over-promising personalization quality. | **Open** |
| R3 | **Notification fatigue** — Daily check-in reminders may be perceived as spam, leading to app deletion. | Medium | High | Default to one gentle daily reminder. Let users choose timing. Never send more than one notification per day. Provide easy snooze/disable. Monitor uninstall-after-notification rates. | **Open** |
| R4 | **Unsafe recommendations** — A rule-based system could suggest actions that are inappropriate for a user with an undisclosed medical condition (e.g., "go for a run" to someone with an injury). | Medium | Critical | Safety layer intercepts red-flag inputs before priority engine runs. Include disclaimers: "Priority is not medical advice." Never use diagnostic language. Encourage users to consult professionals for persistent issues. Conduct expert review of all recommendation templates. | **Open** |
| R5 | **Data-entry burden** — Even a 30-second check-in may feel like too much effort for students with low motivation. | Medium | High | Keep check-in to 5–6 fields with smart defaults (e.g., "same as yesterday"). Use sliders and quick-tap inputs, not free-text. Test check-in flow with real students and iterate on time-to-complete. | **Open** |
| R6 | **Privacy and regulatory concerns** — Collecting self-reported health data raises questions about data protection (FERPA adjacency, state privacy laws, potential HIPAA applicability if medical data is inferred). | Medium | Critical | Do not collect clinical or diagnostic data. Store only self-reported lifestyle inputs. Use Supabase Auth with row-level security. Do not sell or share data with third parties. Consult a privacy attorney before any real launch. Add clear privacy policy and data-deletion capability. | **Open** |
| R7 | **Self-reported data inaccuracy** — Users may under-report unhealthy behaviours (alcohol, poor sleep) or over-report healthy ones, leading to incorrect prioritisation. | High | Medium | Design non-judgmental input UX to reduce social-desirability bias. Use ranges instead of precise numbers where possible. Cross-check internal consistency (e.g., "8 hours sleep" but "very tired" stress report). Never present derived insights as precise medical measurements. | **Open** |
| R8 | **LLM safety / hallucination** — The LLM explanation layer could generate medical claims, diagnoses, or harmful advice despite being given only structured input. | Low–Medium | Critical | LLM receives ONLY the structured output (priority, reason, actions). System prompt explicitly prohibits medical claims. Output is validated/filtered before display. LLM cannot call any other endpoint. Template fallback if LLM output fails validation. | **Open** |
| R9 | **Disordered eating / self-harm escalation** — A student using the app may be in crisis; the app's nutrition or activity recommendations could inadvertently reinforce harmful behaviours. | Low | Critical | Safety layer scans for red-flag keywords and extreme patterns on every check-in. When triggered, suppress the normal recommendation entirely and surface mental-health support resources (e.g., 988 Suicide & Crisis Lifeline, campus counselling). This layer cannot be overridden by other logic. | **Open** |
| R10 | **Single-point-of-failure on LLM API** — If the LLM service is down or rate-limited, the explanation step breaks and the user sees an error or no recommendation. | Medium | Medium | Build a template-based fallback that formats the structured recommendation without LLM involvement. User still gets a useful recommendation, just less polished language. Log LLM failures for monitoring. | **Open** |
| R11 | **Recommendation repetitiveness** — If one health dimension (e.g., sleep) is consistently the worst, the user sees the same priority every day and loses interest. | Medium | Medium | Priority engine applies a "diminishing returns" modifier: if the same dimension has been the top priority for 3+ consecutive days and no improvement is observed, surface the second-highest priority with a note about the ongoing primary concern. Rotate suggested actions within a dimension. | **Open** |
| R12 | **Scope creep into medical device territory** — Feature additions (wearable integrations, symptom tracking, medication reminders) could inadvertently push the product toward regulated medical-device classification. | Low | Critical | Maintain a strict scope boundary: self-reported lifestyle data only. No symptom diagnosis, no treatment recommendations, no medication tracking. Review any new feature against FDA digital health guidance before building. | **Open** |

## Notes

- Probability: Low / Low–Medium / Medium / High
- Impact: Low / Medium / High / Critical
- All risks are currently **Open** because this is a pre-validation prototype.
- This register should be reviewed and updated after each round of user interviews or significant product changes.

---

> ⚠️ **No real user validation has been conducted.** Risks R1 (no user demand) and R2 (cold-start) are especially dangerous because they threaten the fundamental product thesis. These must be addressed through structured interviews with 20–30 college students before committing to further development beyond the prototype stage.
