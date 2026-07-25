# Словник даних Sprint 1

| Сутність | Ключові дані | Призначення |
| --- | --- | --- |
| Community | code, oblast, population | контекст кореневого агрегату |
| Risk | scores, evidence, confidence | документована оцінка ризику |
| PreparednessAssessment | dimensions, evidence, maturity | профіль готовності |
| Scenario | hazards, injects, objectives | версіонований навчальний сценарій |
| Simulation | status, timeline, decisions | проведення сесії |
| Evaluation | criteria, gaps, findings | навчальні висновки |
| ImprovementPlan | actions, deadlines, indicators | відстеження покращень |

```mermaid
stateDiagram-v2
[*] --> draft
draft --> scheduled
draft --> active
scheduled --> active
active --> paused
paused --> active
active --> completed
paused --> completed
```

```mermaid
flowchart LR
Evidence --> Dimensions --> PreparednessAssessment --> CPMM --> CPP
```

| CommunityMap / MapLayer / GeoFeature | межі, шари, GeoJSON, атрибуція | геопросторовий контекст громади |
