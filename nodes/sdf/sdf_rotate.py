import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok_extra.dependencies import sdf
from sverchok_extra.utils.sdf import *
from sverchok.utils.sv_transform_helper import AngleUnits, SvAngleHelper

if sdf is None:
    add_dummy('SvExSdfRotateNode', "SDF Rotate", 'sdf')

class SvExSdfRotateNode(bpy.types.Node, SverchCustomTreeNode, SvAngleHelper):
    """
    Triggers: SDF Rotate
    Tooltip: SDF Rotate
    """
    bl_idname = 'SvExSdfRotateNode'
    bl_label = 'SDF Rotate'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ROTATE'

    axis_v: FloatVectorProperty(
        name="Axis",
        default=(0, 0, 1),
        size=3,
        update=updateNode)

    angle: FloatProperty(
        name = "Angle",
        default = 0.0,
        update = SvAngleHelper.update_angle)

    last_angle_units: EnumProperty(
        name="Last Angle Units", description="Angle units (Radians/Degrees/Unities)",
        default=AngleUnits.RADIANS, items=AngleUnits.get_blender_enum())

    def update_angles(self, context, au):
        ''' Update all the angles to preserve their values in the new units '''
        self.angle = self.angle * au

    def draw_buttons(self, context, layout):
        self.draw_angle_units_buttons(context, layout)

    def sv_init(self, context):
        self.inputs.new('SvScalarFieldSocket', "SDF")
        self.inputs.new('SvVerticesSocket', "Axis").prop_name = 'axis_v'
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'
        self.outputs.new('SvScalarFieldSocket', "SDF")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        sdf_s = self.inputs['SDF'].sv_get()
        axis_s = self.inputs['Axis'].sv_get()
        angle_s = self.inputs['Angle'].sv_get()

        input_level = get_data_nesting_level(sdf_s, data_types=(SvScalarField,))
        flat_output = input_level == 1
        sdf_s = ensure_nesting_level(sdf_s, 2, data_types=(SvScalarField,))
        axis_s = ensure_nesting_level(axis_s, 3)
        angle_s = ensure_nesting_level(angle_s, 2)

        au = self.radians_conversion_factor()

        sdf_out = []
        for params in zip_long_repeat(sdf_s, axis_s, angle_s):
            new_sdf = []
            for sdf, axis, angle in zip_long_repeat(*params):
                sdf = scalar_field_to_sdf(sdf, 0)
                sdf = sdf.rotate(angle*au, axis)
                field = SvExSdfScalarField(sdf)
                new_sdf.append(field)
            if flat_output:
                sdf_out.extend(new_sdf)
            else:
                sdf_out.append(new_sdf)

        self.outputs['SDF'].sv_set(sdf_out)

def register():
    if sdf is not None:
        bpy.utils.register_class(SvExSdfRotateNode)

def unregister():
    if sdf is not None:
        bpy.utils.unregister_class(SvExSdfRotateNode)

