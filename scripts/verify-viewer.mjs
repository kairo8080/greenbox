import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Script } from 'node:vm';
import { inflateSync } from 'node:zlib';

// Usage: node scripts/verify-viewer.mjs [standalone-html]
// Parses the delivered bytes; never executes the viewer or imports its implementation.
const repository = dirname(dirname(fileURLToPath(import.meta.url)));
const filename = process.argv[2] ? resolve(process.argv[2]) : join(repository, 'public', 'viewer', 'index.html');
const failures = [];
const characterIds = ['rasta_grower', 'corporate_boss', 'robot', 'chef', 'blonde_lady', 'party_woman', 'skeleton'];
const chibiIds = characterIds.map(id => `${id}_chibi`);
// Chibi totals independently measured from real GLB accessors and source VOX.
// See outputs/greenbox-chibi-pack/pack_validation.json and work/chibi/verify_chibi.py.
const expectedStyleTotals = { original: { triangles: 5954, voxels: 16055 }, chibi: { triangles: 4030, voxels: 28071 } };
const styleTotals = { original: { triangles: 0, voxels: 0, models: 0 }, chibi: { triangles: 0, voxels: 0, models: 0 } };
const requiredIds = ['viewer-canvas', 'canvas-wrap', 'loading-status', 'error-banner', 'selected-label', 'stats',
  'scene-labels', 'asset-select', 'character-style', 'view-mode', 'character-select', 'framing', 'sync-cameras', 'motion-toggle',
  'reset-view', 'camera-front', 'camera-right', 'camera-left', 'camera-back', 'palette-select', 'protect-identity',
  'palette-swatches', 'palette-status', 'export-palette', 'export-vox', 'export-glb'];
const roleNames = ('air ink slate wall wall_shadow trim floor floor_dark floor_light wood wood_light linen teal '
  + 'teal_light pink pink_light warm_light leaf_dark leaf leaf_light leaf_tip soil clay clay_light blue water white '
  + 'yellow navy purple stem metal screen violet rasta_red rasta_gold rasta_green skin locs skin_light skin_pale '
  + 'skin_tan hair_blonde hair_blonde_shadow hair_brown suit suit_light tie_red steel steel_dark chrome cyan '
  + 'chef_white bone bone_shadow dress_pink dress_violet heel_dark hair_auburn lapel eye_blue lip gold blush').split(' ');
// SHA-256 of the independently read robot.json source's 256 RGBA slots, in VOX index order.
const canonicalPaletteHash = '09cb38d6cb39613d53228591ed2d7cdefc47a98cbdb81f78ab19b65dd3c36293';
const pngSignature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
let htmlBytes = 0, triangleTotal = 0, voxelTotal = 0, verifiedModels = 0;

function check(condition, message) { if (!condition) failures.push(message); }
function requireValue(condition, message) { if (!condition) throw new Error(message); }
function integer(value, minimum = 0) { return Number.isSafeInteger(value) && value >= minimum; }
function attributes(tag) {
  const result = new Map();
  for (const match of tag.matchAll(/([^\s=<>/'"]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g))
    result.set(match[1].toLowerCase(), match[2] ?? match[3] ?? match[4]);
  return result;
}
function base64(value, label) {
  requireValue(typeof value === 'string' && value.length > 0
    && /^(?:[A-Za-z\d+/]{4})*(?:[A-Za-z\d+/]{2}==|[A-Za-z\d+/]{3}=)?$/.test(value), `${label}: invalid base64.`);
  const bytes = Buffer.from(value, 'base64');
  requireValue(bytes.length > 0 && bytes.toString('base64') === value, `${label}: noncanonical base64.`);
  return bytes;
}
function embeddedUri(value, label) {
  const match = typeof value === 'string' && value.match(/^data:[^;,]+;base64,([A-Za-z\d+/=]+)$/);
  requireValue(match, `${label}: external URI is forbidden.`);
  return base64(match[1], label);
}
function sameColor(a, b) { return a.length === b.length && a.every((value, index) => value === b[index]); }
function inertHttpReference(source, index, url) {
  if (url === 'http://www.w3.org/1999/xhtml' || url === 'http://www.w3.org/2000/svg') return true;
  const before = source.slice(0, index);
  if (before.lastIndexOf('<!--') > before.lastIndexOf('-->') || before.lastIndexOf('/*') > before.lastIndexOf('*/')) return true;
  // Bundled GLSL strings retain escaped newlines and scholarly comments.
  const lineStart = Math.max(before.lastIndexOf('\n'), before.lastIndexOf('\\n'));
  return /(?:^|\s)\/\//.test(before.slice(lineStart + 1).replace(/\\t/g, ' '));
}
function validColors(colors) {
  return Array.isArray(colors) && colors.length === 256 && colors.every(color => Array.isArray(color)
    && color.length === 4 && color.every(value => Number.isInteger(value) && value >= 0 && value <= 255));
}

function validateCatalog(catalog) {
  requireValue(catalog?.schema === 'greenbox-palettes-v1', 'Unrecognized palette catalog schema.');
  requireValue(validColors(catalog.original), 'Canonical palette must contain exactly 256 RGBA byte colors.');
  check(catalog.slotCount === 256 && catalog.usedSlotCount === 64, 'Palette slot totals must be 256/64.');
  check(createHash('sha256').update(Buffer.from(catalog.original.flat())).digest('hex') === canonicalPaletteHash,
    'Canonical palette differs from the independently verified character source.');
  check(catalog.original[0][3] === 0, 'Air palette slot 0 must be transparent.');
  const roles = catalog.roles;
  check(roles && typeof roles === 'object' && Object.keys(roles).length === roleNames.length,
    'Palette must contain the complete 64-role mapping.');
  for (const [index, name] of roleNames.entries()) check(roles?.[name] === index, `Palette role ${name} must map to index ${index}.`);
  check(catalog.texture?.width === 16 && catalog.texture?.height === 16 && catalog.texture?.sampling === 'nearest',
    'Palette texture contract must use a 16x16 nearest-sampled atlas.');
  requireValue(Array.isArray(catalog.identityRoles) && Array.isArray(catalog.identityIndices), 'Identity protection mapping is missing.');
  const identity = catalog.identityRoles.map(role => roles?.[role]);
  check(identity.every(index => integer(index, 1) && index <= 255)
    && new Set(identity).size === identity.length
    && JSON.stringify([...identity].sort((a, b) => a - b)) === JSON.stringify([...catalog.identityIndices].sort((a, b) => a - b)),
    'Identity role names and protected indices must agree without duplicates.');
  for (const name of ['original', 'island', 'pastel', 'neon', 'mono']) {
    const preset = catalog.presets?.[name];
    requireValue(validColors(preset?.colors), `Palette preset ${name} needs 256 RGBA colors.`);
    check(typeof preset.label === 'string' && preset.label.length > 0, `Palette preset ${name} needs a label.`);
    check(preset.colors[0][3] === 0, `Palette preset ${name} must preserve transparent air.`);
  }
  check(JSON.stringify(catalog.presets.original.colors) === JSON.stringify(catalog.original), 'Original preset must match the canonical palette.');
}

const crcTable = Uint32Array.from({ length: 256 }, (_, value) => {
  for (let bit = 0; bit < 8; bit++) value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
  return value >>> 0;
});
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const value of bytes) crc = crcTable[(crc ^ value) & 255] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}
function palettePng(bytes, label) {
  requireValue(bytes.subarray(0, 8).equals(pngSignature), `${label}: image has no PNG signature.`);
  const compressed = [];
  let position = 8, header = false, ended = false;
  while (position < bytes.length) {
    requireValue(position + 12 <= bytes.length, `${label}: truncated PNG chunk.`);
    const length = bytes.readUInt32BE(position), end = position + 12 + length;
    requireValue(end <= bytes.length, `${label}: PNG chunk exceeds the image.`);
    const tag = bytes.toString('ascii', position + 4, position + 8), data = bytes.subarray(position + 8, end - 4);
    requireValue(crc32(bytes.subarray(position + 4, end - 4)) === bytes.readUInt32BE(end - 4), `${label}: PNG CRC mismatch.`);
    if (tag === 'IHDR') {
      requireValue(!header && position === 8 && length === 13, `${label}: invalid PNG header.`);
      requireValue(data.readUInt32BE(0) === 16 && data.readUInt32BE(4) === 16
        && data[8] === 8 && data[9] === 6 && data[10] === 0 && data[11] === 0 && data[12] === 0,
      `${label}: expected a noninterlaced 16x16 RGBA8 palette image.`);
      header = true;
    } else if (tag === 'IDAT') compressed.push(data);
    else if (tag === 'IEND') { requireValue(length === 0 && end === bytes.length, `${label}: invalid PNG end.`); ended = true; }
    position = end;
  }
  requireValue(header && ended && compressed.length > 0, `${label}: incomplete PNG.`);
  const packed = inflateSync(Buffer.concat(compressed), { maxOutputLength: 1040 });
  requireValue(packed.length === 1040, `${label}: invalid PNG scanline length.`);
  const rgba = Buffer.alloc(1024);
  for (let row = 0; row < 16; row++) {
    const filter = packed[row * 65];
    requireValue(filter <= 4, `${label}: unsupported PNG filter.`);
    for (let column = 0; column < 64; column++) {
      const index = row * 64 + column;
      const left = column >= 4 ? rgba[index - 4] : 0, up = row > 0 ? rgba[index - 64] : 0;
      const upperLeft = row > 0 && column >= 4 ? rgba[index - 68] : 0;
      let predictor = 0;
      if (filter === 1) predictor = left;
      else if (filter === 2) predictor = up;
      else if (filter === 3) predictor = Math.floor((left + up) / 2);
      else if (filter === 4) {
        const p = left + up - upperLeft, dl = Math.abs(p - left), du = Math.abs(p - up), dul = Math.abs(p - upperLeft);
        predictor = dl <= du && dl <= dul ? left : du <= dul ? up : upperLeft;
      }
      rgba[index] = (packed[row * 65 + column + 1] + predictor) & 255;
    }
  }
  return rgba;
}

function validateGlb(bytes, model, palette) {
  const label = model.id;
  if (model.glbSha256 !== undefined) check(/^[\da-f]{64}$/i.test(model.glbSha256)
    && createHash('sha256').update(bytes).digest('hex') === model.glbSha256.toLowerCase(), `${label}: GLB SHA-256 differs from its declared hash.`);
  requireValue(bytes.length >= 28 && bytes.toString('ascii', 0, 4) === 'glTF'
    && bytes.readUInt32LE(4) === 2 && bytes.readUInt32LE(8) === bytes.length, `${label}: invalid GLB v2 header/length.`);
  let position = 12, json, binary;
  while (position < bytes.length) {
    requireValue(position + 8 <= bytes.length, `${label}: truncated GLB chunk.`);
    const length = bytes.readUInt32LE(position), type = bytes.readUInt32LE(position + 4);
    requireValue(length % 4 === 0 && position + 8 + length <= bytes.length, `${label}: invalid GLB chunk alignment/length.`);
    const content = bytes.subarray(position + 8, position + 8 + length);
    if (type === 0x4e4f534a) {
      requireValue(!json && position === 12, `${label}: JSON must be the first and only JSON chunk.`);
      json = JSON.parse(content.toString('utf8'));
    } else if (type === 0x004e4942) { requireValue(!binary, `${label}: duplicate BIN chunk.`); binary = content; }
    position += 8 + length;
  }
  requireValue(json?.asset?.version === '2.0' && binary, `${label}: GLB requires glTF2 JSON and a BIN chunk.`);
  const buffers = (json.buffers ?? []).map((buffer, index) => {
    requireValue(integer(buffer.byteLength, 1), `${label}: invalid buffer length.`);
    const data = buffer.uri === undefined ? (index === 0 ? binary : null) : embeddedUri(buffer.uri, `${label} buffer ${index}`);
    requireValue(data && data.length >= buffer.byteLength && data.length <= buffer.byteLength + 3, `${label}: buffer length mismatch.`);
    return data.subarray(0, buffer.byteLength);
  });
  requireValue(buffers.length > 0, `${label}: no embedded geometry buffer.`);
  function view(index) {
    const value = json.bufferViews?.[index];
    requireValue(integer(index) && value && integer(value.buffer) && buffers[value.buffer]
      && integer(value.byteOffset ?? 0) && integer(value.byteLength, 1), `${label}: invalid bufferView ${index}.`);
    const offset = value.byteOffset ?? 0;
    requireValue(offset + value.byteLength <= buffers[value.buffer].length, `${label}: bufferView ${index} exceeds its buffer.`);
    return { bytes: buffers[value.buffer].subarray(offset, offset + value.byteLength), stride: value.byteStride };
  }
  for (let index = 0; index < (json.bufferViews ?? []).length; index++) view(index);
  function accessor(index, type, components, allowedTypes) {
    const value = json.accessors?.[index];
    requireValue(integer(index) && value?.type === type && integer(value.count, 1) && allowedTypes.includes(value.componentType)
      && !value.sparse && integer(value.byteOffset ?? 0), `${label}: invalid ${type} accessor ${index}.`);
    const componentSize = { 5121: 1, 5123: 2, 5125: 4, 5126: 4 }[value.componentType];
    const data = view(value.bufferView), elementSize = components * componentSize, stride = data.stride ?? elementSize;
    requireValue(integer(stride, elementSize) && (value.byteOffset ?? 0) + (value.count - 1) * stride + elementSize <= data.bytes.length,
      `${label}: accessor ${index} exceeds its bufferView.`);
    return { ...value, bytes: data.bytes, offset: value.byteOffset ?? 0, stride };
  }
  const images = (json.images ?? []).map((image, index) => {
    requireValue(image.mimeType === 'image/png' || image.uri?.startsWith('data:image/png;'), `${label}: image ${index} must be an embedded PNG.`);
    const pixels = palettePng(image.uri === undefined ? view(image.bufferView).bytes : embeddedUri(image.uri, `${label} image ${index}`), `${label} image ${index}`);
    if (model.style === 'chibi') for (let texel = 0; texel < 256; texel++)
      requireValue(sameColor([...pixels.subarray(texel * 4, texel * 4 + 4)], palette[(texel + 1) % 256]),
        `${label}: chibi embedded atlas differs from canonical palette slot ${(texel + 1) % 256}.`);
    return pixels;
  });
  requireValue(images.length > 0, `${label}: no embedded palette image.`);
  const meshTriangles = (json.meshes ?? []).map((mesh, meshIndex) => {
    requireValue(Array.isArray(mesh.primitives) && mesh.primitives.length > 0, `${label}: empty mesh ${meshIndex}.`);
    let total = 0;
    for (const primitive of mesh.primitives) {
      requireValue((primitive.mode ?? 4) === 4, `${label}: voxel mesh must use triangle primitives.`);
      const vertices = accessor(primitive.attributes?.POSITION, 'VEC3', 3, [5126]);
      let count = vertices.count;
      if (primitive.indices !== undefined) {
        const indices = accessor(primitive.indices, 'SCALAR', 1, [5121, 5123, 5125]);
        count = indices.count;
        for (let index = 0; index < count; index++) {
          const offset = indices.offset + index * indices.stride;
          const vertex = indices.componentType === 5121 ? indices.bytes[offset]
            : indices.componentType === 5123 ? indices.bytes.readUInt16LE(offset) : indices.bytes.readUInt32LE(offset);
          requireValue(vertex < vertices.count, `${label}: mesh index exceeds the POSITION accessor.`);
        }
      }
      requireValue(count % 3 === 0, `${label}: triangle index/vertex count is not divisible by three.`);
      total += count / 3;
      const material = json.materials?.[primitive.material];
      const textureInfo = material?.pbrMetallicRoughness?.baseColorTexture;
      requireValue(textureInfo && (textureInfo.texCoord ?? 0) === 0, `${label}: primitive lacks the indexed UV0 palette material.`);
      const texture = json.textures?.[textureInfo.index], pixels = images[texture?.source];
      requireValue(pixels, `${label}: invalid palette texture reference.`);
      const uv = accessor(primitive.attributes?.TEXCOORD_0, 'VEC2', 2, [5126]);
      requireValue(uv.count === vertices.count, `${label}: UV/POSITION counts differ.`);
      for (let index = 0; index < uv.count; index++) {
        const offset = uv.offset + index * uv.stride, u = uv.bytes.readFloatLE(offset), v = uv.bytes.readFloatLE(offset + 4);
        requireValue(Number.isFinite(u) && Number.isFinite(v) && u >= 0 && u < 1 && v >= 0 && v < 1,
          `${label}: palette UV outside the atlas.`);
        const texel = Math.floor(v * 16) * 16 + Math.floor(u * 16), paletteIndex = (texel + 1) % 256;
        requireValue(paletteIndex !== 0 && sameColor([...pixels.subarray(texel * 4, texel * 4 + 4)], palette[paletteIndex]),
          `${label}: used GLB texel differs from canonical palette slot ${paletteIndex}.`);
      }
    }
    return total;
  });
  requireValue(meshTriangles.length > 0 && Array.isArray(json.nodes) && Array.isArray(json.scenes), `${label}: missing mesh scene.`);
  const scene = json.scenes[json.scene ?? 0];
  requireValue(Array.isArray(scene?.nodes) && scene.nodes.length > 0, `${label}: invalid default scene.`);
  const visited = new Set();
  function visit(index) {
    requireValue(integer(index) && json.nodes[index] && !visited.has(index), `${label}: invalid/repeated/cyclic scene node ${index}.`);
    visited.add(index);
    const node = json.nodes[index];
    let triangles = 0;
    if (node.mesh !== undefined) {
      requireValue(integer(node.mesh) && meshTriangles[node.mesh] !== undefined, `${label}: invalid node mesh.`);
      triangles += meshTriangles[node.mesh];
    }
    for (const child of node.children ?? []) triangles += visit(child);
    return triangles;
  }
  const triangles = scene.nodes.reduce((sum, node) => sum + visit(node), 0);
  check(triangles === model.triangles, `${label}: declared ${model.triangles} triangles, actual scene has ${triangles}.`);
  return triangles;
}

function validateVox(bytes, model, palette) {
  const label = model.id;
  requireValue(bytes.length >= 20 && bytes.toString('ascii', 0, 4) === 'VOX '
    && [150, 200].includes(bytes.readUInt32LE(4)) && bytes.toString('ascii', 8, 12) === 'MAIN'
    && bytes.readUInt32LE(12) === 0 && bytes.readUInt32LE(16) === bytes.length - 20, `${label}: invalid VOX header/MAIN size.`);
  let count = 0, models = 0, size, rgba, pack;
  const colorsUsed = new Set();
  function chunks(start, end, depth = 0) {
    requireValue(depth <= 128, `${label}: VOX nesting is too deep.`);
    while (start < end) {
      requireValue(start + 12 <= end, `${label}: truncated VOX chunk.`);
      const tag = bytes.toString('ascii', start, start + 4), content = start + 12;
      const children = content + bytes.readUInt32LE(start + 4), next = children + bytes.readUInt32LE(start + 8);
      requireValue(next <= end, `${label}: VOX chunk exceeds its parent.`);
      const length = children - content;
      if (tag === 'PACK') { requireValue(length === 4 && pack === undefined, `${label}: invalid PACK.`); pack = bytes.readUInt32LE(content); }
      else if (tag === 'SIZE') {
        requireValue(length === 12 && !size, `${label}: invalid/unpaired SIZE.`);
        size = [0, 4, 8].map(offset => bytes.readUInt32LE(content + offset));
        requireValue(size.every(value => value > 0 && value <= 256), `${label}: invalid voxel dimensions.`);
      } else if (tag === 'XYZI') {
        requireValue(size && length >= 4, `${label}: XYZI has no SIZE.`);
        const cells = bytes.readUInt32LE(content);
        requireValue(cells > 0 && length === 4 + cells * 4, `${label}: XYZI length does not match its cell count.`);
        const occupied = new Set();
        for (let index = 0; index < cells; index++) {
          const offset = content + 4 + index * 4, x = bytes[offset], y = bytes[offset + 1], z = bytes[offset + 2], color = bytes[offset + 3];
          requireValue(x < size[0] && y < size[1] && z < size[2] && color !== 0, `${label}: invalid voxel coordinate/color.`);
          colorsUsed.add(color);
          const key = x + y * 256 + z * 65536;
          requireValue(!occupied.has(key), `${label}: duplicate occupied voxel cell.`);
          occupied.add(key);
        }
        count += cells; models++; size = undefined;
      } else if (tag === 'RGBA') {
        requireValue(length === 1024 && !rgba, `${label}: invalid/duplicate RGBA palette.`);
        rgba = bytes.subarray(content, children);
      }
      chunks(children, next, depth + 1); start = next;
    }
  }
  chunks(20, bytes.length);
  requireValue(models > 0 && !size && (pack === undefined || pack === models), `${label}: incomplete/mismatched VOX models.`);
  if (model.kind === 'character') {
    requireValue(rgba, `${label}: editable character VOX needs its canonical RGBA palette.`);
    // Older assets legitimately leave newer, unused semantic slots black.
    const indices = model.style === 'chibi' ? Array.from({ length: 256 }, (_, index) => index) : colorsUsed;
    for (const index of indices) {
      const texel = (index + 255) % 256;
      requireValue(sameColor([...rgba.subarray(texel * 4, texel * 4 + 4)], palette[index]), `${label}: VOX palette slot ${index} is not canonical.`);
    }
  }
  if (model.voxels !== null) check(count === model.voxels, `${label}: declared ${model.voxels} voxel cells, embedded VOX has ${count}.`);
  return count;
}

try {
  const html = await readFile(filename, 'utf8');
  htmlBytes = Buffer.byteLength(html);
  check(/<!doctype html>/i.test(html) && /<html\b/i.test(html), 'Viewer must be a standalone HTML document.');
  check(!/<!--\s*VIEWER_(?:STYLE|DATA|SCRIPT)\s*-->|\{\{\{|\$GODOT_[A-Z_]+/.test(html), 'Viewer contains unresolved build placeholders.');
  const dom = html.replace(/(<(?:script|style)\b[^>]*>)[\s\S]*?(<\/(?:script|style)\s*>)/gi, '$1$2').replace(/<!--[\s\S]*?-->/g, '');
  const tags = [...dom.matchAll(/<([A-Za-z][\w:-]*)\b[^>]*>/g)].map(match => ({ name: match[1].toLowerCase(), attrs: attributes(match[0]) }));
  const ids = tags.map(tag => tag.attrs.get('id')).filter(Boolean);
  check(new Set(ids).size === ids.length, 'Viewer contains duplicate HTML IDs.');
  for (const id of requiredIds) check(ids.includes(id), `Required viewer control/region is missing: ${id}.`);
  for (const id of ['asset-select', 'character-style', 'view-mode', 'character-select', 'framing', 'palette-select'])
    check(tags.some(tag => tag.name === 'select' && tag.attrs.get('id') === id), `${id} must be a select control.`);
  for (const id of ['motion-toggle', 'reset-view', 'camera-front', 'camera-right', 'camera-left', 'camera-back', 'export-palette', 'export-vox', 'export-glb'])
    check(tags.some(tag => tag.name === 'button' && tag.attrs.get('id') === id), `${id} must be a button.`);
  for (const id of ['sync-cameras', 'protect-identity'])
    check(tags.some(tag => tag.name === 'input' && tag.attrs.get('id') === id && tag.attrs.get('type') === 'checkbox'), `${id} must be a checkbox.`);
  check(tags.some(tag => tag.name === 'canvas' && tag.attrs.get('id') === 'viewer-canvas'), 'viewer-canvas must be a canvas element.');
  const optionSets = { 'asset-select': ['characters', 'room', 'props'], 'view-mode': ['compare', 'solo', 'lineup'],
    'character-style': ['chibi', 'original'], 'framing': ['body', 'portrait'], 'character-select': characterIds,
    'palette-select': ['original', 'island', 'pastel', 'neon', 'mono'] };
  for (const match of dom.matchAll(/<select\b([^>]*)>([\s\S]*?)<\/select\s*>/gi)) {
    const id = attributes(match[1]).get('id'), expected = optionSets[id];
    if (!expected) continue;
    const options = [...match[2].matchAll(/<option\b[^>]*>/gi)];
    const values = options.map(option => attributes(option[0]).get('value'));
    check(expected.every(value => values.includes(value)), `${id} is missing a required option.`);
    if (id === 'character-style') {
      check(values.length === 2 && new Set(values).size === 2, 'Character style must offer exactly chibi and original.');
      const selected = options.filter(option => /\sselected(?:\s*=|\s|>)/i.test(option[0]));
      check(selected.length <= 1 && attributes((selected[0] ?? options[0])[0]).get('value') === 'chibi',
        'Character style must default to chibi.');
    }
  }
  for (const tag of tags) {
    if (tag.name === 'script') check(!tag.attrs.has('src'), 'Single-file viewer cannot load an external script.');
    if (tag.name === 'link' && /(?:^|\s)stylesheet(?:\s|$)/i.test(tag.attrs.get('rel') ?? ''))
      check((tag.attrs.get('href') ?? '').startsWith('data:'), 'Single-file viewer cannot load an external stylesheet.');
    for (const key of ['src', 'href', 'poster', 'data']) {
      const value = tag.attrs.get(key);
      if (value === undefined || value.startsWith('#') || value.startsWith('data:')) continue;
      check(!/^(?:https?:)?\/\//i.test(value), `External HTTP resource/link is forbidden: ${key}=${value}.`);
      if (key !== 'href') check(false, `Single-file viewer has a separate resource: ${key}=${value}.`);
    }
  }
  const styles = [...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style\s*>/gi)].map(match => match[1]).join('\n');
  check(styles.trim().length > 100, 'Viewer needs embedded styling.');
  check(!/@import\s|url\(\s*(?:"(?!data:|#)[^"]+"|'(?!data:|#)[^']+'|(?!["']|data:|#)[^)]*)\)/i.test(styles),
    'Viewer CSS contains an external/separate resource.');
  const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)];
  const dataScripts = scripts.filter(match => attributes(match[1]).get('id') === 'viewer-data');
  requireValue(dataScripts.length === 1 && attributes(dataScripts[0][1]).get('type') === 'application/json', 'Exactly one viewer-data JSON script is required.');
  const runtime = scripts.filter(match => !['application/json', 'application/ld+json'].includes(attributes(match[1]).get('type')));
  requireValue(runtime.length > 0 && runtime.some(match => match[2].length > 5000), 'Runnable inline viewer bundle is missing.');
  for (const match of runtime) {
    requireValue(attributes(match[1]).get('type') !== 'module', 'Offline viewer must use a bundled classic script, without module resolution.');
    new Script(match[2], { filename: 'viewer-inline.js' });
    check(!/\bimport\s*\(/.test(match[2]), 'Viewer bundle must not use runtime dynamic imports.');
    check(!/\b(?:fetch|importScripts|WebSocket|EventSource)\s*\(\s*["'`]\s*(?:https?:)?\/\//i.test(match[2]),
      'Viewer bundle contains an external HTTP runtime request.');
    for (const url of match[2].matchAll(/https?:\/\/[^\s"'`<>\\)]+/gi))
      check(inertHttpReference(match[2], url.index, url[0]), `Viewer bundle contains an executable HTTP reference: ${url[0]}.`);
  }
  const data = JSON.parse(dataScripts[0][2]);
  requireValue(data.schema === 'greenbox-viewer-v2', 'Unrecognized viewer data schema.');
  validateCatalog(data.catalog);
  requireValue(Array.isArray(data.models) && data.models.length === 16, 'Viewer must embed seven original characters, seven chibi characters, bedroom, and props.');
  const modelIds = data.models.map(model => model.id);
  check(new Set(modelIds).size === 16, 'Embedded model IDs must be unique.');
  for (const id of [...characterIds, ...chibiIds, 'bedroom', 'props']) check(modelIds.includes(id), `Missing embedded model: ${id}.`);
  for (const model of data.models) {
    try {
      const expectedStyle = characterIds.includes(model.id) ? 'original' : chibiIds.includes(model.id) ? 'chibi' : null;
      const expectedKind = expectedStyle ? 'character' : model.id === 'bedroom' ? 'room' : model.id === 'props' ? 'props' : null;
      requireValue(expectedKind && model.kind === expectedKind, `${model.id}: invalid asset kind.`);
      if (expectedStyle) requireValue(model.style === expectedStyle
        && model.characterId === (expectedStyle === 'chibi' ? model.id.slice(0, -6) : model.id),
        `${model.id}: character style or identity mapping is incorrect.`);
      requireValue(typeof model.label === 'string' && model.label.trim().length > 0 && integer(model.triangles, 1)
        && (integer(model.voxels) || (model.kind !== 'character' && model.voxels === null))
        && ((Number.isFinite(model.height) && model.height > 0) || (model.kind !== 'character' && model.height === null)),
      `${model.id}: invalid asset label/statistics.`);
      const triangles = validateGlb(base64(model.glb, `${model.id} GLB`), model, data.catalog.original);
      requireValue(model.kind !== 'character' || model.vox !== null, `${model.id}: editable character VOX is missing.`);
      const voxels = model.vox === null ? null : validateVox(base64(model.vox, `${model.id} VOX`), model, data.catalog.original);
      if (model.kind === 'character') {
        triangleTotal += triangles; voxelTotal += voxels;
        styleTotals[expectedStyle].triangles += triangles;
        styleTotals[expectedStyle].voxels += voxels;
        styleTotals[expectedStyle].models++;
      }
      verifiedModels++;
    } catch (error) { failures.push(error.message); }
  }
  for (const [style, expected] of Object.entries(expectedStyleTotals)) {
    const actual = styleTotals[style];
    check(actual.models === 7, `${style}: expected seven verified character models; actual is ${actual.models}.`);
    check(actual.triangles === expected.triangles, `${style}: character geometry must total ${expected.triangles} triangles; actual is ${actual.triangles}.`);
    check(actual.voxels === expected.voxels, `${style}: sources must total ${expected.voxels} occupied cells; actual is ${actual.voxels}.`);
  }
} catch (error) { failures.push(error.code ?? error.message); }

console.log('Static integrity validation does not establish interactive behavior, browser performance, or offline rendering success.');
if (failures.length) {
  for (const failure of failures) console.error(`Error: ${failure}`);
  process.exitCode = 1;
} else console.log(`Offline viewer verified: ${(htmlBytes / 1024 / 1024).toFixed(2)} MiB, ${verifiedModels} embedded models, ${triangleTotal} character triangles, ${voxelTotal} character voxel cells, 256 canonical colors.`);
