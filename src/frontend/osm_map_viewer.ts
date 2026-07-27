/**
 * TPS360 OpenStreetMap GIS Helper
 * Renders OpenStreetMap infrastructure layers, bounding boxes, and crisis hazard radii.
 */

export interface MapCoordinates {
  latitude: number;
  longitude: number;
}

export interface MapBoundingBox {
  min_latitude: number;
  max_latitude: number;
  min_longitude: number;
  max_longitude: number;
}

export interface InfrastructureMarker {
  id: string;
  name: string;
  category: string;
  coordinates: MapCoordinates;
  is_critical: boolean;
}

export interface HazardZoneOverlay {
  zone_id: string;
  hazard_type: string;
  center: MapCoordinates;
  radius_meters: number;
  severity_level: number;
}

export class OSMMapViewer {
  private boundingBox: MapBoundingBox;
  private markers: InfrastructureMarker[] = [];
  private hazardZones: HazardZoneOverlay[] = [];

  constructor(boundingBox: MapBoundingBox) {
    this.boundingBox = boundingBox;
  }

  addMarker(marker: InfrastructureMarker): void {
    if (this.isCoordinatesInBounds(marker.coordinates)) {
      this.markers.push(marker);
    }
  }

  addHazardZone(zone: HazardZoneOverlay): void {
    this.hazardZones.push(zone);
  }

  isCoordinatesInBounds(coords: MapCoordinates): boolean {
    return (
      coords.latitude >= this.boundingBox.min_latitude &&
      coords.latitude <= this.boundingBox.max_latitude &&
      coords.longitude >= this.boundingBox.min_longitude &&
      coords.longitude <= this.boundingBox.max_longitude
    );
  }

  getRenderState(): {
    boundingBox: MapBoundingBox;
    markersCount: number;
    hazardZonesCount: number;
    activeMarkers: InfrastructureMarker[];
    activeHazardZones: HazardZoneOverlay[];
  } {
    return {
      boundingBox: this.boundingBox,
      markersCount: this.markers.length,
      hazardZonesCount: this.hazardZones.length,
      activeMarkers: [...this.markers],
      activeHazardZones: [...this.hazardZones],
    };
  }
}
