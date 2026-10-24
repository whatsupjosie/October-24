/* Foresight GL — the Counter's renderer, on the graphics card.

   One canvas sits behind the whole Counter. It draws the bench, then every tray,
   fan blade, the lantern and the system bar, each as a rounded polygon from
   foresight_shapes.js: a thick polished rim with bevels and highlights, a
   recessed floor of stone, wood, pearl or jewel glass (glass shows the bench
   blurred behind it), an inlay line, a seated lip around the content, a cast
   shadow and a coloured glow. Because it runs on the graphics card, shapes can
   change every frame while trays push against each other.

   Materials are the ones from the C++ renderer (foresight_matter.cpp), ported
   line for line to GLSL, plus the canonical Wallet palette and the looks in
   Josie's mockups (rose gold, champagne, frosted pearl glass, burgundy glass,
   parchment).

   API: const gl = new ForesightGL(canvas); gl.setTheme('walnut'|'pearl'|'indigo');
        gl.draw(items)   items = [{q, r, rim, pad, rimMat, floorMat, glow:[r,g,b,a],
                                   focus, content:[x0,y0,x1,y1]|null, seed, height,
                                   inlay, emissive:[r,g,b,a], center:[x,y]}]
   Coordinates are CSS pixels of the canvas. */
(function(root){
  'use strict';

  const MAT = {
    GOLD:0, ROSE_GOLD:1, BRASS:2, COPPER:3, SILVER:4, BRONZE:5, CHAMPAGNE:6,
    MARBLE_WHITE:10, MARBLE_ROSE:11, MARBLE_VERDE:12, MARBLE_BLACK:13, MARBLE_INDIGO:14,
    GRANITE:20, GRANITE_BLACK:21, SANDSTONE:30, WALNUT:40, OAK:41, MAHOGANY:42,
    NACRE:50, PEARL:51, PEARL_GLASS:52, TORTOISE:60,
    GLASS_AMETHYST:70, GLASS_EMERALD:71, GLASS_SAPPHIRE:72, GLASS_SMOKE:73, GLASS_BURGUNDY:74,
    EMERALD_ENAMEL:75, OBSIDIAN:76, PARCHMENT:80, LEATHER:81,
  };
  const THEME = {walnut:0, pearl:1, indigo:2};
  const MAXV = 40;

  const COMMON = `#version 300 es
precision highp float; precision highp int;
const float PI = 3.14159265;
uint hashu(int x, int y, uint s){ uint h = uint(x)*0x8da6b343u ^ uint(y)*0xd8163841u ^ s*0xcb1ab31fu; h ^= h>>13; h *= 0x5bd1e995u; h ^= h>>15; return h; }
float hash(int x, int y, uint s){ return float(hashu(x,y,s) & 0xFFFFFFu) / 16777216.0; }
float vnoise(vec2 p, uint s){
  vec2 f = floor(p); ivec2 i = ivec2(f); vec2 t = p - f;
  vec2 u = t*t*t*(t*(t*6.0-15.0)+10.0);
  float a = hash(i.x,i.y,s), b = hash(i.x+1,i.y,s), c = hash(i.x,i.y+1,s), d = hash(i.x+1,i.y+1,s);
  return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}
float fbm(vec2 p, int oct, uint s){
  float v = 0.0, a = 0.5, n = 0.0;
  for(int i=0;i<8;i++){ if(i>=oct) break; v += a*vnoise(p, s + uint(i)*101u); n += a;
    p = vec2(1.6*p.x + 1.2*p.y + 3.1, -1.2*p.x + 1.6*p.y + 1.7); a *= 0.5; }
  return v/n;
}
float worley(vec2 p, uint s, out float id){
  ivec2 i = ivec2(floor(p)); float best = 9.0; id = 0.0;
  for(int y=-1;y<=1;y++) for(int x=-1;x<=1;x++){
    ivec2 c = i + ivec2(x,y);
    vec2 q = vec2(c) + vec2(hash(c.x,c.y,s), hash(c.x,c.y,s+7u));
    float d = dot(q-p, q-p);
    if(d < best){ best = d; id = hash(c.x,c.y,s+13u); }
  }
  return sqrt(best);
}
vec3 rgb(int h){ return vec3(float((h>>16)&255), float((h>>8)&255), float(h&255)) / 255.0; }
vec3 lin(vec3 c){ return pow(max(c, 0.0), vec3(2.2)); }
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14), 0.0, 1.0); }
vec3 encode(vec3 c){ return pow(aces(c*0.92), vec3(1.0/2.2)); }
`;

  // ---------- bench (rendered once into a texture) ----------
  const BENCH_FS = COMMON + `
uniform vec2 uView; uniform int uTheme; uniform vec3 uL; uniform vec3 uKey;
in vec2 vP; out vec4 o;
vec3 walnut(vec2 p, out float h){
  float x = p.x, y = p.y; uint seed = 7u;
  vec3 light = rgb(0x6E4A30), dark = rgb(0x2E1C12);
  float plankH = 118.0, pi_ = floor(y/plankH), py_ = y - pi_*plankH;
  float off = hash(int(pi_), 0, seed)*900.0;
  float joint = floor((x + off)/1100.0);
  uint ps = seed + uint(pi_*31.0 + joint*7.0 + 1000.0);
  float tone = hash(int(pi_), int(joint), seed+1u);
  float drift = fbm(vec2(x*0.0007, pi_*3.1), 3, ps+5u)*22.0 + fbm(vec2(x*0.003, y*0.004), 2, ps+8u)*3.0;
  float gy = y + drift;
  float fib = fbm(vec2(x*0.0015, gy*0.30), 5, ps);
  float ring = fract(gy*0.045 + fbm(vec2(x*0.0006, gy*0.01), 3, ps+2u)*2.2 + vnoise(vec2(x*0.002, gy*0.05), ps+3u)*0.25);
  float late = smoothstep(0.55, 0.95, ring) * smoothstep(1.0, 0.95, ring);
  float figure = fbm(vec2(x*0.0009, gy*0.012), 3, ps+11u);
  float pore = smoothstep(0.82, 0.9, vnoise(vec2(x*0.09, gy*1.6), ps+13u));
  vec3 col = mix(light, dark, clamp(late*0.38 + (fib-0.5)*0.22 + (figure-0.5)*0.6 + 0.22, 0.0, 1.0));
  col *= (0.84 + 0.26*tone) * (1.0 - pore*0.28);
  float seamY = min(py_, plankH - py_);
  float xj = x + off; float seamX = abs(xj - floor(xj/1100.0 + 0.5)*1100.0);
  float seam = 1.0 - smoothstep(0.0, 1.6, min(seamY, seamX));
  col *= 1.0 - seam*0.75;
  h = late*0.04 + fib*0.03 - pore*0.05 - seam*0.8;
  return lin(col);
}
vec3 marbleSlab(vec2 p, vec3 base, vec3 vein, vec3 cloud, uint seed, out float h){
  float sc = 0.0021;
  float warp = fbm(p*sc*2.0, 6, seed);
  float t = sin((p.x*0.82 + p.y*0.57)*sc*9.0 + warp*9.5);
  float v1 = pow(1.0 - abs(t), 22.0);
  float t2 = sin((p.x*-0.4 + p.y*0.92)*sc*5.0 + fbm(p*sc*3.0, 5, seed+41u)*12.0);
  float v2 = pow(1.0 - abs(t2), 60.0)*0.6;
  float c = fbm(p*sc*1.2, 5, seed+77u);
  vec3 col = mix(base, cloud, smoothstep(0.35, 0.8, c)*0.6);
  col = mix(col, vein, clamp(v1*0.7 + v2, 0.0, 1.0));
  h = (v1+v2)*0.02;
  return lin(col);
}
void main(){
  vec2 p = vP; float h = 0.0; vec3 alb;
  if(uTheme == 0) alb = walnut(p, h);
  else if(uTheme == 1) alb = marbleSlab(p, rgb(0xEFEAE3), rgb(0xA79C90), rgb(0xDCD4CA), 11u, h);
  else alb = marbleSlab(p, rgb(0x120E24), rgb(0x3B3060), rgb(0x1E1838), 23u, h);
  vec3 n = normalize(vec3(-dFdx(h)*6.0, -dFdy(h)*6.0, 1.0));
  // one key light from the upper left, a pool of light, and a soft vignette
  vec2 pool = vec2(uView.x*0.28, uView.y*0.18);
  float dpool = length((p - pool)/uView);
  float lightPool = 0.55 + 0.75*exp(-dpool*dpool*2.6);
  float nl = max(dot(n, uL), 0.0);
  vec3 col = alb * (uKey*nl*0.55 + vec3(0.36)) * lightPool;
  // polished stone and varnished wood catch a broad reflection
  float coat = uTheme == 0 ? 0.35 : 0.8;
  float fres = 0.04 + 0.96*pow(1.0 - n.z, 5.0);
  float sheen = exp(-pow((p.x/uView.x)*0.8 + (p.y/uView.y) - 0.55, 2.0)*14.0);
  col += vec3(1.0, 0.95, 0.88) * sheen * coat * 0.10 + fres*0.05;
  if(uTheme == 2) col += rgb(0x5B3BA6) * 0.10 * exp(-dpool*dpool*1.4);   // violet ambience
  vec2 q = p/uView - 0.5; col *= 1.0 - dot(q,q)*0.55;
  o = vec4(encode(col), 1.0);
}`;

  const QUAD_VS = `#version 300 es
in vec2 aPos; uniform vec4 uRect; uniform vec2 uView; out vec2 vP;
void main(){ vec2 p = mix(uRect.xy, uRect.zw, aPos); vP = p; vec2 c = p/uView*2.0 - 1.0; gl_Position = vec4(c.x, -c.y, 0.0, 1.0); }`;

  const BLIT_FS = `#version 300 es
precision highp float; uniform sampler2D uTex; uniform vec2 uRes; out vec4 o;
void main(){ o = texture(uTex, gl_FragCoord.xy / uRes); }`;

  // ---------- trays, blades, lantern, bar ----------
  const TRAY_FS = COMMON + `
#define MAXV ${MAXV}
uniform vec2 uQ[MAXV]; uniform int uN; uniform float uR, uRim, uPad, uHeight, uThick, uBack, uGloss;
uniform int uRimMat, uFloorMat, uInlay, uScreen; uniform float uSeed, uFocus;
uniform vec4 uGlow, uEmissive, uContent; uniform vec2 uCenter;
uniform vec3 uL, uKey; uniform float uAmb; uniform vec2 uView, uRes; uniform sampler2D uBench;
in vec2 vP; out vec4 o;

float sdPoly(vec2 p, out vec2 grad){
  float d = dot(p-uQ[0], p-uQ[0]); vec2 bb = p - uQ[0]; float s = 1.0;
  for(int i=0;i<MAXV;i++){
    if(i>=uN) break;
    int j = i==0 ? uN-1 : i-1;
    vec2 vi = uQ[i], vj = uQ[j];
    vec2 e = vj - vi, w = p - vi;
    vec2 b = w - e*clamp(dot(w,e)/dot(e,e), 0.0, 1.0);
    float db = dot(b,b); if(db < d){ d = db; bb = b; }
    bool c1 = p.y >= vi.y, c2 = p.y < vj.y, c3 = e.x*w.y > e.y*w.x;
    if((c1&&c2&&c3) || (!c1&&!c2&&!c3)) s = -s;
  }
  float l = sqrt(d); grad = s*bb/max(l, 1e-4); return s*l;
}
float sdPolyOnly(vec2 p){ vec2 g; return sdPoly(p, g); }

struct Surf { vec3 alb; vec3 f0; float rough; float metal; float coat; float h; float sparkle; float irid; float glass; vec3 tint; };

Surf metalSurf(int m, vec2 p, vec2 tdir){
  Surf s; s.coat = 0.0; s.sparkle = 0.0; s.irid = 0.0; s.glass = 0.0; s.tint = vec3(0); s.metal = 1.0;
  vec3 c = m==0 ? vec3(1.00,0.74,0.32) : m==1 ? vec3(0.98,0.66,0.55) : m==2 ? vec3(0.91,0.74,0.40)
         : m==3 ? vec3(0.95,0.58,0.43) : m==4 ? vec3(0.96,0.96,0.95) : m==5 ? vec3(0.80,0.53,0.30) : vec3(0.95,0.85,0.66);
  float along = dot(p, tdir), across = dot(p, vec2(-tdir.y, tdir.x));
  float brush = vnoise(vec2(along*0.04, across*1.6), 3u);
  s.f0 = c; s.alb = c;
  s.rough = clamp((m==0||m==1||m==6 ? 0.14 : m==4 ? 0.12 : 0.2) + brush*0.06, 0.05, 0.9);
  s.h = brush*0.15;
  return s;
}

Surf floorSurf(int m, vec2 p, vec2 rel, uint seed){
  if(m < 10){ Surf ms = metalSurf(m, p, vec2(1.0, 0.0)); ms.rough = 0.32; ms.h *= 0.25; return ms; }
  Surf s; s.f0 = vec3(0.04); s.metal = 0.0; s.coat = 0.0; s.h = 0.0; s.sparkle = 0.0; s.irid = 0.0; s.glass = 0.0; s.tint = vec3(0); s.rough = 0.5;
  float x = p.x, y = p.y;
  if(m >= 10 && m <= 14){
    vec3 base, vein, cloud;
    if(m==10){ base=rgb(0xF2EEE6); vein=rgb(0x8C8478); cloud=rgb(0xD9D2C6); }
    else if(m==11){ base=rgb(0xF3E4DA); vein=rgb(0xB0806C); cloud=rgb(0xE6C7B8); }
    else if(m==12){ base=rgb(0x1E4B40); vein=rgb(0xC8DCCF); cloud=rgb(0x2F6A5A); }
    else if(m==13){ base=rgb(0x17181B); vein=rgb(0xE8E2D4); cloud=rgb(0x2A2B30); }
    else { base=rgb(0x1A1433); vein=rgb(0xB9A6E6); cloud=rgb(0x2C2152); }
    float sc = 0.0042;
    float warp = fbm(vec2(x,y)*sc*2.0, 6, seed);
    float t = sin((x*0.82 + y*0.57)*sc*9.0 + warp*9.5);
    float v1 = pow(1.0-abs(t), 26.0);
    float t2 = sin((x*-0.4 + y*0.92)*sc*5.0 + fbm(vec2(x,y)*sc*3.0, 5, seed+41u)*12.0);
    float v2 = pow(1.0-abs(t2), 60.0)*0.7;
    float c = fbm(vec2(x,y)*sc*1.2, 5, seed+77u);
    vec3 col = mix(base, cloud, smoothstep(0.35, 0.8, c)*0.55);
    col = mix(col, vein, clamp(v1*0.85 + v2, 0.0, 1.0));
    s.alb = lin(col); s.rough = 0.10 + c*0.06; s.coat = 0.9; s.h = (v1+v2)*0.04;
    return s;
  }
  if(m == 20 || m == 21){
    float id1, id2, id3;
    float f1 = worley(vec2(x,y)*0.16, seed, id1);
    worley(vec2(x,y)*0.42, seed+5u, id2);
    worley(vec2(x,y)*1.10, seed+9u, id3);
    vec3 col;
    if(m == 20){
      vec3 quartz=rgb(0xD9D4CD), feld=rgb(0xD4A897), feld2=rgb(0xB98476), bio=rgb(0x16151A), grey=rgb(0x8F8984);
      col = id1<0.30 ? quartz : id1<0.52 ? feld : id1<0.66 ? feld2 : id1<0.84 ? grey : bio;
      col = mix(col, id2<0.5 ? quartz : bio, (id2>0.78 || id2<0.12) ? 0.85 : 0.0);
      col = mix(col, id3<0.5 ? grey : bio, id3>0.86 ? 0.7 : 0.0);
    } else {
      float j1, j2; worley(vec2(x,y)*0.24, seed+21u, j1); worley(vec2(x,y)*0.7, seed+23u, j2);
      vec3 a=rgb(0x0B0C0F), b=rgb(0x1C1E23), c=rgb(0x3E414A), d=rgb(0x8A8E98);
      col = j1<0.58 ? a : j1<0.86 ? b : j1<0.97 ? c : d;
      col = mix(col, j2<0.6 ? a : c, j2>0.8 ? 0.7 : 0.0);
      col = mix(col, id2<0.5 ? a : c, id2>0.85 ? 0.8 : 0.0);
      col = mix(col, d, id3>0.93 ? 0.6 : 0.0);
    }
    col *= 0.9 + 0.18*vnoise(vec2(x,y)*2.0, seed+2u);
    s.alb = lin(col); s.rough = 0.10; s.coat = 0.95; s.h = smoothstep(0.0, 0.06, f1)*0.03;
    s.sparkle = hash(int(x), int(y), seed+99u) > 0.996 ? 0.8 : 0.0;
    return s;
  }
  if(m == 30){
    float warp = fbm(vec2(x,y)*0.006, 5, seed);
    float band = y*0.035 + warp*6.0 + fbm(vec2(x,y)*0.02, 3, seed+3u)*1.5;
    float strata = 0.5 + 0.5*sin(band), fine = 0.5 + 0.5*sin(band*3.7 + 1.3);
    vec3 col = mix(mix(rgb(0xD8B38A), rgb(0xC08A5C), strata), rgb(0xE6CBA6), fine*0.35);
    float grain = hash(int(x), int(y), seed+8u);
    col *= (0.86 + 0.22*grain) * (0.9 + 0.2*vnoise(vec2(x,y)*0.3, seed+4u));
    s.alb = lin(col); s.rough = 0.88; s.h = grain*0.35 + strata*0.2;
    return s;
  }
  if(m >= 40 && m <= 42){
    vec3 light = m==40 ? rgb(0x6E4A30) : m==41 ? rgb(0xB8925E) : rgb(0x7C3420);
    vec3 dark  = m==40 ? rgb(0x2E1C12) : m==41 ? rgb(0x6E4C2C) : rgb(0x3A140A);
    float drift = fbm(vec2(x*0.0007, y*0.002), 3, seed+5u)*22.0;
    float gy = y + drift;
    float fib = fbm(vec2(x*0.0015, gy*0.30), 5, seed);
    float ring = fract(gy*0.045 + fbm(vec2(x*0.0006, gy*0.01), 3, seed+2u)*2.2);
    float late = smoothstep(0.55, 0.95, ring)*smoothstep(1.0, 0.95, ring);
    float figure = fbm(vec2(x*0.0009, gy*0.012), 3, seed+11u);
    float pore = smoothstep(0.82, 0.9, vnoise(vec2(x*0.09, gy*1.6), seed+13u));
    vec3 col = mix(light, dark, clamp(late*0.38 + (fib-0.5)*0.22 + (figure-0.5)*0.6 + 0.22, 0.0, 1.0));
    col *= 1.0 - pore*0.28;
    s.alb = lin(col); s.rough = 0.35; s.coat = 0.6; s.h = late*0.04 + fib*0.03 - pore*0.05;
    return s;
  }
  if(m == 50){
    float radial = atan(rel.x, -rel.y);
    float ribs = pow(0.5 + 0.5*cos(radial*26.0), 0.7);
    float growth = 0.5 + 0.5*sin(length(rel)*0.11 + fbm(vec2(x,y)*0.01, 4, seed)*5.0);
    vec3 base = mix(rgb(0xF6EEE8), rgb(0xE8D6CC), growth*0.45 + (1.0-ribs)*0.25);
    s.alb = lin(base); s.rough = 0.16; s.coat = 0.8; s.h = ribs*0.4 + growth*0.05; s.irid = 0.7;
    return s;
  }
  if(m == 51 || m == 52){
    float n1 = fbm(vec2(x,y)*0.006, 5, seed), n2 = fbm(vec2(x,y)*0.03, 3, seed+2u);
    vec3 warm=rgb(0xFAF7F0), mid=rgb(0xE9E6DF), cool=rgb(0xCFD9DF), blush=rgb(0xEBDCE6);
    vec3 col = mix(mix(warm, mid, n1), cool, smoothstep(0.55, 0.8, n1)*0.6);
    col = mix(col, blush, smoothstep(0.6, 0.85, n2)*0.35);
    float sheen = fbm(vec2(x*0.0025 + n1, y*0.0025), 3, seed+5u);
    col = mix(col, cool, smoothstep(0.45, 0.75, sheen)*0.45);
    float ph = sheen*1.8 + n1*0.9;
    vec3 film = 0.5 + 0.5*cos(6.283*(ph + vec3(0.0, 0.33, 0.67)));
    col *= vec3(0.86) + film*0.16;
    s.alb = lin(col); s.rough = 0.24; s.coat = 0.7; s.h = n2*0.03 + sheen*0.05; s.irid = 0.45;
    if(m == 52){ s.glass = 0.55; s.tint = lin(rgb(0xF4F1EC)); }    // frosted pearl glass: the bench shows through, milky
    return s;
  }
  if(m == 60){
    float wx = fbm(vec2(x,y)*0.006, 4, seed+30u)*90.0, wy = fbm(vec2(x*0.006+7.0, y*0.006), 4, seed+31u)*90.0;
    vec2 Q = vec2(x+wx, y+wy);
    float a = fbm(vec2(Q.x*0.011, Q.y*0.026), 6, seed), b = fbm(vec2(Q.x*0.04, Q.y*0.09), 4, seed+4u);
    float spot = smoothstep(0.52, 0.60, a + (b-0.5)*0.22), core = smoothstep(0.60, 0.70, a);
    float fleck = smoothstep(0.70, 0.74, b)*(1.0-spot);
    vec3 col = mix(rgb(0xD99A45), rgb(0x9C5418), clamp((a-0.3)*2.2, 0.0, 1.0));
    col = mix(col, rgb(0x55230A), spot*0.9 + fleck*0.5);
    col = mix(col, rgb(0x1E0B04), core*0.85);
    s.alb = lin(col); s.rough = 0.05; s.coat = 1.0;
    return s;
  }
  if(m >= 70 && m <= 74){
    vec3 tint = m==70 ? rgb(0x5A2E7E) : m==71 ? rgb(0x135C47) : m==72 ? rgb(0x1B4F86) : m==73 ? rgb(0x2A2C33) : rgb(0x6E1A26);
    float depth = fbm(vec2(x,y)*0.003, 4, seed);
    float swirl = fbm(vec2(x*0.012 + depth*2.0, y*0.012), 3, seed+6u);
    s.tint = lin(tint) * (0.75 + 0.5*depth + swirl*0.25);
    s.alb = s.tint * 0.35; s.rough = 0.03; s.coat = 1.0; s.h = swirl*0.01; s.glass = 0.42;
    return s;
  }
  if(m == 75){
    float n1 = fbm(vec2(x,y)*0.004, 4, seed); float id; float f = worley(vec2(x,y)*0.08, seed+3u, id);
    float bubble = (1.0 - smoothstep(0.0, 0.12, f))*(id > 0.8 ? 1.0 : 0.0);
    vec3 col = mix(rgb(0x0B2A20), rgb(0x1C5A47), n1)*(1.0 + bubble*0.25);
    s.alb = lin(col); s.rough = 0.05; s.coat = 1.0; s.h = -bubble*0.05;
    return s;
  }
  if(m == 76){
    float n1 = fbm(vec2(x,y)*0.003, 4, seed), peel = fbm(vec2(x,y)*0.05, 2, seed+7u);
    s.alb = lin(mix(rgb(0x040507), rgb(0x150F0E), n1*0.6)); s.rough = 0.04; s.coat = 1.0; s.h = peel*0.006;
    return s;
  }
  if(m == 80){
    float n1 = fbm(vec2(x,y)*0.008, 5, seed), fib = fbm(vec2(x*0.08, y*0.08), 3, seed+3u);
    vec3 col = mix(rgb(0xF3E7CF), rgb(0xE2CFA9), n1*0.7) * (0.95 + fib*0.08);
    s.alb = lin(col); s.rough = 0.7; s.coat = 0.15; s.h = fib*0.03;
    return s;
  }
  float id; float f = worley(vec2(x,y)*0.18, seed, id);
  s.alb = lin(rgb(0x4A2C1C)*(0.85 + 0.3*id)); s.rough = 0.62; s.h = smoothstep(0.0, 0.5, f)*0.1;
  return s;
}

// A warm, lamp-lit room for reflections: dark low, warm high, a big softbox toward
// the key light, a cool fill opposite, and two hot strip lights.
vec3 env(vec3 r, float rough){
  float up = r.z, hz = r.y;
  vec3 low = vec3(0.05,0.035,0.025), mid = vec3(0.30,0.23,0.17), high = vec3(0.80,0.70,0.55);
  float t = clamp(up*0.6 + 0.4 - hz*0.35, 0.0, 1.0);
  vec3 room = t < 0.5 ? mix(low, mid, t*2.0) : mix(mid, high, (t-0.5)*2.0);
  float spread = 6.0 + 260.0*(1.0-rough)*(1.0-rough);
  float key = pow(max(dot(r, uL), 0.0), spread);
  vec3 fillDir = normalize(vec3(-uL.x, -uL.y, 0.45));
  float fill = pow(max(dot(r, fillDir), 0.0), 4.0 + 50.0*(1.0-rough));
  float sharp = 30.0*(1.0-rough) + 3.0;
  float strip = exp(-(hz+0.35)*(hz+0.35)*sharp*3.0) * clamp(up*1.5 + 0.3, 0.0, 1.0);
  float strip2 = exp(-(r.x-0.45)*(r.x-0.45)*sharp*2.0) * clamp(up*1.2, 0.0, 1.0);
  return room*0.85 + uKey*3.4*key + vec3(0.45,0.55,0.7)*fill + vec3(3.0,2.7,2.2)*strip + vec3(1.3,1.15,0.95)*strip2*0.8;
}
vec3 fresnel(vec3 f0, float c){ return f0 + (1.0-f0)*pow(1.0-c, 5.0); }
float ggx(float nh, float r){ float a = r*r, a2 = a*a, d = nh*nh*(a2-1.0) + 1.0; return a2/(PI*d*d + 1e-6); }

vec3 shade(Surf s, vec3 n, float ao, float shadow){
  vec3 V = vec3(0,0,1), H = normalize(uL + V);
  float nl = max(dot(n, uL), 0.0), nv = max(dot(n, V), 0.0) + 1e-3, nh = max(dot(n, H), 0.0);
  vec3 r = reflect(-V, n);
  vec3 col;
  if(s.metal > 0.5){
    vec3 F = fresnel(s.f0, nv);
    col = uKey*F*ggx(nh, max(s.rough, 0.04))*nl*0.6*shadow + env(r, s.rough)*F*ao + s.f0*uAmb*0.15*ao;
  } else {
    col = s.alb*(nl*shadow)*uKey*(2.0/PI) + s.alb*uAmb*ao*1.7;
    if(s.coat > 0.0){
      float Fc = 0.04 + 0.96*pow(1.0-nv, 5.0);
      col = col*(1.0 - Fc*s.coat) + (uKey*ggx(nh, 0.06)*nl*0.25*shadow + env(r, 0.08)*ao*Fc)*s.coat;
    }
    if(s.irid > 0.0){
      float ph = nv*2.6 + n.x*1.7 + n.y*1.3;
      vec3 film = 0.5 + 0.5*cos(6.283*(ph + vec3(0.0, 0.33, 0.67)));
      col = mix(col, col*(film*0.6 + 0.7), s.irid);
    }
  }
  col += vec3(2.5,2.4,2.2)*s.sparkle*nl*shadow;
  return col;
}

// Rim profile: one big polished roll and a smaller bead, as a smooth height curve
// (no hard steps, so highlights stay clean instead of stair-stepping).
float rimH(float u){
  float roll = exp(-pow((u - 0.34)/0.24, 2.0));
  float bead = 0.55*exp(-pow((u - 0.80)/0.11, 2.0));
  float drop = smoothstep(0.90, 1.0, u)*-0.5;          // steps down to the screen
  float lip  = smoothstep(0.08, 0.0, u)*-0.35;          // rounds over at the outer edge
  return roll + bead + drop + lip;
}

void main(){
  vec2 p = vP;
  vec2 g; float d = sdPoly(p, g) - uR;
  vec2 tdir = vec2(-g.y, g.x);
  float aa = max(fwidth(d), 0.5);
  vec2 L2 = normalize(uL.xy + 1e-5);
  vec2 rel = p - uCenter;

  // Weight: the frame is a thick object. Its side wall shows on the side away
  // from the light and toward the viewer; it stands on the bench and casts a shadow.
  vec2 T = normalize(vec2(-L2.x*0.4, 1.0)) * uThick;
  float dw = min(min(sdPolyOnly(p - T*0.34), sdPolyOnly(p - T*0.67)), sdPolyOnly(p - T)) - uR;   // the extruded body
  dw = min(dw, d);

  vec3 metalTint = metalSurf(uRimMat, p, tdir).f0;
  vec4 res = vec4(0);

  // ---- on the bench around the tray: shadow, light underneath, reflection, backlight ----
  if(dw > -aa){
    vec2 S = -L2*(uHeight*1.3) + T;
    float ds = sdPolyOnly(p - S) - uR;
    float blur = 7.0 + uHeight*1.4;
    float sh = (1.0 - smoothstep(-blur, blur*1.2, ds))*0.62;
    float contact = exp(-max(dw, 0.0)/3.0)*0.55;
    float a = clamp(max(sh, contact), 0.0, 0.85);
    float dwp = max(dw, 0.0);
    // subtle light underneath, in the tray's own colour
    vec3 add = uGlow.rgb * uGlow.a * exp(-dwp/10.0) * 0.30;
    // a faint reflection of the frame on a polished bench, below the tray (toward the viewer)
    float facing = smoothstep(0.15, 0.85, g.y);
    add += metalTint * uGloss * exp(-dwp/6.0) * facing * 0.35;
    // selected: a bright backlight from behind the whole tray
    // light from behind the frame spills out around its edge: brightest right at the rim
    vec3 bl = mix(vec3(1.0, 0.90, 0.72), uGlow.rgb, 0.45);
    float dp = max(dw, 0.0);
    add += bl * uBack * (exp(-dp/5.0)*1.1 + exp(-dp/16.0)*0.45 + exp(-dp/40.0)*0.10);
    add *= 1.0 - smoothstep(70.0, 88.0, dp);
    res = vec4(encode(add), a);
  }

  // ---- the side wall ----
  if(dw < aa && d > -aa){
    float wallT = clamp(d / max(dot(normalize(T), g)*uThick, 1.0), 0.0, 1.0);   // 0 at the rim, 1 at the bench
    Surf ms = metalSurf(uRimMat, p, tdir);
    vec3 n = normalize(vec3(g*0.95, 0.30 - wallT*0.25));
    vec3 c = shade(ms, n, 0.85 - wallT*0.45, 1.0) * (0.85 - wallT*0.45);
    c += metalTint * smoothstep(0.22, 0.0, wallT) * 0.35;           // the lip where the wall meets the rim
    float cw = clamp(0.5 - dw/aa, 0.0, 1.0);
    res = vec4(encode(c), 1.0)*cw + res*(1.0 - cw);
  }

  // ---- rim and floor ----
  if(d < aa){
    float into = -d;
    vec3 inside;
    if(into < uRim){
      float u = clamp(into/uRim, 0.0, 1.0), e = 0.02;
      float slope = (rimH(u + e) - rimH(u - e)) / (2.0*e);
      Surf s = metalSurf(uRimMat, p + vec2(uSeed*37.0, uSeed*53.0), tdir);
      vec3 n = normalize(vec3(g*slope*0.42, 1.0));
      float ao = 0.78 + 0.22*smoothstep(-0.3, 0.9, rimH(u));
      vec3 c = shade(s, n, ao, 1.0);
      c *= 1.0 + uFocus*0.06 + uBack*0.18;
      c += vec3(1.0, 0.95, 0.85) * uBack * smoothstep(0.25, 0.0, u) * 0.35;   // backlight catching the outer edge
      inside = c;
    } else {
      float dd = into - uRim;
      if(uScreen > 0 && dd > uPad + 1.0){
        inside = vec3(0.012);                     // covered by the screen
      } else {
        Surf s = floorSurf(uFloorMat, p + vec2(uSeed*131.0, uSeed*71.0), rel, uint(uSeed) + 3u);
        vec3 n = normalize(vec3(-dFdx(s.h)*2.2, -dFdy(s.h)*2.2, 1.0));
        float ao = 1.0 - 0.6*exp(-dd/(uRim*0.8 + 4.0));
        float sideAway = clamp(dot(-g, -L2), 0.0, 1.0);
        float shadow = 1.0 - 0.45*exp(-dd/(uHeight*1.2 + 3.0))*sideAway;
        vec3 c = shade(s, n, ao, shadow);
        if(s.glass > 0.0){
          vec2 suv = gl_FragCoord.xy / uRes;
          vec3 behind = lin(textureLod(uBench, suv, 4.5).rgb);
          c = mix(c, behind*(s.tint*1.6 + 0.08) + c*0.45, s.glass);
          c += s.tint * exp(-dd/22.0) * clamp(dot(-g, L2), 0.0, 1.0) * 1.3;
        }
        float ext = max(max(uContent.z - uContent.x, uContent.w - uContent.y)*0.5 + 40.0, 60.0);
        c *= 0.80 + 0.34*clamp(0.5 + 0.5*dot(rel, -L2)/ext, 0.0, 1.0);
        c += uGlow.rgb * uGlow.a * exp(-dd/10.0) * 0.18;
        if(uInlay > 0 && uScreen == 0){
          float li = 1.0 - smoothstep(0.9, 1.9, abs(dd - 7.0));
          Surf ms = metalSurf(uRimMat, p, tdir);
          c = mix(c, shade(ms, normalize(vec3(g*(dd < 7.0 ? 0.6 : -0.6), 1.0)), 1.0, 1.0), li*0.85);
        }
        if(uEmissive.a > 0.0){
          float core = exp(-dot(rel, rel)/(uEmissive.a*900.0 + 1.0));
          c = c*0.55 + uEmissive.rgb*(core*2.2 + 0.35);
        }
        // the screen's edge sits in the frame: a soft dark bevel against the rim
        if(uScreen > 0) c *= 0.35;
        inside = c;
      }
    }
    float cov = clamp(0.5 - d/aa, 0.0, 1.0);
    res = vec4(encode(inside), 1.0)*cov + res*(1.0 - cov);
  }
  o = res;
}`;

  function compile(gl, type, src){
    const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)){
      const log = gl.getShaderInfoLog(s); gl.deleteShader(s);
      throw new Error('Foresight GL shader: ' + log);
    }
    return s;
  }
  function program(gl, vs, fs){
    const p = gl.createProgram();
    gl.attachShader(p, compile(gl, gl.VERTEX_SHADER, vs)); gl.attachShader(p, compile(gl, gl.FRAGMENT_SHADER, fs));
    gl.bindAttribLocation(p, 0, 'aPos'); gl.linkProgram(p);
    if(!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error('Foresight GL link: ' + gl.getProgramInfoLog(p));
    const u = {}; const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for(let i=0;i<n;i++){ const info = gl.getActiveUniform(p, i); const name = info.name.replace(/\[0\]$/, ''); u[name] = gl.getUniformLocation(p, info.name); }
    return {p, u};
  }

  function kelvin(K){
    const t = Math.max(1000, Math.min(40000, K))/100; let r, g, b;
    if(t <= 66){ r = 1; g = Math.max(0, Math.min(1, (99.4708025861*Math.log(t) - 161.1195681661)/255)); }
    else { r = Math.max(0, Math.min(1, 329.698727446*Math.pow(t-60, -0.1332047592)/255)); g = Math.max(0, Math.min(1, 288.1221695283*Math.pow(t-60, -0.0755148492)/255)); }
    b = t >= 66 ? 1 : t <= 19 ? 0 : Math.max(0, Math.min(1, (138.5177312231*Math.log(t-10) - 305.0447927307)/255));
    return [r*r, g*g, b*b];
  }

  class ForesightGL {
    constructor(canvas){
      this.canvas = canvas;
      const gl = canvas.getContext('webgl2', {premultipliedAlpha:true, antialias:false, alpha:false});
      if(!gl) throw new Error('WebGL2 is not available in this browser');
      this.gl = gl;
      this.bench = program(gl, QUAD_VS, BENCH_FS);
      this.blit = program(gl, QUAD_VS, BLIT_FS);
      this.tray = program(gl, QUAD_VS, TRAY_FS);
      const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0,0, 1,0, 0,1, 1,1]), gl.STATIC_DRAW);
      gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
      this.theme = 'walnut'; this.gloss = 0.35; this.quality = 'full';
      this.setLight({az:135, el:48, kelvin:4300, intensity:1, fill:0.35});
      this.benchDirty = true;
      this.qbuf = new Float32Array(MAXV*2);
    }
    // gloss: how much the bench mirrors what stands on it (varnished wood a little, polished stone more)
    setTheme(name){ if(THEME[name] === undefined) throw new Error('unknown theme '+name); this.theme = name; this.gloss = {walnut:0.35, pearl:0.75, indigo:0.65}[name]; this.benchDirty = true; }
    // Lighting Explorer values: key azimuth/elevation (degrees), Kelvin, intensity, fill level.
    setLight({az=135, el=48, kelvin:K=4300, intensity=1, fill=0.35}={}){
      const a = az*Math.PI/180, e = el*Math.PI/180;
      this.L = [Math.cos(a)*Math.cos(e), -Math.sin(a)*Math.cos(e), Math.sin(e)];
      const l = Math.hypot(...this.L); this.L = this.L.map(v=>v/l);
      const kc = kelvin(K), lum = Math.max(0.05, kc[0]*0.2126 + kc[1]*0.7152 + kc[2]*0.0722);
      this.key = kc.map(v => v*2.85*intensity/lum);
      this.amb = 0.10 + 0.34*fill;
      this.benchDirty = true;
    }
    // quality 'full' renders at least twice the screen's pixel density (smooth edges
    // and highlights); 'fast' renders at the screen's own density (used mid-drag).
    resize(){
      const base = window.devicePixelRatio || 1;
      const dpr = this.quality === 'fast' ? Math.min(base, 2) : Math.min(Math.max(base, 2), 3);
      const w = Math.round(this.canvas.clientWidth*dpr), h = Math.round(this.canvas.clientHeight*dpr);
      if(this.canvas.width !== w || this.canvas.height !== h){ this.canvas.width = w; this.canvas.height = h; this.benchDirty = true; }
      this.dpr = dpr; this.view = [this.canvas.clientWidth, this.canvas.clientHeight];
    }
    renderBench(){
      const gl = this.gl, W = this.canvas.width, H = this.canvas.height;
      if(!this.benchTex || this.benchW !== W || this.benchH !== H){
        if(this.benchTex) gl.deleteTexture(this.benchTex);
        if(this.fbo) gl.deleteFramebuffer(this.fbo);
        this.benchTex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, this.benchTex);
        gl.texStorage2D(gl.TEXTURE_2D, Math.floor(Math.log2(Math.max(W,H)))+1, gl.RGBA8, W, H);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        this.fbo = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, this.fbo);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, this.benchTex, 0);
        this.benchW = W; this.benchH = H;
      }
      gl.bindFramebuffer(gl.FRAMEBUFFER, this.fbo); gl.viewport(0, 0, W, H); gl.disable(gl.BLEND);
      const P = this.bench; gl.useProgram(P.p);
      gl.uniform4f(P.u.uRect, 0, 0, this.view[0], this.view[1]); gl.uniform2f(P.u.uView, this.view[0], this.view[1]);
      gl.uniform1i(P.u.uTheme, THEME[this.theme]); gl.uniform3fv(P.u.uL, this.L); gl.uniform3fv(P.u.uKey, this.key);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      gl.bindTexture(gl.TEXTURE_2D, this.benchTex); gl.generateMipmap(gl.TEXTURE_2D);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      this.benchDirty = false;
    }
    draw(items){
      this.resize();
      if(this.benchDirty) this.renderBench();
      const gl = this.gl, W = this.canvas.width, H = this.canvas.height;
      gl.viewport(0, 0, W, H);
      // bench
      gl.disable(gl.BLEND);
      gl.useProgram(this.blit.p); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.benchTex);
      gl.uniform1i(this.blit.u.uTex, 0); gl.uniform2f(this.blit.u.uRes, W, H);
      gl.uniform4f(this.blit.u.uRect, 0, 0, this.view[0], this.view[1]); gl.uniform2f(this.blit.u.uView, this.view[0], this.view[1]);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      // trays and the rest, in order
      gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      const P = this.tray; gl.useProgram(P.p);
      gl.uniform1i(P.u.uBench, 0); gl.uniform2f(P.u.uRes, W, H); gl.uniform2f(P.u.uView, this.view[0], this.view[1]);
      gl.uniform3fv(P.u.uL, this.L); gl.uniform3fv(P.u.uKey, this.key); gl.uniform1f(P.u.uAmb, this.amb);
      for(const it of items){
        if(!it.q || it.q.length < 3) continue;
        const n = Math.min(MAXV, it.q.length);
        const qb = this.qbuf; qb.fill(0);
        let x0=Infinity, y0=Infinity, x1=-Infinity, y1=-Infinity;
        for(let i=0;i<n;i++){ const [x,y] = it.q[i]; qb[2*i]=x; qb[2*i+1]=y; x0=Math.min(x0,x); y0=Math.min(y0,y); x1=Math.max(x1,x); y1=Math.max(y1,y); }
        const m = it.r + 90 + (it.height||10)*2 + (it.thick ?? 10);
        gl.uniform4f(P.u.uRect, x0-m, y0-m, x1+m, y1+m);
        gl.uniform2fv(P.u.uQ, qb); gl.uniform1i(P.u.uN, n);
        gl.uniform1f(P.u.uR, it.r); gl.uniform1f(P.u.uRim, it.rim); gl.uniform1f(P.u.uPad, it.pad||5); gl.uniform1f(P.u.uHeight, it.height||10);
        gl.uniform1i(P.u.uRimMat, it.rimMat ?? MAT.GOLD); gl.uniform1i(P.u.uFloorMat, it.floorMat ?? MAT.MARBLE_WHITE);
        gl.uniform1i(P.u.uInlay, it.inlay ? 1 : 0); gl.uniform1f(P.u.uSeed, it.seed||0); gl.uniform1f(P.u.uFocus, it.focus||0);
        gl.uniform1f(P.u.uThick, it.thick ?? 10); gl.uniform1f(P.u.uBack, it.backlight || 0); gl.uniform1f(P.u.uGloss, this.gloss);
        gl.uniform1i(P.u.uScreen, it.screen ? 1 : 0);
        gl.uniform4fv(P.u.uGlow, it.glow || [0,0,0,0]); gl.uniform4fv(P.u.uEmissive, it.emissive || [0,0,0,0]);
        gl.uniform4fv(P.u.uContent, it.content || [0,0,0,0]);
        const c = it.center || [(x0+x1)/2, (y0+y1)/2]; gl.uniform2f(P.u.uCenter, c[0], c[1]);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      }
    }
  }
  ForesightGL.MAT = MAT; ForesightGL.THEMES = Object.keys(THEME);
  root.ForesightGL = ForesightGL;
})(window);
