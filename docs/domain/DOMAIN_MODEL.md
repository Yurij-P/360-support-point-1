# Доменна модель TPS360

Sprint 1 реалізує типізовану модель Community як кореня агрегату, з Risk, Capability, PreparednessAssessment, Scenario, Simulation, Evaluation і ImprovementPlan. Розрахунки ізольовані в сервісах і не є затвердженою методологією.

```mermaid
classDiagram
Community "1" --> "*" Risk
Community "1" --> "*" PreparednessAssessment
Scenario "1" --> "*" Inject
Simulation --> Scenario
Simulation --> Community
Simulation --> Evaluation
Evaluation --> ImprovementPlan
Risk --> Hazard
Risk --> Vulnerability
```
