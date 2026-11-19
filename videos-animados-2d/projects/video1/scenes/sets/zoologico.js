// sets/zoologico.js — zoológico de Edimburgo bajo la lluvia: castillo en la colina, rocas del recinto, reja, farol frío.
import { E, V, mood, layer, backdrop, rr, seg, circle, poly, linGrad, glow, alpha, shade, mix } from '/engine/core.js';
import * as FX from '/engine/fx2d.js';

export const GYz = () => E.H * V(0.8, 0.68);
function castle(g, x, y, s, c) {
  g.fillStyle = c; g.beginPath(); g.moveTo(x - 700 * s, y + 60 * s); g.quadraticCurveTo(x - 200 * s, y - 40 * s, x - 100 * s, y - 120 * s); g.lineTo(x + 260 * s, y - 120 * s); g.quadraticCurveTo(x + 420 * s, y - 20 * s, x + 800 * s, y + 60 * s); g.fill();
  g.fillRect(x - 120 * s, y - 220 * s, 360 * s, 110 * s); g.fillRect(x - 90 * s, y - 300 * s, 70 * s, 90 * s); g.fillRect(x + 140 * s, y - 280 * s, 80 * s, 70 * s);
  for (let i = 0; i < 9; i++) g.fillRect(x - 120 * s + i * 42 * s, y - 236 * s, 22 * s, 18 * s);
  poly(g, [[x - 98 * s, y - 300 * s], [x - 55 * s, y - 350 * s], [x - 12 * s, y - 300 * s]], c);
}
export function zoologico(g, t, cam, o = {}) {
  const M = mood(o.mood || 'storm'), GY = GYz(), CX = E.W / 2;
  layer(g, cam, 0.1, (g) => { backdrop(g, M.sky); FX.clouds(g, { y: GY - V(900, 1500), h: 300, color: '#c8d0ee', a: 0.1, seed: 12, count: 8 }); });
  layer(g, cam, 0.25, (g) => {
    const y = GY - V(330, 520);
    castle(g, CX - V(200, 120), y, V(0.9, 0.75), mix(M.sky[1], M.dark, 0.6));
    for (let i = 0; i < 10; i++) circle(g, CX - V(200, 120) - 110 + i * 34, y - V(200, 170), 3, alpha(M.practical, 0.7));
    FX.fog(g, y - 60, 220, M.fog, 0.35);
  });
  layer(g, cam, 0.5, (g) => {
    const y = GY - V(150, 260);
    for (const x of [-700, -300, 200, 650, 1100]) FX.tree(g, CX + x, y + 20, V(1.4, 1.6), mix(M.wall, M.dark, 0.5));
    g.fillStyle = shade(M.wall, -0.2); g.fillRect(-E.W, y, E.W * 3, 40); // muro del recinto
    g.fillStyle = shade(M.wall, -0.45); g.fillRect(-E.W, y + 40, E.W * 3, 600);
    FX.lampPost(g, CX + V(520, 330), y + 40, V(330, 420), { color: '#0c0e18', light: M.practical, a: 0.25 });
  });
  layer(g, cam, 0.8, (g) => {
    g.fillStyle = linGrad(g, 0, GY - 40, 0, GY + 700, [shade(M.floor, 0.12), M.dark]); g.fillRect(-E.W, GY - 40, E.W * 3, E.H * 2);
    // rocas
    for (const [dx, w, h] of [[-V(560, 380), 380, 150], [-V(280, 200), 240, 90], [V(520, 380), 420, 180]]) { g.fillStyle = shade(M.wall, -0.1); g.beginPath(); g.ellipse(CX + dx, GY - 10, w / 2, h, 0, Math.PI, Math.PI * 2); g.fill(); g.fillStyle = alpha(M.rim, 0.25); g.beginPath(); g.ellipse(CX + dx - 10, GY - 10 - h * 0.6, w * 0.35, h * 0.28, 0, Math.PI * 1.1, Math.PI * 1.7); g.fill(); }
    // charcos
    for (const [dx, w] of [[-200, 200], [260, 160]]) { g.fillStyle = alpha(M.sky[2] || M.sky[1], 0.35); g.beginPath(); g.ellipse(CX + dx, GY + 60, w, 16, 0, 0, 7); g.fill(); }
    FX.pool(g, CX + V(300, 200), GY + 20, 360, 60, M.practical, 0.2);
  });
  return { GY, CX, M };
}
// reja en primer plano (barrotes)
export function fence(g, cam, a = 1) {
  layer(g, cam, 1.4, (g) => { g.globalAlpha *= a; for (let x = -E.W; x < E.W * 2; x += V(130, 120)) { g.fillStyle = '#0a0b12'; g.fillRect(x, -E.H, 18, E.H * 3); } g.fillRect(-E.W, E.H * 0.12, E.W * 3, 16); g.fillRect(-E.W, E.H * 0.88, E.W * 3, 16); });
}
