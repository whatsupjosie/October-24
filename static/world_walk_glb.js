/* PubCast world walk: GLB avatars.
 *
 * Loads any rigged GLB, stands it on the floor point the walker gives it, scales it to exactly the pixel
 * height the picture's size rule says that character should be there, turns it to face where it is walking
 * and plays its Walk / Idle clips (or sways a little if the file has none).
 *
 * The model is drawn with an orthographic camera into one shared offscreen WebGL canvas and copied onto the
 * picture's 2D canvas with drawImage, so the cut-outs that go in front of avatars keep working unchanged.
 * Nothing here knows about rooms: the page hands in (character, feet x, feet y, height in picture pixels).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { clone as cloneSkinned } from "three/addons/utils/SkeletonUtils.js";

const PITCH_DEG = 8;                 // the pictures look slightly down on the floor
const PITCH = PITCH_DEG * Math.PI / 180;
const HALF = 0.53;                   // the frame is the avatar's height plus a 6% margin, centred on its middle
const FEET_ABOVE_BOTTOM = HALF - 0.5 * Math.cos(PITCH);   // the feet sit this far (in avatar heights) above the frame's bottom edge
const ASPECT = 0.8;                  // width / height of the frame each avatar is drawn in (arms out fit)
const TURN_RATE = 9;                 // how fast an avatar turns, per second
const BLEND_RATE = 7;                // how fast walk/idle weights cross-fade, per second
const MAX_PX = 1100;                 // never render bigger than this, whatever the picture says

let gl = null;                       // {renderer, scene, camera, key, fill} built on first use
const avatars = new Map();           // character id -> instance
const state = { hologram: false, lastError: "" };

function ensureGL() {
  if (gl) return gl;
  const canvas = document.createElement("canvas");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, premultipliedAlpha: true, preserveDrawingBuffer: false });
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const hemi = new THREE.HemisphereLight(0xfff2e0, 0x5a4a40, 1.6); scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffe2b8, 2.2); key.position.set(1.5, 3, 4); scene.add(key);
  const camera = new THREE.OrthographicCamera(-HALF * ASPECT, HALF * ASPECT, HALF, -HALF, 0.01, 50);   // centred on the avatar's middle
  const p = PITCH * 1, dist = 6;
  camera.position.set(0, 0.5 + dist * Math.sin(p), dist * Math.cos(p));
  camera.lookAt(0, 0.5, 0);
  gl = { renderer, scene, camera };
  return gl;
}

/* A cyan glow outline over a dark-blue body: bright where the surface turns away from the viewer. */
function hologramMaterial() {
  return new THREE.ShaderMaterial({
    transparent: true, premultipliedAlpha: true,
    vertexShader: `
      varying vec3 vN; varying vec3 vV;
      #include <common>
      #include <skinning_pars_vertex>
      void main() {
        #include <beginnormal_vertex>
        #include <skinbase_vertex>
        #include <skinnormal_vertex>
        #include <defaultnormal_vertex>
        #include <begin_vertex>
        #include <skinning_vertex>
        vec4 mv = modelViewMatrix * vec4(transformed, 1.0);
        vN = normalize(transformedNormal);
        vV = normalize(-mv.xyz);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `
      varying vec3 vN; varying vec3 vV;
      void main() {
        float f = pow(1.0 - abs(dot(normalize(vN), normalize(vV))), 2.0);
        vec3 body = vec3(0.02, 0.28, 0.42);
        vec3 rim = vec3(0.35, 0.98, 1.0);
        float a = clamp(0.42 + 0.58 * f, 0.0, 1.0);
        vec3 col = mix(body, rim, f) * (0.85 + 0.6 * f);
        gl_FragColor = vec4(col * a, a);
      }`,
  });
}

function findClip(clips, re) { return clips.find(c => re.test(c.name)) || null; }

function normalise(root) {
  root.updateMatrixWorld(true);
  root.traverse(o => { if (o.isSkinnedMesh) o.skeleton.update(); });
  const box = new THREE.Box3().setFromObject(root, true);
  const size = box.getSize(new THREE.Vector3()), ctr = box.getCenter(new THREE.Vector3());
  if (!(size.y > 1e-6)) throw new Error("the model has no height");
  const wrap = new THREE.Group();
  root.position.set(-ctr.x, -box.min.y, -ctr.z);                      // feet centre at the origin
  const scaled = new THREE.Group(); scaled.add(root); scaled.scale.setScalar(1 / size.y);   // height becomes exactly 1
  wrap.add(scaled);
  return { wrap, nativeHeight: size.y, nativeWidth: size.x };
}

async function load(character, url, label) {
  ensureGL();
  let gltf;
  try { gltf = await new GLTFLoader().loadAsync(url); }
  catch (e) { throw new Error("that is not a GLB/glTF avatar I can read (" + String((e && e.message) || e).slice(0, 90) + ")"); }
  const root = cloneSkinned(gltf.scene);
  let meshCount = 0, skinned = 0;
  root.traverse(o => { if (o.isMesh) { meshCount++; if (o.isSkinnedMesh) skinned++; o.frustumCulled = false; } });
  if (!meshCount) throw new Error("that file has no mesh in it");
  const norm = normalise(root);
  const mixer = skinned && gltf.animations.length ? new THREE.AnimationMixer(norm.wrap) : null;
  const walk = findClip(gltf.animations, /walk/i), idle = findClip(gltf.animations, /idle|stand|breath/i);
  const actions = {};
  if (mixer) {
    if (walk) { actions.walk = mixer.clipAction(walk); actions.walk.play(); actions.walk.setEffectiveWeight(0); }
    if (idle) { actions.idle = mixer.clipAction(idle); actions.idle.play(); actions.idle.setEffectiveWeight(1); }
  }
  const normalMaterials = new Map(), holo = hologramMaterial();
  root.traverse(o => { if (o.isMesh) normalMaterials.set(o, o.material); });
  const inst = { character, label: label || character, group: norm.wrap, mixer, actions, yaw: 0, wWalk: 0, phase: 0,
                 clips: gltf.animations.map(a => a.name), nativeHeight: norm.nativeHeight, meshCount, skinned, normalMaterials, holo };
  const old = avatars.get(character); if (old) dispose(old);
  avatars.set(character, inst);
  return { clips: inst.clips, nativeHeight: inst.nativeHeight, meshes: meshCount, skinned, hasWalk: !!walk, hasIdle: !!idle };
}

function dispose(inst) {
  inst.group.traverse(o => { if (o.geometry) o.geometry.dispose(); });
  if (inst.holo) inst.holo.dispose();
  if (inst.mixer) inst.mixer.stopAllAction();
}
function clear(character) { const i = avatars.get(character); if (i) { dispose(i); avatars.delete(character); } }
function has(character) { return avatars.has(character); }
function angleLerp(a, b, k) { let d = ((b - a + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI; return a + d * Math.min(1, k); }

/* Draw `character` standing at feet (cx, fy), `H` picture pixels tall, onto the 2D context ctx (already in picture space).
   motion = {vx, vy, moving, dt, pxScale}: the walk direction in picture space, whether it is walking, seconds since the
   last frame, and screen pixels per picture pixel (so the offscreen render is sharp but never wasteful). */
function draw(ctx, character, cx, fy, H, motion) {
  const inst = avatars.get(character); if (!inst || !(H > 1) || !Number.isFinite(H) || !Number.isFinite(cx) || !Number.isFinite(fy)) return false;
  const { renderer, scene, camera } = ensureGL();
  const raw = motion || {};
  const fin = (v, d) => (Number.isFinite(v) ? v : d);
  // one bad number (NaN from a zero-length step, say) must never reach the turn or the animation, or the avatar is lost for good
  const m = { vx: fin(raw.vx, 0), vy: fin(raw.vy, 0), moving: !!raw.moving, pxScale: fin(raw.pxScale, 1) };
  const dt = Math.min(0.1, Math.max(0, fin(raw.dt, 0)));
  // turn to face where it walks: toward the viewer is +z (yaw 0), right is yaw +90 degrees, away is 180
  const moving = !!m.moving && Math.hypot(m.vx || 0, m.vy || 0) > 1e-3;
  const target = moving ? Math.atan2(m.vx, m.vy) : 0;
  inst.yaw = angleLerp(inst.yaw, target, TURN_RATE * dt);
  inst.group.rotation.y = inst.yaw;
  // walk / idle cross-fade, or a small bob and lean when the file has no clips
  inst.wWalk += ((moving ? 1 : 0) - inst.wWalk) * Math.min(1, BLEND_RATE * dt);
  if (inst.mixer) {
    if (inst.actions.walk) inst.actions.walk.setEffectiveWeight(inst.actions.idle ? inst.wWalk : 1);
    if (inst.actions.idle) inst.actions.idle.setEffectiveWeight(inst.actions.walk ? 1 - inst.wWalk : 1);
    if (inst.actions.walk && !inst.actions.idle) inst.actions.walk.paused = !moving;
    inst.mixer.update(dt);
    inst.group.position.y = 0;
  } else {
    inst.phase += dt * (moving ? 9 : 1.4);
    inst.group.position.y = moving ? Math.abs(Math.sin(inst.phase)) * 0.012 : 0;
    inst.group.rotation.z = moving ? Math.sin(inst.phase) * 0.035 : 0;
  }
  // look
  inst.group.traverse(o => { if (o.isMesh) o.material = state.hologram ? inst.holo : (inst.normalMaterials.get(o) || o.material); });

  const hr = Math.max(48, Math.min(MAX_PX, Math.round(H * (m.pxScale || 1) * (window.devicePixelRatio || 1))));
  const wr = Math.round(hr * 2 * HALF * ASPECT);
  renderer.setPixelRatio(1); renderer.setSize(wr, Math.round(hr * 2 * HALF), false);
  scene.add(inst.group);
  renderer.render(scene, camera);
  scene.remove(inst.group);
  // place the frame so the feet land exactly on (cx, fy)
  const fh = H * 2 * HALF, fw = fh * ASPECT;
  ctx.drawImage(renderer.domElement, cx - fw / 2, fy + FEET_ABOVE_BOTTOM * H - fh, fw, fh);
  return true;
}

function setHologram(on) { state.hologram = !!on; }
function info(character) {
  const i = avatars.get(character); if (!i) return null;
  return { label: i.label, clips: i.clips, nativeHeight: i.nativeHeight, meshes: i.meshCount, skinned: i.skinned };
}

window.PubCastGLB = { load, clear, has, draw, setHologram, info, state };
document.dispatchEvent(new Event("pubcast-glb-ready"));
