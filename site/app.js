import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const CAT_RU = { Weapons: 'Оружие', Props: 'Пропсы', Characters: 'Персонажи', Items: 'Предметы', Models: 'Прочее' };

let filterCat = 'Все', query = '';
let visible = [];
let current = -1;

// ---------- каталог ----------
const grid = document.getElementById('grid');
const catsEl = document.getElementById('cats');

function fmt(t) { return t >= 1000 ? (t / 1000).toFixed(1).replace('.0', '') + 'k' : t; }

function buildCats() {
  const set = ['Все', ...new Set(MODELS.map(m => m.c))];
  catsEl.innerHTML = '';
  for (const c of set) {
    const b = document.createElement('button');
    b.textContent = c === 'Все' ? 'Все' : (CAT_RU[c] || c);
    if (c === filterCat) b.classList.add('on');
    b.onclick = () => { filterCat = c; buildCats(); render(); };
    catsEl.appendChild(b);
  }
}

function render() {
  const q = query.trim().toLowerCase();
  visible = MODELS.filter(m => (filterCat === 'Все' || m.c === filterCat) && (!q || m.n.toLowerCase().includes(q)));
  document.getElementById('count').textContent = visible.length + ' / ' + MODELS.length;
  grid.innerHTML = '';
  for (const m of visible) {
    const card = document.createElement('button');
    card.className = 'card';
    card.innerHTML =
      `<img loading="lazy" src="thumbs/${m.n}.jpg" alt="${m.n}">` +
      `<div class="meta"><span class="nm">${m.n}</span><span class="ct">${CAT_RU[m.c] || m.c} · ${fmt(m.t)}</span></div>`;
    card.onclick = () => open(visible.indexOf(m));
    grid.appendChild(card);
  }
}

document.getElementById('q').addEventListener('input', e => { query = e.target.value; render(); });

// ---------- 3D-вьювер ----------
const viewer = document.getElementById('viewer');
let renderer, scene, camera, controls, modelGroup, gridHelper;
let autoRotate = true, wire = false, currentUrl = '';
const loader = new GLTFLoader();

function initThree() {
  if (renderer) return;
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  viewer.appendChild(renderer.domElement);
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0d0b);
  camera = new THREE.PerspectiveCamera(38, 1, 0.01, 100);
  camera.position.set(2.6, 1.7, 3.0);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 0.9, 0);
  scene.add(new THREE.HemisphereLight(0xe8fff0, 0x1a221c, 1.05));
  const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(3, 5, 2); scene.add(key);
  const rim = new THREE.DirectionalLight(0x9fffc4, 1.2); rim.position.set(-4, 2.5, -3); scene.add(rim);
  gridHelper = new THREE.GridHelper(7, 28, 0x2c4a38, 0x161f19); scene.add(gridHelper);
  modelGroup = new THREE.Group(); scene.add(modelGroup);
  addEventListener('resize', fit);
  const loop = () => {
    requestAnimationFrame(loop);
    if (viewer.classList.contains('hidden')) return;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 1.5;
    controls.update();
    renderer.render(scene, camera);
  };
  loop();
}

function fit() {
  if (!renderer) return;
  const w = viewer.clientWidth, h = viewer.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

function applyWire() {
  modelGroup.traverse(o => {
    if (o.isMesh && o.material) o.material.wireframe = wire;
  });
}

function open(idx) {
  if (idx < 0 || idx >= visible.length) return;
  current = idx;
  const m = visible[idx];
  viewer.classList.remove('hidden');
  initThree(); fit();
  document.getElementById('vname').textContent = m.n;
  document.getElementById('vinfo').textContent =
    `${CAT_RU[m.c] || m.c} · ${m.t.toLocaleString('ru')} трис · ${m.k} КБ`;
  if (currentUrl === m.n) return;
  currentUrl = m.n;
  loader.load(`models/${m.n}.glb`, g => {
    modelGroup.clear();
    const root = g.scene;
    // нормировка: центр по XZ, низ на полу, масштаб под камеру
    const box = new THREE.Box3().setFromObject(root);
    const size = box.getSize(new THREE.Vector3());
    const s = 2.2 / Math.max(size.x, size.y, size.z, 0.0001);
    root.scale.setScalar(s);
    box.setFromObject(root);
    const ctr = box.getCenter(new THREE.Vector3());
    root.position.x -= ctr.x;
    root.position.z -= ctr.z;
    root.position.y -= box.min.y;
    modelGroup.add(root);
    applyWire();
    controls.target.set(0, Math.min(1.1, box.max.y * 0.55), 0);
  });
}

function closeViewer() {
  viewer.classList.add('hidden');
  currentUrl = '';
}

document.getElementById('close').onclick = closeViewer;
document.getElementById('prev').onclick = () => open(current - 1);
document.getElementById('next').onclick = () => open(current + 1);
document.getElementById('autorot').onclick = e => {
  autoRotate = !autoRotate;
  e.currentTarget.classList.toggle('on', autoRotate);
};
document.getElementById('wire').onclick = e => {
  wire = !wire;
  e.currentTarget.classList.toggle('on', wire);
  applyWire();
};
addEventListener('keydown', e => {
  if (viewer.classList.contains('hidden')) return;
  if (e.key === 'Escape') closeViewer();
  else if (e.key === 'ArrowLeft') open(current - 1);
  else if (e.key === 'ArrowRight') open(current + 1);
});

buildCats();
render();
