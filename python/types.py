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
OperatorReturnItems: typing.TypeAlias = typing.Literal[
    "RUNNING_MODAL",  # Running Modal.Keep the operator running with blender.
    "CANCELLED",  # Cancelled.The operator exited without doing anything, so no undo entry should be pushed.
    "FINISHED",  # Finished.The operator exited after completing its action.
    "PASS_THROUGH",  # Pass Through.Do nothing and pass the event on.
    "INTERFACE",  # Interface.Handled but not executed (popup menus).
]