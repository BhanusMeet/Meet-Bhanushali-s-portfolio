const entry = document.getElementById('entry-screen');
const main = document.getElementById('main-interface');
const enterBtn = document.getElementById('enter-btn');
const glitch = document.getElementById('glitch-layer');
const crack = document.getElementById('crack-layer');
const control = document.getElementById('control-panel');
const overlay = document.getElementById('overlay-panel');

function tone(freq = 440, duration = 0.1, type = 'square') {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.value = 0.03;
  osc.connect(gain).connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + duration);
}

function noiseBurst(duration = 0.4) {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const buffer = ctx.createBuffer(1, ctx.sampleRate * duration, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
  const source = ctx.createBufferSource();
  const gain = ctx.createGain();
  gain.gain.value = 0.05;
  source.buffer = buffer;
  source.connect(gain).connect(ctx.destination);
  source.start();
}

function cinematicEnter() {
  tone(190, 0.09);
  const tl = gsap.timeline({
    onComplete: () => {
      entry.classList.add('hidden');
      main.classList.remove('hidden');
      gsap.to(control, { x: 0, duration: 0.65, ease: 'power2.out' });
      [...control.querySelectorAll('button')].forEach((btn, i) => {
        gsap.from(btn, { x: 130, rotate: 8, duration: 0.45, delay: i * 0.07, ease: 'back.out(2.2)' });
      });
    }
  });

  tl.to(glitch, { opacity: 1, duration: 0.08, repeat: 4, yoyo: true }, 0)
    .to('body', { x: 8, yoyo: true, repeat: 6, duration: 0.05 }, 0)
    .to(entry, { filter: 'contrast(1.8) blur(1px)', duration: 1 }, 0)
    .to(control, { x: 0, duration: 1, ease: 'power4.out' }, 1)
    .to(crack, { opacity: 1, duration: 0.08 }, 2)
    .to('body', { x: 14, yoyo: true, repeat: 9, duration: 0.04 }, 2)
    .to(glitch, { opacity: 1, duration: 0.06, yoyo: true, repeat: 6 }, 2.08)
    .to(entry, { opacity: 0, duration: 0.6 }, 2.35);

  setTimeout(() => { tone(520, 0.08, 'sawtooth'); noiseBurst(); }, 2100);
}

if (enterBtn) enterBtn.addEventListener('click', cinematicEnter);

function activatePanel(action) {
  tone(320, 0.06);
  const sections = {
    projects: '#projects',
    'cert-summary': '#cert-summary',
    'thm-badges': '#thm-badges',
  };
  const links = window.CONTROL_LINKS || {};
  if (sections[action]) {
    document.querySelector(sections[action])?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    overlay.classList.remove('hidden');
    overlay.innerHTML = `<strong>COMMAND EXECUTED:</strong> ${action.toUpperCase().replace('-', ' ')}`;
    gsap.fromTo(overlay, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.35 });
    return;
  }

  if (action === 'cert-page') return window.open('/certifications', '_blank');
  if (action === 'thm-profile') return window.open(links.tryhackme, '_blank');
  if (action === 'reset') return window.location.reload();
  if (links[action]) return window.open(links[action], '_blank');
}

document.querySelectorAll('#control-panel button').forEach(btn => {
  btn.addEventListener('click', () => activatePanel(btn.dataset.action));
});

const cursorGlow = document.querySelector('.cursor-glow');
window.addEventListener('mousemove', e => {
  cursorGlow.style.left = `${e.clientX}px`;
  cursorGlow.style.top = `${e.clientY}px`;
});

const cvs = document.getElementById('particles');
if (cvs) {
  const ctx = cvs.getContext('2d');
  let w, h, dots;
  const init = () => {
    w = cvs.width = innerWidth; h = cvs.height = innerHeight;
    dots = Array.from({ length: 90 }, () => ({ x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3 }));
  };
  const draw = () => {
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#00ff9935';
    dots.forEach(d => { d.x += d.vx; d.y += d.vy; if (d.x < 0 || d.x > w) d.vx *= -1; if (d.y < 0 || d.y > h) d.vy *= -1; ctx.beginPath(); ctx.arc(d.x, d.y, 1.2, 0, Math.PI * 2); ctx.fill(); });
    requestAnimationFrame(draw);
  };
  init(); draw(); addEventListener('resize', init);
}
