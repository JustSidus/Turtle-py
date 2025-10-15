// Simple animated renderer for regions JSON on an HTML5 Canvas

const els = {
  canvas: document.getElementById('stage'),
  bloomBtn: document.getElementById('startBtn'),
  status: document.getElementById('status'),
  speed: document.getElementById('speed'),
  margin: document.getElementById('margin'),
  pauseBtn: document.getElementById('pauseBtn'),
  resumeBtn: document.getElementById('resumeBtn'),
  finishBtn: document.getElementById('finishBtn'),
};

const ctx = els.canvas.getContext('2d');
let regions = []; // [{ color:[..], contour:[[x,y],...] }]
let screenPolys = []; // [{ color: '#hex', pts: [x,y,...] }]
let anim = { idx: 0, timer: null, paused: false, delay: 60 };

function getDelayFromSpeed(){
  if(!els.speed) return anim.delay;
  const min = Number(els.speed.min) || 1;
  const max = Number(els.speed.max) || 200;
  const v = Number(els.speed.value);
  // Invert: mayor valor = menor delay (más rápido)
  const inverted = (min + max) - (Number.isFinite(v) ? v : (min + max) / 2);
  return Math.max(1, inverted);
}

function getMarginRatio(){
  // If there's no margin slider in the DOM, use a sensible default
  if(!els.margin) return 0.10; // 10% default margin
  const v = Number(els.margin.value);
  if(Number.isFinite(v)) return v/100;
  return 0.10;
}

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

function hsvRadToRgb01(hRad, s, v){
  const TAU = Math.PI * 2;
  let h = ((hRad % TAU) + TAU) % TAU; // [0,2pi)
  h /= TAU;
  const i = Math.floor(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - f * s);
  const t = v * (1 - (1 - f) * s);
  const m = i % 6;
  let r,g,b;
  if (m===0){ r=v; g=t; b=p; }
  else if (m===1){ r=q; g=v; b=p; }
  else if (m===2){ r=p; g=v; b=t; }
  else if (m===3){ r=p; g=q; b=v; }
  else if (m===4){ r=t; g=p; b=v; }
  else { r=v; g=p; b=q; }
  return [clamp(r,0,1), clamp(g,0,1), clamp(b,0,1)];
}

function colorToHex(color){
  if (!Array.isArray(color) || color.length !== 3) return '#ffffff';
  const [c0,c1,c2] = color.map(Number);
  // HSV(rad) si s,v en [0,1] y h en [0, ~6.3]
  if (c1>=0 && c1<=1 && c2>=0 && c2<=1 && c0>=0 && c0<= (Math.PI*2+1e-6)){
    const [r,g,b] = hsvRadToRgb01(c0,c1,c2);
    return rgb01ToHex(r,g,b);
  }
  // RGB 0..1
  if (c0>=0 && c0<=1 && c1>=0 && c1<=1 && c2>=0 && c2<=1){
    return rgb01ToHex(c0,c1,c2);
  }
  // RGB 0..255
  return rgb255ToHex(c0,c1,c2);
}

function rgb01ToHex(r,g,b){
  const R = Math.round(clamp(r,0,1)*255);
  const G = Math.round(clamp(g,0,1)*255);
  const B = Math.round(clamp(b,0,1)*255);
  return `#${R.toString(16).padStart(2,'0')}${G.toString(16).padStart(2,'0')}${B.toString(16).padStart(2,'0')}`;
}
function rgb255ToHex(r,g,b){
  const R = Math.round(clamp(r,0,255));
  const G = Math.round(clamp(g,0,255));
  const B = Math.round(clamp(b,0,255));
  return `#${R.toString(16).padStart(2,'0')}${G.toString(16).padStart(2,'0')}${B.toString(16).padStart(2,'0')}`;
}

function polyArea(pts){
  let s=0; const n=pts.length;
  for(let i=0;i<n;i++){
    const [x1,y1]=pts[i]; const [x2,y2]=pts[(i+1)%n];
    s += x1*y2 - x2*y1;
  }
  return Math.abs(s)*0.5;
}

function fitAndProject(regs, canvas, marginRatio){
  // bbox datos
  const xs=[]; const ys=[];
  regs.forEach(r=> r.contour.forEach(([x,y])=>{ xs.push(x); ys.push(y); }));
  const minX=Math.min(...xs), maxX=Math.max(...xs);
  const minY=Math.min(...ys), maxY=Math.max(...ys);
  const dataW=Math.max(1e-9, maxX-minX);
  const dataH=Math.max(1e-9, maxY-minY);
  const cx=(minX+maxX)/2, cy=(minY+maxY)/2;

  // área segura en canvas
  const cw=canvas.width, ch=canvas.height;
  const safeW=cw*(1-2*marginRatio);
  const safeH=ch*(1-2*marginRatio);
  const scaleFit=Math.min(safeW/dataW, safeH/dataH)*0.995;

  function toCanvasXY(x,y){
    // coords centradas (origen en centro del canvas)
    const sx=(x-cx)*scaleFit;
    const sy=(y-cy)*scaleFit;
    return [Math.round(cw/2+sx), Math.round(ch/2+sy)];
  }

  // proyectar a pantalla
  const projected = regs.map(r=>{
    const pts = r.contour.map(([x,y])=> toCanvasXY(x,y));
    // quitar duplicados consecutivos (evita dientes)
    const dedup=[]; let last=null;
    for(const p of pts){ if(!last || p[0]!==last[0] || p[1]!==last[1]){ dedup.push(p); last=p; } }
    return { color: colorToHex(r.color), pts: dedup };
  });
  return projected;
}

function clearCanvas(){
  ctx.save();
  ctx.setTransform(1,0,0,1,0,0);
  ctx.clearRect(0,0,els.canvas.width, els.canvas.height);
  ctx.restore();
}

function drawPoly(hex, pts){
  if(pts.length<3) return;
  ctx.fillStyle = hex;
  ctx.strokeStyle = hex;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for(let i=1;i<pts.length;i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

function setStatus(msg){ els.status.textContent = msg; }

function startAnimation(){
  stopAnimation();
  anim.idx=0; anim.paused=false; anim.delay = getDelayFromSpeed();
  clearCanvas();
  const total=screenPolys.length;
  function step(){
    if(anim.paused) return;
    if(anim.idx>=total){ setStatus('Listo'); return; }
    const {color, pts} = screenPolys[anim.idx++];
    drawPoly(color, pts);
    setStatus(`${anim.idx}/${total}`);
    anim.timer = setTimeout(step, anim.delay);
  }
  step();
}

function stopAnimation(){ if(anim.timer){ clearTimeout(anim.timer); anim.timer=null; } }

function handleJSON(jsonText){
  try{
    const data = JSON.parse(jsonText);
    // Acepta tanto [ {contour,...} ] como { regions: [ ... ] }
    const list = Array.isArray(data) ? data : (data && Array.isArray(data.regions) ? data.regions : null);
    if(!list) throw new Error('JSON no es una lista ni contiene regions[]');
    regions = list.filter(r=> Array.isArray(r.contour) && r.contour.length>=3);
    // Orden por área (grandes primero)
    regions.sort((a,b)=> polyArea(b.contour)-polyArea(a.contour));
    const m = getMarginRatio(); // slider 0..30 -> 0..0.3 (default 0.10 if missing)
    screenPolys = fitAndProject(regions, els.canvas, m);
    startAnimation();
  }catch(err){
    console.error(err);
    setStatus(`Error leyendo JSON: ${err.message || err}`);
  }
}

// Eventos UI
function isFileProtocol(){
  return typeof window !== 'undefined' && window.location && window.location.protocol.startsWith('file');
}

async function fetchWithFallback(paths){
  const errors = [];
  for(const p of paths){
    try{
      setStatus(`Cargando: ${p}`);
      const res = await fetch(p, { cache: 'no-store' });
      if(!res.ok) throw new Error(`HTTP ${res.status}`);
      const txt = await res.text();
      if(!txt || !txt.trim()) throw new Error('Respuesta vacía');
      return txt;
    }catch(e){
      console.warn('Fallo al cargar', p, e);
      errors.push(`${p}: ${e.message || e}`);
    }
  }
  throw new Error(errors.join(' | '));
}

els.bloomBtn.addEventListener('click', async ()=>{
  // Aviso útil si está abriendo como file://
  if(isFileProtocol()){
    setStatus('Estás abriendo el archivo localmente (file://). Sirve la carpeta web con un servidor HTTP para que la carga funcione.');
  }
  setStatus('Cargando rosa…');
  try{
    // recursos ahora dentro de /web/resources
    const candidates = [
      './resources/rosas.json',
      'resources/rosas.json',
      './rosas.json',
      '../resources/rosas.json'
    ];
    const text = await fetchWithFallback(candidates);
    handleJSON(text);
  }catch(err){
    console.error('No se pudo cargar rosas.json', err);
    setStatus(`No se pudo cargar rosas.json. ${isFileProtocol() ? 'Abierto como file://; usa un servidor HTTP.' : ''} Detalle: ${err.message || err}`);
  }
});

// Sin drag&drop en esta versión dedicada

// Controles
if(els.speed){ els.speed.addEventListener('input', ()=>{ anim.delay = getDelayFromSpeed(); }); }
if(els.margin){
  els.margin.addEventListener('input', ()=>{
    if(!regions.length) return;
    const m = getMarginRatio();
    screenPolys = fitAndProject(regions, els.canvas, m);
    startAnimation();
  });
}
if(els.pauseBtn){ els.pauseBtn.addEventListener('click', ()=>{ anim.paused=true; stopAnimation(); }); }
if(els.resumeBtn){ els.resumeBtn.addEventListener('click', ()=>{ if(anim.paused){ anim.paused=false; startAnimation(); } }); }
if(els.finishBtn){
  els.finishBtn.addEventListener('click', ()=>{
    stopAnimation();
    clearCanvas();
    for(const {color, pts} of screenPolys) drawPoly(color, pts);
    setStatus('Listo');
  });
}

// Responsive: redibujar al cambiar tamaño visual (ajusta tamaño real del canvas)
function resizeCanvas(){
  const rect = els.canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  els.canvas.width = Math.round(rect.width * ratio);
  els.canvas.height = Math.round(rect.height * ratio);
  ctx.setTransform(ratio,0,0,ratio,0,0); // mantener CSS px como unidad
  if(regions.length){
    const m = getMarginRatio();
    screenPolys = fitAndProject(regions, els.canvas, m);
    startAnimation();
  } else {
    clearCanvas();
  }
}
window.addEventListener('resize', ()=> { clearTimeout(resizeCanvas._t); resizeCanvas._t=setTimeout(resizeCanvas, 120); });
window.addEventListener('load', resizeCanvas);
