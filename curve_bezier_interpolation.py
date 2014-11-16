import bpy
import math
from mathutils import Vector

bl_info = {
    "name": "Bezier To PolyLine",
    "author": "MasicBlack",
    "version": (0, 1, 0),
    "blender": (2, 72, 0),
    "location": "View3D > Object",
    "description": "Convert a curve object to polyline mesh with specified number of points.",
    "warning": "",
    "category": "Object"}

#-----------------funtions--------------------
def bezier_interpolation(cp1, cp2, cp3, cp4, t):
    '''
    blender use 4-order bezier curve.
    control poinst for every segment is : p1.co, p1.handle_right, p2.handle_left, p2.co.  
    '''
    #cp is control point Vector().
    c1 = (1-t)*(1-t)*(1-t)
    c2 = 3*t*(1-t)*(1-t)
    c3 = 3*t*t*(1-t)
    c4 = t*t*t

    return c1*cp1 + c2*cp2 + c3*cp3 + c4*cp4

def get_knots_list(order, ctrl_points, use_end_point, use_cyclic):
    pass

def generateNurbsBiasFunction(u, order, knots):
    '''blender use 2 to 6 order for nurbs.
    '''
    # cache = {2:None, 3:None, 4:None, 5:None, 6:None}
    # if cache[order] is None:
    #     cache = [0 for i in range]
    #cache = [0 for i in range(len(knots))]
    #for i in xrange(order - 1):

    pass
#-----------------bpy access-------------------
def getActiveCurveObject():
    obj = bpy.context.active_object
    if obj.type == 'CURVE':
        return obj
    else:
        return None

def interpolatePoints(curve_obj, points):
    '''
    curve object can contains mutiple curves(splines) with different types(poly, bezier, nurbs),
    only process splines[0].
    '''
    if points < 2:
        raise RuntimeError("At least 2 points is needed.")
    verts = []
    edges = []
    if curve_obj == None or len(curve_obj.data.splines) < 1:
        raise RuntimeError("Not a Curve Object")
    if len(curve_obj.data.splines) < 1:
        raise RuntimeError("Curve Object Not Contains Curve Spline!")
    spline = curve_obj.data.splines[0]
    if spline.type != 'BEZIER':
        raise RuntimeError("Not a Bezier Curve!") 

    segments = len(spline.bezier_points) if spline.use_cyclic_u else len(spline.bezier_points) - 1
    step = 1.0*segments/points if spline.use_cyclic_u else 1.0*segments/(points - 1)
    #make edges first.
    edges = [(i, i+1) for i in range(points - 1)]
    if spline.use_cyclic_u:
        edges.append((points - 1, 0))#connect tail to head.

    #TODO:fix.
    for i in range(points):
        progress = step*i
        print(progress)
        offset, index = math.modf(progress)
        print(offset, index, len(spline.bezier_points))
        cp1 = spline.bezier_points[int(index)    %len(spline.bezier_points)].co
        cp2 = spline.bezier_points[int(index)    %len(spline.bezier_points)].handle_right
        cp3 = spline.bezier_points[(int(index)+1)%len(spline.bezier_points)].handle_left
        cp4 = spline.bezier_points[(int(index)+1)%len(spline.bezier_points)].co
        new_point = bezier_interpolation(cp1, cp2, cp3, cp4, offset)
        verts.append(new_point)

    return verts, edges

def createPolyLineFromList(curve_obj, verts, edges):
    # Create mesh and object
    name = curve_obj.name+'_polyline'
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    #copy transform
    ob.location = curve_obj.location
    ob.rotation_euler = curve_obj.rotation_euler
    ob.scale = curve_obj.scale

    #remove curve_obj
    bpy.ops.object.delete()

    #ob.show_name = True
    # Link object to scene and make active
    scn = bpy.context.scene
    scn.objects.link(ob)
    scn.objects.active = ob
    ob.select = True
 
    # Create mesh from given verts, edges.
    me.from_pydata(verts, edges, [])
    # Update mesh with new data
    me.update()    
    return ob

#-------------------ui and addon-------------------
class ConvertBezierToPolyLine(bpy.types.Operator):
    bl_idname = "curve.bezier_to_polyline"
    bl_label = "Convert Bezier To PolyLine"
    bl_options = {'REGISTER', 'UNDO'}
    points = bpy.props.IntProperty(name = "Points",
                                   description = "Point count for generated polyline.",
                                   default = 12,
                                   soft_min = 2,
                                   soft_max = 1000)

    def execute(self, context):
        curve_obj = getActiveCurveObject()
        verts, edges = interpolatePoints(curve_obj, self.points)
        createPolyLineFromList(curve_obj, verts, edges)
        return{'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self) 
        #return self.excute(context)

    def draw(self, context) :
        col = self.layout.column()
        col.prop(self, "points")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'CURVE' and context.mode == 'OBJECT')

class VIEW3D_MT_tools_curve_to_polyline(bpy.types.Menu):
    bl_label = "BezierToPolyLine"

    def draw(self, context):
        layout = self.layout
        layout.operator("curve.bezier_to_polyline")

def menu_func(self, context):
    #self.layout.menu("VIEW3D_MT_tools_curve_to_polyline")#this will create sub menu.
    layout = self.layout
    layout.operator("curve.bezier_to_polyline")
    layout.separator()

def register():
    #bpy.utils.register_module(__name__)
    bpy.utils.register_class(ConvertBezierToPolyLine)
    bpy.utils.register_class(VIEW3D_MT_tools_curve_to_polyline)
    bpy.types.VIEW3D_MT_object_specials.prepend(menu_func)

def unregister():
    #bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)
    bpy.utils.unregister_class(ConvertBezierToPolyLine)

if __name__ == '__main__':
    register()