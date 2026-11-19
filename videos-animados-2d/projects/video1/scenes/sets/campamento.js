// sets/campamento.js — campamento polaco en el desierto de Irán, hora dorada: dunas, tiendas con faroles, camión, fogata opcional.
import { E, V, mood, layer, backdrop, rr, seg, circle, poly, linGrad, glow, alpha, shade, mix, rng } from '/engine/core.js';
import * as FX from '/engine/fx2d.js';

export const GYc = () => E.H * V(0.8, 0.68);
export function tent(g, x, y, w, h, c, lit, M) {
  poly(g, [[x - w / 2, y], [x, y - h], [x + w / 2, y]], c);
  poly(g, [[x, y - h], [x + w / 2, y], [x + w * 0.62, y]], shade(c, -0.35));
  if (lit) { poly(g, [[x - w * 0.12, y], [x, y - h * 0.45], [x + w * 0.12, y]], M.practical); glow(g, x, y - h * 0.2, w * 0.9, M.practical, 0.35); }
  seg(g, [[x, y - h], [x, y - h - 26]], 4, shade(c, -0.4));
}
export function truck(g, x, y, s, c) {
  g.save(); g.translate(x, y); g.scale(s, s);
  rr(g, -220, -170, 280, 130, 10); g.fillStyle = c; g.fill();
  rr(g, 60, -130, 110, 90, 14); g.fill(); g.fillStyle = shade(c, 0.25); rr(g, 92, -122, 56, 40, 6); g.fill();
  g.fillStyle = c; g.fillRect(-230, -50, 410, 20);
  for (const dx of [-160, -60, 120]) { circle(g, dx, -26, 32, '#0d0a0c'); circle(g, dx, -26, 11, '#3a3036'); }
  g.restore();
}
export function campfire(g, x, y, t, s = 1, M) {
  for (const a of [-0.5, 0.5]) seg(g, [[x - 50 * s * Math.cos(a), y], [x + 50 * s * Math.cos(a), y - 18 * s]], 12 * s, '#2a1a12');
  glow(g, x, y - 40 * s, 520 * s, M.practical, 0.45 + 0.08 * Math.sin(t * 11));
  for (let i = 0; i < 3; i++) { const fl = 1 + 0.15 * Math.sin(t * 9 + i * 2); poly(g, [[x - 34 * s + i * 22 * s, y - 6 * s], [x - 22 * s + i * 22 * s + Math.sin(t * 6 + i) * 6 * s, y - (70 + i * 14) * fl * s], [x - 6 * s + i * 22 * s, y - 6 * s]], i === 1 ? '#ffe2a0' : '#ff9a4a'); }
  FX.pool(g, x, y + 10, 340 * s, 60 * s, M.practical, 0.35);
}
export function campamento(g, t, cam, o = {}) {
  const M = mood(o.mood || 'golden'), GY = GYc(), CX = E.W / 2, night = o.mood === 'dusk' || o.mood === 'night';
  layer(g, cam, 0.1, (g) => {
    backdrop(g, M.sky);
    if (!night) FX.sun(g, CX - V(380, 200), GY - V(360, 560), V(70, 80), '#fff3dc', M.key, 5);
    else FX.stars(g, t, { count: 50, area: [-E.W, -E.H, E.W * 3, E.H * 0.9] });
    FX.clouds(g, { y: GY - V(800, 1300), h: 200, color: '#ffe7c7', a: 0.12, seed: 3 });
  });
  layer(g, cam, 0.25, (g) => {
    FX.hills(g, { y: GY - V(260, 420), amp: V(60, 80), color: mix(M.sky[1], M.wall, 0.55), seed: 2, freq: 0.0025 });
    FX.hills(g, { y: GY - V(170, 300), amp: V(40, 60), color: mix(M.sky[1], M.wall, 0.75), seed: 6, freq: 0.004 });
  });
  layer(g, cam, 0.55, (g) => {
    const y = GY - V(110, 200);
    g.fillStyle = shade(M.floor, 0.05); g.fillRect(-E.W, y, E.W * 3, 400);
    const tc = shade('#5a5236', -0.35);
    tent(g, CX - V(700, 520), y + 6, 300, 170, tc, true, M); tent(g, CX + V(620, 420), y + 6, 340, 190, tc, true, M); tent(g, CX + V(1200, 900), y + 6, 280, 160, tc, false, M); tent(g, CX - V(1250, 1000), y + 6, 280, 150, tc, false, M);
    if (!o.noTruck) truck(g, CX + V(80, 60), y + 4, V(0.8, 0.7), shade('#4b5638', -0.5));
    for (const x of [-900, -300, 340, 1000]) FX.lampPost(g, CX + x, y + 4, 170, { color: '#14100c', light: M.practical, a: 0.18 });
    FX.fog(g, y - 60, 120, M.fog, 0.18);
  });
  layer(g, cam, 0.85, (g) => {
    g.fillStyle = linGrad(g, 0, GY - V(110, 200), 0, GY + 700, [shade(M.floor, 0.12), M.floor, shade(M.dark, -0.1)]); g.fillRect(-E.W, GY - V(80, 150), E.W * 3, E.H * 2);
    g.strokeStyle = alpha('#000', 0.12); g.lineWidth = 2; for (let i = 0; i < 6; i++) { g.beginPath(); g.moveTo(-E.W, GY + i * 60); for (let x = -E.W; x < E.W * 2; x += 40) g.lineTo(x, GY + i * 60 + Math.sin(x * 0.004 + i) * 14); g.stroke(); }
    FX.pool(g, CX, GY + 20, 460, 70, M.key, 0.2);
    if (o.fire) campfire(g, CX + (o.fireX || 0), GY + 10, t, V(1, 1.1), M);
  });
  return { GY, CX, M };
}
