import React from 'react';
import {AbsoluteFill, Easing, Sequence, continueRender, delayRender, interpolate, staticFile, useCurrentFrame} from 'remotion';

const BANGERS = 'Bangers';
if (typeof window !== 'undefined' && typeof FontFace !== 'undefined') {
  const h = delayRender('fuente Bangers');
  const ff = new FontFace(BANGERS, `url(${staticFile('Bangers.ttf')})`);
  ff.load().then((x) => {
    document.fonts.add(x);
    continueRender(h);
  });
}

// ---------- Tiempos (30 fps) ----------
// S1 plano general 0-100 · S2 cara 100-190 · S3 cuervo 190-290 · S4 ojos + ¡CRAC! 290-370 · S5 final 370-480
export const SCENES = [
  {from: 0, dur: 100},
  {from: 100, dur: 90},
  {from: 190, dur: 100},
  {from: 290, dur: 80},
  {from: 370, dur: 110},
];
export const TOTAL = 480;
const SLIDE = 8; // cuadros que tarda una viñeta en entrar

const INK = '#111';
const SKIN = '#e2a473';
const SKIN_D = '#b87650';
const HAIR = '#2a1a10';
const SHIRT = '#cdb68a';
const SHIRT_D = '#9c855c';
const JEANS = '#3d5a80';
const JEANS_D = '#2a3f5c';
const WOOD = '#8a5a2b';
const WOOD_D = '#5e3b1a';
const ROPE = '#c9a35a';
const BANDANA = '#c0282d';

const ease = Easing.bezier(0.45, 0, 0.55, 1);
const lerp = (f: number, a: number, b: number, from: number, to: number) =>
  interpolate(f, [a, b], [from, to], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

// ---------- Utilidades de cómic ----------
const Defs: React.FC = () => (
  <defs>
    <pattern id="ht" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <circle cx="8" cy="8" r="3.4" fill="#000" />
    </pattern>
    <pattern id="htRed" width="18" height="18" patternUnits="userSpaceOnUse" patternTransform="rotate(30)">
      <circle cx="9" cy="9" r="4.5" fill="#7a0d12" />
    </pattern>
    <linearGradient id="skyG" x1="0" y1="-600" x2="0" y2="1420" gradientUnits="userSpaceOnUse">
      <stop offset="0" stopColor="#2b1840" />
      <stop offset="0.38" stopColor="#8c2a4e" />
      <stop offset="0.68" stopColor="#e2603a" />
      <stop offset="1" stopColor="#ffc46a" />
    </linearGradient>
    <linearGradient id="fadeTop" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stopColor="#fff" stopOpacity="0.55" />
      <stop offset="0.5" stopColor="#fff" stopOpacity="0" />
    </linearGradient>
    <mask id="maskTop">
      <rect x="0" y="0" width="1080" height="1920" fill="url(#fadeTop)" />
    </mask>
  </defs>
);

const Caption: React.FC<{lines: string[]; x?: number; y?: number; show: number}> = ({lines, x = 70, y = 70, show}) => {
  const w = Math.max(...lines.map((l) => l.length)) * 31 + 60;
  const h = lines.length * 62 + 40;
  return (
    <g opacity={show} transform={`translate(${x + (1 - show) * -30},${y})`}>
      <rect x={8} y={8} width={w} height={h} fill={INK} />
      <rect width={w} height={h} fill="#ffe46b" stroke={INK} strokeWidth={6} />
      {lines.map((l, i) => (
        <text key={i} x={30} y={68 + i * 62} fontFamily={BANGERS} fontSize={56} fill={INK} letterSpacing={1.5}>
          {l}
        </text>
      ))}
    </g>
  );
};

const Bubble: React.FC<{
  lines: string[];
  x: number;
  y: number;
  tail: [number, number];
  show: number;
  size?: number;
}> = ({lines, x, y, tail, show, size = 58}) => {
  const w = Math.max(...lines.map((l) => l.length)) * size * 0.52 + 90;
  const h = lines.length * size * 1.05 + 70;
  const s = interpolate(show, [0, 0.7, 1], [0.3, 1.08, 1]);
  return (
    <g opacity={Math.min(1, show * 2)} transform={`translate(${x},${y}) scale(${s})`}>
      <path d={`M${-w * 0.12},${h * 0.32} L${tail[0]},${tail[1]} L${w * 0.12},${h * 0.38} Z`} fill="#fff" stroke={INK} strokeWidth={6} strokeLinejoin="round" />
      <ellipse rx={w / 2} ry={h / 2} fill="#fff" stroke={INK} strokeWidth={6} />
      <path d={`M${-w * 0.1},${h * 0.36} L${tail[0]},${tail[1]} L${w * 0.1},${h * 0.4}`} fill="#fff" />
      {lines.map((l, i) => (
        <text
          key={i}
          x={0}
          y={(i - (lines.length - 1) / 2) * size * 1.05 + size * 0.36}
          textAnchor="middle"
          fontFamily={BANGERS}
          fontSize={size}
          fill={INK}
          letterSpacing={1.5}
        >
          {l}
        </text>
      ))}
    </g>
  );
};

const SpeedLines: React.FC<{cx: number; cy: number; color: string; f: number; n?: number}> = ({cx, cy, color, f, n = 64}) => {
  const lines = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + ((i * 37) % 7) * 0.01;
    const r0 = 330 + (((i * 53 + f * 13) % 160) as number);
    const r1 = 2200;
    const wdt = 6 + ((i * 29) % 5) * 5;
    const ax = Math.cos(a), ay = Math.sin(a);
    const px = -ay * wdt, py = ax * wdt;
    lines.push(
      <path
        key={i}
        d={`M${cx + ax * r0},${cy + ay * r0} L${cx + ax * r1 + px},${cy + ay * r1 + py} L${cx + ax * r1 - px},${cy + ay * r1 - py} Z`}
        fill={color}
      />,
    );
  }
  return <g>{lines}</g>;
};

// Viñeta: papel, marco negro y la entrada deslizándose como página de cómic
const Panel: React.FC<{children: React.ReactNode; enter: boolean; dir?: number}> = ({children, enter, dir = 1}) => {
  const f = useCurrentFrame();
  const t = enter ? lerp(f, 0, SLIDE, 0, 1) : 1;
  const x = (1 - t) * 1150 * dir;
  const rot = (1 - t) * 6 * dir;
  return (
    <AbsoluteFill style={{transform: `translateX(${x}px) rotate(${rot}deg)`, transformOrigin: '50% 100%'}}>
      <AbsoluteFill style={{background: '#f3ead6'}}>
        <svg width={1080} height={1920} viewBox="0 0 1080 1920">
          <Defs />
          <clipPath id="panelClip">
            <rect x={26} y={26} width={1028} height={1868} />
          </clipPath>
          <g clipPath="url(#panelClip)">{children}</g>
          <rect x={26} y={26} width={1028} height={1868} fill="none" stroke={INK} strokeWidth={12} />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Cam: React.FC<{cx: number; cy: number; z: number; shake?: number; children: React.ReactNode}> = ({cx, cy, z, shake = 0, children}) => (
  <g transform={`translate(${540 + shake},${960 + shake * 0.6}) scale(${z}) translate(${-cx},${-cy})`}>{children}</g>
);

// ---------- Mundo: desierto al atardecer ----------
const Vulture: React.FC<{x: number; y: number; f: number; s: number}> = ({x, y, f, s}) => {
  const flap = Math.sin(f * 0.25) * 14;
  return (
    <path
      transform={`translate(${x},${y}) scale(${s})`}
      d={`M-70,${-flap} Q-35,${-22 - flap} 0,0 Q35,${-22 - flap} 70,${-flap} Q35,${-6 - flap * 0.4} 0,12 Q-35,${-6 - flap * 0.4} -70,${-flap} Z`}
      fill="#1d1020"
    />
  );
};

const Desert: React.FC<{f: number; vultures?: boolean}> = ({f, vultures = true}) => (
  <g>
    <rect x={-2500} y={-2000} width={6000} height={3500} fill="url(#skyG)" />
    {/* sol con trama */}
    <circle cx={270} cy={1130} r={230} fill="#ffe07a" />
    <circle cx={270} cy={1130} r={230} fill="url(#ht)" opacity={0.12} />
    {/* nubes alargadas */}
    {[
      [-200, 760, 520],
      [650, 860, 420],
      [100, 980, 380],
    ].map(([x, y, w], i) => (
      <path key={i} d={`M${x},${y} q${w * 0.25},-28 ${w * 0.5},-6 q${w * 0.25},-30 ${w * 0.5},6 l0,14 l${-w},0 Z`} fill="#f39a7c" opacity={0.75} />
    ))}
    {/* mesetas al fondo */}
    <path d="M-2500,1320 L-300,1320 L-240,1180 L80,1170 L130,1320 L760,1320 L820,1220 L1060,1210 L1100,1320 L3500,1320 L3500,1500 L-2500,1500 Z" fill="#5a2b4a" stroke={INK} strokeWidth={5} />
    <path d="M-240,1180 L80,1170 L95,1215 L-225,1222 Z M820,1220 L1060,1210 L1072,1245 L832,1252 Z" fill="#3c1c34" />
    {/* cerro */}
    <path d="M-2500,1450 Q540,1280 3500,1460 L3500,3500 L-2500,3500 Z" fill="#d98b3a" stroke={INK} strokeWidth={6} />
    <path d="M-2500,1560 Q540,1430 3500,1580 L3500,3500 L-2500,3500 Z" fill="#bf6f2a" />
    <path d="M-2500,1700 Q540,1600 3500,1720 L3500,3500 L-2500,3500 Z" fill="url(#ht)" opacity={0.18} />
    {/* piedras y cactus */}
    <path d="M110,1470 q30,-40 70,-6 q20,10 12,24 l-90,0 Z" fill="#8a4a22" stroke={INK} strokeWidth={5} />
    <g transform="translate(900,1420)" stroke={INK} strokeWidth={5} fill="#4f6b2e">
      <rect x={-18} y={-170} width={36} height={180} rx={18} />
      <path d="M-18,-80 l-40,0 q-14,0 -14,-14 l0,-46 q0,-12 12,-12 q12,0 12,12 l0,32 l30,0 Z" />
      <path d="M18,-110 l34,0 q14,0 14,-14 l0,-36 q0,-12 -12,-12 q-12,0 -12,12 l0,22 l-24,0 Z" />
    </g>
    {vultures &&
      [0, 1, 2].map((i) => {
        const a = f * 0.02 + i * 2.1;
        return <Vulture key={i} x={540 + Math.cos(a) * (260 + i * 60)} y={300 + i * 40 + Math.sin(a) * 70} f={f + i * 9} s={0.55 + i * 0.12} />;
      })}
  </g>
);

// ---------- Personaje: Logan (diseño original: vaquero del desierto) ----------
const Head: React.FC<{tilt: number; eyes: number; angry?: boolean; hat?: boolean; sweat?: number; mouthOpen?: number}> = ({
  tilt,
  eyes,
  angry = false,
  hat = false,
  sweat = 0,
  mouthOpen = 0,
}) => (
  <g transform={`translate(0,112) rotate(${tilt})`}>
    {/* orejas */}
    <ellipse cx={-55} cy={6} rx={12} ry={18} fill={SKIN} stroke={INK} strokeWidth={6} />
    <ellipse cx={55} cy={6} rx={12} ry={18} fill={SKIN} stroke={INK} strokeWidth={6} />
    {/* cara */}
    <clipPath id="faceClip">
      <ellipse rx={54} ry={68} />
    </clipPath>
    <ellipse rx={54} ry={68} fill={SKIN} />
    <g clipPath="url(#faceClip)">
      <path d="M14,-80 Q70,-10 20,90 L90,90 L90,-80 Z" fill={SKIN_D} opacity={0.55} />
      <path d="M14,-80 Q70,-10 20,90 L90,90 L90,-80 Z" fill="url(#ht)" opacity={0.18} />
      {/* barba */}
      <path d="M-60,4 C-56,62 -22,78 0,78 C22,78 56,62 60,4 C44,34 26,42 0,42 C-26,42 -44,34 -60,4 Z" fill="#3b2617" />
      <path d="M-24,34 Q0,26 24,34 Q0,44 -24,34 Z" fill="#3b2617" />
    </g>
    <ellipse rx={54} ry={68} fill="none" stroke={INK} strokeWidth={6} />
    {/* boca */}
    {mouthOpen > 0.05 ? (
      <ellipse cx={0} cy={50} rx={14} ry={4 + mouthOpen * 8} fill="#4a1010" stroke={INK} strokeWidth={4} />
    ) : (
      <path d={angry ? 'M-16,50 L16,48' : 'M-14,52 Q0,46 14,52'} stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" />
    )}
    {/* nariz */}
    <path d="M0,4 L-8,26 Q0,30 8,26" stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    {/* ojos */}
    {[-1, 1].map((sd) => (
      <g key={sd} transform={`translate(${sd * 21},-6)`}>
        {eyes > 0.1 ? (
          <>
            <ellipse rx={11} ry={9 * eyes} fill="#fff" stroke={INK} strokeWidth={4} />
            <circle cx={0} cy={0} r={5 * Math.min(1, eyes + 0.3)} fill={INK} />
          </>
        ) : (
          <path d="M-12,0 Q0,7 12,0" stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" />
        )}
        <path
          d={angry ? (sd < 0 ? 'M-18,-22 L14,-12' : 'M18,-22 L-14,-12') : 'M-16,-18 Q0,-24 16,-18'}
          stroke={INK}
          strokeWidth={9}
          strokeLinecap="round"
        />
      </g>
    ))}
    {/* pelo despeinado */}
    {!hat && (
      <path
        d="M-60,-6 C-66,-70 -22,-96 8,-92 C52,-90 70,-52 60,-6 L50,-30 L42,-6 L32,-38 L18,-14 L6,-44 L-8,-16 L-22,-42 L-34,-10 L-46,-34 Z"
        fill={HAIR}
        stroke={INK}
        strokeWidth={5}
        strokeLinejoin="round"
      />
    )}
    {hat && (
      <g>
        <path d="M-48,-44 C-50,-110 50,-110 48,-44 Z" fill="#6b4423" stroke={INK} strokeWidth={6} />
        <path d="M-46,-56 L46,-56 L47,-44 L-47,-44 Z" fill="#2b1a0e" />
        <path d="M-118,-40 Q-60,-62 0,-58 Q60,-62 118,-40 Q60,-26 0,-30 Q-60,-26 -118,-40 Z" fill="#7a4e28" stroke={INK} strokeWidth={6} strokeLinejoin="round" />
      </g>
    )}
    {/* sudor */}
    {sweat > 0 &&
      [
        [-44, -30],
        [38, -40],
        [48, 10],
      ].map(([x, y], i) => (
        <path
          key={i}
          transform={`translate(${x},${y + ((sweat * 40 + i * 13) % 26)})`}
          d="M0,-12 Q8,0 0,6 Q-8,0 0,-12 Z"
          fill="#cfefff"
          stroke={INK}
          strokeWidth={3}
        />
      ))}
  </g>
);

const Limb: React.FC<{pts: [number, number][]; color: string; w: number}> = ({pts, color, w}) => {
  const d = 'M' + pts.map((p) => p.join(',')).join(' L');
  return (
    <g>
      <path d={d} stroke={INK} strokeWidth={w + 13} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} stroke={color} strokeWidth={w} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  );
};

const Torso: React.FC = () => (
  <g>
    {/* cuello */}
    <rect x={-20} y={160} width={40} height={50} fill={SKIN} stroke={INK} strokeWidth={6} />
    {/* camisa rota */}
    <path d="M-82,204 L82,204 L64,466 L-64,466 Z" fill={SHIRT} stroke={INK} strokeWidth={7} strokeLinejoin="round" />
    <path d="M20,204 L82,204 L64,466 L30,466 Z" fill={SHIRT_D} />
    <path d="M20,204 L82,204 L64,466 L30,466 Z" fill="url(#ht)" opacity={0.15} />
    {/* pecho descubierto */}
    <path d="M-30,204 L30,204 L0,300 Z" fill={SKIN} stroke={INK} strokeWidth={5} strokeLinejoin="round" />
    {/* rasgaduras */}
    <path d="M-60,330 l22,14 l-10,10 l26,10 M40,380 l-18,12 l12,8 l-20,12" stroke={INK} strokeWidth={4} fill="none" />
    {/* paliacate */}
    <path d="M-40,196 L40,196 L0,246 Z" fill={BANDANA} stroke={INK} strokeWidth={5} strokeLinejoin="round" />
    {/* cinturón */}
    <rect x={-66} y={448} width={132} height={28} fill="#3a2414" stroke={INK} strokeWidth={6} />
    <rect x={-16} y={446} width={32} height={32} fill="#d8b24a" stroke={INK} strokeWidth={5} />
  </g>
);

const Rope: React.FC<{x: number; y: number; vertical?: boolean}> = ({x, y, vertical}) => (
  <g transform={`translate(${x},${y}) rotate(${vertical ? 90 : 0})`}>
    {[-14, 0, 14].map((o) => (
      <rect key={o} x={o - 5} y={-34} width={10} height={68} rx={4} fill={ROPE} stroke={INK} strokeWidth={4} transform={`rotate(12 ${o} 0)`} />
    ))}
  </g>
);

const Cross: React.FC<{ropesHanging?: boolean; f?: number}> = ({ropesHanging = false, f = 0}) => (
  <g>
    <rect x={-24} y={-40} width={48} height={960} fill={WOOD} stroke={INK} strokeWidth={7} />
    <rect x={8} y={-40} width={16} height={960} fill={WOOD_D} />
    <rect x={-340} y={118} width={680} height={54} fill={WOOD} stroke={INK} strokeWidth={7} />
    <rect x={-340} y={156} width={680} height={16} fill={WOOD_D} />
    <path d="M-300,135 l120,4 M-120,148 l90,-3 M60,132 l140,6 M230,150 l80,-2 M-6,300 l2,140 M-10,560 l3,120" stroke={WOOD_D} strokeWidth={4} />
    {ropesHanging &&
      [-1, 1].map((sd) => {
        const sw = Math.sin(f * 0.12 + sd) * 10;
        return (
          <g key={sd}>
            <Rope x={sd * 270} y={145} />
            <path d={`M${sd * 270},170 q${sw},40 ${sw * 0.4},90`} stroke={ROPE} strokeWidth={10} fill="none" strokeLinecap="round" />
            <path d={`M${sd * 270},170 q${sw},40 ${sw * 0.4},90`} stroke={INK} strokeWidth={3} fill="none" strokeLinecap="round" opacity={0.6} />
          </g>
        );
      })}
    {ropesHanging && <Rope x={0} y={770} />}
  </g>
);

// Logan atado a la cruz (coordenadas locales: tope de la cruz en y=0)
const Crucified: React.FC<{tilt: number; eyes: number; sweat: number; mouthOpen?: number; leftEyeOnly?: boolean}> = ({tilt, eyes, sweat, mouthOpen = 0}) => (
  <g>
    <Cross />
    {/* piernas */}
    <path d="M-62,470 L-2,470 L-10,760 L-50,760 Z" fill={JEANS} stroke={INK} strokeWidth={7} strokeLinejoin="round" />
    <path d="M62,470 L2,470 L10,760 L50,760 Z" fill={JEANS_D} stroke={INK} strokeWidth={7} strokeLinejoin="round" />
    <path d="M-58,752 L-4,752 L-2,812 L-70,812 Q-74,780 -58,752 Z" fill="#4a2c16" stroke={INK} strokeWidth={6} />
    <path d="M58,752 L4,752 L2,812 L70,812 Q74,780 58,752 Z" fill="#4a2c16" stroke={INK} strokeWidth={6} />
    <Rope x={0} y={770} />
    {/* brazos estirados */}
    {[-1, 1].map((sd) => (
      <g key={sd}>
        <Limb pts={[[sd * 72, 222], [sd * 180, 182]]} color={sd < 0 ? SHIRT : SHIRT_D} w={60} />
        <Limb pts={[[sd * 180, 182], [sd * 282, 150]]} color={SKIN} w={44} />
        <circle cx={sd * 302} cy={146} r={28} fill={SKIN} stroke={INK} strokeWidth={6} />
        <path d={`M${sd * 292},128 l${sd * 22},0 M${sd * 294},142 l${sd * 22},0`} stroke={INK} strokeWidth={4} />
        <Rope x={sd * 262} y={150} />
      </g>
    ))}
    <Torso />
    <Head tilt={tilt} eyes={eyes} sweat={sweat} mouthOpen={mouthOpen} />
  </g>
);

const Standing: React.FC<{f: number}> = ({f}) => {
  const breathe = Math.sin(f * 0.15) * 3;
  return (
    <g>
      {/* piernas abiertas */}
      <path d="M-62,470 L-4,470 L-34,780 L-92,780 Z" fill={JEANS} stroke={INK} strokeWidth={7} strokeLinejoin="round" />
      <path d="M62,470 L4,470 L34,780 L92,780 Z" fill={JEANS_D} stroke={INK} strokeWidth={7} strokeLinejoin="round" />
      <path d="M-98,770 L-30,770 L-26,832 L-120,832 Q-124,796 -98,770 Z" fill="#4a2c16" stroke={INK} strokeWidth={6} />
      <path d="M98,770 L30,770 L26,832 L120,832 Q124,796 98,770 Z" fill="#4a2c16" stroke={INK} strokeWidth={6} />
      {/* brazos abajo, puños con cuerda rota */}
      {[-1, 1].map((sd) => (
        <g key={sd}>
          <Limb pts={[[sd * 74, 224], [sd * 104, 340 + breathe]]} color={sd < 0 ? SHIRT : SHIRT_D} w={60} />
          <Limb pts={[[sd * 104, 340 + breathe], [sd * 116, 440 + breathe]]} color={SKIN} w={44} />
          <circle cx={sd * 118} cy={466 + breathe} r={30} fill={SKIN} stroke={INK} strokeWidth={6} />
          <path d={`M${sd * 100},${454 + breathe} l${sd * 30},0 M${sd * 100},${470 + breathe} l${sd * 30},0`} stroke={INK} strokeWidth={4} />
          <Rope x={sd * 116} y={418 + breathe} vertical />
          <path d={`M${sd * 130},${418 + breathe} q${sd * 30},30 ${sd * 18},80`} stroke={ROPE} strokeWidth={10} fill="none" strokeLinecap="round" />
        </g>
      ))}
      <Torso />
      <g transform={`translate(0,${breathe * 0.5})`}>
        <Head tilt={0} eyes={0.75} angry hat />
      </g>
    </g>
  );
};

const Hat: React.FC<{x: number; y: number; r?: number}> = ({x, y, r = 14}) => (
  <g transform={`translate(${x},${y}) rotate(${r}) scale(0.9)`}>
    <path d="M-48,-14 C-50,-80 50,-80 48,-14 Z" fill="#6b4423" stroke={INK} strokeWidth={6} />
    <path d="M-118,-10 Q-60,-32 0,-28 Q60,-32 118,-10 Q60,4 0,0 Q-60,4 -118,-10 Z" fill="#7a4e28" stroke={INK} strokeWidth={6} />
  </g>
);

const Crow: React.FC<{x: number; y: number; f: number; landed: boolean; s?: number}> = ({x, y, f, landed, s = 1}) => {
  const flap = landed ? 0 : Math.sin(f * 0.9) * 40;
  return (
    <g transform={`translate(${x},${y}) scale(${s})`}>
      {/* alas */}
      {!landed && (
        <>
          <path d={`M-10,-30 Q-70,${-60 - flap} -120,${-30 - flap * 1.4} Q-60,-20 -10,-14 Z`} fill="#141018" stroke={INK} strokeWidth={4} />
          <path d={`M10,-30 Q70,${-60 - flap} 120,${-30 - flap * 1.4} Q60,-20 10,-14 Z`} fill="#141018" stroke={INK} strokeWidth={4} />
        </>
      )}
      <path d="M-34,-24 Q-30,-62 6,-60 Q34,-58 38,-30 L60,-8 Q20,-6 -6,0 Q-30,0 -34,-24 Z" fill="#1c1622" stroke={INK} strokeWidth={4} />
      {landed && <path d="M-30,-28 Q0,-44 30,-26 Q4,-14 -30,-28 Z" fill="#2c2433" />}
      <path d="M-34,-24 L-64,-10 L-38,-6 Z" fill="#1c1622" stroke={INK} strokeWidth={4} />
      {/* cabeza */}
      <circle cx={-26} cy={-62} r={20} fill="#1c1622" stroke={INK} strokeWidth={4} />
      <path d="M-44,-66 L-72,-58 L-44,-54 Z" fill="#e0b84a" stroke={INK} strokeWidth={3} />
      <circle cx={-30} cy={-66} r={5} fill="#ffd84a" />
      <circle cx={-31} cy={-66} r={2.2} fill={INK} />
      {/* patas */}
      <path d="M-6,0 L-10,14 M8,-2 L6,14" stroke="#e0b84a" strokeWidth={5} strokeLinecap="round" />
    </g>
  );
};

// cruz en el mundo
const CROSS_T = 'translate(540,560) scale(0.9)';

// ---------- Escenas ----------
const S1: React.FC = () => {
  const f = useCurrentFrame();
  const z = lerp(f, 0, 100, 0.8, 1.0);
  const cy = lerp(f, 0, 100, 1010, 930);
  return (
    <Panel enter={false}>
      <Cam cx={540} cy={cy} z={z}>
        <Desert f={f} />
        <g transform={CROSS_T}>
          <Crucified tilt={-14} eyes={0} sweat={f} />
        </g>
        <Hat x={700} y={1392} />
      </Cam>
      <Caption lines={['SONORA, 1887.', 'DÍA TRES.']} show={lerp(f, 10, 22, 0, 1)} />
    </Panel>
  );
};

const S2: React.FC = () => {
  const f = useCurrentFrame();
  const z = lerp(f, 0, 90, 3.5, 4.1);
  return (
    <Panel enter dir={1}>
      <Cam cx={545} cy={640} z={z}>
        <Desert f={f + 100} vultures={false} />
        <g transform={CROSS_T}>
          <Crucified tilt={-14 + Math.sin(f * 0.08) * 1.5} eyes={0} sweat={f} />
        </g>
      </Cam>
      <rect x={0} y={0} width={1080} height={1920} fill="url(#ht)" mask="url(#maskTop)" opacity={0.5} />
      <Caption lines={['LOS BANDIDOS LO DEJARON', 'AQUÍ PARA QUE EL SOL', 'HICIERA EL RESTO.']} show={lerp(f, 10, 22, 0, 1)} />
    </Panel>
  );
};

const S3: React.FC = () => {
  const f = useCurrentFrame();
  const z = lerp(f, 0, 100, 2.0, 2.3);
  const landT = lerp(f, 6, 34, 0, 1);
  const crowX = interpolate(landT, [0, 1], [1050, 742]);
  const crowY = interpolate(landT, [0, 1], [380, 667]);
  const tilt = lerp(f, 50, 66, -14, -4);
  const eyes = lerp(f, 52, 62, 0, 0.55);
  const talk = f > 66 && f < 92 ? Math.abs(Math.sin(f * 0.7)) : 0;
  return (
    <Panel enter dir={-1}>
      <Cam cx={690} cy={700} z={z}>
        <Desert f={f + 190} />
        <g transform={CROSS_T}>
          <Crucified tilt={tilt} eyes={eyes} sweat={f} mouthOpen={talk} />
        </g>
        <Crow x={crowX} y={crowY} f={f} landed={landT >= 1} s={0.9} />
      </Cam>
      <Bubble lines={['¿CRAAA?']} x={800} y={430} tail={[-150, 250]} show={lerp(f, 36, 44, 0, 1)} size={54} />
      <Bubble lines={['TODAVÍA NO,', 'AMIGO.']} x={360} y={1500} tail={[-130, -440]} show={lerp(f, 64, 72, 0, 1)} size={66} />
    </Panel>
  );
};

const S4: React.FC = () => {
  const f = useCurrentFrame();
  const open = lerp(f, 6, 16, 0, 1);
  const hit = 40;
  const shake = f >= hit && f < hit + 10 ? (f % 2 === 0 ? 1 : -1) * (10 - (f - hit)) * 3 : 0;
  const flash = f >= hit && f < hit + 3 ? 1 - (f - hit) / 3 : 0;
  const pop = interpolate(f, [hit, hit + 4, hit + 8], [0.2, 1.25, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const crac = f >= hit ? 1 : 0;
  const push = lerp(f, 0, 80, 1, 1.12);
  return (
    <Panel enter dir={1}>
      <rect x={0} y={0} width={1080} height={1920} fill="#d4232c" />
      <rect x={0} y={0} width={1080} height={1920} fill="url(#htRed)" opacity={0.6} />
      <SpeedLines cx={540} cy={960} color="#fff3c4" f={f} />
      <g transform={`translate(${540 + shake},${960}) scale(${push}) translate(-540,-960)`}>
        {/* franja de la cara */}
        <path d="M-40,690 L1120,660 L1120,1260 L-40,1290 Z" fill={SKIN} stroke={INK} strokeWidth={12} />
        <path d="M640,670 L1120,660 L1120,1260 L700,1270 Z" fill={SKIN_D} opacity={0.5} />
        <path d="M640,670 L1120,660 L1120,1260 L700,1270 Z" fill="url(#ht)" opacity={0.2} />
        {[310, 770].map((cx, i) => (
          <g key={i} transform={`translate(${cx},990)`}>
            <clipPath id={`eye${i}`}>
              <path d="M-170,0 Q0,-120 170,0 Q0,110 -170,0 Z" />
            </clipPath>
            <path d="M-170,0 Q0,-120 170,0 Q0,110 -170,0 Z" fill="#fff" />
            <g clipPath={`url(#eye${i})`}>
              <circle cx={i === 0 ? 20 : -20} cy={0} r={74} fill="#6a4524" stroke={INK} strokeWidth={8} />
              <circle cx={i === 0 ? 20 : -20} cy={0} r={34} fill={INK} />
              <circle cx={i === 0 ? 44 : 4} cy={-26} r={14} fill="#fff" />
              {/* párpado */}
              <rect x={-200} y={-140} width={400} height={interpolate(open, [0, 1], [260, 60])} fill={SKIN} />
              <path d={`M-200,${-140 + interpolate(open, [0, 1], [260, 60])} L200,${-140 + interpolate(open, [0, 1], [260, 60])}`} stroke={INK} strokeWidth={10} />
            </g>
            <path d="M-170,0 Q0,-120 170,0 Q0,110 -170,0 Z" fill="none" stroke={INK} strokeWidth={12} />
            {/* ceja furiosa */}
            <path d={i === 0 ? 'M-190,-170 L170,-100 L160,-60 L-190,-120 Z' : 'M190,-170 L-170,-100 L-160,-60 L190,-120 Z'} fill={HAIR} stroke={INK} strokeWidth={8} />
          </g>
        ))}
        <path d="M540,940 L520,1250" stroke={INK} strokeWidth={8} opacity={0.6} />
      </g>
      {/* pedazos de cuerda volando */}
      {crac > 0 &&
        [0, 1, 2, 3, 4, 5].map((i) => {
          const t = f - hit;
          const a = -0.9 + i * 0.5;
          const x = 540 + Math.cos(a) * t * 60 * (i % 2 ? 1 : -1);
          const y = 1500 + Math.sin(a) * t * 30 - t * 20 + t * t * 0.8;
          return <rect key={i} x={x} y={y} width={90} height={18} rx={8} fill={ROPE} stroke={INK} strokeWidth={4} transform={`rotate(${t * 25 + i * 40} ${x + 45} ${y + 9})`} />;
        })}
      {crac > 0 && (
        <g transform={`translate(540,420) rotate(-8) scale(${pop})`}>
          <text textAnchor="middle" y={80} fontFamily={BANGERS} fontSize={300} fill={INK} stroke={INK} strokeWidth={40} strokeLinejoin="round" letterSpacing={6}>
            ¡CRAC!
          </text>
          <text textAnchor="middle" y={80} fontFamily={BANGERS} fontSize={300} fill="#ffe14a" stroke="#ff7a00" strokeWidth={10} strokeLinejoin="round" letterSpacing={6}>
            ¡CRAC!
          </text>
        </g>
      )}
      <rect x={0} y={0} width={1080} height={1920} fill="#fff" opacity={flash} />
    </Panel>
  );
};

const S5: React.FC = () => {
  const f = useCurrentFrame();
  const z = lerp(f, 0, 110, 1.1, 1.28);
  const cy = lerp(f, 0, 110, 1060, 1000);
  const title = interpolate(f, [44, 50, 54], [0, 1.15, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <Panel enter dir={-1}>
      <Cam cx={540} cy={cy} z={z}>
        <Desert f={f + 370} />
        <g transform={CROSS_T}>
          <Cross ropesHanging f={f} />
        </g>
        <g transform="translate(540,594) scale(0.95)">
          <Standing f={f} />
        </g>
      </Cam>
      <Caption lines={['PRIMER ERROR DE LOS BANDIDOS:', 'NO REMATARLO.']} show={lerp(f, 10, 22, 0, 1)} />
      <g transform={`translate(540,1650) rotate(-4) scale(${title})`} opacity={title > 0 ? 1 : 0}>
        <text textAnchor="middle" y={0} fontFamily={BANGERS} fontSize={250} fill={INK} stroke={INK} strokeWidth={36} strokeLinejoin="round" letterSpacing={14}>
          LOGAN
        </text>
        <text textAnchor="middle" y={0} fontFamily={BANGERS} fontSize={250} fill={BANDANA} stroke="#ffe14a" strokeWidth={8} strokeLinejoin="round" letterSpacing={14}>
          LOGAN
        </text>
      </g>
      <text x={1010} y={1840} textAnchor="end" fontFamily={BANGERS} fontSize={64} fill={INK} opacity={lerp(f, 70, 80, 0, 1)} letterSpacing={3}>
        CONTINUARÁ...
      </text>
    </Panel>
  );
};

export const LoganComic: React.FC = () => {
  const comps = [S1, S2, S3, S4, S5];
  return (
    <AbsoluteFill style={{background: '#f3ead6'}}>
      {comps.map((C, i) => {
        const sc = SCENES[i];
        const from = i === 0 ? 0 : sc.from - SLIDE;
        const dur = sc.dur + (i === 0 ? 0 : SLIDE);
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            <C />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
