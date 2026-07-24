from ..domain.models import CommunityMap, GeoFeature, MapLayer
from ..repositories import CommunityMapRepository


class MapService:
    def __init__(self, r: CommunityMapRepository) -> None:
        self.r = r

    def create_map(self, m: CommunityMap) -> CommunityMap:
        return self.r.add(m)

    def add_layer(self, m: CommunityMap, l: MapLayer) -> CommunityMap:
        m.add_layer(l)
        return self.r.save(m)

    def add_feature(self, l: MapLayer, f: GeoFeature) -> GeoFeature:
        l.add_feature(f)
        return f

    def verify_feature(self, f: GeoFeature, by: str) -> GeoFeature:
        f.verify(by)
        return f

    def activate_map_version(self, m: CommunityMap) -> CommunityMap:
        m.activate()
        return self.r.save(m)

    def archive_map(self, m: CommunityMap) -> CommunityMap:
        m.archive()
        return self.r.save(m)
