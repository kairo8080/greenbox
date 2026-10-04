"""Greedy surface export and studio preview for an actual cubic-voxel room.

Run with Blender 5.1, for example:
  blender.exe --background --disable-autoexec --python-exit-code 1 \
    --python work/bedroom/render_bedroom.py -- work/bedroom/scene.json \
    --output-dir outputs/bedroom --samples 32 --resolution 1400 1100

Geometry helpers can also be imported by ordinary Python for verification.
The input scene and voxel sources are never changed. Output replacement requires
--force. Lights and ground belong to the Blender preview and are excluded from
both mesh exports. Lamp effects are aesthetic; no gameplay control is implied.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zlib

try:
    import bpy
    from mathutils import Vector
except ImportError:
    bpy = None
    Vector = None


NEIGHBORS = ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1))


def linear_color(rgba):
    def convert(value):
        value /= 255.0
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
    return tuple(convert(channel) for channel in rgba[:3]) + (rgba[3] / 255.0,)


def face_corners(axis, sign, plane, u, v, width, height):
    """Counterclockwise corners viewed from the exterior, at integer cube edges."""
    if axis == 0:
        positive = ((plane, u, v), (plane, u + width, v),
                    (plane, u + width, v + height), (plane, u, v + height))
    elif axis == 1:
        positive = ((u + width, plane, v), (u, plane, v),
                    (u, plane, v + height), (u + width, plane, v + height))
    else:
        positive = ((u, v, plane), (u + width, v, plane),
                    (u + width, v + height, plane), (u, v + height, plane))
    return positive if sign > 0 else tuple(reversed(positive))


def greedy_surface(voxels):
    """Merge only adjacent exposed faces of the same axis, plane and exact color.

    Every group is independently covered once. Area and normal checks compare
    against the original exposed unit faces, rather than against a derived mesh.
    """
    groups = defaultdict(set)
    original_surface_cells = 0
    for point, color in voxels.items():
        for axis, sign in NEIGHBORS:
            neighbor = list(point)
            neighbor[axis] += sign
            if tuple(neighbor) in voxels:
                continue
            plane = point[axis] + (1 if sign > 0 else 0)
            remaining_axes = [index for index in range(3) if index != axis]
            u, v = point[remaining_axes[0]], point[remaining_axes[1]]
            groups[(axis, sign, plane, color)].add((u, v))
            original_surface_cells += 1

    quads = []
    verified_area = 0
    area_by_color = Counter()
    for (axis, sign, plane, color), cells in sorted(groups.items()):
        expected_area = len(cells)
        group_area = 0
        for u, v in sorted(cells, key=lambda point: (point[1], point[0])):
            if (u, v) not in cells:
                continue
            width = 1
            while (u + width, v) in cells:
                width += 1
            height = 1
            while all((u + step, v + height) in cells for step in range(width)):
                height += 1
            for dv in range(height):
                for du in range(width):
                    cells.remove((u + du, v + dv))
            corners = face_corners(axis, sign, plane, u, v, width, height)
            a, b, c = corners[:3]
            edge_a = tuple(b[i] - a[i] for i in range(3))
            edge_b = tuple(c[i] - b[i] for i in range(3))
            cross = (edge_a[1] * edge_b[2] - edge_a[2] * edge_b[1],
                     edge_a[2] * edge_b[0] - edge_a[0] * edge_b[2],
                     edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0])
            expected_normal = tuple(sign * width * height if i == axis else 0 for i in range(3))
            if cross != expected_normal:
                raise ValueError(f"Face winding/area mismatch: {cross} != {expected_normal}")
            quads.append((corners, color, width * height))
            group_area += width * height
            area_by_color[color] += width * height
        if cells or group_area != expected_area:
            raise ValueError("Greedy surface did not cover exactly the exposed faces")
        verified_area += group_area
    if verified_area != original_surface_cells:
        raise ValueError("Greedy surface area differs from exposed unit-cube faces")
    return quads, original_surface_cells, dict(sorted(area_by_color.items()))


def validate_scene(scene):
    pitch = scene.get("voxel_pitch", 0.05)
    if not isinstance(pitch, (int, float)) or not math.isfinite(pitch) or pitch <= 0:
        raise ValueError("voxel_pitch must be positive and finite")
    palette = scene.get("palette")
    if not isinstance(palette, list) or len(palette) != 256:
        raise ValueError("palette must contain 256 RGBA colors, with air at index zero")
    for rgba in palette:
        if len(rgba) != 4 or any(type(channel) is not int or not 0 <= channel <= 255 for channel in rgba):
            raise ValueError("palette channels must be integers in 0..255")
    models = {}
    for asset in scene.get("assets", []):
        name, dimensions = asset["name"], asset["dimensions"]
        if not isinstance(name, str) or not name or name in models:
            raise ValueError("Asset names must be unique nonempty strings")
        if len(dimensions) != 3 or any(type(size) is not int or not 1 <= size <= 256 for size in dimensions):
            raise ValueError(f"Invalid single-model dimensions: {name}")
        voxels = {}
        for cell in asset["voxels"]:
            if len(cell) != 4 or any(type(value) is not int for value in cell):
                raise ValueError(f"Voxel must have four integer components: {name}")
            x, y, z, color = cell
            point = x, y, z
            if not 1 <= color <= 255 or any(point[i] < 0 or point[i] >= dimensions[i] for i in range(3)):
                raise ValueError(f"Voxel outside dimensions or invalid color: {name} {cell}")
            if point in voxels:
                raise ValueError(f"Duplicate occupied coordinate: {name} {point}")
            voxels[point] = color
        if not voxels:
            raise ValueError(f"Empty asset: {name}")
        models[name] = (asset, voxels)
    if not models:
        raise ValueError("Scene must contain assets")
    instance_names = set()
    for instance in scene.get("instances", []):
        name = instance["name"]
        if not isinstance(name, str) or not name or name in instance_names:
            raise ValueError("Instance names must be unique nonempty strings")
        instance_names.add(name)
        if instance["asset"] not in models:
            raise ValueError(f"Unknown instance asset: {instance['asset']}")
        offset = instance["offset"]
        if len(offset) != 3 or any(type(value) is not int for value in offset):
            raise ValueError("Instance canvas offsets must be three integers")
        if type(instance.get("hidden", False)) is not bool:
            raise ValueError("Instance hidden must be boolean")
    if not instance_names:
        raise ValueError("Scene must contain instances")
    emissive = set(scene.get("emissive_indices", []))
    if any(type(index) is not int or not 1 <= index <= 255 for index in emissive):
        raise ValueError("Invalid emissive palette indices")
    return models, palette, float(pitch), emissive


def write_palette_atlas(path, palette):
    """Write exact source sRGB bytes: index 1 at the top-left texel, air last."""
    colors = palette[1:] + [palette[0]]
    rows = b"".join(b"\0" + b"".join(bytes(rgba) for rgba in colors[row * 16:(row + 1) * 16])
                    for row in range(16))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0))
            + chunk(b"sRGB", b"\0") + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))
    path.write_bytes(data)
    image = bpy.data.images.load(str(path), check_existing=False)
    image.name = "Bedroom exact voxel palette (sRGB)"
    image.colorspace_settings.name = "sRGB"
    image.pack()
    return image, hashlib.sha256(data).hexdigest()


def make_material(name, image, emissive=False):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.use_backface_culling = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    color = material.node_tree.nodes.new("ShaderNodeTexImage")
    color.image = image
    color.interpolation = "Closest"
    color.extension = "EXTEND"
    color.label = "Exact palette texel center, nearest interpolation"
    material.node_tree.links.new(color.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.83 if not emissive else 0.65
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Specular IOR Level"].default_value = 0.2
    if emissive:
        material.node_tree.links.new(color.outputs["Color"], shader.inputs["Emission Color"])
        shader.inputs["Emission Strength"].default_value = 2.0
    return material


def mesh_for_asset(asset, voxels, palette, pitch, emissive, materials):
    quads, surface_cells, color_areas = greedy_surface(voxels)
    mins = tuple(min(point[i] for point in voxels) for i in range(3))
    maxs = tuple(max(point[i] for point in voxels) + 1 for i in range(3))
    pivot = ((mins[0] + maxs[0]) / 2.0, (mins[1] + maxs[1]) / 2.0, mins[2])
    vertices, polygons, indices = [], [], {}
    for corners, color, area in quads:
        polygon = []
        for point in corners:
            if point not in indices:
                indices[point] = len(vertices)
                vertices.append(tuple((point[i] - pivot[i]) * pitch for i in range(3)))
            polygon.append(indices[point])
        polygons.append(polygon)
    mesh = bpy.data.meshes.new(asset["name"] + "_greedy_surface")
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()
    mesh.materials.append(materials[0])
    mesh.materials.append(materials[1])
    # A degenerate UV per face points at one exact palette texel center. It has
    # no spatial gradient, preserving flat colors while permitting GLB emissive
    # textures. No COLOR_0 is exported, avoiding accidental double multiplication.
    attribute = mesh.uv_layers.new(name="PaletteUV")
    emissive_quads = 0
    for polygon, (_, color, _) in zip(mesh.polygons, quads):
        polygon.use_smooth = False
        polygon.material_index = int(color in emissive)
        emissive_quads += int(color in emissive)
        for loop_index in polygon.loop_indices:
            texel = color - 1
            attribute.data[loop_index].uv = ((texel % 16 + .5) / 16,
                                           1 - (texel // 16 + .5) / 16)
    mesh.calc_loop_triangles()
    if len(mesh.loop_triangles) != len(quads) * 2:
        raise ValueError("Mesh triangulation differs from rectangular surface count")
    mesh["source_voxel_count"] = len(voxels)
    mesh["source_surface_cells"] = surface_cells
    mesh["verified_surface_area_voxels"] = surface_cells
    mesh["greedy_quads"] = len(quads)
    mesh["source_asset"] = asset["name"]
    record = {
        "name": asset["name"], "dimensions_voxels": asset["dimensions"],
        "filled_voxels": len(voxels), "exposed_unit_faces": surface_cells,
        "greedy_quads": len(quads), "triangles": len(quads) * 2,
        "vertices": len(vertices), "ordinary_quads": len(quads) - emissive_quads,
        "emissive_quads": emissive_quads, "surfaces_used": int(emissive_quads < len(quads)) + int(emissive_quads > 0),
        "occupied_bounds_min": list(mins), "occupied_bounds_max_exclusive": list(maxs),
        "mesh_dimensions_meters": [(maxs[i] - mins[i]) * pitch for i in range(3)],
        "ground_pivot_source_voxels": list(pivot), "colors_used": sorted(set(voxels.values())),
        "surface_area_by_palette_index": color_areas,
        "verification": "Exact exposed-cell coverage and outward winding checked for every coplanar color group",
        "metadata": asset.get("metadata", {}),
        "palette_uv": "Index minus one; every face corner samples the same nearest texel center",
    }
    return mesh, pivot, record


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area_light(collection, name, position, target, power, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.shape, data.size, data.color = power, "DISK", size, color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = position
    aim(obj, target)
    return obj


def bounds_for_objects(objects):
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    mins = tuple(min(point[i] for point in corners) for i in range(3))
    maxs = tuple(max(point[i] for point in corners) for i in range(3))
    return mins, maxs, corners


def export_objects(path, objects):
    bpy.ops.object.select_all(action="DESELECT")
    hidden = [(obj, obj.hide_get(), obj.hide_render) for obj in objects]
    for obj, _, _ in hidden:
        obj.hide_set(False)
        obj.hide_render = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                              export_yup=True, export_materials="EXPORT", export_extras=True,
                              export_normals=True, export_cameras=False, export_lights=False)
    for obj, viewport_hidden, render_hidden in hidden:
        obj.select_set(False)
        obj.hide_set(viewport_hidden)
        obj.hide_render = render_hidden


def verify_glb(path, objects, palette_path):
    """Verify the written GLB, including the embedded source color bytes."""
    data = path.read_bytes()
    magic, version, declared_size = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2 or declared_size != len(data):
        raise ValueError("Invalid GLB container")
    json_size, tag = struct.unpack_from("<II", data, 12)
    if tag != 0x4e4f534a:
        raise ValueError("Missing GLB JSON chunk")
    document = json.loads(data[20:20 + json_size])
    binary_size, binary_tag = struct.unpack_from("<II", data, 20 + json_size)
    if binary_tag != 0x004e4942:
        raise ValueError("Missing GLB binary chunk")
    if document.get("cameras") or document.get("extensions", {}).get("KHR_lights_punctual"):
        raise ValueError("Preview camera or lights leaked into mesh export")
    actual_names = {node.get("name") for node in document.get("nodes", [])}
    if actual_names != {obj.name for obj in objects}:
        raise ValueError("GLB nodes differ from selected voxel asset instances")
    if len(document.get("materials", [])) > 2 or any(len(mesh["primitives"]) > 2 for mesh in document["meshes"]):
        raise ValueError("GLB exceeds two shared surface materials")
    triangles = 0
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            if "COLOR_0" in primitive["attributes"] or "TEXCOORD_0" not in primitive["attributes"]:
                raise ValueError("GLB palette UV missing or multiplied by redundant vertex colors")
            triangles += document["accessors"][primitive["indices"]]["count"] // 3
    unique_meshes = {obj.data.name: obj.data for obj in objects}
    expected_triangles = sum(len(mesh.loop_triangles) for mesh in unique_meshes.values())
    if triangles != expected_triangles:
        raise ValueError("GLB triangle count differs from verified greedy mesh")
    if len(document.get("images", [])) != 1:
        raise ValueError("Expected exactly one shared embedded palette image")
    image = document["images"][0]
    view = document["bufferViews"][image["bufferView"]]
    begin = 28 + json_size + view.get("byteOffset", 0)
    image_bytes = data[begin:begin + view["byteLength"]]
    if image_bytes != palette_path.read_bytes():
        raise ValueError("GLB palette image differs from exact source RGBA PNG")
    if any(sampler.get("magFilter") != 9728 for sampler in document["samplers"]):
        raise ValueError("GLB palette magnification must use nearest interpolation")
    emissive_material_count = 0
    for material in document["materials"]:
        if "emissiveTexture" in material:
            emissive_material_count += 1
            emission = document["textures"][material["emissiveTexture"]["index"]]
            base = document["textures"][material["pbrMetallicRoughness"]["baseColorTexture"]["index"]]
            if emission["source"] != base["source"] or emission["sampler"] != base["sampler"]:
                raise ValueError("Base and emission must use the same exact palette image/sampler")
    return {"bytes": len(data), "nodes": len(document["nodes"]), "unique_meshes": len(document["meshes"]),
            "materials": len(document["materials"]), "emissive_material_count": emissive_material_count,
            "triangles_unique_mesh_data": triangles, "source_palette_png_embedded_exactly": True,
            "max_surface_primitives_per_mesh": max(len(mesh["primitives"]) for mesh in document["meshes"]),
            "nearest_palette_sampling": True, "preview_objects_excluded": True}


def setup_preview(scene_data, asset_models, objects, preview_collection, pitch, palette, emissive, args):
    scene = bpy.context.scene
    if args.engine == "cycles":
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = args.samples
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 6
    else:
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = args.samples
    scene.render.resolution_x, scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world = bpy.data.worlds.new("Quiet sage studio")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.33, 0.38, 0.34, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    visible = [obj for obj in objects if not obj.hide_render]
    mins, maxs, corners = bounds_for_objects(visible)
    span = max(maxs[i] - mins[i] for i in range(3))
    center = Vector(tuple((mins[i] + maxs[i]) / 2 for i in range(3)))
    target = Vector((center.x, center.y, mins[2] + (maxs[2] - mins[2]) * 0.44))
    camera_data = bpy.data.cameras.new("Bedroom isometric camera")
    camera = bpy.data.objects.new("Bedroom isometric camera", camera_data)
    preview_collection.objects.link(camera)
    camera.location = target + Vector((1.0, -1.45, 1.13)).normalized() * span * 6
    aim(camera, target)
    camera_data.type = "ORTHO"
    camera_data.clip_start, camera_data.clip_end = 0.01, span * 100
    bpy.context.view_layer.update()
    projection = [camera.matrix_world.inverted() @ point for point in corners]
    projected_width = max(point.x for point in projection) - min(point.x for point in projection)
    projected_height = max(point.y for point in projection) - min(point.y for point in projection)
    # Fit against Blender's actual camera frame rather than assuming that
    # ortho_scale refers to its vertical dimension for a landscape sensor.
    camera_data.ortho_scale = 1.0
    frame = camera_data.view_frame(scene=scene)
    frame_width = max(point.x for point in frame) - min(point.x for point in frame)
    frame_height = max(point.y for point in frame) - min(point.y for point in frame)
    camera_data.ortho_scale = max(projected_width / frame_width, projected_height / frame_height) * 1.20
    projected_center = Vector(((max(point.x for point in projection) + min(point.x for point in projection)) / 2,
                               (max(point.y for point in projection) + min(point.y for point in projection)) / 2, 0))
    camera.location += camera.matrix_world.to_3x3() @ projected_center
    scene.camera = camera
    ground_mesh = bpy.data.meshes.new("Studio ground mesh")
    radius = span * 50
    ground_mesh.from_pydata([(-radius,-radius,mins[2]-.01),(radius,-radius,mins[2]-.01),
                             (radius,radius,mins[2]-.01),(-radius,radius,mins[2]-.01)], [], [(0,1,2,3)])
    ground = bpy.data.objects.new("Preview ground (excluded from export)", ground_mesh)
    preview_collection.objects.link(ground)
    ground_material = bpy.data.materials.new("Warm stone studio floor")
    ground_material.use_nodes = True
    ground_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.37,0.40,0.34,1)
    ground_material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
    ground_mesh.materials.append(ground_material)
    area_light(preview_collection, "Warm broad studio key", target + Vector((-span*.75,-span,span*1.5)),
               target, 100 * span * span, span, (1.0,.87,.71))
    area_light(preview_collection, "Soft cool fill", target + Vector((span,-span*.25,span*.7)),
               target, 40 * span * span, span*.8, (.77,.86,1.0))
    area_light(preview_collection, "Gentle top edge", target + Vector((0,span,span*1.5)),
               target, 55 * span * span, span*.8, (1.0,.95,.84))
    lamp_records = []
    for instance in scene_data["instances"]:
        if instance.get("hidden", False):
            continue
        asset, voxels = asset_models[instance["asset"]]
        cells = [(point, index) for point, index in voxels.items() if index in emissive]
        if not cells:
            continue
        indexes = {index for _, index in cells}
        label = (instance["name"] + " " + instance["asset"]).casefold()
        grow = "grow" in label
        # Each emissive fixture gets one small preview-only downward area source.
        # These are lighting effects, never geometry or runtime lamp controls.
        mean = [sum(point[i] + .5 for point, _ in cells) / len(cells) + instance["offset"][i] for i in range(3)]
        position = Vector(tuple(value * pitch for value in mean))
        position.z = max(position.z - pitch, mins[2] + pitch*2)
        color = (1.0,.18,.54) if grow else (1.0,.66,.32)
        power = 85 if grow else 35
        source = area_light(preview_collection, f"Preview {'pink grow' if grow else 'warm lamp'} light: {instance['name']}",
                            position, position + Vector((0,0,-1)), power, .45 if grow else .25, color)
        lamp_records.append({"fixture": instance["name"], "kind": "grow accent" if grow else "room lamp accent",
                             "position_meters": list(source.location), "watts_preview": power,
                             "aesthetic_only": True})
        if len(lamp_records) >= 12:
            break
    return camera, lamp_records


def main():
    if bpy is None:
        raise RuntimeError("Run scene export with Blender's Python, using --python-exit-code 1")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/bedroom"))
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--resolution", nargs=2, type=int, default=[1400,1100], metavar=("WIDTH","HEIGHT"))
    parser.add_argument("--engine", choices=("eevee","cycles"), default="eevee")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-render", action="store_true", help="Export and save the preview scene without rendering PNG")
    args = parser.parse_args(argv)
    if args.samples < 1 or any(not 64 <= size <= 8192 for size in args.resolution):
        raise ValueError("Positive samples and resolution dimensions in 64..8192 are required")
    source_bytes = args.scene.read_bytes()
    scene_data = json.loads(source_bytes)
    models, palette, pitch, emissive = validate_scene(scene_data)
    directory = args.output_dir.resolve()
    outputs = {"blend": directory/"bedroom.blend", "glb": directory/"bedroom.glb",
               "full_room_glb": directory/"bedroom_full_room.glb", "preview": directory/"bedroom_preview.png",
               "report": directory/"bedroom_mesh_report.json", "palette": directory/"bedroom_palette.png"}
    existing = [str(path) for path in outputs.values() if path.exists()]
    if existing and not args.force:
        raise ValueError("Refusing to overwrite outputs: " + ", ".join(existing))
    directory.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system, scene.unit_settings.scale_length = "METRIC", 1.0
    asset_collection = bpy.data.collections.new("Bedroom voxel assets")
    preview_collection = bpy.data.collections.new("Studio preview (excluded from GLB)")
    scene.collection.children.link(asset_collection)
    scene.collection.children.link(preview_collection)
    layer_collections = {}
    for layer in sorted({instance.get("layer", 0) for instance in scene_data["instances"]}):
        collection = bpy.data.collections.new(f"Voxel layer {layer}")
        asset_collection.children.link(collection)
        layer_collections[layer] = collection
    palette_image, palette_sha256 = write_palette_atlas(outputs["palette"], palette)
    materials = (make_material("Voxel exact palette colors", palette_image),
                 make_material("Voxel luminous palette colors", palette_image, True))
    asset_meshes, asset_records = {}, []
    for name, (asset, voxels) in models.items():
        mesh, pivot, record = mesh_for_asset(asset, voxels, palette, pitch, emissive, materials)
        asset_meshes[name] = mesh, pivot
        asset_records.append(record)
    objects, instances = [], []
    for instance in scene_data["instances"]:
        mesh, pivot = asset_meshes[instance["asset"]]
        obj = bpy.data.objects.new(instance["name"], mesh)
        layer_collections[instance.get("layer", 0)].objects.link(obj)
        obj.location = tuple((instance["offset"][i] + pivot[i]) * pitch for i in range(3))
        hidden = instance.get("hidden", False)
        obj.hide_render = hidden
        obj.hide_set(hidden)
        obj["voxel_asset"] = instance["asset"]
        obj["source_canvas_offset_voxels"] = instance["offset"]
        obj["voxel_pitch_meters"] = pitch
        obj["source_layer"] = instance.get("layer", 0)
        obj["cutaway_hidden"] = hidden
        objects.append(obj)
        instances.append({"name": obj.name, "asset": instance["asset"], "offset_voxels": instance["offset"],
                          "layer": instance.get("layer", 0), "hidden_in_cutaway": hidden,
                          "mesh_data": mesh.name})
    visible = [obj for obj in objects if not obj.hide_render]
    if not visible:
        raise ValueError("At least one visible asset instance is required")
    export_objects(outputs["glb"], visible)
    export_objects(outputs["full_room_glb"], objects)
    glb_verification = {
        "cutaway": verify_glb(outputs["glb"], visible, outputs["palette"]),
        "full_room": verify_glb(outputs["full_room_glb"], objects, outputs["palette"]),
    }
    camera, lamp_records = setup_preview(scene_data, models, objects, preview_collection, pitch, palette, emissive, args)
    scene.render.filepath = str(outputs["preview"])
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = visible[0]
    visible[0].select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(outputs["blend"]))
    if not args.no_render:
        bpy.ops.render.render(write_still=True)
    counts = Counter(instance["asset"] for instance in scene_data["instances"])
    visible_counts = Counter(instance["asset"] for instance in scene_data["instances"] if not instance.get("hidden",False))
    mins, maxs, _ = bounds_for_objects(visible)
    full_mins, full_maxs, _ = bounds_for_objects(objects)
    report = {
        "schema": "voxel-bedroom-mesh-v1", "scene_file": str(args.scene.resolve()),
        "scene_sha256": hashlib.sha256(source_bytes).hexdigest(), "voxel_pitch_meters": pitch,
        "source_axes": "Z up", "glb_axes": "Y up, converted by Blender exporter",
        "asset_count": len(asset_records), "instance_count": len(instances), "visible_instance_count": len(visible),
        "asset_mesh_data_shared_between_instances": True, "shared_surface_material_count": 2,
        "total_asset_voxels_unique_mesh_data": sum(record["filled_voxels"] for record in asset_records),
        "total_instanced_voxels": sum(record["filled_voxels"] * counts[record["name"]] for record in asset_records),
        "visible_instanced_voxels": sum(record["filled_voxels"] * visible_counts[record["name"]] for record in asset_records),
        "total_asset_exposed_unit_faces": sum(record["exposed_unit_faces"] for record in asset_records),
        "total_asset_greedy_quads": sum(record["greedy_quads"] for record in asset_records),
        "total_asset_triangles": sum(record["triangles"] for record in asset_records),
        "visible_instanced_triangles": sum(record["triangles"] * visible_counts[record["name"]] for record in asset_records),
        "full_instanced_triangles": sum(record["triangles"] * counts[record["name"]] for record in asset_records),
        "visible_bounds_meters": {"min": list(mins), "max_exclusive": list(maxs)},
        "full_bounds_meters": {"min": list(full_mins), "max_exclusive": list(full_maxs)},
        "assets": asset_records, "instances": instances, "preview_lamp_effects": lamp_records,
        "preview_engine": scene.render.engine, "blender_version": bpy.app.version_string,
        "preview_camera": {"location": list(camera.location), "orthographic_scale": camera.data.ortho_scale,
                           "resolution": args.resolution},
        "palette_texture": {"width": 16, "height": 16, "sha256": palette_sha256,
                            "source_encoding": "Exact 8-bit source RGBA; sRGB image colorspace",
                            "sampling": "Nearest; all corners of each face at one texel center",
                            "source_index_mapping": "palette index minus one, PNG top-left first",
                            "embedded_in_glb": True},
        "emission_note": "Shared palette image drives baseColorTexture and emissiveTexture; emission strength 2 is aesthetic and lamp accent lights are preview-only.",
        "verification": "Per asset, greedy quad area equals original exposed unit-cube face area; each quad normal is outward; no smoothing/bevel/resampling.",
        "preview_objects_excluded_from_exports": True,
        "glb_verification": glb_verification,
        "outputs": {name: str(path) for name,path in outputs.items()},
    }
    outputs["report"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("BEDROOM_MESH_REPORT " + json.dumps({key: report[key] for key in (
        "asset_count","instance_count","visible_instance_count","total_instanced_voxels",
        "total_asset_exposed_unit_faces","total_asset_greedy_quads","total_asset_triangles","outputs")}), flush=True)


if __name__ == "__main__":
    main()
