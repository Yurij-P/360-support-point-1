"""Static role catalog: 7 categories, 23 UX positions (TPS360-ROLE-UX-001 §4)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RoleCatalogEntry:
    role_id: str
    position: str
    category: str
    category_key: str


_CATALOG: tuple[RoleCatalogEntry, ...] = (
    # Органи місцевого самоврядування
    RoleCatalogEntry("local-gov-head", "Голова громади", "Органи місцевого самоврядування", "local_government"),
    RoleCatalogEntry("local-gov-deputy-head", "Заступник голови", "Органи місцевого самоврядування", "local_government"),
    RoleCatalogEntry("local-gov-civil-protection", "Керівник або спеціаліст із цивільного захисту", "Органи місцевого самоврядування", "local_government"),
    RoleCatalogEntry("local-gov-executive-rep", "Представник виконавчих органів ради", "Органи місцевого самоврядування", "local_government"),
    # Старости
    RoleCatalogEntry("starost-district", "Староста старостинського округу", "Старости", "starosty"),
    RoleCatalogEntry("starost-remote-rep", "Представник віддаленого населеного пункту", "Старости", "starosty"),
    RoleCatalogEntry("starost-info-coordinator", "Координатор первинного збору інформації з території", "Старости", "starosty"),
    # Добровільні пожежні команди
    RoleCatalogEntry("vol-fire-commander", "Керівник ДПК", "Добровільні пожежні команди", "volunteer_fire"),
    RoleCatalogEntry("vol-fire-member", "Представник або член ДПК", "Добровільні пожежні команди", "volunteer_fire"),
    # Заклади освіти
    RoleCatalogEntry("edu-director", "Директор закладу освіти", "Заклади освіти", "education"),
    RoleCatalogEntry("edu-deputy-director", "Заступник директора", "Заклади освіти", "education"),
    RoleCatalogEntry("edu-civil-protection", "Відповідальна особа за цивільний захист", "Заклади освіти", "education"),
    RoleCatalogEntry("edu-shelter-evac", "Відповідальна особа за укриття або евакуацію", "Заклади освіти", "education"),
    # Екстрені та безпекові служби
    RoleCatalogEntry("emerg-dsns", "Представник ДСНС", "Екстрені та безпекові служби", "emergency_services"),
    RoleCatalogEntry("emerg-police", "Представник поліції", "Екстрені та безпекові служби", "emergency_services"),
    RoleCatalogEntry("emerg-ems", "Представник екстреної медичної допомоги", "Екстрені та безпекові служби", "emergency_services"),
    # Комунальні та соціальні служби
    RoleCatalogEntry("communal-utility", "Керівник або представник комунального підприємства", "Комунальні та соціальні служби", "communal_social"),
    RoleCatalogEntry("communal-medical", "Представник медичного закладу", "Комунальні та соціальні служби", "communal_social"),
    RoleCatalogEntry("communal-social-service", "Представник соціальної служби", "Комунальні та соціальні служби", "communal_social"),
    RoleCatalogEntry("communal-child-services", "Представник служби у справах дітей", "Комунальні та соціальні служби", "communal_social"),
    # Громадський сектор
    RoleCatalogEntry("civil-ngo", "Представник громадської організації", "Громадський сектор", "civil_society"),
    RoleCatalogEntry("civil-volunteer-group", "Представник волонтерської групи", "Громадський сектор", "civil_society"),
    RoleCatalogEntry("civil-humanitarian-hub", "Представник місцевого гуманітарного штабу", "Громадський сектор", "civil_society"),
)


class RoleCatalogService:
    def list_entries(self, category_key: str | None = None) -> tuple[RoleCatalogEntry, ...]:
        if category_key is None:
            return _CATALOG
        return tuple(e for e in _CATALOG if e.category_key == category_key)

    def get_entry(self, role_id: str) -> RoleCatalogEntry | None:
        return next((e for e in _CATALOG if e.role_id == role_id), None)
