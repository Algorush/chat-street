import google.generativeai as genai

# Segment Type Schema with Nested Variant Enums
segment_type = genai.protos.Schema(
    type=genai.protos.Type.OBJECT,
    properties={
        "width": genai.protos.Schema(
            type=genai.protos.Type.NUMBER,
            description="Segment width in imperial feet units"
        ),
        "variantString": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="Variant of segment. Depends on the selected segment type. variantString values are separated by a pipe character (literally '|'). Most drive lane segments have an 'inbound' or 'outbound' value as the first variant."
        ),
        "type": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            enum=[
                "sidewalk", "streetcar", "bus-lane", "drive-lane", "light-rail",
                "streetcar", "turn-lane", "divider", "temporary", "stencils",
                "food-truck", "flex-zone", "sidewalk-wayfinding", "sidewalk-bench",
                "sidewalk-bike-rack", "magic-carpet", "outdoor-dining", "parklet",
                "bikeshare", "utilities", "sidewalk-tree", "sidewalk-lamp",
                "transit-shelter", "parking-lane"
            ],
            description="Street segment type"
        ),
        "elevation": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            enum=['0', '1', '2'],
            description="Elevation level for segment. 1 is default for sidewalks and buildings, 0 is default for roads, lanes, parking, etc"
        )
    }
)

# Main Streetmix Schema
streetmix_schema = genai.protos.Schema(
    type=genai.protos.Type.OBJECT,
    properties={
        "name": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="Name of created street. If not provided, it will be 'default street'"
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
                    required=["width", "segments"]
                )
            },
            required=["rightBuildingVariant", "leftBuildingVariant", "street"]
        )
    },
    required=["data"]
)
