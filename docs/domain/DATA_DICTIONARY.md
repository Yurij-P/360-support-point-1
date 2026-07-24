# РЎР»РѕРІРЅРёРє РґР°РЅРёС… Sprint 1

| РЎСѓС‚РЅС–СЃС‚СЊ | РљР»СЋС‡РѕРІС– РґР°РЅС– | РџСЂРёР·РЅР°С‡РµРЅРЅСЏ |
| --- | --- | --- |
| Community | code, oblast, population | РєРѕРЅС‚РµРєСЃС‚ РєРѕСЂРµРЅРµРІРѕРіРѕ Р°РіСЂРµРіР°С‚Сѓ |
| Risk | scores, evidence, confidence | РґРѕРєСѓРјРµРЅС‚РѕРІР°РЅР° РѕС†С–РЅРєР° СЂРёР·РёРєСѓ |
| PreparednessAssessment | dimensions, evidence, maturity | РїСЂРѕС„С–Р»СЊ РіРѕС‚РѕРІРЅРѕСЃС‚С– |
| Scenario | hazards, injects, objectives | РІРµСЂСЃС–РѕРЅРѕРІР°РЅРёР№ РЅР°РІС‡Р°Р»СЊРЅРёР№ СЃС†РµРЅР°СЂС–Р№ |
| Simulation | status, timeline, decisions | РїСЂРѕРІРµРґРµРЅРЅСЏ СЃРµСЃС–С— |
| Evaluation | criteria, gaps, findings | РЅР°РІС‡Р°Р»СЊРЅС– РІРёСЃРЅРѕРІРєРё |
| ImprovementPlan | actions, deadlines, indicators | РІС–РґСЃС‚РµР¶РµРЅРЅСЏ РїРѕРєСЂР°С‰РµРЅСЊ |

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
