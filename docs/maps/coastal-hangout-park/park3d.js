// Japan Coastal Hangout Park: three.js viewer for the massing model made by model3d.py.
// Plan metres map to x = east, z = south, y = level above sea (±0.00).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const MASCOT = ['...O......O...', '..OYO....OYO..', '..OYYOOOOYYO..', '.OYYYYYYYYYYO.', '.OYYKYYYYKYYO.',
  'OYYYKYYYYKYYYO', 'OYPYYYYYYYYPYO', 'OYYYYYKKYYYYYO', '.OYYYYYYYYYYO.', '..OOYYYYYYOO..', '....OOOOOO....'];
const FONT_D = '"Bricolage Grotesque", "Arial Black", sans-serif';
const FONT_C = '"Barlow Condensed", "Arial Narrow", sans-serif';

function rng(seed) {
  let s = seed * 9301 + 49297;
  return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
}

function canvasFor(w, h, ppm) {
  const c = document.createElement('canvas');
  c.width = Math.max(8, Math.min(2048, Math.round(w * ppm)));
  c.height = Math.max(8, Math.min(2048, Math.round(h * ppm)));
  return c;
}

function rrectPath(g, x, y, w, h, r) {
  g.beginPath();
  g.moveTo(x + r, y); g.lineTo(x + w - r, y); g.quadraticCurveTo(x + w, y, x + w, y + r);
  g.lineTo(x + w, y + h - r); g.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  g.lineTo(x + r, y + h); g.quadraticCurveTo(x, y + h, x, y + h - r);
  g.lineTo(x, y + r); g.quadraticCurveTo(x, y, x + r, y); g.closePath();
}

function mullions(g, W, H, n, col = '#2E333B', lw = 6) {
  g.strokeStyle = col; g.lineWidth = lw;
  g.strokeRect(lw / 2, lw / 2, W - lw, H - lw);
  for (let i = 1; i < n; i++) { g.beginPath(); g.moveTo(W * i / n, 0); g.lineTo(W * i / n, H); g.stroke(); }
}

function glints(g, W, H, n) {
  g.strokeStyle = 'rgba(255,255,255,.55)'; g.lineWidth = Math.max(2, W / 120);
  for (let i = 0; i < n; i++) {
    const x = W * (i + .25) / n;
    g.beginPath(); g.moveTo(x, H * .78); g.lineTo(x + W * .25 / n, H * .22); g.stroke();
  }
}

function drawLabel(L) {
  const ppm = L.k === 'text' || L.k === 'pill' ? 160 : L.k === 'mascot' ? 40 : 64;
  const c = canvasFor(L.w, L.h, ppm);
  const g = c.getContext('2d');
  const W = c.width, H = c.height;
  if (L.k === 'text') {
    g.font = `${L.font || 800} ${Math.round(H * .82)}px ${FONT_D}`;
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.lineJoin = 'round'; g.lineWidth = H * .1; g.strokeStyle = L.stroke || '#000';
    g.strokeText(L.txt, W / 2, H * .55); g.fillStyle = L.fg; g.fillText(L.txt, W / 2, H * .55);
  } else if (L.k === 'pill') {
    g.fillStyle = L.bg; rrectPath(g, 0, 0, W, H, Math.min(H / 2, W / 2)); g.fill();
    g.fillStyle = L.fg; g.textAlign = 'center'; g.textBaseline = 'middle';
    let fs = Math.round(H * .62);
    g.font = `700 ${fs}px ${FONT_C}`;
    while (g.measureText(L.txt).width > W * .9 && fs > 6) { fs -= 2; g.font = `700 ${fs}px ${FONT_C}`; }
    g.fillText(L.txt, W / 2, H * .54);
  } else if (L.k === 'mascot') {
    const cols = { O: '#E3AE1F', Y: '#FFE27A', K: '#2E333B', P: '#F59BC3' };
    const px = Math.min(W / 14, H / 11);
    MASCOT.forEach((row, r) => [...row].forEach((ch, k) => {
      if (cols[ch]) { g.fillStyle = cols[ch]; g.fillRect(k * px, r * px, px + 1, px + 1); }
    }));
  } else if (L.k === 'door' || L.k === 'glow') {
    const grd = g.createLinearGradient(0, 0, 0, H);
    grd.addColorStop(0, '#FFE9B8'); grd.addColorStop(1, '#FFD27A');
    g.fillStyle = grd; g.fillRect(0, 0, W, H);
    const R = rng(W + H);
    if (L.k === 'door') {
      g.fillStyle = '#F59BC3'; g.fillRect(0, H * .08, W, H * .02);
      g.fillStyle = '#24ABCC'; g.fillRect(0, H * .16, W, H * .02);
      let x = W * .04;
      while (x < W * .92) {
        const w = W * (.11 + R() * .03), h = H * (.55 + R() * .08);
        g.fillStyle = ['#F59BC3', '#F7F2E6', '#A9DCC6', '#F7F2E6'][Math.floor(R() * 4)];
        g.fillRect(x, H - h, w, h);
        g.fillStyle = R() > .5 ? '#2F8FE8' : '#2E333B'; g.fillRect(x + w * .15, H - h * .85, w * .7, h * .3);
        x += w + W * (.02 + R() * .04);
      }
      g.fillStyle = '#F7CB3B'; g.fillRect(W * .54, H * .1, W * .17, H * .9);
      g.fillStyle = '#2E333B'; g.font = `700 ${Math.round(H * .07)}px ${FONT_C}`; g.textAlign = 'center';
      ['PLAY', 'MEET', 'ENJOY'].forEach((t, i) => g.fillText(t, W * .625, H * (.3 + i * .09)));
      g.fillStyle = 'rgba(203,232,238,.35)'; g.fillRect(0, 0, W, H);
      mullions(g, W, H, 4, '#2E333B', Math.max(4, W / 90)); glints(g, W, H, 4);
    } else {
      for (let i = 0; i < 6; i++) {
        g.fillStyle = ['#F59BC3', '#A9DCC6', '#F7F2E6', '#2F8FE8'][i % 4];
        g.fillRect(W * (.05 + i * .155), H * .55, W * .11, H * .45);
      }
      g.fillStyle = 'rgba(203,232,238,.35)'; g.fillRect(0, 0, W, H);
      mullions(g, W, H, Math.max(1, Math.round(L.w / 2.4)), '#2E333B', Math.max(3, W / 160));
    }
  } else if (L.k === 'glass') {
    const grd = g.createLinearGradient(0, 0, W, H);
    grd.addColorStop(0, '#D7EEF4'); grd.addColorStop(.5, '#9CCFDB'); grd.addColorStop(1, '#C7E6EE');
    g.fillStyle = grd; g.fillRect(0, 0, W, H);
    const n = Math.max(1, Math.round(L.w / 2.2));
    mullions(g, W, H, n, '#2E333B', Math.max(3, W / 200)); glints(g, W, H, n);
  } else if (L.k === 'stripe') {
    const n = Math.max(2, Math.round(L.w / .6));
    for (let i = 0; i < n; i++) { g.fillStyle = i % 2 ? L.b2 : L.a; g.fillRect(W * i / n, 0, W / n + 1, H); }
  } else if (L.k === 'poster') {
    g.fillStyle = '#FFE27A'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#3D8BE0'; g.fillRect(0, 0, W, H * .55);
    g.fillStyle = '#fff'; g.textAlign = 'center'; g.font = `800 ${Math.round(H * .11)}px ${FONT_D}`;
    g.fillText('あそぼう!', W / 2, H * .16);
    const px = W / 22;
    MASCOT.forEach((row, r) => [...row].forEach((ch, k) => {
      const cols = { O: '#E3AE1F', Y: '#FFE27A', K: '#2E333B', P: '#F59BC3' };
      if (cols[ch]) { g.fillStyle = cols[ch]; g.fillRect(W * .18 + k * px, H * .2 + r * px, px + 1, px + 1); }
    }));
    g.fillStyle = '#2E333B'; g.textAlign = 'left'; g.font = `700 ${Math.round(H * .065)}px ${FONT_C}`;
    ['GAMES', 'FRIENDS', 'GOOD TIMES'].forEach((t, i) => g.fillText(t, W * .1, H * (.66 + i * .085)));
  } else if (L.k === 'panel') {
    g.fillStyle = '#F7F2E6'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#2E333B'; g.textAlign = 'left'; g.font = `700 ${Math.round(H * .075)}px ${FONT_C}`;
    ['SMALL', 'GAMES', 'BIG', 'HAPPINESS'].forEach((t, i) => g.fillText(t, W * .12, H * (.36 + i * .1)));
    g.strokeStyle = '#3D8BE0'; g.lineWidth = H * .012; g.beginPath();
    for (let x = 0; x <= W * .5; x += 2) g.lineTo(W * .12 + x, H * .82 + Math.sin(x / W * 40) * H * .015);
    g.stroke();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function skyTexture() {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const g = c.getContext('2d');
  const grd = g.createLinearGradient(0, 0, 0, 256);
  grd.addColorStop(0, '#79BEEB'); grd.addColorStop(.55, '#BFE2F7'); grd.addColorStop(1, '#F1F8FC');
  g.fillStyle = grd; g.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function hEval(spec, x, z) {
  if (typeof spec === 'number') return spec;
  const [ox, oz, dx, dz] = spec.ax;
  const t = (x - ox) * dx + (z - oz) * dz;
  const p = spec.pts;
  if (t <= p[0][0]) return p[0][1];
  for (let i = 1; i < p.length; i++) {
    if (t <= p[i][0]) return p[i - 1][1] + (p[i][1] - p[i - 1][1]) * (t - p[i - 1][0]) / (p[i][0] - p[i - 1][0]);
  }
  return p[p.length - 1][1];
}

// polygon with a top surface (height per vertex) and skirts down to a base level
function surfaceGeom(o, holes, heightOf, base) {
  const shape = new THREE.Shape(o.map(([x, z]) => new THREE.Vector2(x, z)));
  holes.forEach(h => shape.holes.push(new THREE.Path(h.map(([x, z]) => new THREE.Vector2(x, z)))));
  const sg = new THREE.ShapeGeometry(shape);
  const p = sg.attributes.position;
  const pos = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getY(i);
    pos[i * 3] = x; pos[i * 3 + 1] = heightOf(x, z); pos[i * 3 + 2] = z;
  }
  const idx = Array.from(sg.index.array);
  for (let i = 0; i < idx.length; i += 3) { const t = idx[i + 1]; idx[i + 1] = idx[i + 2]; idx[i + 2] = t; }
  const top = new THREE.BufferGeometry();
  top.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  top.setIndex(idx);
  top.computeVertexNormals();
  const sk = [];
  for (const ring of [o, ...holes]) {
    for (let i = 0; i < ring.length; i++) {
      const [x0, z0] = ring[i], [x1, z1] = ring[(i + 1) % ring.length];
      const h0 = heightOf(x0, z0), h1 = heightOf(x1, z1);
      sk.push(x0, h0, z0, x1, h1, z1, x1, base, z1, x0, h0, z0, x1, base, z1, x0, base, z0);
    }
  }
  const skirt = new THREE.BufferGeometry();
  skirt.setAttribute('position', new THREE.Float32BufferAttribute(sk, 3));
  skirt.computeVertexNormals();
  return [top.toNonIndexed(), skirt];
}

export function mountPark(canvas, D, opt = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: !!opt.still });
  renderer.setPixelRatio(opt.pixelRatio || Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.background = skyTexture();
  scene.fog = new THREE.Fog(0xE4F2FA, 280, 900);
  const cam = new THREE.PerspectiveCamera(50, 16 / 9, .3, 2000);
  const C = new THREE.Vector3(...D.center);
  scene.add(new THREE.HemisphereLight(0xEAF5FF, 0xC9B48F, 1.35));
  const sun = new THREE.DirectionalLight(0xFFF1DC, 2.4);
  sun.position.copy(C).add(new THREE.Vector3(...D.sun));
  sun.target.position.copy(C);
  sun.castShadow = true;
  const sm = opt.shadow || 4096;
  sun.shadow.mapSize.set(sm, sm);
  Object.assign(sun.shadow.camera, { left: -140, right: 140, top: 140, bottom: -140, near: 20, far: 520 });
  sun.shadow.bias = -0.0003;
  sun.shadow.normalBias = 0.04;
  scene.add(sun, sun.target);

  const matCache = new Map();
  function mat(ci, kind) {
    const key = ci + ':' + kind;
    if (!matCache.has(key)) {
      const color = new THREE.Color(D.pal[ci]);
      let m;
      if (kind === 'glass') m = new THREE.MeshStandardMaterial({ color, roughness: .05, metalness: .2, transparent: true, opacity: .42, depthWrite: false });
      else m = new THREE.MeshStandardMaterial({ color, roughness: .86, metalness: 0, side: THREE.DoubleSide, flatShading: kind === 'flat' });
      matCache.set(key, m);
    }
    return matCache.get(key);
  }
  const buckets = new Map();
  function put(ci, kind, geom, cast = true) {
    const key = ci + ':' + kind + ':' + (cast ? 1 : 0);
    if (!buckets.has(key)) buckets.set(key, { ci, kind, cast, list: [] });
    const g = geom.index ? geom.toNonIndexed() : geom;
    if (g.attributes.uv) g.deleteAttribute('uv');
    if (!g.attributes.normal) g.computeVertexNormals();
    buckets.get(key).list.push(g);
  }

  // ground slabs and prisms
  for (const s of D.slabs) {
    let hf;
    if (s.vo) {
      const m = new Map();
      s.o.forEach(([x, z], i) => m.set(x.toFixed(2) + ',' + z.toFixed(2), s.vo[i]));
      s.h.forEach((r, j) => r.forEach(([x, z], i) => m.set(x.toFixed(2) + ',' + z.toFixed(2), s.vh[j][i])));
      hf = (x, z) => m.get(x.toFixed(2) + ',' + z.toFixed(2)) ?? 0;
    } else hf = (x, z) => hEval(s.t, x, z);
    const [top, skirt] = surfaceGeom(s.o, s.h, hf, s.b);
    put(s.c, s.m, top, false);
    put(s.c, s.m, skirt, false);
  }
  for (const s of D.prisms) {
    const [top, skirt] = surfaceGeom(s.o, s.h, () => s.y1, s.y0);
    put(s.c, s.m, top, !!s.s);
    put(s.c, s.m, skirt, !!s.s);
  }
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), v = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1);
  const D2R = Math.PI / 180;
  for (const b of D.boxes) {
    const [cx, cy, cz, sx, sy, sz, ry, rx, ci, kind] = b;
    const g = new THREE.BoxGeometry(sx, sy, sz);
    e.set(rx * D2R, ry * D2R, 0, 'YXZ'); q.setFromEuler(e);
    g.applyMatrix4(m4.compose(v.set(cx, cy, cz), q, one));
    put(ci, kind, g, kind !== 'glass');
  }
  for (const c of D.cyls) {
    const [x, y, z, r0, r1, h, ci, axis, seg, kind] = c;
    if (axis === 's') {
      const sg = new THREE.SphereGeometry(r0, 18, 12);
      sg.translate(x, y, z);
      put(ci, kind, sg);
      continue;
    }
    const g = new THREE.CylinderGeometry(r1, r0, h, seg, 1, false);
    if (seg === 4) g.rotateY(Math.PI / 4);
    if (axis === 'y') g.translate(x, y + h / 2, z);
    else if (axis === 'x') { g.rotateZ(-Math.PI / 2); g.translate(x, y, z); }
    else { g.rotateX(Math.PI / 2); g.translate(x, y, z); }
    put(ci, kind, g, kind !== 'glass');
  }
  // trees, sakura, palms
  const pal = name => { const i = D.pal.indexOf(name); return i >= 0 ? i : 0; };
  const TREE = ['#6DAA55', '#5B9A49', '#78B35E'], SAK = ['#F4B8D1', '#F7C8DC'], PALM = '#5E9A4A', TRUNK = '#8A6A4A';
  const extraPal = c => { let i = D.pal.indexOf(c); if (i < 0) { D.pal.push(c); i = D.pal.length - 1; } return i; };
  for (const t of D.trees) {
    const [x, y, z, r, h, kind, seed] = t;
    const R = rng(seed + 11);
    if (kind === 'p') {
      const lean = (R() - .5) * .8;
      const tg = new THREE.CylinderGeometry(.16, .24, h, 7);
      tg.translate(0, h / 2, 0); tg.rotateZ(lean * .12); tg.translate(x, y, z);
      put(extraPal(TRUNK), 'std', tg);
      const tx = x - Math.sin(lean * .12) * h, ty = y + h;
      for (let k = 0; k < 9; k++) {
        const a = k / 9 * Math.PI * 2 + R() * .3, L = r * (.95 + R() * .25);
        const fg = new THREE.BoxGeometry(L, .06, .75);
        fg.translate(L / 2, 0, 0); fg.rotateZ(-.35 - R() * .25); fg.rotateY(a); fg.translate(tx, ty, z);
        put(extraPal(PALM), 'flat', fg);
      }
      continue;
    }
    const trunkH = h * .45;
    const tg = new THREE.CylinderGeometry(.18 + r * .02, .26 + r * .03, trunkH + .5, 7);
    tg.translate(x, y + (trunkH + .5) / 2, z);
    put(extraPal(TRUNK), 'std', tg);
    const cols = kind === 's' ? SAK : TREE;
    const n = 4 + Math.floor(r / 3);
    for (let k = 0; k < n; k++) {
      const a = R() * Math.PI * 2, d = k === 0 ? 0 : r * (.35 + R() * .3);
      const rr = k === 0 ? r * .72 : r * (.42 + R() * .2);
      const g = new THREE.IcosahedronGeometry(rr, 1);
      g.scale(1, .82, 1);
      g.translate(x + Math.cos(a) * d, y + trunkH + rr * .75 + (k === 0 ? .2 : R() * r * .25), z + Math.sin(a) * d);
      put(extraPal(cols[k % cols.length]), 'flat', g);
    }
  }
  // shrubs and rocks (instanced)
  const ig = new THREE.IcosahedronGeometry(1, 0);
  const shrubMesh = new THREE.InstancedMesh(ig, new THREE.MeshStandardMaterial({ color: '#4F8F45', roughness: .9, flatShading: true }), D.shrubs.length);
  D.shrubs.forEach(([x, y, z, r], i) => { shrubMesh.setMatrixAt(i, m4.compose(v.set(x, y + r * .4, z), q.identity(), new THREE.Vector3(r, r * .8, r))); });
  shrubMesh.castShadow = true; shrubMesh.receiveShadow = true; scene.add(shrubMesh);
  const dg = new THREE.DodecahedronGeometry(1, 0);
  const rockMesh = new THREE.InstancedMesh(dg, new THREE.MeshStandardMaterial({ color: '#A9A39A', roughness: .95, flatShading: true }), D.rocks.length);
  D.rocks.forEach(([x, y, z, r, s], i) => {
    const R = rng(s + 3);
    e.set(R() * 3, R() * 3, R() * 3); q.setFromEuler(e);
    rockMesh.setMatrixAt(i, m4.compose(v.set(x, y, z), q, new THREE.Vector3(r, r * .7, r * (.8 + R() * .3))));
  });
  rockMesh.castShadow = true; rockMesh.receiveShadow = true; scene.add(rockMesh);

  for (const bk of buckets.values()) {
    const g = mergeGeometries(bk.list, false);
    const mesh = new THREE.Mesh(g, mat(bk.ci, bk.kind));
    mesh.castShadow = bk.cast; mesh.receiveShadow = true;
    if (bk.kind === 'glass') mesh.renderOrder = 2;
    scene.add(mesh);
  }

  // labels: signs, glazing, awnings and the water
  function addLabels() {
    for (const L of D.labels) {
      if (L.k === 'water') {
        const wm = new THREE.MeshStandardMaterial({ color: '#43A9C6', roughness: .12, metalness: .1, transparent: true, opacity: .8 });
        const w = new THREE.Mesh(new THREE.PlaneGeometry(L.w, L.h), wm);
        w.rotation.x = -Math.PI / 2; w.position.set(...L.p); w.receiveShadow = true; w.renderOrder = 1;
        scene.add(w);
        continue;
      }
      const tex = drawLabel(L);
      const lit = L.k === 'glow' || L.k === 'door';
      const transparent = L.k === 'text' || L.k === 'mascot';
      const m = transparent ? new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.DoubleSide })
        : new THREE.MeshStandardMaterial({ map: tex, roughness: L.k === 'glass' ? .15 : .7, metalness: L.k === 'glass' ? .2 : 0,
          emissive: lit ? 0xffffff : 0x000000, emissiveMap: lit ? tex : null, emissiveIntensity: lit ? .55 : 0, side: THREE.DoubleSide });
      m.polygonOffset = true; m.polygonOffsetFactor = -2; m.polygonOffsetUnits = -2;
      const mesh = new THREE.Mesh(new THREE.PlaneGeometry(L.w, L.h), m);
      mesh.position.set(...L.p);
      mesh.rotation.set((L.rx || 0) * D2R, L.ry * D2R, 0, 'YXZ');
      mesh.receiveShadow = !transparent;
      scene.add(mesh);
    }
  }
  const fontsReady = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
  const ready = fontsReady.then(() => { addLabels(); render(); });

  const controls = opt.still ? null : new OrbitControls(cam, canvas);
  if (controls) {
    controls.enableDamping = true;
    controls.dampingFactor = .08;
    controls.maxPolarAngle = Math.PI * .495;
    controls.minDistance = 4;
    controls.maxDistance = 520;
    controls.addEventListener('change', () => requestRender());
  }
  let anim = null, pending = false;
  function render() { renderer.render(scene, cam); }
  function requestRender() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; tick(); });
  }
  function tick() {
    if (anim) {
      const t = Math.min(1, (performance.now() - anim.t0) / anim.ms), k = t * t * (3 - 2 * t);
      cam.position.lerpVectors(anim.p0, anim.p1, k);
      if (controls) controls.target.lerpVectors(anim.q0, anim.q1, k);
      cam.fov = anim.f0 + (anim.f1 - anim.f0) * k; cam.updateProjectionMatrix();
      if (t >= 1) anim = null;
    }
    const moving = controls ? controls.update() : false;
    if (!controls) cam.lookAt(anim ? anim.q1 : cam.userData.tgt);
    render();
    if (anim || moving) requestRender();
  }
  function setView(name, animate = true) {
    const V = D.views[name];
    if (!V) return;
    const p1 = new THREE.Vector3(...V.pos), q1 = new THREE.Vector3(...V.tgt);
    if (!animate || !controls) {
      cam.position.copy(p1); cam.fov = V.fov; cam.updateProjectionMatrix();
      cam.userData.tgt = q1;
      if (controls) { controls.target.copy(q1); controls.update(); } else cam.lookAt(q1);
      render();
      return;
    }
    anim = { t0: performance.now(), ms: 900, p0: cam.position.clone(), p1, q0: controls.target.clone(), q1, f0: cam.fov, f1: V.fov };
    requestRender();
  }
  function resize() {
    const w = canvas.clientWidth || canvas.width, h = canvas.clientHeight || canvas.height;
    renderer.setSize(w, h, false);
    cam.aspect = w / h; cam.updateProjectionMatrix();
    render();
  }
  if (!opt.still && 'ResizeObserver' in window) new ResizeObserver(resize).observe(canvas);
  resize();
  setView(opt.view || 'aerial', false);
  return { setView, render, resize, ready, renderer, scene, camera: cam };
}
