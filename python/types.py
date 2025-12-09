import typing

ObjectModeItems: typing.TypeAlias = typing.Literal[
    "OBJECT",  # Object Mode.
    "EDIT",  # Edit Mode.
    "POSE",  # Pose Mode.
    "SCULPT",  # Sculpt Mode.
    "VERTEX_PAINT",  # Vertex Paint.
    "WEIGHT_PAINT",  # Weight Paint.
    "TEXTURE_PAINT",  # Texture Paint.
    "PARTICLE_EDIT",  # Particle Edit.
    "EDIT_GPENCIL",  # Edit Mode.Edit Grease Pencil Strokes.
    "SCULPT_GPENCIL",  # Sculpt Mode.Sculpt Grease Pencil Strokes.
    "PAINT_GPENCIL",  # Draw Mode.Paint Grease Pencil Strokes.
    "WEIGHT_GPENCIL",  # Weight Paint.Grease Pencil Weight Paint Strokes.
    "VERTEX_GPENCIL",  # Vertex Paint.Grease Pencil Vertex Paint Strokes.
    "SCULPT_CURVES",  # Sculpt Mode.
]