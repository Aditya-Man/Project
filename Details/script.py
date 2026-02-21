import bpy
import math
import os

path = r"C:\work\blender\solar_texture\\"
start_frame = 1
end_frame = 1800
frame_rate = 60

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

world = bpy.data.worlds.new("Space")
bpy.context.scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

bg = nodes.new("ShaderNodeBackground")
bg.inputs[0].default_value = (0.01, 0.02, 0.05, 1)
bg.inputs[1].default_value = 0.08

output = nodes.new("ShaderNodeOutputWorld")
links.new(bg.outputs[0], output.inputs[0])

bpy.ops.mesh.primitive_plane_add(size=500, location=(0, 0, 0))
emitter = bpy.context.object
emitter.hide_viewport = True
emitter.hide_render = True

noise_tex = bpy.data.textures.new("StarNoise", type='CLOUDS')
displace = emitter.modifiers.new(name="DisplaceStars", type='DISPLACE')
displace.texture = noise_tex
displace.strength = 180
displace.mid_level = 0.5

part_mod = emitter.modifiers.new(name="Stars", type='PARTICLE_SYSTEM')
ps = emitter.particle_systems[0]
ps_settings = ps.settings

ps_settings.type = 'EMITTER'
ps_settings.emit_from = 'VERT'
ps_settings.count = 3000
ps_settings.frame_start = start_frame
ps_settings.frame_end = start_frame
ps_settings.lifetime = end_frame + 200
ps_settings.particle_size = 0.012
ps_settings.normal_factor = 0
ps_settings.render_type = 'OBJECT'

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.018, location=(0, 0, 10000))
star_proto = bpy.context.object
star_proto.hide_viewport = True
star_proto.hide_render = True

mat_star = bpy.data.materials.new("StarMat")
mat_star.use_nodes = True
nodes = mat_star.node_tree.nodes
nodes.clear()

emission = nodes.new("ShaderNodeEmission")
emission.inputs[0].default_value = (1, 0.98, 0.92, 1)
emission.inputs[1].default_value = 12

output = nodes.new("ShaderNodeOutputMaterial")
mat_star.node_tree.links.new(emission.outputs[0], output.inputs[0])
star_proto.data.materials.append(mat_star)

ps_settings.instance_object = star_proto

def make_mat(name, file, glow=False, alpha=False, bump_file=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    try:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(os.path.join(path, file))
    except:
        tex = nodes.new("ShaderNodeRGB")
        tex.outputs[0].default_value = (0.8, 0.4, 0.2, 1)

    output = nodes.new("ShaderNodeOutputMaterial")

    if glow:
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Strength"].default_value = 18
        links.new(tex.outputs["Color"], emission.inputs["Color"])
        links.new(emission.outputs[0], output.inputs[0])
    else:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = 0.8

        subsurface = bsdf.inputs.get("Subsurface")
        if subsurface:
            subsurface.default_value = 0.03 if "Jupiter" in name or "Saturn" in name else 0.0

        radius = bsdf.inputs.get("Subsurface Radius")
        if radius:
            radius.default_value = (0.8, 0.4, 0.2)

        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs[0], output.inputs[0])

    if alpha:
        mat.blend_method = 'BLEND'
        if "Alpha" in tex.outputs:
            links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])

    return mat

bpy.ops.mesh.primitive_uv_sphere_add(radius=4)
sun = bpy.context.object
sun.data.materials.append(make_mat("Sun", "sun.jpg", glow=True))

bpy.ops.object.light_add(type='AREA', location=(0, 0, 0))
sun_light = bpy.context.object
sun_light.data.shape = 'DISK'
sun_light.data.size = 8.0
sun_light.data.energy = 300000000.0
sun_light.data.color = (1.0, 0.92, 0.85)

planets = [
    ("Mercury", 0.24, 8, "mercury.jpg", None, 88),
    ("Venus", 0.48, 12, "venus.jpg", None, 225),
    ("Earth", 0.50, 16, "earth.jpg", None, 365),
    ("Mars", 0.27, 22, "mars.jpg", None, 687),
    ("Jupiter", 5.60, 45, "jupiter.jpg", None, 4333),
    ("Saturn", 4.70, 70, "saturn.jpg", None, 10759),
    ("Uranus", 2.00, 100, "uranus.jpg", None, 30687),
    ("Neptune", 1.95, 130, "neptune.jpg", None, 60190),
]

orbit_empties = {}

for name, size, dist, texfile, bumpfile, orbit_days in planets:
    bpy.ops.object.empty_add(location=(0, 0, 0))
    orbit = bpy.context.object
    orbit_empties[name] = orbit

    bpy.ops.mesh.primitive_uv_sphere_add(radius=size, location=(dist, 0, 0))
    planet = bpy.context.object
    planet.name = name
    planet.parent = orbit
    planet.data.materials.append(make_mat(name, texfile))

    orbit_frames = orbit_days * 2.0
    orbit.rotation_euler = (0, 0, 0)
    orbit.keyframe_insert("rotation_euler", frame=start_frame)
    orbit.rotation_euler = (0, 0, math.radians(360))
    orbit.keyframe_insert("rotation_euler", frame=start_frame + orbit_frames)

    planet.rotation_euler = (0, 0, 0)
    planet.keyframe_insert("rotation_euler", frame=start_frame)
    planet.rotation_euler = (0, 0, math.radians(720))
    planet.keyframe_insert("rotation_euler", frame=end_frame)

earth_orbit = orbit_empties.get("Earth")
if earth_orbit:
    bpy.ops.object.empty_add(location=(0, 0, 0))
    moon_orbit = bpy.context.object
    moon_orbit.parent = earth_orbit

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, location=(1.8, 0, 0))
    moon = bpy.context.object
    moon.parent = moon_orbit
    moon.data.materials.append(make_mat("Moon", "moon.jpg"))

    moon_orbit.rotation_euler = (0, 0, 0)
    moon_orbit.keyframe_insert("rotation_euler", frame=start_frame)
    moon_orbit.rotation_euler = (0, 0, math.radians(360 * 12))
    moon_orbit.keyframe_insert("rotation_euler", frame=end_frame)

bpy.ops.object.camera_add(location=(0, -160, 80), rotation=(math.radians(80), 0, 0))
cam = bpy.context.object
bpy.context.scene.camera = cam
cam.data.lens = 24.0
cam.data.clip_end = 20000.0

bpy.ops.object.empty_add(location=(0, 0, 0))
cam_orbit = bpy.context.object
cam.parent = cam_orbit

cam_orbit.rotation_euler = (0, 0, math.radians(-90))
cam_orbit.keyframe_insert("rotation_euler", frame=start_frame)
cam_orbit.rotation_euler = (0, 0, math.radians(270))
cam_orbit.keyframe_insert("rotation_euler", frame=end_frame)

constraint = cam.constraints.new(type='TRACK_TO')
constraint.target = sun
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'

scene = bpy.context.scene
scene.frame_start = start_frame
scene.frame_end = end_frame
scene.render.fps = frame_rate

scene.render.engine = 'CYCLES'
scene.cycles.samples = 200
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True
scene.render.use_motion_blur = True

for obj in bpy.data.objects:
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for key in fcurve.keyframe_points:
                key.interpolation = 'LINEAR'
            fcurve.modifiers.new(type='CYCLES')