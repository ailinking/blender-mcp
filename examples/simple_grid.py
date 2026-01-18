# Demo: Create a simple colorful grid

import bpy
import random

def create_grid():
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()
    
    # Create material helper
    def get_random_mat():
        mat = bpy.data.materials.new(name="RandomMat")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (random.random(), random.random(), random.random(), 1)
        return mat

    # Create Grid
    for x in range(5):
        for y in range(5):
            bpy.ops.mesh.primitive_cube_add(location=(x*2, y*2, 0))
            cube = bpy.context.active_object
            cube.data.materials.append(get_random_mat())

create_grid()
print("Grid created!")
