// Planazo · elevator pitch · single source of truth for picture, cursor, music and VO cues.
// Times in output seconds; x/y in SOURCE pixels of the screen recording (1180×2556).
window.TL = {
  DUR: 93.0,          // design length; output = DUR + (b1o - b1)
  warp: { b1: 13.6, b1o: 16.6 },   // block 1 (design 0–13.6 s) plays over 0–16.6 s of output
  FPS_SRC: 60,

  // ---- voice-over cues (recorded by the founder later) ----
  vo: [
    { id: 1,  t0: 1.0,  t1: 4.4,  block: 'Bloque 1 · Presentación', text: 'Entre la universidad, el trabajo y la rutina...' },
    { id: 2,  t0: 5.0,  t1: 8.7,  block: 'Bloque 1 · Presentación', text: '...los jóvenes sabemos que el entretenimiento no es un lujo...' },
    { id: 3,  t0: 9.0,  t1: 13.0, block: 'Bloque 1 · Presentación', text: '...es una parte vital para estar tranquilos y recargar energías.' },
    { id: 4,  t0: 13.9, t1: 18.5, block: 'Bloque 1 · Presentación', text: 'Somos Planazo, una plataforma creada para resolver un problema cotidiano...' },
    { id: 5,  t0: 19.1, t1: 25.2, block: 'Bloque 1 · Presentación', text: '...siempre es muy complicado organizar salidas con amigos entre indecisiones y presupuestos que no cuadran.' },
    { id: 6,  t0: 25.8, t1: 31.4, block: 'Bloque 2 · Propuesta de valor', text: 'A diferencia de otras opciones, somos una app web que automatiza tus planes al toque' },
    { id: 7,  t0: 31.9, t1: 33.9, block: 'Bloque 2 · Propuesta de valor', text: 'sin necesidad de descargar nada:' },
    { id: 8,  t0: 34.4, t1: 36.3, block: 'Bloque 2 · Propuesta de valor', text: 'entras desde tu navegador,' },
    { id: 9,  t0: 37.4, t1: 39.6, block: 'Bloque 2 · Propuesta de valor', text: 'filtras por presupuesto y gustos,' },
    { id: 10, t0: 42.6, t1: 45.4, block: 'Bloque 2 · Propuesta de valor', text: 'y armas el itinerario perfecto en segundos.' },
    { id: 11, t0: 49.9, t1: 58.4, block: 'Bloque 3 · Mercado objetivo', text: 'Está pensada para jóvenes entre estudios y trabajo que buscan despejarse y disfrutar su tiempo libre sin complicarse la vida coordinando.' },
    { id: 12, t0: 60.1, t1: 64.3, block: 'Bloque 4 · Modelo de negocio', text: 'Operamos con un modelo Freemium: acceso gratuito para empezar' },
    { id: 13, t0: 65.3, t1: 68.7, block: 'Bloque 4 · Modelo de negocio', text: 'y una suscripción mensual accesible de S/ 9,90' },
    { id: 14, t0: 69.4, t1: 74.0, block: 'Bloque 4 · Modelo de negocio', text: 'con más itinerarios, mayor personalización y más opciones de modificación.' },
    { id: 15, t0: 75.9, t1: 80.9, block: 'Bloque 5 · Cierre (CTA)', text: 'Porque tu tiempo libre también importa y cuidarte es salir a disfrutar.' },
    { id: 16, t0: 82.4, t1: 89.4, block: 'Bloque 5 · Cierre (CTA)', text: 'Entra desde tu navegador, arma tu próximo planazo y deja que coordinar sea lo más fácil de la salida.' },
    { id: 17, t0: 89.9, t1: 91.0, block: 'Bloque 5 · Cierre (CTA)', text: '¡Muchas gracias!' },
  ],

  // ---- what plays inside the phone: src = s0 + (t-t0)/(t1-t0)*(s1-s0); xf = crossfade from the previous segment ----
  seg: [
    { t0: 0.0,   t1: 13.6,  clip: 'rec1', s0: 0.2,   s1: 2.2 },
    { t0: 13.6,  t1: 16.4,  clip: 'rec3', s0: 7.0,   s1: 8.68, xf: 0.5 },
    { t0: 16.4,  t1: 19.0,  clip: 'rec3', s0: 8.68,  s1: 8.68 },
    { t0: 19.0,  t1: 25.6,  clip: 'rec1', s0: 19.4,  s1: 26.0, xf: 0.45 },
    { t0: 25.6,  t1: 31.8,  clip: 'rec3', s0: 0.0,   s1: 3.1,  xf: 0.45 },
    { t0: 31.8,  t1: 37.0,  clip: 'rec1', s0: 0.0,   s1: 2.6,  xf: 0.45 },
    { t0: 37.0,  t1: 38.2,  clip: 'rec1', s0: 2.6,   s1: 5.0 },
    { t0: 38.2,  t1: 40.3,  clip: 'rec1', s0: 5.0,   s1: 5.70 },
    { t0: 40.3,  t1: 42.15, clip: 'rec1', s0: 5.70,  s1: 7.55 },
    { t0: 42.15, t1: 45.35, clip: 'rec1', s0: 26.75, s1: 29.95, xf: 0.4 },
    { t0: 45.35, t1: 48.10, clip: 'rec1', s0: 36.7,  s1: 39.45, xf: 0.4 },
    { t0: 48.10, t1: 49.6,  clip: 'rec1', s0: 39.45, s1: 39.85 },
    { t0: 49.6,  t1: 55.8,  clip: 'rec1', s0: 29.75, s1: 34.4,  xf: 0.45 },
    { t0: 55.8,  t1: 59.8,  clip: 'rec1', s0: 40.75, s1: 44.35, xf: 0.4 },
    { t0: 59.8,  t1: 62.3,  clip: 'rec2', s0: 0.0,   s1: 2.5,   xf: 0.45 },
    { t0: 62.3,  t1: 65.2,  clip: 'rec2', s0: 2.5,   s1: 3.8 },
    { t0: 65.2,  t1: 67.5,  clip: 'rec2', s0: 3.8,   s1: 6.1 },
    { t0: 67.5,  t1: 69.2,  clip: 'rec2', s0: 6.1,   s1: 7.8 },
    { t0: 69.2,  t1: 75.6,  clip: 'rec2', s0: 7.8,   s1: 11.6 },
    { t0: 75.6,  t1: 82.2,  clip: 'rec1', s0: 0.3,   s1: 1.6,   xf: 0.5 },
    { t0: 82.2,  t1: 85.56, clip: 'rec3', s0: 7.0,   s1: 8.68,  xf: 0.5 },
    { t0: 85.56, t1: 93.0,  clip: 'rec3', s0: 8.68,  s1: 8.68 },
  ],
  // extracted frame ranges (frame n = round(src*60))
  avail: { rec1: [[0, 465], [1158, 2070], [2196, 2397], [2439, 2667]], rec2: [[0, 702]], rec3: [[0, 192], [414, 520]] },

  // ---- camera: focus point F (source px) placed at the anchor, zoom z (1 = whole phone) ----
  cam: [
    [0, 590, 1278, 1.0], [13.4, 590, 1240, 1.045], [14.2, 590, 1278, 1.0], [18.9, 590, 1278, 1.0],
    [19.9, 590, 1000, 1.45], [25.3, 590, 1000, 1.45], [26.1, 590, 1278, 1.0],
    [34.5, 590, 1278, 1.0], [35.2, 620, 1908, 1.3], [36.75, 620, 1908, 1.3], [37.3, 590, 1278, 1.0],
    [38.15, 590, 1278, 1.0], [38.85, 590, 1350, 1.4], [42.2, 590, 1350, 1.4], [42.6, 590, 1100, 1.4],
    [44.7, 590, 1100, 1.4], [45.3, 590, 1278, 1.0], [46.6, 590, 1278, 1.0], [47.6, 610, 720, 1.38],
    [49.5, 610, 720, 1.38], [50.2, 590, 1278, 1.0], [56.2, 590, 1278, 1.0], [56.9, 590, 1300, 1.35],
    [58.6, 590, 1300, 1.35], [59.3, 590, 1278, 1.0], [62.4, 590, 1278, 1.0], [63.1, 590, 1000, 1.35],
    [65.15, 590, 1000, 1.35], [65.7, 590, 1278, 1.0], [67.45, 590, 1278, 1.0], [68.1, 590, 900, 1.5],
    [69.2, 590, 900, 1.5], [69.9, 590, 1440, 1.42], [75.3, 590, 1440, 1.42], [76.1, 590, 1278, 1.0],
    [93, 590, 1278, 1.0],
  ],
  // phone placement on the canvas: [t, dy, scale, alpha]
  place: [
    [0, 300, 1, 0], [1.1, 0, 1, 1], [75.4, 0, 1, 1], [76.3, 420, 0.9, 1], [81.9, 420, 0.9, 1],
    [82.7, 0, 1, 1], [85.8, 0, 1, 1], [86.8, 520, 0.82, 0], [93, 520, 0.82, 0],
  ],
  // screen "tired" filter: [t, saturation, brightness]
  dim: [[0, 0.3, 0.78], [10.4, 0.3, 0.78], [12.6, 1, 1]],

  // ---- digital cursor (source px): taps synced to the recording's real frames; swipes before each scroll ----
  taps: [
    { t: 19.38, x: 361, y: 1170 }, { t: 20.52, x: 300, y: 1339 }, { t: 22.31, x: 361, y: 1170 },
    { t: 22.85, x: 300, y: 1464 }, { t: 24.16, x: 361, y: 1170 }, { t: 24.58, x: 300, y: 1592 },
    { t: 35.3, x: 632, y: 2382 },
    { t: 40.44, x: 336, y: 1083 }, { t: 41.96, x: 285, y: 953 },
    { t: 42.55, x: 590, y: 1362 },
    { t: 45.87, x: 285, y: 1775 },
    { t: 57.91, x: 588, y: 1525 },
    { t: 82.65, x: 590, y: 2382 },
  ],
  swipes: [
    { t: 26.2, x: 780, y0: 1950, y1: 1250 },
    { t: 36.9, x: 780, y0: 2000, y1: 1300 },
    { t: 46.5, x: 780, y0: 1900, y1: 1200 },
    { t: 49.85, x: 780, y0: 1950, y1: 1250 }, { t: 52.75, x: 780, y0: 1950, y1: 1250 },
    { t: 55.85, x: 780, y0: 1900, y1: 1250 },
    { t: 61.0, x: 780, y0: 1950, y1: 1250 }, { t: 62.15, x: 780, y0: 1950, y1: 1300 },
    { t: 65.12, x: 780, y0: 1950, y1: 1250 }, { t: 67.2, x: 780, y0: 1950, y1: 1300 },
  ],

  // ---- point-and-show annotations (source px) ----
  circles: [
    { t0: 15.0, t1: 18.6, x: 243, y: 278, rx: 255, ry: 88 },
    { t0: 23.3, t1: 25.35, x: 838, y: 398, rx: 290, ry: 98 },
    { t0: 35.0, t1: 36.95, x: 632, y: 2382, rx: 330, ry: 100, label: 'Tu navegador', icon: 'globe', side: 'above' },
    { t0: 38.4, t1: 40.25, x: 838, y: 1088, rx: 290, ry: 102, label: 'Presupuesto', icon: 'wallet', side: 'above' },
    { t0: 39.2, t1: 40.25, x: 582, y: 1602, rx: 545, ry: 150, label: 'Gustos', icon: 'heart', side: 'below' },
    { t0: 62.8, t1: 65.1, x: 330, y: 945, rx: 255, ry: 95, label: 'Gratis para empezar', side: 'below' },
    { t0: 67.9, t1: 69.15, x: 420, y: 940, rx: 320, ry: 105 },
    { t0: 83.6, t1: 85.8, x: 430, y: 940, rx: 440, ry: 205 },
  ],
  boxes: [
    { t0: 47.85, t1: 49.5, x0: 150, y0: 110, x1: 1180, y1: 1285, label: 'Itinerario listo', icon: 'check', side: 'above' },
    { t0: 56.9, t1: 57.8, x0: 110, y0: 1030, x1: 1065, y1: 1240, label: 'Todo tu grupo', icon: 'users', side: 'above' },
    { t0: 69.7, t1: 75.4, x0: 112, y0: 1088, x1: 1112, y1: 1312, dark: true },
    { t0: 70.9, t1: 75.4, x0: 112, y0: 1556, x1: 1112, y1: 1784, dark: true },
    { t0: 71.9, t1: 75.4, x0: 112, y0: 1440, x1: 1112, y1: 1550, dark: true },
  ],
};
