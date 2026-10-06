const viewer = document.getElementById("viewer");
const maskLayer = document.getElementById("mask-layer");
const comparisonLine = document.getElementById("comparison-line");
const comparisonRange = document.getElementById("comparison-range");
const hitMap = document.getElementById("hit-map");
const histogram = document.getElementById("histogram");
const particleFields = document.getElementById("particle-fields");
const selectionHelp = document.getElementById("selection-help");

function setComparison(percent) {
  const bounded = Math.max(0, Math.min(100, percent));
  maskLayer.style.clipPath = `inset(0 0 0 ${bounded}%)`;
  comparisonLine.style.left = `${bounded}%`;
  comparisonRange.value = String(bounded);
}

function buildHistogram() {
  const diameters = particles.map((particle) => particle.diameter_nm);
  const min = 7;
  const max = 21;
  const binCount = 18;
  const counts = Array.from({ length: binCount }, () => 0);
  diameters.forEach((diameter) => {
    const index = Math.min(binCount - 1, Math.max(0, Math.floor((diameter - min) / (max - min) * binCount)));
    counts[index] += 1;
  });
  const peak = Math.max(...counts);
  counts.forEach((count) => {
    const bar = document.createElement("span");
    bar.style.height = `${Math.max(1, count / peak * 100)}%`;
    bar.title = `${count} particles`;
    histogram.appendChild(bar);
  });
}

function selectParticle(particle, path) {
  hitMap.querySelector(".selected")?.classList.remove("selected");
  path.classList.add("selected");
  document.getElementById("particle-id").textContent = `#${particle.id}`;
  document.getElementById("particle-diameter").textContent = `${particle.diameter_nm.toFixed(2)} nm`;
  document.getElementById("particle-area").textContent = `${particle.area_nm2.toFixed(2)} nm²`;
  document.getElementById("particle-circularity").textContent = particle.circularity.toFixed(3);
  document.getElementById("particle-neighbor").textContent = `${particle.nearest_neighbor_nm.toFixed(2)} nm`;
  document.getElementById("particle-shape").textContent = particle.shape;
  particleFields.hidden = false;
  selectionHelp.hidden = true;
}

function buildHitMap() {
  const namespace = "http://www.w3.org/2000/svg";
  particles.forEach((particle) => {
    const path = document.createElementNS(namespace, "path");
    const points = particle.contour;
    if (points.length < 3) return;
    path.setAttribute("d", `M${points.map(([x, y]) => `${x} ${y}`).join("L")}Z`);
    path.setAttribute("aria-label", `Particle ${particle.id}`);
    path.addEventListener("click", () => selectParticle(particle, path));
    hitMap.appendChild(path);
  });
}

let draggingDivider = false;
viewer.addEventListener("pointerdown", (event) => {
  const bounds = viewer.getBoundingClientRect();
  const dividerX = bounds.left + bounds.width * Number(comparisonRange.value) / 100;
  if (Math.abs(event.clientX - dividerX) > 28) return;
  draggingDivider = true;
  viewer.setPointerCapture(event.pointerId);
  event.preventDefault();
});
viewer.addEventListener("pointermove", (event) => {
  if (!draggingDivider) return;
  const bounds = viewer.getBoundingClientRect();
  setComparison((event.clientX - bounds.left) / bounds.width * 100);
});
viewer.addEventListener("pointerup", () => { draggingDivider = false; });
viewer.addEventListener("pointercancel", () => { draggingDivider = false; });
comparisonRange.addEventListener("input", () => setComparison(Number(comparisonRange.value)));

setComparison(50);
buildHistogram();
buildHitMap();
