import google.generativeai as genai
import json

# Here is all the supported segment types and their possible variants in array format:
segmentTypes = {
  'sidewalk': ['empty', 'sparse', 'normal', 'dense'],
  'sidewalk-wayfinding': ['large'],
  'sidewalk-bench': ['left', 'right', 'center'],
  'sidewalk-bike-rack': [
    'left|sidewalk-parallel',
    'right|sidewalk-parallel',
    'left|sidewalk',
    'right|sidewalk'
  ],
  'sidewalk-tree': ['big', 'palm-tree'],
  'utilities': ['left', 'right'],
  'sidewalk-lamp': [
    'right|modern',
    'both|modern',
    'left|modern',
    'right|traditional',
    'both|traditional',
    'left|traditional',
    'right|pride',
    'both|pride',
    'left|pride'
  ],
  'parklet': ['left', 'right'],
  'outdoor-dining': ['empty|sidewalk', 'empty|road'],
  'bikeshare': ['left|road', 'right|road', 'left|sidewalk', 'right|sidewalk'],
  'bike-lane': [
    'inbound|green|sidewalk',
    'inbound|green|road',
    'outbound|green|sidewalk',
    'outbound|green|road',
    'inbound|regular|sidewalk',
    'inbound|regular|road',
    'outbound|regular|sidewalk',
    'outbound|regular|road',
    'inbound|red|sidewalk',
    'inbound|red|road',
    'outbound|red|sidewalk',
    'outbound|red|road'
  ],
  'scooter': [
    'inbound|regular',
    'inbound|green',
    'inbound|red',
    'outbound|regular',
    'outbound|green',
    'outbound|red'
  ],
  'bus-lane': [
    'inbound|colored|typical',
    'outbound|colored|typical',
    'inbound|regular|typical',
    'outbound|regular|typical',
    'inbound|red|typical',
    'outbound|red|typical'
  ],
  'drive-lane': [
    'inbound|car',
    'outbound|car',
    'inbound|truck',
    'outbound|truck',
    'outbound|av',
    'inbound|av',
    'outbound|pedestrian',
    'inbound|pedestrian',
    'inbound|sharrow',
    'outbound|sharrow'
  ],
  'turn-lane': [
    'inbound|left',
    'inbound|right',
    'inbound|left-right-straight',
    'inbound|shared',
    'inbound|both',
    'inbound|left-straight',
    'inbound|right-straight',
    'inbound|straight',
    'outbound|left',
    'outbound|right',
    'outbound|left-right-straight',
    'outbound|shared',
    'outbound|both',
    'outbound|left-straight',
    'outbound|right-straight',
    'outbound|straight'
  ],
  'parking-lane': [
    'sideways|right',
    'sideways|left',
    'inbound|right',
    'inbound|left',
    'outbound|left',
    'outbound|right',
    'angled-front-left|left',
    'angled-front-right|left',
    'angled-rear-left|left',
    'angled-rear-right|left',
    'angled-front-left|right',
    'angled-front-right|right',
    'angled-rear-left|right',
    'angled-rear-right|right'
  ],
  'food-truck': ['left', 'right'],
  'flex-zone': [
    'taxi|inbound|right',
    'taxi|inbound|left',
    'taxi|outbound|right',
    'taxi|outbound|left',
    'rideshare|outbound|right',
    'rideshare|outbound|right',
    'rideshare|inbound|right',
    'rideshare|inbound|left'
  ],
  'streetcar': [
    'inbound|regular',
    'inbound|colored',
    'inbound|grass',
    'outbound|regular',
    'outbound|colored',
    'outbound|grass'
  ],
  'light-rail': [
    'inbound|regular',
    'inbound|colored',
    'inbound|grass',
    'outbound|regular',
    'outbound|colored',
    'outbound|grass'
  ],
  'brt-station': ['center'],
  'transit-shelter': [
    'left|street-level',
    'right|street-level',
    'right|light-rail',
    'left|light-rail'
  ],
  'divider': [
    'buffer',
    'flowers',
    'planting-strip',
    'planter-box',
    'palm-tree',
    'big-tree',
    'bush',
    'dome',
    'bollard',
    'striped-buffer'
  ],
  'temporary': [
    'barricade',
    'traffic-cone',
    'jersey-barrier-plastic',
    'jersey-barrier-concrete'
  ],
  'magic-carpet': ['aladdin']
}

# Segment Type Schema with Nested Variant Enums
segment_type = genai.protos.Schema(
    type=genai.protos.Type.OBJECT,
    properties={
        "width": genai.protos.Schema(
            type=genai.protos.Type.NUMBER,
            description="Segment width in meters. 2 meters is default for sidewalks, 3 meters for roads, parking, etc."
        ),
        "variantString": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="Variant of segment. Based on the value of the current segment type, a variantString from the list of variants from function description is used."
        ),
        "type": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            enum=['sidewalk', 'sidewalk-wayfinding', 'sidewalk-bench', 'sidewalk-bike-rack', 'sidewalk-tree', 'utilities', 'sidewalk-lamp', 'parklet', 'outdoor-dining', 'bikeshare', 'bike-lane', 'scooter', 'bus-lane', 'drive-lane', 'turn-lane', 'parking-lane', 'food-truck', 'flex-zone', 'streetcar', 'light-rail', 'brt-station', 'transit-shelter', 'divider', 'temporary', 'magic-carpet'],
            description="Street segment type. Used only segment types from the list of supported segment types"
        ),
        "elevation": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            enum=['0', '1', '2'],
            description="Elevation level for segment. 1 is default for sidewalks segments and buildings, 0 is default for road segments, parking, bus-lane. But if last word after | in variantString is sidewalk (for example in variantString inbound|green|sidewalk) then elevation level is 1, if last word id road, elevation is 0."
        )
    },
    required=["width", "variantString", "type", "elevation"]
)

# Main Streetmix Schema
streetmix_schema = genai.protos.Schema(
    type=genai.protos.Type.OBJECT,
    properties={
        "name": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="Name of created street. If not provided, it will be generated by description, less then 15 characters without spaces, - or _ instead of spaces"
        ),
        "data": genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "rightBuildingVariant": genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    enum=["grass", "narrow", "residential", "fence", "parking-lot", "waterfront", "wide"],
                    description="A string to determine which building variant to create for the right side of the street",
                ),
                "leftBuildingVariant": genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    enum=["grass", "narrow", "residential", "fence", "parking-lot", "waterfront", "wide"],
                    description="A string to determine which building variant to create for the left side of the street",
                ),
                "street": genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "width": genai.protos.Schema(
                            type=genai.protos.Type.NUMBER,
                            description="Street length in meters. Default is 50"
                        ),
                        "segments": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=segment_type,
                            description="List of segments of a cross-section perspective of the 3D scene, each with a width in imperial feet units, a type in string format, and a variantString that applies modifications to the segment type",
                        )
                    },
                    required=["segments"]
                )
            },
            required=["rightBuildingVariant", "leftBuildingVariant", "street"]
        )
    },
    required=["data"]
)
