// Array slots are VOX indices: air=0, occupied colors=1..255.
// Existing GLB UVs sample texture texel index-1; exports never remap occupancy.
const encoder = new TextEncoder();
const decoder = new TextDecoder();
const PNG_SIGNATURE = [137, 80, 78, 71, 13, 10, 26, 10];

function bytes(value, name) {
  if (!(value instanceof Uint8Array)) throw new TypeError(`${name} must be a Uint8Array.`);
  return value;
}

function color(value, alpha = 255) {
  if (typeof value === 'string' && /^#[\da-f]{6}(?:[\da-f]{2})?$/i.test(value)) {
    value = value.slice(1).match(/../g).map(component => parseInt(component, 16));
  }
  if (!Array.isArray(value) || (value.length !== 3 && value.length !== 4)
    || value.some(component => !Number.isInteger(component) || component < 0 || component > 255))
    throw new TypeError('Colors must contain RGB/RGBA bytes or #RRGGBB/#RRGGBBAA.');
  return [...value.slice(0, 3), value.length === 4 ? value[3] : alpha];
}

function paletteColors(value) {
  if (!Array.isArray(value) || value.length !== 256) throw new TypeError('A palette must have exactly 256 colors.');
  return value.map(entry => color(entry));
}

export function buildPalette(catalog, presetId, protectIdentity = true, overrides = {}) {
  if (!catalog || catalog.schema !== 'greenbox-palettes-v1') throw new TypeError('Unrecognized palette catalog.');
  const original = paletteColors(catalog.original);
  const preset = catalog.presets?.[presetId];
  if (!preset || !Array.isArray(preset.colors)) throw new RangeError(`Unknown palette preset: ${presetId}`);
  const result = paletteColors(preset.colors);
  if (protectIdentity) {
    for (const index of catalog.identityIndices ?? []) {
      if (!Number.isInteger(index) || index < 1 || index > 255) throw new RangeError('Invalid identity palette index.');
      result[index] = original[index].slice();
    }
  }
  // An explicit user edit wins over preset protection; all models share that slot.
  for (const [key, value] of Object.entries(overrides)) {
    const index = Number(key);
    if (!/^\d+$/.test(key) || !Number.isInteger(index) || index < 0 || index > 255) throw new RangeError(`Invalid palette index: ${key}`);
    result[index] = color(value, result[index][3]);
  }
  result[0][3] = 0;
  return result;
}

function concatenate(parts) {
  const length = parts.reduce((total, part) => total + part.length, 0);
  if (!Number.isSafeInteger(length) || length > 0xffffffff) throw new RangeError('Output exceeds the binary format size limit.');
  const output = new Uint8Array(length);
  let offset = 0;
  for (const part of parts) { output.set(part, offset); offset += part.length; }
  return output;
}

function voxChunk(tag, content, children) {
  const header = new Uint8Array(12);
  header.set(tag);
  const view = new DataView(header.buffer);
  view.setUint32(4, content.length, true);
  view.setUint32(8, children.length, true);
  return concatenate([header, content, children]);
}

export function writeVoxPalette(originalUint8Array, palette) {
  const input = bytes(originalUint8Array, 'VOX input');
  const colors = paletteColors(palette);
  colors[0][3] = 0;
  if (input.length < 20 || decoder.decode(input.subarray(0, 4)) !== 'VOX '
    || decoder.decode(input.subarray(8, 12)) !== 'MAIN') throw new Error('Invalid VOX header/MAIN chunk.');
  const view = new DataView(input.buffer, input.byteOffset, input.byteLength);
  if (![150, 200].includes(view.getUint32(4, true)) || view.getUint32(12, true) !== 0)
    throw new Error('Unsupported VOX version or invalid MAIN content.');
  const rgba = new Uint8Array(1024);
  for (let texel = 0; texel < 256; texel++) rgba.set(colors[(texel + 1) % 256], texel * 4);
  let paletteChunks = 0;

  function rewrite(start, end, depth) {
    if (depth > 128) throw new Error('VOX chunk nesting is too deep.');
    const output = [];
    let position = start;
    while (position < end) {
      if (position + 12 > end) throw new Error('Truncated VOX chunk header.');
      const contentStart = position + 12;
      const childrenStart = contentStart + view.getUint32(position + 4, true);
      const next = childrenStart + view.getUint32(position + 8, true);
      if (next > end) throw new Error('VOX chunk exceeds its parent.');
      const tag = input.subarray(position, position + 4);
      const id = decoder.decode(tag);
      let content = input.subarray(contentStart, childrenStart);
      let children = rewrite(childrenStart, next, depth + 1);
      if (id === 'RGBA') {
        if (content.length !== 1024) throw new Error('VOX RGBA chunks must contain 256 entries.');
        content = rgba;
        paletteChunks++;
      }
      if (depth === 0 && id === 'MAIN' && paletteChunks === 0) {
        children = concatenate([children, voxChunk(encoder.encode('RGBA'), rgba, new Uint8Array())]);
        paletteChunks++;
      }
      output.push(voxChunk(tag, content, children));
      position = next;
    }
    return concatenate(output);
  }
  const rootEnd = 20 + view.getUint32(12, true) + view.getUint32(16, true);
  if (rootEnd !== input.length) throw new Error('VOX MAIN length does not match the file.');
  return concatenate([input.subarray(0, 8), rewrite(8, input.length, 0)]);
}

function crc32(value) {
  let crc = 0xffffffff;
  for (const byte of value) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function pngSize(input) {
  if (input.length < 33 || PNG_SIGNATURE.some((byte, index) => input[index] !== byte)) throw new Error('Invalid palette PNG signature.');
  const view = new DataView(input.buffer, input.byteOffset, input.byteLength);
  let position = 8;
  let dimensions;
  let imageData = false;
  let ended = false;
  while (position < input.length) {
    if (position + 12 > input.length) throw new Error('Truncated palette PNG chunk.');
    const length = view.getUint32(position, false);
    const end = position + 12 + length;
    if (end > input.length) throw new Error('Palette PNG chunk exceeds the file.');
    const name = decoder.decode(input.subarray(position + 4, position + 8));
    if (crc32(input.subarray(position + 4, end - 4)) !== view.getUint32(end - 4, false)) throw new Error('Palette PNG checksum failed.');
    if (position === 8) {
      if (name !== 'IHDR' || length !== 13) throw new Error('Palette PNG must start with IHDR.');
      dimensions = [view.getUint32(position + 8, false), view.getUint32(position + 12, false)];
    }
    if (name === 'IDAT') imageData = true;
    if (name === 'IEND') {
      if (length !== 0 || end !== input.length) throw new Error('Invalid palette PNG end chunk.');
      ended = true;
    }
    position = end;
  }
  if (!imageData || !ended) throw new Error('Palette PNG is incomplete.');
  return dimensions;
}

function padded(input, fill = 0) {
  const result = new Uint8Array(Math.ceil(input.length / 4) * 4);
  if (fill) result.fill(fill);
  result.set(input);
  return result;
}

function glbChunk(type, content) {
  const header = new Uint8Array(8);
  const view = new DataView(header.buffer);
  view.setUint32(0, content.length, true);
  view.setUint32(4, type, true);
  return concatenate([header, content]);
}

function jsonWithSignedZero(value) {
  // Blender joint metadata can contain -0. JSON.stringify normally turns it into 0.
  if (typeof value === 'number' && Object.is(value, -0)) return '-0';
  if (Array.isArray(value)) return `[${value.map(jsonWithSignedZero).join(',')}]`;
  if (value && typeof value === 'object')
    return `{${Object.entries(value).map(([key, child]) => `${JSON.stringify(key)}:${jsonWithSignedZero(child)}`).join(',')}}`;
  return JSON.stringify(value);
}

export function writeGlbPalette(originalUint8Array, pngBytes) {
  const input = bytes(originalUint8Array, 'GLB input');
  const png = bytes(pngBytes, 'Palette PNG');
  if (pngSize(png).some(dimension => dimension !== 16)) throw new Error('Palette PNG must be 16 by 16 pixels.');
  const view = new DataView(input.buffer, input.byteOffset, input.byteLength);
  if (input.length < 20 || view.getUint32(0, true) !== 0x46546c67 || view.getUint32(4, true) !== 2
    || view.getUint32(8, true) !== input.length) throw new Error('Invalid GLB version 2 header.');
  const chunks = [];
  let position = 12;
  while (position < input.length) {
    if (position + 8 > input.length) throw new Error('Truncated GLB chunk header.');
    const length = view.getUint32(position, true);
    const type = view.getUint32(position + 4, true);
    const end = position + 8 + length;
    if (length % 4 || end > input.length) throw new Error('Invalid GLB chunk length/alignment.');
    chunks.push({ type, content: input.subarray(position + 8, end) });
    position = end;
  }
  if (chunks[0]?.type !== 0x4e4f534a || chunks.filter(chunk => chunk.type === 0x4e4f534a).length !== 1
    || chunks.filter(chunk => chunk.type === 0x004e4942).length !== 1) throw new Error('GLB must have one JSON chunk and one embedded BIN chunk.');
  const document = JSON.parse(decoder.decode(chunks[0].content).replace(/\0+$/, '').trim());
  const binary = chunks.find(chunk => chunk.type === 0x004e4942);
  if (document.buffers?.length !== 1 || document.buffers[0].uri
    || !Number.isInteger(document.buffers[0].byteLength) || document.buffers[0].byteLength > binary.content.length)
    throw new Error('Palette replacement requires one embedded GLB buffer.');
  const byteLength = document.buffers[0].byteLength;
  if (byteLength < 0 || binary.content.length - byteLength > 3) throw new Error('Invalid GLB buffer byteLength/padding.');
  for (const bufferView of document.bufferViews ?? []) {
    if (bufferView.buffer !== 0 || !Number.isInteger(bufferView.byteLength) || bufferView.byteLength < 0
      || !Number.isInteger(bufferView.byteOffset ?? 0) || (bufferView.byteOffset ?? 0) < 0
      || (bufferView.byteOffset ?? 0) + bufferView.byteLength > byteLength) throw new Error('Invalid GLB bufferView bounds.');
  }
  const paletteViews = new Set();
  for (const image of document.images ?? []) {
    if (image.mimeType !== 'image/png' || !Number.isInteger(image.bufferView)) continue;
    const bufferView = document.bufferViews?.[image.bufferView];
    if (!bufferView) throw new Error('GLB image references an absent bufferView.');
    const start = bufferView.byteOffset ?? 0;
    const dimensions = pngSize(binary.content.subarray(start, start + bufferView.byteLength));
    if (dimensions.every(dimension => dimension === 16)) paletteViews.add(image.bufferView);
  }
  if (!paletteViews.size) throw new Error('GLB has no embedded 16 by 16 palette PNG.');
  function rejectGeometryAlias(value) {
    if (!value || typeof value !== 'object') return;
    for (const [key, child] of Object.entries(value)) {
      if (key === 'bufferView' && paletteViews.has(child)) throw new Error('Palette bufferView is also used by non-image data.');
      rejectGeometryAlias(child);
    }
  }
  for (const [key, value] of Object.entries(document)) if (key !== 'images') rejectGeometryAlias(value);

  // Append instead of shifting geometry. Only the palette image view moves;
  // all mesh accessors, existing geometry bytes, pivots and unknown chunks survive.
  const imageOffset = Math.ceil(byteLength / 4) * 4;
  const newBinary = new Uint8Array(imageOffset + png.length);
  newBinary.set(binary.content.subarray(0, byteLength));
  newBinary.set(png, imageOffset);
  for (const index of paletteViews) {
    document.bufferViews[index].byteOffset = imageOffset;
    document.bufferViews[index].byteLength = png.length;
  }
  document.buffers[0].byteLength = newBinary.length;
  const rebuilt = chunks.map(chunk => glbChunk(chunk.type, chunk.type === 0x4e4f534a
    ? padded(encoder.encode(jsonWithSignedZero(document)), 32)
    : chunk.type === 0x004e4942 ? padded(newBinary) : chunk.content));
  const payload = concatenate(rebuilt);
  const header = new Uint8Array(12);
  const headerView = new DataView(header.buffer);
  headerView.setUint32(0, 0x46546c67, true);
  headerView.setUint32(4, 2, true);
  headerView.setUint32(8, header.length + payload.length, true);
  return concatenate([header, payload]);
}
