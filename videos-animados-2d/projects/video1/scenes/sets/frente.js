// sets/frente.js — el frente de Montecassino de noche: colinas, monasterio en la cima, fogonazos naranjas, trincheras y sacos.
import { E, V, mood, layer, backdrop, rr, seg, circle, poly, linGrad, radGrad, glow, alpha, shade, mix, rng, noise } from '/engine/core.js';
import * as FX from '/engine/fx2d.js';

export const GYf = () => E.H * V(0.8, 0.68);
export const FIRE = '#ff9a4a';
// explosión determinista: t0 = momento del estallido (s), t = tiempo de la toma
export function explosion(g, x, y, t, t0, size = 1, o = {}) {
  const k = t - t0; if (k < 0 || k > 3.2) return 0;
  const r = rng(o.seed || 7), grow = 1 - Math.exp(-k * 5), fade = Math.max(0, 1 - k / 3.2), flash = Math.max(0, 1 - k / 0.35), fire = Math.max(0, 1 - k / 1.1);
  glow(g, x, y - 80 * size, 1100 * size * (0.5 + grow), FIRE, 0.5 * fade + 0.6 * flash);
  // humo: oscuro, sube, borde inferior encendido
  for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + (r() - 0.5) * 2.0, d = (50 + r() * 150) * size * grow, rr0 = (60 + r() * 80) * size * (0.5 + grow * 0.7);
    const cx = x + Math.cos(a) * d, cy = y - 90 * size + Math.sin(a) * d - k * 60 * size;
    g.fillStyle = radGrad(g, cx, cy + rr0 * 0.3, 0, rr0, [alpha(mix('#3a2a2c', FIRE, 0.5 * fire), 0.8 * fade), alpha('#1c1416', 0.7 * fade), alpha('#1c1416', 0)]);
    g.beginPath(); g.arc(cx, cy, rr0, 0, 7); g.fill(); }
  // bola de fuego
  if (fire > 0) { const R = 190 * size * (0.4 + grow) ; g.save(); g.globalCompositeOperation = 'lighter';
    g.fillStyle = radGrad(g, x, y - 70 * size, 0, R, [alpha('#fff6d8', fire), alpha('#ffc860', 0.9 * fire), alpha(FIRE, 0.6 * fire), alpha(FIRE, 0)]); g.beginPath(); g.arc(x, y - 70 * size, R, 0, 7); g.fill();
    for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + (r() - 0.5) * 2, d = (40 + r() * 90) * size * grow, rr1 = (50 + r() * 50) * size * fire;
      g.fillStyle = radGrad(g, x + Math.cos(a) * d, y - 80 * size + Math.sin(a) * d, 0, rr1, [alpha('#ffe2a0', 0.9 * fire), alpha(FIRE, 0)]); g.beginPath(); g.arc(x + Math.cos(a) * d, y - 80 * size + Math.sin(a) * d, rr1, 0, 7); g.fill(); }
    g.restore(); }
  if (!o.noDebris) for (let i = 0; i < 18; i++) { const a = -Math.PI / 2 + (r() - 0.5) * 2.6, v = (300 + r() * 600) * size, px = x + Math.cos(a) * v * k, py = y - 30 + Math.sin(a) * v * k + 500 * k * k;
    if (py < y + 40) { rr(g, px, py, 9 * size, 9 * size, 2); g.fillStyle = alpha('#140e0c', fade); g.fill(); } }
  return flash;
}
// fogonazos lejanos (horizonte)
export function farFlashes(g, t, y, w = E.W * 3, seed = 3) {
  const r = rng(seed);
  for (let i = 0; i < 7; i++) { const x = -E.W + r() * w, per = 1.6 + r() * 2.2, ph = r() * per, k = ((t + ph) % per) / per; const a = Math.max(0, 1 - k * 4);
    if (a > 0) { glow(g, x, y, 380, FIRE, 0.5 * a); circle(g, x, y - 10, 18 * a, alpha('#ffe2a0', a)); } }
}
export function cannon(g, x, GY, s = 1, facing = 1, recoil = 0, M) {
  const ink = '#0e0b10';
  g.save(); g.translate(x, GY); g.scale(facing * s, s);
  g.save(); g.translate(-recoil * 30, 0); g.rotate(-0.35);
  rr(g, -20, -110, 260, 30, 10); g.fillStyle = ink; g.fill(); rr(g, 220, -114, 28, 38, 6); g.fill();
  if (M) { g.fillStyle = alpha(M.rim, 0.7); g.fillRect(-10, -112, 240, 4); }
  g.restore();
  poly(g, [[-90, 0], [-40, -90], [40, -90], [90, -40], [60, 0]], ink);
  rr(g, -40, -150, 60, 80, 6); g.fillStyle = ink; g.fill();
  for (const dx of [-30, 40]) { circle(g, dx, -34, 46, '#141016'); g.strokeStyle = M ? alpha(M.rim, 0.6) : '#333'; g.lineWidth = 4; g.beginPath(); g.arc(dx, -34, 46, -2.4, -0.8); g.stroke(); circle(g, dx, -34, 10, '#2a2228'); }
  g.restore();
}
export function sandbags(g, x, y, n = 6, s = 1, c = '#3a3028') {
  for (let row = 0; row < 3; row++) for (let i = 0; i < n - row; i++) { rr(g, x + (i + row * 0.5) * 90 * s, y - (row + 1) * 40 * s, 92 * s, 44 * s, 20 * s); g.fillStyle = shade(c, -row * 0.08 - (i % 2) * 0.06); g.fill(); }
}
export function monastery(g, x, y, s, c) {
  g.fillStyle = c; g.fillRect(x - 160 * s, y - 70 * s, 320 * s, 70 * s); g.fillRect(x - 40 * s, y - 130 * s, 80 * s, 70 * s);
  poly(g, [[x - 50 * s, y - 130 * s], [x, y - 175 * s], [x + 50 * s, y - 130 * s]], c);
  for (let i = 0; i < 8; i++) g.fillRect(x - 150 * s + i * 40 * s, y - 85 * s, 22 * s, 16 * s);
}
export function frente(g, t, cam, o = {}) {
  const M = mood(o.mood || 'night'), GY = GYf(), CX = E.W / 2, quiet = !!o.quiet;
  layer(g, cam, 0.1, (g) => {
    backdrop(g, quiet ? M.sky : [M.sky[0], M.sky[1], mix(M.sky[2], FIRE, 0.35)]);
    if (!quiet) FX.stars(g, t, { count: 60, area: [-E.W, -E.H, E.W * 3, E.H * 1.2], color: '#dfe4ff' });
    else FX.sun(g, CX + V(300, 180), GY - V(420, 640), V(60, 70), '#fff1d8', M.key, 4);
  });
  layer(g, cam, 0.25, (g) => {
    const hy = GY - V(330, 520);
    if (!quiet) farFlashes(g, t, hy + 40, E.W * 3, 5);
    FX.hills(g, { y: hy, amp: V(70, 90), color: mix(M.sky[1], M.dark, 0.6), seed: 4, freq: 0.003 });
    // monte Cassino con el monasterio
    const mx = CX + V(380, 160), my = hy - V(120, 200);
    g.fillStyle = mix(M.sky[1], M.dark, 0.72); g.beginPath(); g.moveTo(mx - 900, hy + 80); g.quadraticCurveTo(mx - 250, my - 10, mx, my); g.quadraticCurveTo(mx + 250, my - 10, mx + 900, hy + 80); g.fill();
    monastery(g, mx, my + 6, V(0.8, 0.75), mix(M.sky[1], M.dark, 0.72));
    if (!quiet) glow(g, mx, my, 300, FIRE, 0.12 + 0.08 * Math.sin(t * 3));
  });
  layer(g, cam, 0.5, (g) => {
    const hy = GY - V(170, 300);
    FX.hills(g, { y: hy, amp: V(40, 50), color: mix(M.wall, M.dark, 0.5), seed: 9, freq: 0.005 });
    if (!quiet) farFlashes(g, t + 0.7, hy + 10, E.W * 3, 11);
    for (const x of [-500, -120, 260, 900, 1400]) { seg(g, [[x, hy + 30], [x + 8, hy - 70], [x - 30, hy - 110]], 8, M.dark); }
    FX.fog(g, hy - 40, 160, quiet ? M.fog : '#6a4a50', 0.35);
  });
  layer(g, cam, 0.85, (g) => {
    g.fillStyle = linGrad(g, 0, GY - 30, 0, GY + 700, [shade(M.floor, 0.1), M.dark, shade(M.dark, -0.3)]); g.fillRect(-E.W, GY - 30, E.W * 3, E.H * 2);
    FX.floorLines(g, GY - 30, GY + 700, 'rgba(0,0,0,.25)', 0.09);
    // alambre de púas
    g.strokeStyle = alpha('#0a0a0e', 0.8); g.lineWidth = 2; for (let k = 0; k < 2; k++) { g.beginPath(); for (let x = -E.W; x < E.W * 2; x += 20) g.lineTo(x, GY - 60 - k * 18 + Math.sin(x * 0.05 + k) * 8); g.stroke(); }
    for (let x = -E.W + 80; x < E.W * 2; x += 260) seg(g, [[x, GY - 20], [x + 6, GY - 110]], 6, '#0c0a0e');
    FX.pool(g, CX, GY + 20, 420, 60, quiet ? M.key : FIRE, quiet ? 0.18 : 0.22);
  });
  return { GY, CX, M };
}
