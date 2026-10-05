// Renders the perspective views of the 3D model to img/view_<name>.jpg (sheet P-601).
//   npm i --no-save three@0.160.0 playwright   (once, in this folder)
//   python3 build.py && node render_views.js && python3 build.py
// Uses headless Chromium with software WebGL; CHROME=/path/to/chrome overrides the browser.
const fs = require('fs');
const os = require('os');
const path = require('path');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const HERE = __dirname;
const three = path.join(HERE, 'node_modules', 'three');
const scene = fs.readFileSync(path.join(HERE, 'model', 'scene.json'), 'utf8');
const views = Object.keys(JSON.parse(scene).views);
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'park3d-'));
fs.copyFileSync(path.join(HERE, 'park3d.js'), path.join(tmp, 'park3d.js'));
const W = 1280, H = 720;
fs.writeFileSync(path.join(tmp, 'index.html'), `<!doctype html><meta charset="utf-8">
<style>body{margin:0}canvas{display:block;width:${W}px;height:${H}px}</style><canvas id="c"></canvas>
<script type="importmap">{"imports":{"three":"file://${three}/build/three.module.js","three/addons/":"file://${three}/examples/jsm/"}}</script>
<script id="scene" type="application/json">${scene}</script>
<script type="module">
import { mountPark } from './park3d.js';
const D = JSON.parse(document.getElementById('scene').textContent);
const v = new URLSearchParams(location.search).get('view');
const P = mountPark(document.getElementById('c'), D, { still: true, pixelRatio: 1, view: v });
P.ready.then(() => { P.setView(v, false); P.render(); window.DONE = true; });
</script>`);

(async () => {
  const b = await chromium.launch({
    executablePath: process.env.CHROME || (fs.existsSync('/opt/pw-browsers/chromium-1194/chrome-linux/chrome') ? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' : undefined),
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--allow-file-access-from-files'],
  });
  fs.mkdirSync(path.join(HERE, 'img'), { recursive: true });
  for (const v of views) {
    const p = await b.newPage({ viewport: { width: W, height: H } });
    p.on('pageerror', e => console.error(v, e.message));
    await p.goto('file://' + path.join(tmp, 'index.html') + '?view=' + v);
    await p.waitForFunction(() => window.DONE, null, { timeout: 120000 });
    await p.screenshot({ path: path.join(HERE, 'img', `view_${v}.jpg`), type: 'jpeg', quality: 84 });
    console.log('rendered', v);
    await p.close();
  }
  await b.close();
})();
