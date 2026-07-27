# Тести

**Статус: реалізовано (v0.2.8).** Автоматизовані тести домену, API та frontend-інтеграції — 47 файлів, 456+ тест-функцій, 100% проходження.

## Автоматизовані тести (`src/tps360/tests/`)

Запуск: `pytest` з кореня репозиторію.  
Інструменти: pytest, ruff, mypy (Python 3.12+, SQLite для тестів).

| Область | Приклади файлів |
|---|---|
| Доменні моделі | `test_core.py`, `test_simulation_domain.py`, `test_geospatial.py`, `test_threat_model.py` |
| Симуляційний рушій | `test_simulation_lifecycle.py`, `test_impact_engine.py`, `test_decision_engine.py`, `test_task_execution.py` |
| Учасники та ролі | `test_participant_capability_compatibility.py`, `test_participant_identity_api.py`, `test_session_lobby.py` |
| Сценарії та громади | `test_scenario_compatibility.py`, `test_passport_read_model.py`, `test_community_catalog_api.py` |
| API та інтеграція | `test_api.py`, `test_api_cors.py`, `test_events_api.py`, `test_directives_api.py` |
| AAR та аналітика | `test_aar_telemetry.py`, `test_facilitator_console.py`, `test_role_dashboard_workspace.py` |
| Frontend-інтеграція | `test_frontend_api_integration.py` |

## Ручні та методологічні тести

Критерії перевірки методології, контенту та пілотних результатів визначатимуться окремо в рамках Етапу 3 (Пілотування). Цей каталог (`16_tests/`) призначений для їхнього майбутнього збереження.
