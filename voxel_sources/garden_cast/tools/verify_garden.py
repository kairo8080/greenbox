"""Independent stdlib verification of actual Greenbox Garden chibi VOX/GLB/PNG files.

--sources-only checks all seven authoritative sources without writing a report.
--asset NAME checks one complete asset without writing the final pack report.
With no arguments, complete actual files are checked and pack_validation.json
is written only after every required export and preview is present.
No authoring or renderer module is imported by this checker.
"""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT
NAMES = ('rasta_grower', 'corporate_boss', 'chef', 'blonde_lady',
         'robot', 'party_woman', 'skeleton')
PARTS = {'torso', 'head', 'arm_left', 'arm_right', 'leg_left', 'leg_right'}
EPSILON = 2e-5
CANONICAL_PALETTE_SHA256 = '09cb38d6cb39613d53228591ed2d7cdefc47a98cbdb81f78ab19b65dd3c36293'
ROOT_PIVOT = [11, 10, 0]
INSPIRATION_REFERENCE = 'Four user-supplied cubic voxel art references, 2026-10-04; art direction only, no imported screenshot content'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def near(a, b, tolerance=EPSILON):
    return len(a) == len(b) and all(abs(x-y) < tolerance for x, y in zip(a, b))


def components(cells):
    remaining = set(cells)
    sizes = []
    while remaining:
        queue = deque([remaining.pop()]); size = 0
        while queue:
            point = queue.popleft(); size += 1
            for axis in range(3):
                for direction in (-1, 1):
                    neighbor = list(point); neighbor[axis] += direction
                    neighbor = tuple(neighbor)
                    if neighbor in remaining:
                        remaining.remove(neighbor); queue.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def source_cells(model):
    cells = {}
    dimensions = model['dimensions']
    require(len(dimensions) == 3 and all(type(v) is int and 1 <= v <= 256 for v in dimensions),
            'Invalid dimensions')
    for cell in model['voxels']:
        require(len(cell) == 4 and all(type(v) is int for v in cell), 'Invalid occupied cell')
        point = tuple(cell[:3]); color = cell[3]
        require(1 <= color <= 255, 'Air or invalid palette index in occupied source')
        require(all(0 <= point[i] < dimensions[i] for i in range(3)), 'Source cell outside dimensions')
        require(point not in cells, 'Duplicate occupied source coordinate')
        cells[point] = color
    require(bool(cells), 'Empty source model')
    require([max(p[i] for p in cells)+1 for i in range(3)] == dimensions,
            'Source SIZE differs from tight occupied bounds')
    require(all(min(p[i] for p in cells) == 0 for i in range(3)), 'Source normalization differs')
    return cells


def read_vox(path):
    raw = path.read_bytes()
    require(len(raw) >= 20 and raw[:4] == b'VOX ', 'Invalid VOX header')
    version = struct.unpack_from('<I', raw, 4)[0]
    require(version == 150, 'Expected editable VOX v150')
    sizes = []; models = []; palette = []

    def chunks(start, end):
        offset = start
        while offset < end:
            require(offset+12 <= end, 'Truncated VOX chunk header')
            tag, n, children = struct.unpack_from('<4sII', raw, offset)
            content = offset+12; child = content+n; stop = child+children
            require(stop <= end, 'Truncated VOX chunk body')
            if tag == b'SIZE':
                require(n == 12, 'Invalid SIZE length')
                sizes.append(list(struct.unpack_from('<3I', raw, content)))
            elif tag == b'XYZI':
                require(n >= 4, 'Invalid XYZI length')
                count = struct.unpack_from('<I', raw, content)[0]
                require(n == 4+4*count, 'XYZI count and bytes disagree')
                cells = [list(raw[i:i+4]) for i in range(content+4, child, 4)]
                models.append(cells)
            elif tag == b'RGBA':
                require(n == 1024, 'Invalid RGBA length')
                entries = [list(raw[i:i+4]) for i in range(content, child, 4)]
                palette.append([entries[-1]] + entries[:255])
            else:
                require(tag == b'MAIN', f'Unsupported VOX scene chunk {tag!r}')
                require(n == 0, 'Invalid MAIN content')
            if children:
                chunks(child, stop)
            offset = stop
        require(offset == end, 'VOX trailing bytes')

    chunks(8, len(raw))
    require(len(sizes) == len(models) == len(palette) == 1, 'VOX must be one model with one palette')
    cells = source_cells({'dimensions': sizes[0], 'voxels': models[0]})
    return {'version': version, 'dimensions': sizes[0], 'cells': cells, 'palette': palette[0]}


def read_png(path, pixels=False):
    raw = path.read_bytes()
    require(raw[:8] == b'\x89PNG\r\n\x1a\n', 'Invalid PNG signature')
    offset = 8; compressed = bytearray(); info = None; ended = False
    while offset < len(raw):
        require(offset+12 <= len(raw), 'Truncated PNG chunk')
        n = struct.unpack_from('>I', raw, offset)[0]
        tag = raw[offset+4:offset+8]; data = raw[offset+8:offset+8+n]
        require(offset+12+n <= len(raw), 'PNG chunk length exceeds file')
        crc = struct.unpack_from('>I', raw, offset+8+n)[0]
        require(zlib.crc32(tag+data) & 0xffffffff == crc, 'PNG CRC mismatch')
        if tag == b'IHDR':
            require(info is None and n == 13, 'Invalid PNG IHDR')
            info = struct.unpack('>IIBBBBB', data)
        elif tag == b'IDAT':
            compressed.extend(data)
        elif tag == b'IEND':
            require(n == 0, 'Invalid PNG IEND'); ended = True
        offset += 12+n
    require(ended and info is not None and compressed, 'Incomplete PNG')
    width, height, depth, color_type, compression, filtering, interlace = info
    require(depth == 8 and color_type in (2, 6) and compression == filtering == interlace == 0,
            'Expected noninterlaced eight-bit RGB/RGBA PNG')
    channels = 3 if color_type == 2 else 4
    stride = width*channels
    filtered = zlib.decompress(compressed)
    require(len(filtered) == height*(stride+1), 'PNG decompressed data length differs')
    result = bytearray(); previous = bytearray(stride); unique = set()
    for y in range(height):
        start = y*(stride+1); kind = filtered[start]
        row = bytearray(filtered[start+1:start+1+stride])
        require(kind in range(5), 'Unsupported PNG row filter')
        for i in range(stride):
            left = row[i-channels] if i >= channels else 0
            up = previous[i]; up_left = previous[i-channels] if i >= channels else 0
            if kind == 1: row[i] = (row[i]+left) & 255
            elif kind == 2: row[i] = (row[i]+up) & 255
            elif kind == 3: row[i] = (row[i]+(left+up)//2) & 255
            elif kind == 4:
                p = left+up-up_left
                distances = (abs(p-left), abs(p-up), abs(p-up_left))
                predictor = (left, up, up_left)[distances.index(min(distances))]
                row[i] = (row[i]+predictor) & 255
        previous = row
        if pixels: result.extend(row)
        if len(unique) < 64:
            for i in range(0, stride, channels):
                unique.add(bytes(row[i:i+channels]))
                if len(unique) >= 64: break
    return {'width': width, 'height': height, 'channels': channels,
            'pixels': bytes(result), 'at_least_distinct_pixel_values': len(unique),
            'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def check_sources(name):
    folder = PACK/name
    asset = load_json(folder/(name+'.json'))
    manifest = load_json(folder/'source_manifest.json')
    require(asset['name'] == name, 'Asset name mismatch')
    require(asset.get('schema') == 'rigid-voxel-avatar-v1', 'Rigid voxel avatar source schema changed')
    require(asset['metadata'].get('style') == 'garden', 'Garden style metadata is missing')
    require(len(asset['palette']) == 256 and all(len(c) == 4 and all(type(v) is int and 0 <= v <= 255 for v in c)
                                              for c in asset['palette']), 'Invalid source palette')
    palette_hash = hashlib.sha256(bytes(v for c in asset['palette'] for v in c)).hexdigest()
    require(palette_hash == CANONICAL_PALETTE_SHA256, 'Full canonical 256-color palette changed')
    require(asset['palette'][0][3] == 0, 'Air palette index must be transparent')
    require(asset['metadata']['voxel_pitch_meters'] == .05, 'Collection voxel pitch changed')
    require(asset['metadata']['source_root_pivot'] == ROOT_PIVOT, 'Collection ground root changed')
    require(len(asset['parts']) == 6 and {p['name'] for p in asset['parts']} == PARTS, 'Six named parts required')
    whole = source_cells(asset)
    proportions = check_garden_proportions(asset)
    require(near(asset['metadata']['mesh_pivot_source_voxels'],
                 [ROOT_PIVOT[i]-asset['normalization_offset'][i] for i in range(3)]),
            'Assembled mesh pivot no longer represents the source ground root')
    assembled = {}; summaries = []; exposed_count = 0
    for model in [asset] + asset['parts']:
        vox_path = folder/(model['name']+'.vox')
        vox = read_vox(vox_path); expected = source_cells(model)
        require(vox['dimensions'] == model['dimensions'] and vox['cells'] == expected,
                f"{model['name']}: VOX occupied coordinates/color indices differ from JSON")
        require(vox['palette'] == asset['palette'], f"{model['name']}: VOX palette differs from JSON")
        require(components(expected) == [len(expected)], f"{model['name']}: disconnected cells")
        require(manifest['vox_sha256'].get(vox_path.name) == sha(vox_path), 'VOX manifest hash mismatch')
        if model is asset: continue
        offset = model['normalization_offset']
        require(model['metadata']['part'] == model['name'], 'Rigid part metadata name mismatch')
        require(near(model['metadata']['mesh_pivot_source_voxels'],
                     [model['metadata']['joint_source_voxels'][i]-offset[i] for i in range(3)]),
                'Rigid part pivot no longer represents its source joint')
        joint = model['metadata']['joint_source_voxels']
        expected_glb_joint = [(joint[0]-ROOT_PIVOT[0])*.05,
                              (joint[2]-ROOT_PIVOT[2])*.05, -(joint[1]-ROOT_PIVOT[1])*.05]
        require(near(model['metadata']['joint_glb_translation_meters'], expected_glb_joint, 1e-8),
                'Source joint metadata no longer matches the collection axes/pitch/root')
        for point, color in expected.items():
            raw = tuple(point[i]+offset[i] for i in range(3))
            require(raw not in assembled, 'Rigid parts overlap')
            assembled[raw] = color
        faces = expected_faces({tuple(p[i]+offset[i] for i in range(3)):c for p,c in expected.items()})
        exposed_count += len(faces)
        summaries.append({'name': model['name'], 'filled_voxels': len(expected),
                          'dimensions_voxels': model['dimensions'], 'connected_components': 1,
                          'exposed_unit_faces': len(faces)})
    raw_whole = {tuple(p[i]+asset['normalization_offset'][i] for i in range(3)):c for p,c in whole.items()}
    require(raw_whole == assembled, 'Six assembled parts differ from whole JSON occupancy')
    require(manifest['source_json_sha256'] == sha(folder/(name+'.json')), 'Source JSON manifest hash mismatch')
    require(manifest['asset'] == name and manifest['metadata'] == asset['metadata'],
            'Manifest asset name/style/root metadata differs from source')
    require(manifest['voxel_count'] == len(whole) and manifest['dimensions_voxels'] == asset['dimensions'],
            'Manifest occupied count/dimensions differ')
    require(len(manifest['vox_sha256']) == 7, 'Manifest must cover all seven VOX files')
    require({p['name'] for p in manifest['parts']} == PARTS, 'Manifest part names differ')
    for part in asset['parts']:
        record = next(p for p in manifest['parts'] if p['name'] == part['name'])
        require(all(record[k] == part[k] for k in ('dimensions', 'normalization_offset', 'metadata')),
                'Manifest part data differs')
    summary = {'asset': name, 'filled_voxels': len(whole), 'dimensions_voxels': asset['dimensions'],
               'colors_used': sorted(set(whole.values())), 'connected_components': 1,
               'part_overlap_cells': 0, 'parts': summaries,
               'source_json_sha256': sha(folder/(name+'.json')), 'vox_sha256': sha(folder/(name+'.vox')),
               'voxel_palette_matches_source_exactly': True, 'source_manifest_hashes_verified': True,
               'all_part_sources_match_json': True, 'rigid_part_surface_unit_faces': exposed_count}
    summary.update({'style':'garden','canonical_palette_sha256':palette_hash,
                    'canonical_256_rgba_slots_preserved':True,'garden_proportions':proportions})
    return asset, summary


def check_garden_proportions(asset):
    """Measure occupied cells, rather than trusting dimension/style declarations.

    A 4x4 neck occupies z9; the broad cubic head starts at z10. Accessories
    such as hair, ears and hats legitimately expand the head's occupied bounds.
    """
    parts = {part['name']:part for part in asset['parts']}
    def raw_cells(part):
        return {tuple(p[i]+part['normalization_offset'][i] for i in range(3)):c
                for p,c in source_cells(part).items()}
    head = raw_cells(parts['head']); torso = raw_cells(parts['torso'])
    head_width = max(p[0] for p in head)-min(p[0] for p in head)+1
    torso_width = max(p[0] for p in torso)-min(p[0] for p in torso)+1
    require(head_width >= 2.2*torso_width, 'Occupied head must be at least 2.2 times the torso width')
    require(min(p[2] for p in head) == 9, 'Head joint/neck must begin at source z9')
    require(parts['head']['metadata']['joint_source_voxels'] == [11,10,9], 'Garden head joint changed')
    layers = defaultdict(list)
    for p in head: layers[p[2]].append(p)
    neck = layers[9]
    require(len(neck) == 16 and max(p[0] for p in neck)-min(p[0] for p in neck)+1 == 4
            and max(p[1] for p in neck)-min(p[1] for p in neck)+1 == 4,
            'Head base must be a connected solid 4x4 neck at z9')
    main_head_starts = min(z for z,points in layers.items()
                           if max(p[0] for p in points)-min(p[0] for p in points)+1 > torso_width)
    require(main_head_starts == 10, 'Broad main head must begin at source z10')
    require(min(p[2] for p in torso) == 4 and max(p[2] for p in torso) == 8,
            'Tiny Garden torso must occupy source z4 through z8')
    whole = raw_cells(asset)
    require(min(p[2] for p in whole) == 0, 'Garden feet must sit on the source ground plane')
    total_height = max(p[2] for p in whole)+1
    height_meters = total_height*asset['metadata']['voxel_pitch_meters']
    require(1.35-1e-8 <= height_meters <= 1.65+1e-8, 'Garden height leaves the expected 1.35 to 1.65m collection range')
    return {'occupied_head_width_voxels':head_width,'occupied_torso_width_voxels':torso_width,
            'head_to_torso_width_ratio':head_width/torso_width,'minimum_head_to_torso_width_ratio':2.2,
            'head_minimum_source_z':9,'neck_layer_dimensions_voxels':[4,4,1],
            'main_head_starts_source_z':main_head_starts,'torso_source_z_range_inclusive':[4,8],
            'total_height_voxels':total_height,'height_meters':height_meters,
            'occupied_proportions_verified':True}


def expected_faces(cells):
    result = {}
    for point, color in cells.items():
        for axis in range(3):
            other = [i for i in range(3) if i != axis]
            for sign in (-1, 1):
                neighbor = list(point); neighbor[axis] += sign
                if tuple(neighbor) in cells: continue
                key = (axis, sign, point[axis]+int(sign > 0), point[other[0]], point[other[1]], color)
                result[key] = 1.0
    return result


def read_glb(path):
    raw = path.read_bytes()
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Invalid GLB header')
    offset = 12; document = None; binary = None
    while offset < len(raw):
        require(offset+8 <= len(raw), 'Truncated GLB chunk header')
        n, kind = struct.unpack_from('<II', raw, offset)
        require(n % 4 == 0 and offset+8+n <= len(raw), 'Invalid GLB chunk length')
        data = raw[offset+8:offset+8+n]
        if kind == 0x4e4f534a:
            require(document is None, 'Repeated GLB JSON'); document = json.loads(data)
        elif kind == 0x004e4942:
            require(binary is None, 'Repeated GLB BIN'); binary = data
        else: raise ValueError('Unknown GLB chunk')
        offset += n+8
    require(document is not None and binary is not None, 'Missing GLB JSON/BIN')
    require(len(document['buffers']) == 1 and 'uri' not in document['buffers'][0], 'External GLB buffer')
    require(0 <= len(binary)-document['buffers'][0]['byteLength'] <= 3, 'GLB buffer size mismatch')
    return document, binary


def accessor(document, binary, index):
    a = document['accessors'][index]
    require('sparse' not in a and not a.get('normalized'), 'Unexpected compressed/normalized accessor')
    components_count = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4}[a['type']]
    format_code = {5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}[a['componentType']]
    layout = struct.Struct('<'+format_code*components_count)
    view = document['bufferViews'][a['bufferView']]
    require(view['buffer'] == 0, 'Nonembedded bufferView')
    start = view.get('byteOffset', 0)+a.get('byteOffset', 0)
    stride = view.get('byteStride', layout.size)
    require(stride >= layout.size and a.get('byteOffset', 0)+(a['count']-1)*stride+layout.size <= view['byteLength'],
            'Accessor exceeds bufferView')
    return [layout.unpack_from(binary, start+i*stride) for i in range(a['count'])]


def clip_polygon(polygon, axis, threshold, keep_greater):
    if not polygon: return []
    output = []
    for start, end in zip(polygon, polygon[1:]+polygon[:1]):
        start_in = start[axis] >= threshold if keep_greater else start[axis] <= threshold
        end_in = end[axis] >= threshold if keep_greater else end[axis] <= threshold
        if start_in: output.append(start)
        if start_in != end_in:
            t = (threshold-start[axis])/(end[axis]-start[axis])
            output.append(tuple(start[i]+t*(end[i]-start[i]) for i in range(2)))
    return output


def area_in_cell(triangle, u, v):
    polygon = list(triangle)
    for axis, threshold, greater in ((0,u,True),(0,u+1,False),(1,v,True),(1,v+1,False)):
        polygon = clip_polygon(polygon, axis, threshold, greater)
    if len(polygon) < 3: return 0
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(polygon,polygon[1:]+polygon[:1])))*.5


def check_mesh(document, binary, node, part, pitch, root_pivot):
    translation = node.get('translation', [0,0,0])
    joint = part['metadata']['joint_source_voxels']
    expected_joint = [(joint[0]-root_pivot[0])*pitch,
                      (joint[2]-root_pivot[2])*pitch, -(joint[1]-root_pivot[1])*pitch]
    require(near(translation, expected_joint, 1e-6), 'Actual GLB joint translation differs')
    require(near(part['metadata']['joint_glb_translation_meters'], expected_joint), 'Source joint axes differ')
    source = source_cells(part); offset = part['normalization_offset']
    raw_source = {tuple(p[i]+offset[i] for i in range(3)):c for p,c in source.items()}
    expected = expected_faces(raw_source); coverage = defaultdict(float)
    triangle_count = 0; vertex_count = 0; global_positions = []
    for primitive in document['meshes'][node['mesh']]['primitives']:
        require(primitive.get('mode',4) == 4 and primitive.get('material') == 0, 'Primitive mode/material differs')
        attributes = primitive['attributes']
        require('NORMAL' in attributes and 'TEXCOORD_0' in attributes and 'COLOR_0' not in attributes,
                'Missing flat normals/palette UV or unexpected color multiplier')
        positions = accessor(document,binary,attributes['POSITION'])
        normals = accessor(document,binary,attributes['NORMAL'])
        uv = accessor(document,binary,attributes['TEXCOORD_0'])
        require(len(positions) == len(normals) == len(uv), 'GLB vertex attributes differ in count')
        indices = [p[0] for p in accessor(document,binary,primitive['indices'])]
        require(len(indices) % 3 == 0 and all(0 <= i < len(positions) for i in indices), 'Invalid triangle indices')
        native = []
        for p in positions:
            global_p = tuple(p[i]+translation[i] for i in range(3))
            global_positions.append(global_p)
            raw = (global_p[0]/pitch+root_pivot[0], -global_p[2]/pitch+root_pivot[1],
                   global_p[1]/pitch+root_pivot[2])
            require(all(math.isfinite(v) and abs(v-round(v)) < EPSILON for v in raw),
                    'GLB vertex leaves .05m source cube boundaries after joint transform')
            native.append(tuple(round(v) for v in raw))
        for normal in normals:
            require(sum(abs(v) > 1e-6 for v in normal) == 1 and abs(sum(v*v for v in normal)-1) < 1e-6,
                    'A GLB normal is smoothed or not axis-aligned')
        for start in range(0, len(indices), 3):
            triangle_count += 1
            ids = indices[start:start+3]; points = [native[i] for i in ids]
            n = normals[ids[0]]
            require(all(near(normals[i], n, 1e-6) for i in ids), 'Triangle has interpolated corner normals')
            native_n = (n[0], -n[2], n[1]); axis = max(range(3),key=lambda i:abs(native_n[i]))
            sign = 1 if native_n[axis] > 0 else -1
            plane = points[0][axis]
            require(all(p[axis] == plane for p in points), 'Triangle is not a square-face plane')
            edges = [[points[k][i]-points[0][i] for i in range(3)] for k in (1,2)]
            cross = (edges[0][1]*edges[1][2]-edges[0][2]*edges[1][1],
                     edges[0][2]*edges[1][0]-edges[0][0]*edges[1][2],
                     edges[0][0]*edges[1][1]-edges[0][1]*edges[1][0])
            require(cross[axis]*sign > 0 and all(cross[i] == 0 for i in range(3) if i != axis),
                    'GLB triangle is degenerate or has inward winding')
            tex = uv[ids[0]]
            require(all(near(uv[i],tex,1e-7) for i in ids), 'Palette UV has a gradient across a face')
            tx, ty = math.floor(tex[0]*16), math.floor(tex[1]*16)
            require(0 <= tx < 16 and 0 <= ty < 16 and near(tex,((tx+.5)/16,(ty+.5)/16),1e-7),
                    'UV does not sample an exact palette texel center')
            color = tx+16*ty+1
            require(color <= 255, 'Occupied triangle samples the air texel')
            other = [i for i in range(3) if i != axis]
            points_2d = [(p[other[0]],p[other[1]]) for p in points]
            for u in range(min(p[0] for p in points_2d), max(p[0] for p in points_2d)):
                for v in range(min(p[1] for p in points_2d), max(p[1] for p in points_2d)):
                    area = area_in_cell(points_2d,u,v)
                    if area < 1e-10: continue
                    key = (axis,sign,plane,u,v,color)
                    require(key in expected, 'GLB triangle covers air, a hidden face, or the wrong source color')
                    coverage[key] += area
        vertex_count += len(positions)
    require(coverage.keys() == expected.keys() and all(abs(a-1) < 1e-6 for a in coverage.values()),
            'Actual GLB surface does not cover every exposed cube face exactly once')
    return {'name': part['name'], 'triangles': triangle_count, 'exported_vertices': vertex_count,
            'exposed_unit_faces_verified': len(expected), 'surface_and_palette_coverage_exact': True}, global_positions


def check_export(asset, summary):
    name = asset['name']; folder = PACK/name
    document, binary = read_glb(folder/(name+'.glb'))
    nodes = document['nodes']
    require(len(nodes) == 7 and len(document['meshes']) == 6, 'Expected seven GLB nodes and six meshes')
    require({n['name'] for n in nodes} == PARTS | {'CharacterRoot'}, 'Preview or unnamed nodes leaked into GLB')
    root_index = next(i for i,n in enumerate(nodes) if n['name'] == 'CharacterRoot')
    root = nodes[root_index]
    require(set(root.get('children',[])) == set(range(7))-{root_index}, 'Rigid mesh hierarchy differs')
    require('mesh' not in root and document['scenes'][document.get('scene',0)]['nodes'] == [root_index],
            'GLB scene root differs')
    for node in nodes:
        require('matrix' not in node and near(node.get('rotation',[0,0,0,1]),[0,0,0,1]), 'Preview rotation leaked into GLB')
        require(near(node.get('scale',[1,1,1]),[1,1,1]), 'Exported node scale changed')
        require(node is root or not node.get('children'), 'Rigid parts have unexpected descendants')
    require(near(root.get('translation',[0,0,0]),[0,0,0]), 'Character root translation changed')
    require({n['mesh'] for n in nodes if 'mesh' in n} == set(range(6)), 'GLB meshes missing or reused')
    require(not document.get('cameras') and not document.get('skins') and not document.get('animations')
            and not document.get('extensions',{}).get('KHR_lights_punctual'), 'Preview, skin, or pose leaked into neutral GLB')
    require(len(document['materials']) == len(document['images']) == len(document['textures']) == 1,
            'Expected one exact embedded palette material/texture/image')
    material = document['materials'][0]['pbrMetallicRoughness']
    require(material['baseColorTexture']['index'] == 0 and near(material.get('baseColorFactor',[1,1,1,1]),[1,1,1,1]),
            'Palette material color is multiplied or changed')
    image = document['images'][0]
    require('uri' not in image and image['mimeType'] == 'image/png', 'Palette image is not embedded PNG')
    view = document['bufferViews'][image['bufferView']]
    start = view.get('byteOffset',0); embedded = binary[start:start+view['byteLength']]
    palette_path = folder/'palette.png'
    require(embedded == palette_path.read_bytes(), 'Embedded GLB palette bytes differ from source atlas')
    palette = read_png(palette_path,pixels=True)
    require((palette['width'],palette['height'],palette['channels']) == (16,16,4), 'Palette image layout differs')
    expected_rgba = b''.join(bytes(c) for c in asset['palette'][1:]+asset['palette'][:1])
    require(palette['pixels'] == expected_rgba, 'Actual atlas colors differ from source RGBA bytes')
    sampler = document['samplers'][document['textures'][0]['sampler']]
    require(sampler.get('magFilter') == 9728 and sampler.get('minFilter') in (9728,9984), 'Palette is not sampled with nearest filtering')
    pitch = asset['metadata']['voxel_pitch_meters']; pivot = asset['metadata']['source_root_pivot']
    mesh_records = []; positions = []
    for part in asset['parts']:
        node = next(n for n in nodes if n['name'] == part['name'])
        mesh, points = check_mesh(document,binary,node,part,pitch,pivot)
        mesh_records.append(mesh); positions.extend(points)
    actual_bounds = [[min(p[i] for p in positions) for i in range(3)],
                     [max(p[i] for p in positions) for i in range(3)]]
    cells = source_cells(asset); offset = asset['normalization_offset']
    mins = [min(p[i] for p in cells)+offset[i] for i in range(3)]
    maxs = [max(p[i] for p in cells)+offset[i]+1 for i in range(3)]
    expected_bounds = [[(mins[0]-pivot[0])*pitch,(mins[2]-pivot[2])*pitch,-(maxs[1]-pivot[1])*pitch],
                       [(maxs[0]-pivot[0])*pitch,(maxs[2]-pivot[2])*pitch,-(mins[1]-pivot[1])*pitch]]
    require(all(near(a,b,1e-6) for a,b in zip(actual_bounds,expected_bounds)), 'GLB global bounds differ from source occupancy')
    rendered_report = load_json(folder/'mesh_validation.json')
    triangles = sum(m['triangles'] for m in mesh_records)
    require(rendered_report['source_json_sha256'] == summary['source_json_sha256'], 'Renderer report is stale for source')
    require(rendered_report['glb']['sha256'] == sha(folder/(name+'.glb')) and rendered_report['glb']['triangles'] == triangles,
            'Renderer report is stale for actual GLB/count')
    require(all(next(r['triangles'] for r in rendered_report['parts'] if r['name'] == m['name']) == m['triangles']
                for m in mesh_records), 'Actual GLB part triangle counts differ from renderer report')
    preview = read_png(folder/(name+'_preview.png'))
    require((preview['width'],preview['height']) == (800,1000), 'Preview PNG dimensions differ')
    require(preview['at_least_distinct_pixel_values'] >= 64, 'Preview image appears blank')
    blend_path = folder/(name+'.blend'); blend_raw = blend_path.read_bytes()
    # Blender can preserve its save-compression preference across factory resets.
    # Recognize the actual uncompressed, gzip, and modern Zstandard containers.
    blend_format = ('uncompressed-blend' if blend_raw.startswith(b'BLENDER') else
                    'zstandard-compressed-blend' if blend_raw.startswith(b'\x28\xb5\x2f\xfd') else
                    'gzip-compressed-blend' if blend_raw.startswith(b'\x1f\x8b') else None)
    require(len(blend_raw) > 1000 and blend_format is not None, 'Missing or unsupported saved Blender container')
    summary['glb'] = {'bytes': (folder/(name+'.glb')).stat().st_size, 'sha256':sha(folder/(name+'.glb')),
                      'nodes':7,'meshes':6,'materials':1,'triangles':triangles,'parts':mesh_records,
                      'bounds_meters_y_up':expected_bounds,'actual_bounds_match_source':True,
                      'all_vertices_on_transformed_voxel_boundaries':True,
                      'flat_axis_aligned_outward_normals':True,'palette_preserved_exactly':True,
                      'surface_coverage_matches_all_exposed_part_faces':True,
                      'neutral_rigid_hierarchy_and_joints':True,'preview_objects_excluded':True}
    summary['preview'] = {k:preview[k] for k in ('width','height','bytes','sha256','at_least_distinct_pixel_values')}
    summary['blend'] = {'bytes':len(blend_raw),'sha256':sha(blend_path),
                        'container_format':blend_format,'supported_container_header':True,
                        'verification_scope':'Nonempty file and supported Blender container magic; internal saved-scene blocks not decoded.'}
    summary['status'] = 'pass'
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-only',action='store_true')
    parser.add_argument('--asset',choices=NAMES)
    args = parser.parse_args()
    names = (args.asset,) if args.asset else NAMES
    if not args.sources_only:
        missing = [str(PACK/n/(n+suffix)) for n in names
                   for suffix in ('.glb','.blend','_preview.png') if not (PACK/n/(n+suffix)).is_file()]
        missing += [str(PACK/n/'mesh_validation.json') for n in names if not (PACK/n/'mesh_validation.json').is_file()]
        require(not missing, 'Wait for complete exports before final validation: '+', '.join(missing))
    summaries = []; palettes = []
    for name in names:
        try:
            asset, summary = check_sources(name); palettes.append(asset['palette'])
            if not args.sources_only: summary = check_export(asset,summary)
            summaries.append(summary)
            print(json.dumps({'asset':name,'status':'sources-pass' if args.sources_only else 'pass',
                              'voxels':summary['filled_voxels'],'dimensions':summary['dimensions_voxels'],
                              'triangles':summary.get('glb',{}).get('triangles')}),flush=True)
        except Exception as error:
            print(json.dumps({'asset':name,'status':'fail','error':str(error)}),flush=True)
            raise
    require(all(p == palettes[0] for p in palettes), 'Shared canonical collection palette colors changed')
    if not args.sources_only and not args.asset:
        report = {'schema':'independent-greenbox-garden-pack-validation-v1','status':'pass',
                  'verification':'Independent stdlib parsing of actual VOX, GLB BIN accessors and PNG pixels; '
                                 'all triangulated faces clipped against unit source cells and exact palette indices.',
                  'assets_verified':len(summaries),'total_filled_voxels':sum(s['filled_voxels'] for s in summaries),
                  'total_triangles':sum(s['glb']['triangles'] for s in summaries),
                  'style':'garden','canonical_256_rgba_slots_preserved':True,
                  'canonical_palette_sha256':CANONICAL_PALETTE_SHA256,
                  'visual_inspiration_reference':INSPIRATION_REFERENCE,
                  'provenance':'Original occupied-cube character artwork; the reference informs art direction only, '
                               'with no downloaded or copied game assets, characters, or textures.',
                  'voxel_pitch_meters':.05,'source_axes':'X/Y horizontal,Z up; front -Y',
                  'glb_axes':'Y up; front +Z','source_root_pivot':ROOT_PIVOT,
                  'assets':summaries}
        report_path = PACK/'pack_validation.json'
        report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('PACK_VALIDATION '+json.dumps({k:report[k] for k in ('status','assets_verified','total_filled_voxels','total_triangles')}),flush=True)


if __name__ == '__main__':
    main()
