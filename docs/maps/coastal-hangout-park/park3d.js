// Umi Seaside Park: three.js viewer for the massing model made by model3d.py.
// Plan metres map to x = east, z = south, y = level above sea (±0.00).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { SMAAPass } from 'three/addons/postprocessing/SMAAPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';

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

function heartPath(g, x, y, s) {
  g.beginPath();
  g.moveTo(x, y + s * .55);
  g.bezierCurveTo(x - s * 1.1, y - s * .1, x - s * .5, y - s * .75, x, y - s * .3);
  g.bezierCurveTo(x + s * .5, y - s * .75, x + s * 1.1, y - s * .1, x, y + s * .55);
  g.closePath();
}

function drawMascotAt(g, x0, y0, px) {
  const cols = { O: '#E3AE1F', Y: '#FFE27A', K: '#2E333B', P: '#F59BC3' };
  MASCOT.forEach((row, r) => [...row].forEach((ch, k) => {
    if (cols[ch]) { g.fillStyle = cols[ch]; g.fillRect(x0 + k * px, y0 + r * px, px + 1, px + 1); }
  }));
}

function drawExtra(L, g, W, H) {
  const k = L.k;
  if (k === 'ring') {
    const r = Math.min(W, H) / 2, rm = r * .775, lw = r * .45;
    g.lineWidth = lw; g.strokeStyle = L.fg || '#2E3FB0'; g.lineCap = 'butt';
    g.beginPath(); g.arc(W / 2, H / 2, rm, (80 + 43) * Math.PI / 180, (80 + 360) * Math.PI / 180); g.stroke();
  } else if (k === 'bubble') {
    const p = W * .04, bh = H * .74;
    g.fillStyle = '#fff'; g.strokeStyle = '#2E333B'; g.lineWidth = Math.max(3, W / 60);
    rrectPath(g, p, p, W - 2 * p, bh - p, bh * .25); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(W * .2, bh - 2); g.lineTo(W * .15, H - p); g.lineTo(W * .38, bh - 2); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#fff'; g.fillRect(W * .2, bh - p - 2, W * .17, p + 3);
    g.fillStyle = '#2E333B';
    for (const d of [-1, 0, 1]) { g.beginPath(); g.arc(W / 2 + d * W * .17, (bh + p) / 2, bh * .09, 0, 7); g.fill(); }
  } else if (k === 'vkana') {
    const chars = [...L.txt], cs = Math.min(W * .95, H / chars.length);
    g.fillStyle = L.fg; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.font = `800 ${Math.round(cs * .92)}px "Noto Sans JP", sans-serif`;
    chars.forEach((c, i) => g.fillText(c, W / 2, cs * (i + .5)));
  } else if (k === 'disc') {
    g.fillStyle = L.bg; g.fillRect(0, 0, W, H);
    const cols = Math.max(2, Math.round(W / (H / 4) * 1.0 / 1.0)), rows = 4;
    const cw = W / cols, rh = H / rows, r = Math.min(cw, rh) * .38;
    for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
      const x = (i + .5) * cw, y = (j + .5) * rh, st = (i * 3 + j * 2) % 4;
      g.beginPath(); g.arc(x, y, r, 0, 7);
      g.fillStyle = ['#C9A24A', '#F7F2E6', '#8C99A6', 'rgba(0,0,0,.3)'][st]; g.fill();
      if (st === 1) { g.beginPath(); g.arc(x, y, r * .55, 0, 7); g.fillStyle = L.bg; g.fill(); }
    }
  } else if (k === 'noren') {
    const n = 3, gap = W * .012;
    g.fillStyle = '#B98B5A'; g.fillRect(0, 0, W, H * .06);
    for (let i = 0; i < n; i++) { g.fillStyle = L.bg; g.fillRect(i * W / n + (i ? gap : 0), H * .06, W / n - gap, H * .94); }
    g.strokeStyle = '#fff'; g.lineWidth = H * .07;
    g.beginPath(); g.arc(W / 2, H * .5, H * .24, 0, 7); g.stroke();
    g.fillStyle = '#fff'; g.beginPath(); g.arc(W / 2, H * .5, H * .08, 0, 7); g.fill();
  } else if (k === 'cloud') {
    const lobes = [[-.32, .1, .3], [-.05, -.28, .34], [.28, -.14, .3], [0, .12, .3], [-.3, .14, .22], [.32, .12, .24]];
    for (const [dx, dy, rr] of lobes) { g.fillStyle = '#2E333B'; g.beginPath(); g.ellipse(W / 2 + dx * W * .9, H / 2 + dy * H * .8, rr * W * .9 + 3, rr * H * 1.0 + 3, 0, 0, 7); g.fill(); }
    for (const [dx, dy, rr] of lobes) { g.fillStyle = '#2F8FE8'; g.beginPath(); g.ellipse(W / 2 + dx * W * .9, H / 2 + dy * H * .8, rr * W * .9, rr * H * 1.0, 0, 0, 7); g.fill(); }
    g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `800 ${Math.round(H * .26)}px ${FONT_C}`;
    g.fillText(L.txt, W / 2, H * .52);
  } else if (k === 'redpanel') {
    g.fillStyle = '#E8414E'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#fff'; g.beginPath(); g.arc(W * .3, H * .5, H * .34, 0, 7); g.fill();
    g.fillStyle = '#E8414E'; heartPath(g, W * .3, H * .5, H * .22); g.fill();
    g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `800 ${Math.round(H * .3)}px "Noto Sans JP", sans-serif`;
    g.fillText(L.txt, W * .68, H * .54);
  } else if (k === 'led') {
    g.fillStyle = '#1B1F26'; g.fillRect(0, 0, W, H);
    g.strokeStyle = '#8C99A6'; g.lineWidth = 3; g.strokeRect(4, 4, W - 8, H - 8);
    g.fillStyle = '#FFB547'; g.textBaseline = 'middle'; g.font = `700 ${Math.round(H * .5)}px ${FONT_C}`;
    let x = H * .4;
    while (x < W) { g.fillText(L.txt + ' · ', x, H * .54); x += g.measureText(L.txt + ' · ').width; }
  } else if (k === 'mural') {
    const R = rng((L.seed || 0) + 5);
    g.fillStyle = '#FAF8F3'; g.fillRect(0, 0, W, H);
    for (let i = 0; i < 18; i++) {
      g.globalAlpha = .55; g.fillStyle = ['#F59BC3', '#FFE27A', '#24ABCC', '#B9A2EE', '#A9DCC6'][i % 5];
      g.beginPath(); g.arc(R() * W, R() * H, (.08 + R() * .14) * H, 0, 7); g.fill();
    }
    g.globalAlpha = 1;
    const even = (L.seed || 0) % 2 === 0, tx = W * (even ? .3 : .68), ty = H * .45, s = H * .3;
    g.fillStyle = '#fff'; g.strokeStyle = '#2E333B'; g.lineWidth = 3;
    for (const d of [-1, 1]) { g.beginPath(); g.ellipse(tx + d * s * 1.35, ty - s * .2, s * .75, s * .4, 0, 0, 7); g.fill(); g.stroke(); }
    g.fillStyle = '#A9DCC6'; rrectPath(g, tx - s, ty - s * .8, 2 * s, 1.6 * s, s * .25); g.fill(); g.stroke();
    g.fillStyle = '#2E333B'; rrectPath(g, tx - s * .72, ty - s * .55, 1.44 * s, 1.07 * s, s * .15); g.fill();
    g.fillStyle = '#CBE8EE'; g.fillRect(tx - s * .4, ty - s * .28, s * .16, s * .24); g.fillRect(tx + s * .24, ty - s * .28, s * .16, s * .24);
    g.strokeStyle = '#CBE8EE'; g.beginPath(); g.moveTo(tx - s * .25, ty + s * .2); g.quadraticCurveTo(tx, ty + s * .42, tx + s * .25, ty + s * .2); g.stroke();
    const cx = W * (even ? .7 : .25), cy = H * .75;
    g.fillStyle = '#F59A3A'; g.strokeStyle = '#2E333B';
    g.beginPath(); g.ellipse(cx, cy, H * .34, H * .14, 0, 0, 7); g.fill(); g.stroke();
    g.beginPath(); g.arc(cx + H * .3, cy - H * .08, H * .12, 0, 7); g.fill(); g.stroke();
    g.strokeStyle = '#fff'; g.lineWidth = 4;
    for (let i = 0; i < 4; i++) { g.beginPath(); g.moveTo(cx - H * .2 + i * H * .12, cy - H * .11); g.lineTo(cx - H * .17 + i * H * .12, cy + H * .06); g.stroke(); }
  } else if (k === 'banner') {
    const D_ = {
      umi: ['#2C3E57', '#24ABCC', 'UMI', '#FFFFFF', 'wave'], cafe: ['#FFFFFF', '#7E5234', 'CAFE', '#7E5234', 'cup'],
      games: ['#D8343F', '#F6C833', 'GAMES', '#FFFFFF', 'pad'], omiyage: ['#F6C833', '#E8414E', 'おみやげ', '#2E333B', 'heart'],
      beach: ['#24ABCC', '#FFFFFF', 'BEACH', '#FFFFFF', 'sun'], sakura: ['#F59BC3', '#FFFFFF', 'さくら', '#FFFFFF', 'petal'],
      fes: ['#EE8A6B', '#FFE07A', '夏まつり', '#FFFFFF', 'sun'], shell: ['#A9DCC6', '#FFFFFF', 'SEA', '#2C3E57', 'wave'],
    }[L.d || 'umi'];
    const [bg, acc, txt, fg, icon] = D_;
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
    g.fillStyle = acc; g.strokeStyle = acc; g.lineWidth = W * .06;
    const cx = W / 2, cy = W * .62, r = W * .3;
    if (icon === 'wave') {
      g.beginPath(); for (let x = 0; x <= W; x += 2) g.lineTo(x, cy + Math.sin(x / W * 12) * r * .35); g.stroke();
      g.beginPath(); for (let x = 0; x <= W; x += 2) g.lineTo(x, cy + r * .6 + Math.sin(x / W * 12 + 1) * r * .35); g.stroke();
    } else if (icon === 'cup') {
      g.beginPath(); g.arc(cx, cy, r, 0, 7); g.fill(); g.fillStyle = bg; rrectPath(g, cx - r * .45, cy - r * .2, r * .7, r * .55, r * .1); g.fill();
    } else if (icon === 'pad') {
      g.fillRect(cx - r * .9, cy - r * .3, r * 1.8, r * .6); g.fillRect(cx - r * .3, cy - r * .9, r * .6, r * 1.8);
    } else if (icon === 'heart') {
      heartPath(g, cx, cy, r); g.fill();
    } else if (icon === 'sun') {
      g.beginPath(); g.arc(cx, cy, r * .7, 0, 7); g.fill();
      for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; g.beginPath(); g.moveTo(cx + Math.cos(a) * r * .85, cy + Math.sin(a) * r * .85); g.lineTo(cx + Math.cos(a) * r * 1.2, cy + Math.sin(a) * r * 1.2); g.stroke(); }
    } else {
      for (let i = 0; i < 5; i++) { const a = i * 1.2566; g.beginPath(); g.ellipse(cx + Math.cos(a) * r * .5, cy + Math.sin(a) * r * .5, r * .32, r * .2, a, 0, 7); g.fill(); }
    }
    g.fillStyle = fg; g.textAlign = 'center'; g.textBaseline = 'middle';
    const chars = [...txt];
    if (txt.length <= 4 || !/^[A-Z]+$/.test(txt)) {
      const cs = Math.min(W * .62, (H - W * 1.2) / chars.length * .95);
      g.font = `800 ${Math.round(cs)}px "Noto Sans JP", ${FONT_C}`;
      chars.forEach((c, i) => g.fillText(c, W / 2, W * 1.15 + cs * (i + .55)));
    } else {
      g.save(); g.translate(W / 2, H * .62); g.rotate(-Math.PI / 2);
      g.font = `800 ${Math.round(W * .5)}px ${FONT_C}`; g.fillText(txt, 0, 0); g.restore();
    }
    g.strokeStyle = 'rgba(0,0,0,.25)'; g.lineWidth = 3; g.strokeRect(1.5, 1.5, W - 3, H - 3);
  } else if (k === 'plaque') {
    g.fillStyle = '#1B1F26'; g.fillRect(0, 0, W, H);
    g.strokeStyle = '#C9A24A'; g.lineWidth = H * .05; g.strokeRect(H * .08, H * .08, W - H * .16, H - H * .16);
    g.fillStyle = '#C9A24A'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.font = `800 ${Math.round(H * .42)}px "Noto Sans JP", sans-serif`; g.fillText(L.txt, W / 2, H * .42);
    g.font = `700 ${Math.round(H * .16)}px ${FONT_C}`; g.fillText(L.sub || '', W / 2, H * .78);
  } else if (k === 'hsign') {
    g.fillStyle = '#fff'; g.fillRect(0, 0, W, H);
    g.strokeStyle = '#2E333B'; g.lineWidth = W * .08; g.strokeRect(W * .08, W * .08, W * .84, H - W * .16);
    const chars = [...L.txt], cs = Math.min(W * .7, (H - W * .4) / chars.length);
    g.fillStyle = '#2E333B'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `700 ${Math.round(cs * .9)}px "Noto Sans JP", sans-serif`;
    chars.forEach((c, i) => g.fillText(c, W / 2, W * .2 + cs * (i + .5)));
  } else if (k === 'heart') {
    g.fillStyle = '#E8414E'; g.strokeStyle = '#2E333B'; g.lineWidth = 4;
    heartPath(g, W / 2, H / 2, H * .55); g.fill(); g.stroke();
    g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `800 ${Math.round(H * .2)}px "Noto Sans JP", sans-serif`;
    g.fillText('すき', W / 2, H * .45);
  } else if (k === 'cafesign') {
    g.fillStyle = '#8A5C3A'; g.fillRect(0, 0, W, H);
    g.strokeStyle = 'rgba(0,0,0,.18)'; g.lineWidth = 2;
    for (let y = H / 8; y < H; y += H / 8) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
    const r = H * .34, cx = H * .75;
    g.fillStyle = '#fff'; g.beginPath(); g.arc(cx, H / 2, r, 0, 7); g.fill();
    g.fillStyle = '#2E333B'; rrectPath(g, cx - r * .4, H / 2 - r * .1, r * .66, r * .52, r * .1); g.fill();
    g.strokeStyle = '#2E333B'; g.lineWidth = r * .08; g.beginPath(); g.arc(cx + r * .3, H / 2 + r * .14, r * .14, 0, 7); g.stroke();
    if (L.txt) {
      g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `700 ${Math.round(H * .44)}px ${FONT_C}`;
      g.fillText(L.txt, W / 2 + H * .4, H * .54);
    }
  } else if (k === 'pier') {
    g.fillStyle = '#FAF8F3'; g.fillRect(0, 0, W, H);
    g.strokeStyle = 'rgba(0,0,0,.12)'; g.lineWidth = 2;
    for (let y = H / 5; y < H; y += H / 5) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
    g.fillStyle = '#2E333B'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `700 ${Math.round(W * .17)}px "Noto Sans JP", sans-serif`;
    ['コーヒー', 'スイーツ', 'やすらぎ'].forEach((t, i) => g.fillText(t, W / 2, H * (.22 + i * .13)));
    g.fillStyle = '#2F8FE8'; g.beginPath(); g.moveTo(W * .2, H * .82); g.quadraticCurveTo(W * .35, H * .68, W * .55, H * .72);
    g.quadraticCurveTo(W * .75, H * .76, W * .7, H * .84); g.quadraticCurveTo(W * .6, H * .78, W * .52, H * .84);
    g.quadraticCurveTo(W * .7, H * .9, W * .82, H * .82); g.lineTo(W * .82, H * .88); g.lineTo(W * .2, H * .88); g.closePath(); g.fill();
  } else if (k === 'tunnel') {
    g.fillStyle = '#9AA3AD'; g.fillRect(0, 0, W, H);
    g.fillStyle = '#14171C'; g.beginPath(); g.moveTo(W * .12, H); g.lineTo(W * .12, H * .45);
    g.quadraticCurveTo(W * .5, -H * .05, W * .88, H * .45); g.lineTo(W * .88, H); g.closePath(); g.fill();
    g.fillStyle = '#FFB547';
    for (let i = 0; i < 5; i++) { g.beginPath(); g.arc(W * (.25 + i * .125), H * .32, W * .012, 0, 7); g.fill(); }
  } else return false;
  return true;
}

function drawLabel(L) {
  const ppm = L.k === 'text' || L.k === 'pill' ? 160 : L.k === 'mascot' ? 40 : ['vkana', 'hsign', 'heart', 'plaque', 'bubble', 'ring', 'cloud', 'redpanel', 'cafesign', 'pier'].includes(L.k) ? 120 : 64;
  const c = canvasFor(L.w, L.h, ppm);
  const g = c.getContext('2d');
  const W = c.width, H = c.height;
  if (drawExtra(L, g, W, H)) {
    // drawn by drawExtra
  } else if (L.k === 'text') {
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


// ------------------------------------------------------------------ procedural PBR textures
// Each material kind gets a tileable height field (canvas) that becomes the albedo modulation,
// a normal map and a roughness map. UVs are world-space metres; repeat = 1 / tile size.
const TEX_N = 512;
function noiseField(n, seed, oct = 4) {
  const R = rng(seed), f = new Float32Array(n * n);
  for (let o = 0; o < oct; o++) {
    const g = 4 << o, amp = 1 / (1 << o), grid = new Float32Array((g + 1) * (g + 1));
    for (let i = 0; i < grid.length; i++) grid[i] = R();
    for (let j = 0; j <= g; j++) grid[j * (g + 1) + g] = grid[j * (g + 1)];
    for (let i = 0; i <= g; i++) grid[g * (g + 1) + i] = grid[i];
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const gx = x / n * g, gy = y / n * g, ix = Math.floor(gx), iy = Math.floor(gy), fx = gx - ix, fy = gy - iy;
      const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
      const a = grid[iy * (g + 1) + ix], b = grid[iy * (g + 1) + ix + 1], c = grid[(iy + 1) * (g + 1) + ix], d = grid[(iy + 1) * (g + 1) + ix + 1];
      f[y * n + x] += amp * (a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy);
    }
  }
  let mn = 1e9, mx = -1e9;
  for (const v of f) { mn = Math.min(mn, v); mx = Math.max(mx, v); }
  for (let i = 0; i < f.length; i++) f[i] = (f[i] - mn) / (mx - mn);
  return f;
}

const TEX_KINDS = {
  // size: metres per tile; h(x, y, nz): height 0..1 at texel; tone: albedo modulation range; rough: [base, var]
  std: { size: 2.0, rough: [.72, .1], tone: .06 },
  paint: { size: 2.0, rough: [.45, .08], tone: .04 },
  plaster: { size: 2.5, rough: [.92, .06], tone: .07 },
  clad: { size: 1.4, rough: [.55, .06], tone: .05, lines: 'h', pitch: .7, w: .012 },
  panel: { size: 3.6, rough: [.6, .08], tone: .06, grid: [.9, 1.8], w: .006 },
  conc: { size: 2.4, rough: [.88, .08], tone: .1, grid: [2.4, 1.2], w: .004, pits: true },
  stone: { size: 2.4, rough: [.85, .1], tone: .14, bond: [.6, .3], w: .02 },
  timber: { size: 1.2, rough: [.62, .12], tone: .2, lines: 'h', pitch: .15, w: .01, grain: 'h' },
  timberv: { size: 1.2, rough: [.62, .12], tone: .2, lines: 'v', pitch: .12, w: .01, grain: 'v' },
  deck: { size: 1.8, rough: [.7, .12], tone: .22, lines: 'v', pitch: .14, w: .012, grain: 'v', ends: true },
  metal: { size: .8, rough: [.32, .08], tone: .05, metal: .7, brushed: true },
  groove: { size: .4, rough: [.35, .05], tone: .25, metal: .7, lines: 'v', pitch: .01, w: .004 },
  kawara: { size: 1.0, rough: [.32, .06], tone: .1, tiles: 'v' },
  kawarar: { size: 1.0, rough: [.32, .06], tone: .1, tiles: 'h' },
  thatch: { size: 1.0, rough: [.95, .03], tone: .3, straw: true },
  facade: { size: 3.2, rough: [.6, .1], tone: .05, facade: true },
  gloss: { size: 2.0, rough: [.25, .05], tone: .02 },
  rubber: { size: 1.0, rough: [.75, .05], tone: .04 },
};

function makeTex(kind) {
  const K = TEX_KINDS[kind] || TEX_KINDS.std, n = TEX_N;
  const h = new Float32Array(n * n), alb = new Float32Array(n * n);
  const nz = noiseField(n, kind.length * 31 + 7, 5), nz2 = noiseField(n, kind.length * 17 + 3, 3);
  const px = K.size / n;  // metres per texel
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const i = y * n + x, mx = x * px, my = y * px;
    let hv = .5 + (nz[i] - .5) * .25, av = 1 - K.tone * (1 - nz[i]);
    if (K.lines) {
      const c = K.lines === 'h' ? my : mx, d = Math.abs(((c + K.pitch / 2) % K.pitch) - K.pitch / 2);
      if (d < K.w) { hv -= .55 * (1 - d / K.w); av *= .72; }
      if (K.grain) {
        const along = K.grain === 'h' ? mx : my, across = K.grain === 'h' ? my : mx;
        const board = Math.floor(across / K.pitch);
        const g = Math.sin((along * 9 + nz2[i] * 6 + board * 3.1) * 2.2) * .5 + .5;
        av *= 1 - K.tone * .55 * g - K.tone * .25 * ((board * 7919) % 5) / 5;
        hv += (g - .5) * .06;
        if (K.ends) {
          const e = (along + ((board * 1.37) % 1) * K.size) % (K.size / 2);
          if (e < .006) { hv -= .4; av *= .75; }
        }
      }
    }
    if (K.grid) {
      const dx = Math.abs(((mx + K.grid[0] / 2) % K.grid[0]) - K.grid[0] / 2), dy = Math.abs(((my + K.grid[1] / 2) % K.grid[1]) - K.grid[1] / 2);
      if (dx < K.w || dy < K.w) { hv -= .4; av *= .82; }
      if (K.pits && nz2[i] > .93) { hv -= .3; av *= .9; }
    }
    if (K.bond) {
      const row = Math.floor(my / K.bond[1]), off = (row % 2) * K.bond[0] / 2;
      const dx = Math.abs(((mx + off + K.bond[0] / 2) % K.bond[0]) - K.bond[0] / 2), dy = Math.abs(((my + K.bond[1] / 2) % K.bond[1]) - K.bond[1] / 2);
      const blk = ((Math.floor((mx + off) / K.bond[0]) * 31 + row * 17) % 7) / 7;
      av *= 1 - K.tone * blk * .6;
      if (dx < K.w || dy < K.w) { hv -= .5; av *= .78; } else hv += .1 * Math.min(1, Math.min(dx, dy) / .05);
    }
    if (K.brushed) { av *= 1 - .05 * Math.sin(my * 900 + nz2[i] * 20); }
    if (K.tiles) {
      // pantiles: channels with rounded caps; courses every 0.28 m
      const across = K.tiles === 'v' ? mx : my, along = K.tiles === 'v' ? my : mx;
      const w = .3, t = ((across % w) + w) % w / w, crs = ((along % .28) + .28) % .28 / .28;
      hv = .5 + .45 * Math.sin(t * Math.PI) - .25 * (crs > .9 ? (crs - .9) * 10 : 0);
      av = (.8 + .2 * Math.sin(t * Math.PI)) * (crs > .92 ? .7 : 1) * (1 - .06 * nz[i]);
    }
    if (K.straw) {
      const s2 = Math.sin(mx * 160 + nz[i] * 12) * .5 + .5, crs = ((my % .2) + .2) % .2 / .2;
      hv = .4 + .4 * s2 * (1 - crs * .5); av = (.75 + .25 * s2) * (crs > .85 ? .75 : 1);
    }
    if (K.facade) {
      // background town facade: 3.2 m floors, 1.6 m window bays with frames and a sill
      const bx = ((mx % 1.6) + 1.6) % 1.6, fy = ((my % 3.2) + 3.2) % 3.2;
      const win = bx > .25 && bx < 1.35 && fy > .9 && fy < 2.6;
      if (win) { av = .32 + .25 * (1 - fy / 3.2) + .1 * nz2[i]; hv = .2; }
      else if (bx > .2 && bx < 1.4 && fy > .82 && fy < .9) { av *= .85; hv = .8; }
    }
    h[i] = Math.max(0, Math.min(1, hv)); alb[i] = Math.max(0, Math.min(1.1, av));
  }
  const mk = (fill) => {
    const c = document.createElement('canvas'); c.width = c.height = n;
    const g = c.getContext('2d'), im = g.createImageData(n, n);
    for (let i = 0; i < n * n; i++) { const [r, gg, b] = fill(i); im.data[i * 4] = r; im.data[i * 4 + 1] = gg; im.data[i * 4 + 2] = b; im.data[i * 4 + 3] = 255; }
    g.putImageData(im, 0, 0);
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8;
    t.repeat.set(1 / K.size, 1 / K.size);
    return t;
  };
  const map = mk(i => { const v = Math.min(255, alb[i] * 255); return [v, v, v]; });
  map.colorSpace = THREE.SRGBColorSpace;
  const str = kind === 'kawara' || kind === 'kawarar' ? 5 : kind === 'stone' || kind === 'deck' || kind === 'thatch' ? 3 : 1.8;
  const normal = mk(i => {
    const x = i % n, y = (i / n) | 0;
    const hx = h[y * n + (x + 1) % n] - h[y * n + (x + n - 1) % n], hy = h[((y + 1) % n) * n + x] - h[((y + n - 1) % n) * n + x];
    const v = new THREE.Vector3(-hx * str, hy * str, 1).normalize();
    return [(v.x * .5 + .5) * 255, (v.y * .5 + .5) * 255, (v.z * .5 + .5) * 255];
  });
  const rough = mk(i => { const v = Math.min(255, (K.rough[0] + K.rough[1] * (1 - h[i])) * 255); return [v, v, v]; });
  return { map, normal, rough, K };
}
const texCache = new Map();
function texFor(kind) { if (!texCache.has(kind)) texCache.set(kind, makeTex(kind)); return texCache.get(kind); }

// world-space UVs in metres, projected per triangle on its dominant axis
function worldUV(g) {
  const p = g.attributes.position, n = p.count, uv = new Float32Array(n * 2);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), e1 = new THREE.Vector3(), e2 = new THREE.Vector3();
  for (let i = 0; i < n; i += 3) {
    a.fromBufferAttribute(p, i); b.fromBufferAttribute(p, i + 1); c.fromBufferAttribute(p, i + 2);
    e1.subVectors(b, a); e2.subVectors(c, a); e1.cross(e2);
    const ax = Math.abs(e1.x), ay = Math.abs(e1.y), az = Math.abs(e1.z);
    for (let k = 0; k < 3; k++) {
      const v = k === 0 ? a : k === 1 ? b : c;
      let u, w;
      if (ay >= ax && ay >= az) { u = v.x; w = v.z; } else if (ax >= az) { u = v.z; w = v.y; } else { u = v.x; w = v.y; }
      uv[(i + k) * 2] = u; uv[(i + k) * 2 + 1] = w;
    }
  }
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

function flipWinding(g) {
  const p = g.attributes.position.array;
  for (let i = 0; i < p.length; i += 9) for (let k = 0; k < 3; k++) { const t = p[i + 3 + k]; p[i + 3 + k] = p[i + 6 + k]; p[i + 6 + k] = t; }
  g.attributes.position.needsUpdate = true;
}

const BEVEL_KINDS = new Set(['std', 'paint', 'plaster', 'clad', 'panel', 'conc', 'stone', 'timber', 'timberv', 'deck', 'metal', 'gloss', 'rubber', 'facade']);

// plate: polygon in plan with a top height per vertex; bottom parallel (t) or flat (bot)
function plateGeom(pts, tops, t, bot) {
  const key = (x, z) => x.toFixed(2) + ',' + z.toFixed(2);
  const m = new Map();
  pts.forEach(([x, z], i) => m.set(key(x, z), tops[i]));
  const Y = (x, z) => {
    const v = m.get(key(x, z));
    if (v !== undefined) return v;
    let bi = 0, bd = 1e9;
    pts.forEach(([px, pz], i) => { const d = (px - x) ** 2 + (pz - z) ** 2; if (d < bd) { bd = d; bi = i; } });
    return tops[bi];
  };
  const B = (x, z) => (t != null ? Y(x, z) - t : bot);
  const sg = new THREE.ShapeGeometry(new THREE.Shape(pts.map(([x, z]) => new THREE.Vector2(x, z))));
  const p = sg.attributes.position, idx = sg.index.array, out = [];
  for (let i = 0; i < idx.length; i += 3) {
    for (const k of [idx[i], idx[i + 2], idx[i + 1]]) { const x = p.getX(k), z = p.getY(k); out.push(x, Y(x, z), z); }
    for (const k of [idx[i], idx[i + 1], idx[i + 2]]) { const x = p.getX(k), z = p.getY(k); out.push(x, B(x, z), z); }
  }
  for (let i = 0; i < pts.length; i++) {
    const [x0, z0] = pts[i], [x1, z1] = pts[(i + 1) % pts.length];
    const h0 = tops[i], h1 = tops[(i + 1) % pts.length], b0 = t != null ? h0 - t : bot, b1 = t != null ? h1 - t : bot;
    out.push(x0, h0, z0, x1, h1, z1, x1, b1, z1, x0, h0, z0, x1, b1, z1, x0, b0, z0);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(out, 3));
  g.computeVertexNormals();
  return g;
}

export function mountPark(canvas, D, opt = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: !!opt.still, powerPreference: 'high-performance' });
  const PR = opt.pixelRatio || Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(PR);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = .82;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.background = skyTexture();
  scene.fog = new THREE.Fog(0xDCEEF8, 320, 950);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const envTex = pmrem.fromScene(new RoomEnvironment(renderer), .04).texture;
  scene.environment = envTex;
  const cam = new THREE.PerspectiveCamera(50, 16 / 9, .3, 2000);
  const C = new THREE.Vector3(...D.center);
  scene.add(new THREE.HemisphereLight(0xDDEEFF, 0xB09A7C, .6));
  const sun = new THREE.DirectionalLight(0xFFEBD0, 3.1);
  sun.position.copy(C).add(new THREE.Vector3(...D.sun));
  sun.target.position.copy(C);
  sun.castShadow = true;
  const sm = opt.shadow || 4096;
  sun.shadow.mapSize.set(sm, sm);
  Object.assign(sun.shadow.camera, { left: -135, right: 135, top: 135, bottom: -135, near: 20, far: 520 });
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.25;
  scene.add(sun, sun.target);

  const matCache = new Map();
  const ENV = .42;
  function mat(ci, kind) {
    const key = ci + ':' + kind;
    if (matCache.has(key)) return matCache.get(key);
    const color = new THREE.Color(D.pal[ci]);
    let m;
    if (kind === 'glass') {
      m = new THREE.MeshStandardMaterial({ color, roughness: .04, metalness: .35, transparent: true, opacity: .38, depthWrite: false, envMapIntensity: 1.4 });
    } else if (kind === 'led') {
      m = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 1.6, roughness: .4 });
    } else if (kind === 'flat' || kind === 'soft') {
      m = new THREE.MeshStandardMaterial({ color, roughness: .88, metalness: 0, side: THREE.DoubleSide, flatShading: kind === 'flat', envMapIntensity: .35 });
      if (kind === 'soft') { m.polygonOffset = true; m.polygonOffsetFactor = 1; m.polygonOffsetUnits = 3; }
    } else if (kind === 'ground') {
      m = new THREE.MeshStandardMaterial({ color, roughness: .9, metalness: 0, side: THREE.DoubleSide, envMapIntensity: .35 });
    } else {
      const T = texFor(kind);
      m = new THREE.MeshStandardMaterial({ color, map: T.map, normalMap: T.normal, roughnessMap: T.rough, roughness: 1,
        metalness: T.K.metal || 0, envMapIntensity: ENV, side: THREE.DoubleSide });
      m.normalScale.set(1, 1);
    }
    matCache.set(key, m);
    return m;
  }
  const buckets = new Map();
  function put(ci, kind, geom, cast = true) {
    const key = ci + ':' + kind + ':' + (cast ? 1 : 0);
    if (!buckets.has(key)) buckets.set(key, { ci, kind, cast, list: [] });
    let g = geom.index ? geom.toNonIndexed() : geom;
    for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
    if (!g.attributes.normal) g.computeVertexNormals();
    worldUV(g);
    buckets.get(key).list.push(g);
  }
  const groundKind = k => (k === 'std' ? 'ground' : k);

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
    put(s.c, groundKind(s.m), top, false);
    put(s.c, groundKind(s.m), skirt, false);
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
    const mn = Math.min(sx, sy, sz);
    const g = (BEVEL_KINDS.has(kind) && mn >= .1) ? new RoundedBoxGeometry(sx, sy, sz, 1, Math.min(.035, mn * .22)) : new THREE.BoxGeometry(sx, sy, sz);
    e.set(rx * D2R, ry * D2R, 0, 'YXZ'); q.setFromEuler(e);
    g.applyMatrix4(m4.compose(v.set(cx, cy, cz), q, one));
    put(ci, kind, g, kind !== 'glass');
  }
  for (const c of D.cyls) {
    const [x, y, z, r0, r1, h, ci, axis, seg, kind] = c;
    if (axis === 's') {
      const sg = new THREE.SphereGeometry(r0, 18, 12);
      if (h) sg.scale(1, h / (2 * r0), 1);
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
  // tubes between two points (rails, posts, wheels, handrails)
  const up = new THREE.Vector3(0, 1, 0), dir = new THREE.Vector3();
  for (const s of D.segs || []) {
    const [x0, y0, z0, x1, y1, z1, r, ci, seg, kind] = s;
    dir.set(x1 - x0, y1 - y0, z1 - z0);
    const L = dir.length();
    if (L < 1e-4) continue;
    const g = new THREE.CylinderGeometry(r, r, L, seg, 1, false);
    q.setFromUnitVectors(up, dir.normalize());
    g.applyMatrix4(m4.compose(v.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), q, one));
    put(ci, kind, g, kind !== 'glass');
  }
  // extrusions of a 2D profile: plane 'xy' extrudes along +z from off, 'zy' along +x from off
  for (const x of D.exts || []) {
    const [plane, pts, off, depth, ci, kind, bev] = x;
    const shape = new THREE.Shape(pts.map(([a, b]) => new THREE.Vector2(a, b)));
    const g = new THREE.ExtrudeGeometry(shape, { depth: Math.max(.001, depth - 2 * bev), bevelEnabled: bev > 0, bevelSize: bev, bevelThickness: bev, bevelSegments: 2, curveSegments: 6 });
    g.translate(0, 0, bev);
    if (plane === 'xy') g.translate(0, 0, off);
    else { g.applyMatrix4(new THREE.Matrix4().set(0, 0, 1, off, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1)); flipWinding(g); g.computeVertexNormals(); }
    put(ci, kind, g);
  }
  for (const pl of D.plates || []) {
    const [pts, tops, t, bot, ci, kind] = pl;
    put(ci, kind, plateGeom(pts, tops, t, bot));
  }
  // tori (ring logo, portholes): centre, R, r, arc, in-plane rotation, facing ry
  for (const t of D.tori || []) {
    const [x, y, z, R, r, arc, rz, ry, ci, kind] = t;
    const g = new THREE.TorusGeometry(R, r, 14, 48, arc * D2R);
    g.rotateZ(rz * D2R); g.rotateY(ry * D2R); g.translate(x, y, z);
    put(ci, kind, g);
  }
  // terrain: hills that wall the map, coloured by height and slope
  if (D.terrain) {
    const T = D.terrain, nx = T.nx, nz = T.nz;
    const pos = new Float32Array(nx * nz * 3), col = new Float32Array(nx * nz * 3);
    const hAt = (i, j) => T.h[j * nx + i] / 10;
    const grass = new THREE.Color('#7DB560'), grass2 = new THREE.Color('#5E9A4A'), rock = new THREE.Color('#A39C92'),
      sand = new THREE.Color('#EFE6CC'), c = new THREE.Color();
    for (let j = 0; j < nz; j++) for (let i = 0; i < nx; i++) {
      const k = j * nx + i, h = hAt(i, j);
      pos[k * 3] = T.x0 + i * T.d; pos[k * 3 + 1] = h; pos[k * 3 + 2] = T.z0 + j * T.d;
      const gx = (hAt(Math.min(i + 1, nx - 1), j) - hAt(Math.max(i - 1, 0), j)) / (2 * T.d);
      const gz = (hAt(i, Math.min(j + 1, nz - 1)) - hAt(i, Math.max(j - 1, 0))) / (2 * T.d);
      const slope = Math.hypot(gx, gz);
      if (h < 1.2) c.copy(sand);
      else c.copy(grass).lerp(grass2, Math.min(1, h / 40)).lerp(rock, Math.min(1, Math.max(0, (slope - .85) / .6)));
      col[k * 3] = c.r; col[k * 3 + 1] = c.g; col[k * 3 + 2] = c.b;
    }
    const idx = [];
    for (let j = 0; j < nz - 1; j++) for (let i = 0; i < nx - 1; i++) {
      const a = j * nx + i, b = a + 1, c2 = a + nx, d2 = c2 + 1;
      if (Math.max(T.h[a], T.h[b], T.h[c2], T.h[d2]) < -25) continue;
      idx.push(a, c2, b, b, c2, d2);
    }
    const tg = new THREE.BufferGeometry();
    tg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    tg.setAttribute('color', new THREE.BufferAttribute(col, 3));
    tg.setIndex(idx);
    tg.computeVertexNormals();
    const tm = new THREE.Mesh(tg, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .95, flatShading: true, envMapIntensity: .3 }));
    tm.receiveShadow = true; tm.castShadow = true;
    scene.add(tm);
  }
  // trees, sakura, palms (placeholders: the engine supplies the real ones)
  const TREE = ['#6DAA55', '#5B9A49', '#78B35E'], SAK = ['#F4B8D1', '#F7C8DC'], PALM = '#5E9A4A', TRUNK = '#8A6A4A';
  const extraPal = c => { let i = D.pal.indexOf(c); if (i < 0) { D.pal.push(c); i = D.pal.length - 1; } return i; };
  for (const t of D.trees) {
    const [x, y, z, r, h, kind, seed] = t;
    const R = rng(seed + 11);
    if (kind === 'p') {
      const lean = (R() - .5) * .8;
      const tg = new THREE.CylinderGeometry(.16, .24, h, 7);
      tg.translate(0, h / 2, 0); tg.rotateZ(lean * .12); tg.translate(x, y, z);
      put(extraPal(TRUNK), 'flat', tg);
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
    put(extraPal(TRUNK), 'flat', tg);
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
  const ig = new THREE.IcosahedronGeometry(1, 0);
  const shrubMesh = new THREE.InstancedMesh(ig, new THREE.MeshStandardMaterial({ color: '#4F8F45', roughness: .9, flatShading: true, envMapIntensity: .3 }), D.shrubs.length);
  D.shrubs.forEach(([x, y, z, r], i) => { shrubMesh.setMatrixAt(i, m4.compose(v.set(x, y + r * .4, z), q.identity(), new THREE.Vector3(r, r * .8, r))); });
  shrubMesh.castShadow = true; shrubMesh.receiveShadow = true; scene.add(shrubMesh);
  const dg = new THREE.DodecahedronGeometry(1, 0);
  const rockMesh = new THREE.InstancedMesh(dg, new THREE.MeshStandardMaterial({ color: '#A9A39A', roughness: .95, flatShading: true, envMapIntensity: .3 }), D.rocks.length);
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
        const wm = new THREE.MeshStandardMaterial({ color: '#3FA6C4', roughness: .08, metalness: .15, transparent: true, opacity: .82, envMapIntensity: 1.1 });
        const w = new THREE.Mesh(new THREE.PlaneGeometry(L.w, L.h), wm);
        w.rotation.x = -Math.PI / 2; w.position.set(...L.p); w.receiveShadow = true; w.renderOrder = 1;
        scene.add(w);
        continue;
      }
      const tex = drawLabel(L);
      const lit = L.k === 'glow' || L.k === 'door' || L.k === 'led';
      const transparent = ['text', 'mascot', 'ring', 'bubble', 'vkana', 'cloud', 'heart'].includes(L.k);
      const m = transparent ? new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.DoubleSide })
        : new THREE.MeshStandardMaterial({ map: tex, roughness: L.k === 'glass' ? .15 : .7, metalness: L.k === 'glass' ? .2 : 0,
          emissive: lit ? 0xffffff : 0x000000, emissiveMap: lit ? tex : null, emissiveIntensity: lit ? .55 : 0, side: THREE.DoubleSide, envMapIntensity: .5 });
      m.polygonOffset = true; m.polygonOffsetFactor = -2; m.polygonOffsetUnits = -2;
      const mesh = new THREE.Mesh(new THREE.PlaneGeometry(L.w, L.h), m);
      mesh.position.set(...L.p);
      mesh.rotation.set((L.rx || 0) * D2R, L.ry * D2R, 0, 'YXZ');
      mesh.receiveShadow = !transparent;
      scene.add(mesh);
    }
  }
  // extruded 3D lettering (Latin signs); Japanese stays on painted panels
  function addText(font) {
    for (const t of D.texts || []) {
      const [txt, x, y, z, size, depth, ry, ci, kind, align] = t;
      const g = new TextGeometry(txt, { font, size, height: depth, curveSegments: 4, bevelEnabled: true, bevelThickness: depth * .15, bevelSize: size * .02, bevelSegments: 1 });
      g.computeBoundingBox();
      const bb = g.boundingBox, w = bb.max.x - bb.min.x;
      g.translate(align === 'l' ? -bb.min.x : -bb.min.x - w / 2, -bb.min.y, 0);
      g.rotateY(ry * D2R); g.translate(x, y, z);
      const mesh = new THREE.Mesh(g, mat(ci, kind));
      mesh.castShadow = true; mesh.receiveShadow = true;
      scene.add(mesh);
    }
  }
  const fontsReady = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
  const fontP = (D.texts && D.texts.length) ? new Promise(res => new FontLoader().load(opt.fontUrl ||
    'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/fonts/helvetiker_bold.typeface.json', f => { addText(f); res(); }, undefined, () => res())) : Promise.resolve();
  const ready = Promise.all([fontsReady.then(addLabels), fontP]).then(() => render());

  // post: ambient occlusion, tone mapping, anti-aliasing
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, cam));
  const ao = new GTAOPass(scene, cam, 16, 16);
  ao.blendIntensity = 1.0;
  ao.updateGtaoMaterial({ radius: .9, distanceExponent: 1.6, thickness: 1.2, scale: 1, samples: 16 });
  ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16 });
  composer.addPass(ao);
  composer.addPass(new OutputPass());
  const smaa = new SMAAPass(16, 16);
  composer.addPass(smaa);

  const controls = opt.still ? null : new OrbitControls(cam, canvas);
  if (controls) {
    controls.enableDamping = true;
    controls.dampingFactor = .08;
    controls.maxPolarAngle = Math.PI * .495;
    controls.minDistance = 3;
    controls.maxDistance = 520;
    controls.addEventListener('change', () => requestRender(true));
  }
  let anim = null, pending = false, idle = null;
  // full quality when still; a plain pass while the camera moves keeps orbiting smooth
  function render(fast = false) { if (fast) { renderer.render(scene, cam); } else composer.render(); }
  function requestRender(fast = false) {
    clearTimeout(idle);
    if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; tick(fast); }); }
    idle = setTimeout(() => render(false), 180);
  }
  function tick(fast) {
    if (anim) {
      const t = Math.min(1, (performance.now() - anim.t0) / anim.ms), k = t * t * (3 - 2 * t);
      cam.position.lerpVectors(anim.p0, anim.p1, k);
      if (controls) controls.target.lerpVectors(anim.q0, anim.q1, k);
      cam.fov = anim.f0 + (anim.f1 - anim.f0) * k; cam.updateProjectionMatrix();
      if (t >= 1) anim = null;
    }
    const moving = controls ? controls.update() : false;
    render(true);
    if (anim || moving) requestRender(true);
  }
  function setView(name, animate = true) {
    const V = D.views[name];
    if (!V) return;
    const p1 = new THREE.Vector3(...V.pos), q1 = new THREE.Vector3(...V.tgt);
    if (!animate || !controls) {
      cam.position.copy(p1); cam.fov = V.fov; cam.updateProjectionMatrix();
      if (controls) { controls.target.copy(q1); controls.update(); } else cam.lookAt(q1);
      render();
      return;
    }
    anim = { t0: performance.now(), ms: 900, p0: cam.position.clone(), p1, q0: controls.target.clone(), q1, f0: cam.fov, f1: V.fov };
    requestRender(true);
  }
  function resize() {
    const w = canvas.clientWidth || canvas.width, h = canvas.clientHeight || canvas.height;
    renderer.setSize(w, h, false);
    composer.setSize(w, h);
    cam.aspect = w / h; cam.updateProjectionMatrix();
    render();
  }
  if (!opt.still && 'ResizeObserver' in window) new ResizeObserver(resize).observe(canvas);
  resize();
  setView(opt.view || 'aerial', false);
  return { setView, render, resize, ready, renderer, scene, camera: cam };
}
