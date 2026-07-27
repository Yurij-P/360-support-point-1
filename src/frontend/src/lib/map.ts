/**
 * Re-exports OSMMapViewer as the single map integration point.
 * Components import from here, not directly from osm_map_viewer.ts.
 */
export {
  OSMMapViewer,
  type MapCoordinates,
  type MapBoundingBox,
  type InfrastructureMarker,
  type HazardZoneOverlay,
} from '../../osm_map_viewer.ts'
