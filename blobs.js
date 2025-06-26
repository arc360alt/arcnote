const canvas = document.getElementById("blob-canvas");
const ctx = canvas.getContext("2d");

// Tune this to your liking: blobs per 120,000 pixels of screen area
const blobDensity = 1 / 120000;

let blobs = [];

// Generate blobs to fill the screen
function generateBlobs() {
  const area = canvas.width * canvas.height;
  const numBlobs = Math.max(6, Math.round(area * blobDensity));

  blobs = [];
  for (let i = 0; i < numBlobs; i++) {
    // Spread blobs randomly, but avoid edges
    const margin = 0.06;
    const x = margin + Math.random() * (1 - 2 * margin);
    const y = margin + Math.random() * (1 - 2 * margin);

    // Radius scales with screen size, but random
    const minR = 0.10, maxR = 0.22;
    const r = minR + Math.random() * (maxR - minR);

    // Random color: blue/purple/cyan family
    const colorVariants = [
      [79, 100, 255, 0.32],
      [123, 79, 255, 0.23],
      [58, 200, 255, 0.20],
      [93, 155, 255, 0.27],
      [103, 186, 255, 0.23],
      [20, 90, 255, 0.19],
      [110, 120, 255, 0.18],
      [100, 80, 230, 0.19]
    ];
    const c = colorVariants[Math.floor(Math.random() * colorVariants.length)];
    const color = `rgba(${c[0]},${c[1]},${c[2]},${c[3]})`;

    // Random movement
    const dx = (Math.random() - 0.5) * 0.2;
    const dy = (Math.random() - 0.5) * 0.2;
    const speed = 0.5 + Math.random() * 0.7;
    const phase = Math.random() * Math.PI * 2;

    blobs.push({ x, y, r, color, dx, dy, speed, phase });
  }
}

// Resize canvas and regenerate blobs
function resizeCanvasToDisplaySize() {
  let width = window.innerWidth;
  let height = window.innerHeight;
  // Fullscreen API support
  const fullscreenElement = document.fullscreenElement || document.webkitFullscreenElement;
  if (fullscreenElement) {
    width = screen.width;
    height = screen.height;
  }
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
    generateBlobs();
  }
}

resizeCanvasToDisplaySize();
window.addEventListener("resize", resizeCanvasToDisplaySize);
["fullscreenchange", "webkitfullscreenchange", "mozfullscreenchange", "MSFullscreenChange"].forEach(eventType => {
  document.addEventListener(eventType, resizeCanvasToDisplaySize);
});

function animateBlobs(t) {
  resizeCanvasToDisplaySize();
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  blobs.forEach((blob, i) => {
    const time = t / 9000;
    // Compute absolute positions
    const baseX = blob.x * canvas.width;
    const baseY = blob.y * canvas.height;
    const radius = blob.r * Math.min(canvas.width, canvas.height);
    const nx = Math.sin(time * blob.speed + blob.phase + i) * blob.dx * 180;
    const ny = Math.cos(time * blob.speed + blob.phase - i) * blob.dy * 180;
    drawBlob(baseX + nx, baseY + ny, radius, blob.color);
  });
  requestAnimationFrame(animateBlobs);
}

function drawBlob(x, y, r, color) {
  ctx.save();
  ctx.globalAlpha = 1;
  ctx.beginPath();
  for (let i = 0; i < 2 * Math.PI; i += 0.1) {
    const noise = Math.sin(i * 3 + Math.cos(i * 5)) * r * 0.07;
    const px = x + Math.cos(i) * (r + noise);
    const py = y + Math.sin(i) * (r + noise);
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = 80;
  ctx.fill();
  ctx.restore();
}

animateBlobs(0);