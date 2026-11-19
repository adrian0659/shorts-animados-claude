// shots/01_gancho.js — s01–s06: el soldado misterioso en el frente, la revelación del oso y el título.
import { E, V, S, registerShot, mood, layer, blurLayer, veil, backdrop, ease, prog, key, clamp, lerp, shake, wordTime, seg, circle, rr, glow, alpha, shade, text, FONTS } from '/engine/core.js';
import { drawFigure, POSES, breathe, walkPose } from '/engine/rig2d.js';
import * as FX from '/engine/fx2d.js';
import * as UI from '/engine/ui2d.js';
import { frente, explosion, cannon, sandbags, FIRE, GYf } from '../sets/frente.js';
import { campamento } from '../sets/campamento.js';
import { drawBear, bearFace, bbreathe, BPOSES, crate, shell } from '../bear.js';
import { SOLDIER, SOLDIER2 } from '../cast.js';

const shadowBear = (o) => drawBear({ ...o });
// oso caminando erguido (balanceo)
export function bearWalk(t, speed = 1) {
  const ph = Math.sin(t * 2 * Math.PI * 0.9 * speed), p = { ...BPOSES.carry };
  p.kF = [12 + ph * 16, -56]; p.fF = [16 + ph * 30, -Math.max(0, ph) * 10]; p.kB = [-10 - ph * 16, -56]; p.fB = [-14 - ph * 30, -Math.max(0, -ph) * 10];
  const bob = Math.abs(ph) * 4; for (const k of ['head', 'sh', 'eF', 'hF', 'eB', 'hB', 'hip']) p[k] = [p[k][0], p[k][1] - bob];
  return p;
}
const silhouette = (M) => ({ fur: '#09070a', far: '#060407' });

// s01 — "En plena Segunda Guerra Mundial,"  toma abierta, silueta enorme cruzando el frente
registerShot('s01', { draw(g, t, info) {
  const cam = { z: 1 + 0.08 * ease.inOut(t / info.dur), x: -20 + 30 * t / info.dur };
  const { GY, M } = frente(g, t, cam);
  layer(g, cam, 0.7, (g) => { explosion(g, E.W * 0.15, GY - V(180, 300), t, 0.5, 0.7, { seed: 2, noDebris: true }); });
  layer(g, cam, 1, (g) => {
    const x = lerp(E.W * 0.2, E.W * 0.5, t / info.dur);
    drawBear(g, { x, y: GY, s: V(1.0, 1.35), facing: 1, pose: bearWalk(t), ...silhouette(M), crate: true, rim: { color: FIRE, dir: [-0.6, -0.8], w: 5 }, hideFace: true });
  });
  blurLayer(g, 10, (g) => sandbags(g, -80, E.H + 20, 8, V(1.6, 2)), cam, 1.6);
  FX.dust(g, t, { count: 50, color: '#ffc68a', a: 0.4 });
  FX.lensStreak(g, E.W * 0.15, GY - V(220, 340), E.W * 1.2, FIRE, 0.15);
}});

// s02 — "un soldado cargó proyectiles de artillería"  detalle de la caja de proyectiles en zarpas oscuras
registerShot('s02', { draw(g, t, info) {
  blurLayer(g, 14, (g) => frente(g, t, { z: 1.6, x: 120, y: -180 })); veil(g, '#0a0610', 0.35);
  const sw = Math.sin(t * 5.6) * 10, cx = E.W / 2 + Math.sin(t * 2.8) * 16, cy = E.H * 0.52 + sw;
  const sc = V(2.6, 3.6) * (1 + 0.04 * t);
  g.save(); g.translate(cx, cy); g.scale(sc, sc);
  for (const sx of [-1, 1]) { seg(g, [[sx * 90, 120], [sx * 80, 20]], 46, '#0b0709'); circle(g, sx * 70, 4, 26, '#0b0709'); for (let i = 0; i < 4; i++) seg(g, [[sx * 70 + (i - 1.5) * 9, -12], [sx * 70 + (i - 1.5) * 10, -24]], 4, '#e8e0d0'); }
  crate(g, 0, 26, 170, 110, { rim: alpha(FIRE, 0.8) });
  g.restore();
  const k = ease.out(prog(t, 0.4, 1.2));
  for (let i = 0; i < 4; i++) FX.sparkle(g, cx - V(160, 220) + i * V(105, 145), cy - V(270, 370), 18 * k, '#ffe6b0', 0.6 * Math.abs(Math.sin(t * 4 + i)));
  FX.dust(g, t, { count: 40, color: '#ffc68a', a: 0.4 });
  const tw = (wordTime('artillería', info.shot.start) ?? info.shot.start + 1.5) - info.shot.start;
  UI.callout(g, t, { at: [cx, cy - V(140, 200)], to: [cx + V(200, 140), cy - V(420, 560)], str: 'PROYECTILES', start: tw - 0.6, color: S().ui.gold });
}});

// s03 — "bajo el fuego enemigo."  explosión, temblor, la silueta pasa junto al cañón
registerShot('s03', { draw(g, t, info) {
  const [sx, sy] = shake(t, 14 * Math.max(0, 1 - (t - 0.3) * 1.2) * (t > 0.3 ? 1 : 0), 22);
  const cam = { z: 1.15 + 0.05 * t, x: sx - 40, y: sy + V(-60, -120) };
  const { GY, M } = frente(g, t, cam);
  layer(g, cam, 0.75, (g) => { explosion(g, E.W * 0.72, GY - V(80, 120), t, 0.3, V(1.1, 1.4), { seed: 5 }); });
  layer(g, cam, 0.95, (g) => cannon(g, E.W * 0.82, GY, V(1.1, 1.2), -1, 0, { ...M, rim: FIRE }));
  layer(g, cam, 1, (g) => {
    const x = lerp(E.W * 0.12, E.W * 0.42, t / info.dur);
    drawBear(g, { x, y: GY, s: V(1.2, 1.4), facing: 1, pose: bearWalk(t), fur: '#09070a', far: '#060407', crate: true, rim: { color: FIRE, dir: [1, -0.4], w: 6 }, hideFace: true });
  });
  FX.dust(g, t, { count: 60, color: '#ffb070', a: 0.5 });
  veil(g, FIRE, 0.18 * Math.max(0, 1 - Math.abs(t - 0.35) * 4), 'lighter');
}});

// s04 — "Medía casi dos metros."  contraluz alto + dos soldados más bajos + medida "2 m"
registerShot('s04', { draw(g, t, info) {
  const cam = { z: 1.05 + 0.05 * ease.inOut(t / info.dur), x: 10 * t };
  const { GY, M } = frente(g, t, cam);
  const bx = E.W * V(0.5, 0.55), bs = V(1.15, 1.45), bb = bs * 1.18;
  layer(g, cam, 0.7, (g) => { glow(g, bx, GY - V(240, 330), V(700, 600), FIRE, 0.55); explosion(g, bx + 60, GY - V(150, 200), t, -0.6, 0.9, { seed: 9, noDebris: true }); });
  layer(g, cam, 1, (g) => {
    const rim = { color: FIRE, dir: [0.2, -1], w: 5 };
    drawFigure(g, { x: bx - V(260, 300), y: GY, s: bs * 0.98, facing: 1, outfit: SOLDIER2, pose: breathe(POSES.stand, t), expr: 'awe', rim });
    drawFigure(g, { x: bx + V(240, 250), y: GY, s: bs * 0.98, facing: -1, outfit: SOLDIER, pose: breathe(POSES.relaxed, t, 1, 2), expr: 'awe', rim });
    drawBear(g, { x: bx, y: GY, s: bb, facing: 1, pose: bbreathe(BPOSES.stand, t), fur: '#09070a', far: '#060407', rim: { color: FIRE, dir: [0, -1], w: 6 }, expr: 'neutral', hideFace: true });
  });
  const tw = (wordTime('metros', info.shot.start) ?? info.shot.start + 1) - info.shot.start - 0.5;
  layer(g, cam, 1, (g) => UI.dimension(g, t, { x1: bx - V(130, 140), y1: GY, x2: bx - V(130, 140), y2: GY - 280 * bb, str: '2 m', start: tw }));
  FX.dust(g, t, { count: 40, color: '#ffc68a', a: 0.35 });
}});

// s05 — "Y era un oso."  revelación: primer plano del oso iluminado por la explosión (entra con flash)
registerShot('s05', { draw(g, t, info) {
  blurLayer(g, 14, (g) => frente(g, t, { z: 1.6, x: -100, y: -160 })); veil(g, '#0a0610', 0.3);
  const light = ease.out(prog(t, 0, 0.5)), r = V(300, 330) * (1 + 0.04 * t);
  glow(g, E.W * 0.15, E.H * 0.3, E.W, FIRE, 0.4 * light);
  bearFace(g, E.W / 2, E.H * V(0.58, 0.52), r, { expr: t < 0.7 ? 'surprised' : 'neutral', rimColor: FIRE, rimSide: -1, blink: t > 1.2 && t < 1.28, shine: true });
  FX.dust(g, t * 0.2, { count: 60, color: '#ffd0a0', a: 0.5 });
}});

// s06 — "1942."  tarjeta de título sobre el desierto + año dorado
registerShot('s06', { draw(g, t, info) {
  const cam = { z: 1.08 - 0.06 * ease.inOut(t / info.dur), y: -10 * t };
  campamento(g, t, cam, { noTruck: true });
  veil(g, '#120a10', 0.35);
  FX.dust(g, t, { count: 30, color: '#ffd9b0', a: 0.4 });
  UI.titleCard(g, t, { lines: ['EL OSO QUE', 'FUE SOLDADO'], dur: info.dur + 0.3, y: E.H * V(0.36, 0.34) });
  const tw = (wordTime('1942', info.shot.start) ?? info.shot.start + 0.5) - info.shot.start, k = ease.outBack(prog(t, tw - 0.1, tw + 0.3));
  if (k > 0) { g.save(); g.translate(E.W / 2, E.H * V(0.62, 0.56)); g.scale(k, k); text(g, '1942', 0, 0, { size: V(150, 190), color: S().ui.gold, font: FONTS.ui, weight: 900, glow: 30, glowColor: alpha(S().ui.gold, 0.7), spacing: 6 }); g.restore(); }
}});
