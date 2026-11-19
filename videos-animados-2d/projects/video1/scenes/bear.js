// bear.js — Wojtek: oso estilizado con la misma lógica que las figuras (silueta oscura + borde de luz + cara mínima).
// drawBear(g, { x, y, s, facing, pose, expr, blink, look, rim:{color,dir,w}, cub, crate, shadow, alpha, tilt })
// bearFace(g, cx, cy, r, { expr, blink, look, rimColor, rimSide, tilt, open })
import { S, seg, circle, ring, rr, poly, alpha, shade, mix, lerp, glow, linGrad } from '/engine/core.js';
import { BEAR } from './cast.js';

const P = (o) => o;
// unidades locales: mirando a +x, pies en y=0; una persona mide ~234
export const BPOSES = {
  stand:  P({ head: [16, -250], sh: [6, -196], hip: [0, -112], eF: [26, -150], hF: [32, -110], eB: [-4, -150], hB: [0, -108], kF: [12, -56], fF: [16, 0], kB: [-10, -56], fB: [-14, 0] }),
  carry:  P({ head: [14, -252], sh: [6, -196], hip: [0, -112], eF: [44, -172], hF: [74, -172], eB: [36, -176], hB: [66, -178], kF: [12, -56], fF: [16, 0], kB: [-10, -56], fB: [-14, 0] }),
  hug:    P({ head: [10, -246], sh: [4, -192], hip: [0, -112], eF: [40, -160], hF: [52, -136], eB: [34, -164], hB: [46, -140], kF: [12, -56], fF: [16, 0], kB: [-10, -56], fB: [-14, 0] }),
  salute: P({ head: [16, -250], sh: [6, -196], hip: [0, -112], eF: [38, -222], hF: [30, -262], eB: [-4, -150], hB: [0, -108], kF: [12, -56], fF: [16, 0], kB: [-10, -56], fB: [-14, 0] }),
  raise:  P({ head: [14, -252], sh: [6, -196], hip: [0, -112], eF: [30, -240], hF: [40, -284], eB: [-16, -238], hB: [-24, -282], kF: [14, -56], fF: [20, 0], kB: [-12, -56], fB: [-18, 0] }),
  wrestle:P({ head: [34, -226], sh: [20, -180], hip: [0, -104], eF: [58, -176], hF: [86, -196], eB: [50, -186], hB: [80, -212], kF: [20, -52], fF: [28, 0], kB: [-18, -52], fB: [-30, 0] }),
  drink:  P({ head: [8, -246], sh: [4, -194], hip: [0, -112], eF: [34, -200], hF: [34, -236], eB: [28, -196], hB: [26, -232], kF: [12, -56], fF: [16, 0], kB: [-10, -56], fB: [-14, 0] }),
  sit:    P({ head: [14, -186], sh: [6, -136], hip: [0, -52], eF: [26, -96], hF: [40, -66], eB: [16, -96], hB: [28, -64], kF: [44, -36], fF: [70, -4], kB: [32, -36], fB: [56, -4] }),
  sitUp:  P({ head: [20, -196], sh: [8, -140], hip: [0, -52], eF: [30, -104], hF: [50, -88], eB: [20, -104], hB: [40, -90], kF: [44, -36], fF: [70, -4], kB: [32, -36], fB: [56, -4] }),
  four:   P({ head: [104, -96], sh: [56, -92], hip: [-52, -86], eF: [64, -46], hF: [70, 0], eB: [44, -46], hB: [46, 0], kF: [-40, -42], fF: [-34, 0], kB: [-60, -42], fB: [-62, 0], four: true }),
};
export const bpose = (n) => (typeof n === 'string' ? BPOSES[n] || BPOSES.stand : n);
export function bposesAt(t, keys, blend = 0.3) {
  let a = keys[0], b = null;
  for (let i = 0; i < keys.length; i++) if (t >= keys[i][0]) { a = keys[i]; b = keys[i + 1] || null; }
  const pa = bpose(a[1]); if (!b) return pa;
  const k = Math.min(1, Math.max(0, (t - (b[0] - blend)) / blend)); if (k <= 0) return pa;
  const pb = bpose(b[1]), e = k * k * (3 - 2 * k), out = { four: k > 0.5 ? pb.four : pa.four };
  for (const key of Object.keys(pa)) if (Array.isArray(pa[key])) out[key] = [lerp(pa[key][0], pb[key][0], e), lerp(pa[key][1], pb[key][1], e)];
  return out;
}
export function bbreathe(p, t, amt = 1, seed = 0) {
  const b = Math.sin(t * 2.1 + seed) * 2.2 * amt, out = { ...p };
  for (const k of ['head', 'sh', 'eF', 'hF', 'eB', 'hB']) out[k] = [p[k][0], p[k][1] - b * (k === 'head' ? 1.2 : 1)];
  return out;
}

function shell(g, x, y, s, ang = -Math.PI / 2) {
  g.save(); g.translate(x, y); g.rotate(ang + Math.PI / 2); g.scale(s, s);
  rr(g, -9, -10, 18, 42, 3); g.fillStyle = '#b8892e'; g.fill();
  g.fillStyle = '#e8c070'; g.fillRect(-9, -10, 5, 42);
  g.fillStyle = '#6f6a5e'; g.beginPath(); g.moveTo(-9, -10); g.quadraticCurveTo(-9, -34, 0, -40); g.quadraticCurveTo(9, -34, 9, -10); g.closePath(); g.fill();
  g.fillStyle = 'rgba(255,255,255,.35)'; g.fillRect(-7, -22, 3, 10);
  g.restore();
}
export { shell };
// caja de proyectiles (madera + latón)
export function crate(g, x, y, w, h, o = {}) {
  const wood = o.wood || '#6a4a2c', dark = shade(wood, -0.45), rim = o.rim;
  g.save(); g.translate(x, y); if (o.rot) g.rotate(o.rot);
  if (rim) { rr(g, -w / 2 - 3, -h - 4, w + 6, h + 6, 6); g.fillStyle = rim; g.fill(); }
  for (let i = 0; i < 4; i++) shell(g, -w * 0.32 + i * w * 0.21, -h + 6, w / 160);
  rr(g, -w / 2, -h, w, h, 5); g.fillStyle = linGrad(g, 0, -h, 0, 0, [shade(wood, 0.12), dark]); g.fill();
  g.fillStyle = shade(wood, -0.25); for (let i = 1; i < 3; i++) g.fillRect(-w / 2, -h + (h * i) / 3 - 2, w, 4);
  g.strokeStyle = shade(wood, -0.55); g.lineWidth = Math.max(2, w * 0.03); g.strokeRect(-w / 2 + 4, -h + 4, w - 8, h - 8);
  g.fillStyle = alpha('#e8dcc0', 0.55); g.font = `900 ${Math.round(h * 0.22)}px Nunito`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(o.label ?? '25 PDR', 0, -h * 0.45);
  g.restore();
}

function limb(g, pts, w, col) { seg(g, pts, w, col); }
function parts(g, p, fur, far, muzzle, sil, grow, cub) {
  const L = 34 + grow, A = 30 + grow, HR = (cub ? 44 : 36) + grow;
  // patas lejanas
  limb(g, [p.hip, p.kB, p.fB], L - 2, sil ? fur : far);
  limb(g, [p.sh, p.eB, p.hB], A - 2, sil ? fur : far);
  if (!sil) { circle(g, p.fB[0] + 6, p.fB[1] - 6, 14, far); circle(g, p.hB[0], p.hB[1], 14, far); }
  // cuerpo
  if (p.four) { g.fillStyle = fur; g.beginPath(); g.ellipse((p.sh[0] + p.hip[0]) / 2, (p.sh[1] + p.hip[1]) / 2 - 6, Math.hypot(p.sh[0] - p.hip[0], p.sh[1] - p.hip[1]) / 2 + 44 + grow, 52 + grow, Math.atan2(p.sh[1] - p.hip[1], p.sh[0] - p.hip[0]), 0, 7); g.fill(); }
  else { seg(g, [p.hip, p.sh], 78 + grow * 2, fur); g.fillStyle = fur; g.beginPath(); g.ellipse(p.hip[0] + 4, p.hip[1] - 22, 48 + grow, 56 + grow, 0, 0, 7); g.fill(); }
  // patas cercanas
  limb(g, [p.hip, p.kF, p.fF], L, fur);
  if (!sil) circle(g, p.fF[0] + 7, p.fF[1] - 7, 15, fur);
  // cabeza
  const [hx, hy] = p.head;
  circle(g, hx - HR * 0.42, hy - HR * 0.8, HR * 0.36 + grow * 0.3, fur); circle(g, hx + HR * 0.32, hy - HR * 0.86, HR * 0.36 + grow * 0.3, fur);
  seg(g, [p.sh, [hx - 4, hy + 10]], 50 + grow, fur);
  circle(g, hx, hy, HR, fur);
  g.fillStyle = sil ? fur : muzzle; g.beginPath(); g.ellipse(hx + HR * 0.78, hy + HR * 0.22, HR * 0.5 + grow * 0.5, HR * 0.38 + grow * 0.5, 0.1, 0, 7); g.fill();
  limb(g, [p.sh, p.eF, p.hF], A, fur);
  if (!sil) circle(g, p.hF[0], p.hF[1], 15, fur);
  return HR;
}
function bearEyes(g, hx, hy, HR, o, col, ink) {
  const ex = o.expr || 'neutral', ey = hy - HR * 0.12, xs = [hx + HR * 0.12, hx + HR * 0.52], look = o.look || [0, 0];
  // ojos
  xs.forEach((x, i) => {
    const s = i === 0 ? 0.85 : 1;
    if (o.blink || ex === 'sleepy') { seg(g, [[x - HR * 0.1 * s, ey], [x + HR * 0.1 * s, ey]], HR * 0.08, col); return; }
    if (ex === 'happy' || ex === 'joy') { g.strokeStyle = col; g.lineWidth = HR * 0.09; g.beginPath(); g.arc(x, ey + HR * 0.05, HR * 0.11 * s, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); return; }
    if (ex === 'surprised' || ex === 'awe' || ex === 'shocked') { ring(g, x, ey, HR * 0.16 * s, HR * 0.07, col); circle(g, x + look[0] * 3, ey + look[1] * 3, HR * 0.06, col); return; }
    circle(g, x + look[0] * HR * 0.04, ey + look[1] * HR * 0.04, HR * 0.1 * s, col);
  });
  const by = ey - HR * 0.27, bw = HR * 0.12;
  if (ex === 'sad' || ex === 'worried') { seg(g, [[xs[0] - bw, by - 3], [xs[0] + bw, by + 3]], HR * 0.06, col); seg(g, [[xs[1] - bw, by + 3], [xs[1] + bw, by - 3]], HR * 0.06, col); }
  if (ex === 'determined' || ex === 'angry') { seg(g, [[xs[0] - bw, by - 4], [xs[0] + bw, by + 4]], HR * 0.07, col); seg(g, [[xs[1] - bw, by + 4], [xs[1] + bw, by - 4]], HR * 0.07, col); }
  // nariz + boca sobre el hocico
  const nx = hx + HR * 1.1, ny = hy + HR * 0.08;
  g.fillStyle = ink; g.beginPath(); g.ellipse(nx, ny, HR * 0.16, HR * 0.11, 0, 0, 7); g.fill();
  g.strokeStyle = ink; g.lineWidth = HR * 0.06; g.lineCap = 'round'; g.beginPath();
  if (ex === 'happy' || ex === 'joy' || ex === 'smile') { g.moveTo(nx - HR * 0.3, hy + HR * 0.36); g.quadraticCurveTo(nx - HR * 0.12, hy + HR * 0.5, nx + HR * 0.02, hy + HR * 0.36); }
  else if (ex === 'surprised' || ex === 'awe' || ex === 'shocked') { g.ellipse(nx - HR * 0.15, hy + HR * 0.42, HR * 0.07, HR * 0.09, 0, 0, 7); }
  else if (o.chew) { const c = Math.abs(Math.sin(o.chew * 14)); g.ellipse(nx - HR * 0.15, hy + HR * 0.4, HR * 0.1, HR * (0.02 + 0.08 * c), 0, 0, 7); }
  else { g.moveTo(nx - HR * 0.28, hy + HR * 0.4); g.lineTo(nx - HR * 0.02, hy + HR * 0.4); }
  g.stroke();
}
export function drawBear(g, o) {
  const st = S(), fur = o.fur || BEAR.fur, far = o.far || BEAR.far, muzzle = o.hideFace ? fur : BEAR.muzzle;
  const p = bpose(o.pose || 'stand'), cub = !!o.cub, s = (o.s ?? 1) * (cub ? 0.42 : 1), f = o.facing ?? 1;
  const rim = o.rim === false ? null : { dir: [-0.8, -0.5], w: st.rimWidth || 4, color: '#ffc68a', ...(o.rim || {}) };
  g.save(); if (o.alpha != null) g.globalAlpha *= o.alpha;
  if (o.shadow !== false) { g.fillStyle = 'rgba(0,0,0,.3)'; g.beginPath(); g.ellipse(o.x + (p.four ? 0 : 0) * s * f, o.y + 2, (p.four ? 120 : 60) * s, 9 * s, 0, 0, 7); g.fill(); }
  const tf = (dx = 0, dy = 0) => { g.translate(o.x + dx, o.y + dy); g.scale(f * s, s); if (o.tilt) { g.translate(p.hip[0], p.hip[1]); g.rotate(o.tilt); g.translate(-p.hip[0], -p.hip[1]); } };
  if (rim) { g.save(); tf(rim.dir[0] * rim.w * 1.2, rim.dir[1] * rim.w * 1.2); parts(g, p, rim.color, rim.color, rim.color, true, 2.4, cub); g.restore(); }
  g.save(); tf();
  const HR = parts(g, p, fur, far, muzzle, false, 0, cub);
  if (o.stripes) { const [ex, ey] = [lerp(p.sh[0], p.eF[0], 0.55), lerp(p.sh[1], p.eF[1], 0.55)]; for (let i = 0; i < 2; i++) seg(g, [[ex - 12, ey - 4 + i * 9], [ex, ey + 4 + i * 9], [ex + 12, ey - 4 + i * 9]], 4, '#ffd47e'); }
  if (!o.hideFace) bearEyes(g, p.head[0], p.head[1], HR, o, st.feature, BEAR.nose);
  if (o.crate) { const cx = (p.hF[0] + p.hB[0]) / 2 + 8, cy = (p.hF[1] + p.hB[1]) / 2 + 44; crate(g, cx, cy, 110, 72, { rim: rim ? alpha(rim.color, 0.9) : null }); circle(g, cx - 50, cy - 40, 16, fur); }
  o.extra?.(g, p);
  g.restore();
  g.restore();
}
export function bearHead(o) { const p = bpose(o.pose || 'stand'), s = (o.s ?? 1) * (o.cub ? 0.42 : 1), f = o.facing ?? 1; return [o.x + p.head[0] * s * f, o.y + p.head[1] * s, (o.cub ? 44 : 36) * s]; }

// primer plano gigante, de frente
export function bearFace(g, cx, cy, r, o = {}) {
  const st = S(), fur = BEAR.fur, col = st.feature, ink = BEAR.nose, rc = o.rimColor || '#ffc68a', side = o.rimSide ?? -1, ex = o.expr || 'neutral';
  g.save(); g.translate(cx, cy); if (o.tilt) g.rotate(o.tilt);
  // hombros
  g.fillStyle = shade(fur, -0.15); g.beginPath(); g.ellipse(0, r * 1.7, r * 1.45, r * 0.95, 0, Math.PI, Math.PI * 2); g.fill();
  // borde de luz (orejas + cabeza)
  const sil = (c, k) => { circle(g, -r * 0.72 + side * k, -r * 0.7 - k * 0.5, r * 0.34 + k, c); circle(g, r * 0.72 + side * k, -r * 0.7 - k * 0.5, r * 0.34 + k, c); circle(g, side * k, 0, r + k, c); };
  sil(rc, r * 0.05);
  sil(fur, 0);
  circle(g, -r * 0.72, -r * 0.7, r * 0.17, shade(BEAR.muzzle, -0.35)); circle(g, r * 0.72, -r * 0.7, r * 0.17, shade(BEAR.muzzle, -0.35));
  // hocico
  g.fillStyle = BEAR.muzzle; g.beginPath(); g.ellipse(0, r * 0.38, r * 0.46, r * 0.36, 0, 0, 7); g.fill();
  g.fillStyle = ink; g.beginPath(); g.ellipse(0, r * 0.22, r * 0.18, r * 0.12, 0, 0, 7); g.fill();
  g.fillStyle = 'rgba(255,255,255,.35)'; g.beginPath(); g.ellipse(-r * 0.05, r * 0.18, r * 0.06, r * 0.03, 0, 0, 7); g.fill();
  seg(g, [[0, r * 0.32], [0, r * 0.44]], r * 0.04, ink);
  g.strokeStyle = ink; g.lineWidth = r * 0.045; g.lineCap = 'round'; g.beginPath();
  if (o.open || ex === 'surprised' || ex === 'awe' || ex === 'shocked') { g.ellipse(0, r * 0.56, r * 0.1, r * (0.06 + 0.08 * (o.open ?? 1)), 0, 0, 7); g.fillStyle = '#3a0d0d'; g.fill(); }
  else if (ex === 'happy' || ex === 'smile' || ex === 'joy') { g.moveTo(-r * 0.2, r * 0.48); g.quadraticCurveTo(-r * 0.1, r * 0.58, 0, r * 0.46); g.quadraticCurveTo(r * 0.1, r * 0.58, r * 0.2, r * 0.48); g.stroke(); }
  else if (ex === 'sad') { g.moveTo(-r * 0.16, r * 0.58); g.quadraticCurveTo(0, r * 0.48, r * 0.16, r * 0.58); g.stroke(); }
  else { g.moveTo(-r * 0.16, r * 0.5); g.quadraticCurveTo(-r * 0.08, r * 0.55, 0, r * 0.46); g.quadraticCurveTo(r * 0.08, r * 0.55, r * 0.16, r * 0.5); g.stroke(); }
  // ojos
  const look = o.look || [0, 0], ey = -r * 0.16, xs = [-r * 0.36, r * 0.36];
  xs.forEach((x) => {
    if (o.blink) { seg(g, [[x - r * 0.1, ey], [x + r * 0.1, ey]], r * 0.06, col); return; }
    if (ex === 'happy' || ex === 'joy') { g.strokeStyle = col; g.lineWidth = r * 0.07; g.beginPath(); g.arc(x, ey + r * 0.04, r * 0.1, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); return; }
    if (ex === 'surprised' || ex === 'awe' || ex === 'shocked') { ring(g, x, ey, r * 0.15, r * 0.06, col); circle(g, x + look[0] * r * 0.05, ey + look[1] * r * 0.05, r * 0.06, col); return; }
    circle(g, x + look[0] * r * 0.04, ey + look[1] * r * 0.04, r * 0.09, col);
    if (o.shine) circle(g, x + r * 0.03, ey - r * 0.03, r * 0.025, '#ffffff');
  });
  const by = ey - r * 0.24;
  if (ex === 'sad' || ex === 'worried') xs.forEach((x, i) => seg(g, [[x - r * 0.12, by + (i ? 1 : -1) * r * -0.04], [x + r * 0.12, by + (i ? -1 : 1) * r * -0.04]], r * 0.05, col));
  if (ex === 'determined') xs.forEach((x, i) => seg(g, [[x - r * 0.12, by + (i ? 1 : -1) * r * 0.05], [x + r * 0.12, by + (i ? -1 : 1) * r * 0.05]], r * 0.055, col));
  if (ex === 'surprised' || ex === 'awe') xs.forEach((x) => { g.strokeStyle = col; g.lineWidth = r * 0.05; g.beginPath(); g.arc(x, by + r * 0.08, r * 0.12, Math.PI * 1.2, Math.PI * 1.8); g.stroke(); });
  g.restore();
}
