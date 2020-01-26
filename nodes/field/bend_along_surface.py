
from sverchok.utils.logging import info, exception

import numpy as np
from math import sqrt

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, fullList, ensure_nesting_level
from sverchok.utils.geom import diameter

from sverchok_extra.data.field.vector import SvExBendAlongSurfaceField

class SvExBendAlongSurfaceFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bend surface
    Tooltip: Generate a vector field which bends the space along the given surface.
    """
    bl_idname = 'SvExBendAlongSurfaceFieldNode'
    bl_label = 'Bend Along Surface Field'
    bl_icon = 'OUTLINER_OB_EMPTY'

    axes = [
            ("X", "X", "X axis", 1),
            ("Y", "Y", "Y axis", 2),
            ("Z", "Z", "Z axis", 3)
        ]

    orient_axis_: EnumProperty(
        name="Orientation axis", description="Which axis of object to put along path",
        default="Z", items=axes, update=updateNode)

    def get_axis_idx(self, letter):
        return 'XYZ'.index(letter)

    def get_orient_axis_idx(self):
        return self.get_axis_idx(self.orient_axis_)

    orient_axis = property(get_orient_axis_idx)

    autoscale: BoolProperty(
        name="Auto scale", description="Scale object along orientation axis automatically",
        default=False, update=updateNode)

    flip: BoolProperty(
        name="Flip surface",
        description="Flip the surface orientation",
        default=False, update=updateNode)

    coord_modes = [
        ('XY', "X Y -> Z", "XY -> Z function", 0),
        ('UV', "U V -> X Y Z", "UV -> XYZ function", 1)
    ]

    coord_mode : EnumProperty(
        name = "Coordinates",
        items = coord_modes,
        default = 'XY',
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND'
        self.outputs.new('SvExVectorFieldSocket', 'Field').display_shape = 'CIRCLE_DOT'

    def draw_buttons(self, context, layout):
        layout.label(text="Surface mode:")
        layout.prop(self, "coord_mode", expand=True)
        layout.label(text="Object vertical axis:")
        layout.prop(self, "orient_axis_", expand=True)
        layout.prop(self, "autoscale", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'flip')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()

        fields_out = []
        for surface in surfaces_s:
            #if surface.get_coord_mode() != self.coord_mode:
            #    self.warning("Input surface mode is %s, but Evaluate node mode is %s; the result can be unexpected", surface.get_coord_mode(), self.coord_mode)

            field = SvExBendAlongSurfaceField(surface, self.orient_axis,
                        self.autoscale, self.flip)
            fields_out.append(field)

        self.outputs['Field'].sv_set(fields_out)

def register():
    bpy.utils.register_class(SvExBendAlongSurfaceFieldNode)

def unregister():
    bpy.utils.unregister_class(SvExBendAlongSurfaceFieldNode)

