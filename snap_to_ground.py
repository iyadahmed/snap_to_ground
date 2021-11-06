#
# Copyright (c) 2021 Iyad Ahmed
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


bl_info = {
    "name": "Snap to Ground",
    "author": "Iyad Ahmed (Twitter: @cgonfire)",
    "version": (0, 0, 1),
    "blender": (2, 93, 4),
    "category": "Object",
}


import numpy as np
import bpy
from mathutils import Vector
import sys


def transform_direction_vector(mat, vec):
    return (mat @ Vector(vec)) - (mat @ Vector((0, 0, 0)))


class STG_OT_snap_to_ground(bpy.types.Operator):
    """Snap active object to ground"""

    bl_idname = "stg.snap_to_ground"
    bl_label = "Snap to Ground"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT":
            return False
        if context.active_object is None:
            return False

        return True

    def execute(self, context):
        obj = context.active_object

        mesh = obj.data
        verts_co_np = np.empty(len(mesh.vertices) * 3)
        mesh.vertices.foreach_get("co", verts_co_np)
        verts_co_np.shape = -1, 3

        world_to_obj_mat = obj.matrix_world.inverted()
        up_vec_local = transform_direction_vector(world_to_obj_mat, (0, 0, 1))
        min_vert = verts_co_np[verts_co_np.dot(up_vec_local).argmin()]
        min_vert_world = obj.matrix_world @ Vector(min_vert)

        dg = context.evaluated_depsgraph_get()

        obj.hide_set(True)  # make object invisible in viewport and to ray cast too
        is_hit, location, normal, face_index, hit_obj, matrix = context.scene.ray_cast(dg, min_vert_world, (0, 0, -1))
        obj.hide_set(False)  # restore object visibility
        obj.select_set(True)  # restore object selection (lose when we hide the object)

        if not is_hit:
            self.report({"WARNING"}, "Nothing is below object's lowest point")
            return {"CANCELLED"}

        translation = location - Vector(min_vert_world)
        obj.location += translation
        return {"FINISHED"}


addon_keymaps = []


def register():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type="VIEW_3D")

    kmi = km.keymap_items.new(STG_OT_snap_to_ground.bl_idname, "D", "PRESS")
    addon_keymaps.append((km, kmi))

    bpy.utils.register_class(STG_OT_snap_to_ground)


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_class(STG_OT_snap_to_ground)
