
import numpy as np

import bpy
from bpy.props import EnumProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception

U_SOCKET = 1
V_SOCKET = 2

class SvExEvalSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Evaluate Surface
    Tooltip: Evaluate Surface
    """
    bl_idname = 'SvExEvalSurfaceNode'
    bl_label = 'Evaluate Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'

    coord_modes = [
        ('XY', "X Y -> Z", "XY -> Z function", 0),
        ('UV', "U V -> X Y Z", "UV -> XYZ function", 1)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs[U_SOCKET].name = "U" if self.coord_mode == 'UV' else "X"
        self.inputs[V_SOCKET].name = "V" if self.coord_mode == 'UV' else "Y"

        self.inputs[U_SOCKET].hide_safe = self.input_mode == 'VERTICES'
        self.inputs[V_SOCKET].hide_safe = self.input_mode == 'VERTICES'
        self.inputs['Vertices'].hide_safe = self.input_mode == 'PAIRS'

    coord_mode : EnumProperty(
        name = "Coordinates",
        items = coord_modes,
        default = 'XY',
        update = update_sockets)

    input_modes = [
        ('PAIRS', "Separate", "Separate U V (or X Y) sockets", 0),
        ('VERTICES', "Vertices", "Single socket for vertices", 1)
    ]

    input_mode : EnumProperty(
        name = "Input mode",
        items = input_modes,
        default = 'PAIRS',
        update = update_sockets)

    axes = [
        ('XY', "X Y", "XOY plane", 0),
        ('YZ', "Y Z", "YOZ plane", 1),
        ('XZ', "X Z", "XOZ plane", 2)
    ]

    orientation : EnumProperty(
            name = "Orientation",
            items = axes,
            default = 'XY',
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Surface type:")
        layout.prop(self, "coord_mode", expand=True)
        layout.label(text="Input mode:")
        layout.prop(self, "input_mode", expand=True)
        if self.input_mode == 'VERTICES':
            layout.label(text="Input orientation:")
            layout.prop(self, "orientation", expand=True)

    def sv_init(self, context):
        self.inputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND' #0
        self.inputs.new('SvStringsSocket', "U") # 1 — U_SOCKET
        self.inputs.new('SvStringsSocket', "V") # 2 — V_SOCKET
        self.inputs.new('SvVerticesSocket', "Vertices") # 3
        self.outputs.new('SvVerticesSocket', "Vertices") # 0
        self.update_sockets(context)

    def parse_input(self, verts):
        verts = np.array(verts)
        if self.orientation == 'XY':
            us, vs = verts[:,0], verts[:,1]
        elif self.orientation == 'YZ':
            us, vs = verts[:,1], verts[:,2]
        else: # XZ
            us, vs = verts[:,0], verts[:,2]
        return us, vs

    def build_output(self, surface, verts):
        orientation = surface.get_input_orientation()
        if orientation == 'X':
            verts[:,1], verts[:,2], verts[:,0] = verts[:,0], verts[:,1], verts[:,2]
        elif orientation == 'Y':
            verts[:,2], verts[:,0], verts[:,1] = verts[:,0], verts[:,1], verts[:,2]
        else: # Z
            pass
        if surface.has_input_matrix:
            matrix = surface.get_input_matrix()
            verts = verts - matrix.translation
            np_matrix = np.array(matrix.to_3x3())
            verts = np.apply_along_axis(lambda v : np_matrix @ v, 2, verts)
        return verts

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        target_us_s = self.inputs[U_SOCKET].sv_get(default=[[]])
        target_vs_s = self.inputs[V_SOCKET].sv_get(default=[[]])
        target_verts_s = self.inputs['Vertices'].sv_get(default = [[]])

        verts_out = []

        inputs = zip_long_repeat(surfaces_s, target_us_s, target_vs_s, target_verts_s)
        for surface, target_us, target_vs, target_verts in inputs:
            if surface.get_coord_mode() != self.coord_mode:
                self.warning("Input surface mode is %s, but Evaluate node mode is %s; the result can be unexpected", surface.get_coord_mode(), self.coord_mode)

            if self.input_mode == 'VERTICES':
                target_us, target_vs = self.parse_input(target_verts)
            else:
                target_us, target_vs = np.array(target_us), np.array(target_vs)
            new_verts = surface.evaluate_array(target_us, target_vs)

            if self.coord_mode == 'XY':
                new_verts = self.build_output(surface, new_verts)
                new_verts = new_verts.tolist()
            else:
                new_verts = new_verts.tolist()
            verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvExEvalSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExEvalSurfaceNode)

