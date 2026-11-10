// State
let currentCameraId = 1;
let currentCameraData = null;
let allCameras = [];

// Tab Navigation
function switchTab(tabId) {
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

  const targetPane = document.getElementById(`tab-${tabId}`);
  if (targetPane) targetPane.classList.add('active');

  const activeBtn = Array.from(document.querySelectorAll('.nav-btn')).find(b => 
    b.getAttribute('onclick')?.includes(tabId)
  );
  if (activeBtn) activeBtn.classList.add('active');

  // Load specific data when entering tab
  if (tabId === 'live-wall') loadCameras();
  if (tabId === 's3-recordings') loadRecordings();
  if (tabId === 'alerts-center') loadAlerts();
  if (tabId === 'aws-infra') loadAWSInfrastructure();
  if (tabId === 'cost-roi') loadCostAnalysis();
}

// ----------------------------------------------------
// 1. LIVE WALL & CAMERAS
// ----------------------------------------------------
async function loadCameras() {
  try {
    const res = await fetch('/api/v1/cameras/');
    const cameras = await res.json();
    allCameras = cameras;
    
    const sidebar = document.getElementById('camera-sidebar-list');
    sidebar.innerHTML = '';

    cameras.forEach(cam => {
      const isSelected = cam.id === currentCameraId;
      const card = document.createElement('div');
      card.className = `cam-thumb-card ${isSelected ? 'active' : ''}`;
      card.onclick = () => selectCamera(cam);

      const statusBadge = cam.is_recording 
        ? '<span style="color: #ef4444; font-size: 0.75rem;">● REC</span>' 
        : '<span style="color: #10b981; font-size: 0.75rem;">● ONLINE</span>';

      card.innerHTML = `
        <div class="cam-thumb-preview">
          <img src="/api/v1/cameras/${cam.id}/snapshot?t=${Date.now()}" alt="${cam.code}">
        </div>
        <div class="cam-thumb-info">
          <h4>${cam.code} - ${cam.name}</h4>
          <span>${cam.location}</span>
          <div style="margin-top: 0.2rem;">${statusBadge} &bull; <small style="color: var(--text-muted);">${cam.resolution}</small></div>
        </div>
      `;
      sidebar.appendChild(card);
    });

    if (!currentCameraData && cameras.length > 0) {
      selectCamera(cameras[0]);
    }
  } catch (err) {
    console.error("Error loading cameras:", err);
  }
}

function selectCamera(cam) {
  currentCameraId = cam.id;
  currentCameraData = cam;

  const playerImg = document.getElementById('main-stream-player');
  playerImg.src = `/api/v1/cameras/${cam.id}/stream?t=${Date.now()}`;

  document.getElementById('player-cam-title').innerText = `${cam.code}: ${cam.name}`;
  document.getElementById('player-cam-location').innerText = `${cam.location} • ${cam.resolution} @ ${cam.fps}FPS • Cifrado AWS KMS`;

  const btnRec = document.getElementById('btn-toggle-rec');
  if (cam.is_recording) {
    btnRec.innerText = "⏹️ Pausar Grabación";
    btnRec.style.borderColor = "var(--border-color)";
  } else {
    btnRec.innerText = "🔴 Iniciar Grabación";
    btnRec.style.borderColor = "var(--accent-red)";
  }

  // Update selected class in sidebar
  document.querySelectorAll('.cam-thumb-card').forEach(c => c.classList.remove('active'));
  loadCameras();
}

async function toggleRecordingCurrentCam() {
  if (!currentCameraId) return;
  try {
    const res = await fetch(`/api/v1/cameras/${currentCameraId}/toggle-recording`, { method: 'PATCH' });
    const data = await res.json();
    alert(`Estado de grabación actualizado para ${currentCameraData?.code || 'cámara'}: ${data.status}`);
    loadCameras();
  } catch (err) {
    alert("Error al cambiar estado de grabación");
  }
}

function takeSnapshot() {
  window.open(`/api/v1/cameras/${currentCameraId}/snapshot?t=${Date.now()}`, '_blank');
}

// ----------------------------------------------------
// 2. S3 RECORDINGS & LIFECYCLE
// ----------------------------------------------------
async function loadRecordings() {
  try {
    const [recRes, summaryRes] = await Promise.all([
      fetch('/api/v1/recordings/'),
      fetch('/api/v1/recordings/storage-summary')
    ]);
    const recordings = await recRes.json();
    const summary = await summaryRes.json();

    // Update GB distribution
    const dist = summary.distribution_gb;
    document.getElementById('metric-standard-gb').innerText = `${dist.STANDARD} GB`;
    document.getElementById('metric-ia-gb').innerText = `${dist.STANDARD_IA} GB`;
    document.getElementById('metric-glacier-gb').innerText = `${dist.GLACIER_FLEXIBLE} GB`;
    document.getElementById('metric-deep-archive-gb').innerText = `${dist.DEEP_ARCHIVE} GB`;

    // Populate Table
    const tbody = document.getElementById('recordings-table-body');
    tbody.innerHTML = '';

    recordings.forEach(rec => {
      const tr = document.createElement('tr');
      const tierBadge = getTierBadge(rec.storage_class);
      const formattedDate = new Date(rec.recorded_at).toLocaleDateString('es-ES', {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });

      tr.innerHTML = `
        <td>#${rec.id}</td>
        <td><strong>${rec.camera_name}</strong></td>
        <td style="font-family: monospace; font-size: 0.8rem; color: var(--accent-cyan);">${rec.s3_key}</td>
        <td>${rec.file_size_mb} MB</td>
        <td>${tierBadge}</td>
        <td>${formattedDate}</td>
        <td><span style="color: var(--accent-green); font-size: 0.75rem;">🔒 Compliance WORM</span></td>
        <td>
          <button class="btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="viewPresignedUrl(${rec.id})">🔑 Presigned URL</button>
          ${rec.storage_class === 'STANDARD' ? `
            <button class="btn-primary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="transitionToGlacier(${rec.id})">❄️ A Glacier</button>
          ` : ''}
        </td>
      `;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("Error loading recordings:", err);
  }
}

function getTierBadge(tier) {
  if (tier === 'STANDARD') return '<span class="badge-tier badge-standard">STANDARD</span>';
  if (tier === 'STANDARD_IA') return '<span class="badge-tier badge-ia">STANDARD_IA</span>';
  if (tier === 'GLACIER_FLEXIBLE') return '<span class="badge-tier badge-glacier">GLACIER</span>';
  if (tier === 'DEEP_ARCHIVE') return '<span class="badge-tier badge-deep-archive">DEEP ARCHIVE</span>';
  return `<span class="badge-tier">${tier}</span>`;
}

async function viewPresignedUrl(recId) {
  try {
    const res = await fetch(`/api/v1/recordings/${recId}/presigned-url`);
    const data = await res.json();
    document.getElementById('presigned-url-content').innerText = data.presigned_url;
    document.getElementById('presigned-modal').classList.add('active');
  } catch (err) {
    alert("Error al generar URL prefirmada de AWS S3");
  }
}

function copyPresignedUrl() {
  const text = document.getElementById('presigned-url-content').innerText;
  navigator.clipboard.writeText(text);
  alert("URL Prefirmada copiada al portapapeles.");
}

function closeModal() {
  document.getElementById('presigned-modal').classList.remove('active');
}

async function transitionToGlacier(recId) {
  try {
    const res = await fetch(`/api/v1/recordings/${recId}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_tier: 'GLACIER_FLEXIBLE' })
    });
    const data = await res.json();
    alert(`Operación AWS S3 completada: ${data.message} (Ahorro del 84% en almacenamiento)`);
    loadRecordings();
  } catch (err) {
    alert("Error al migrar tier en S3");
  }
}

async function runLifecyclePolicy() {
  try {
    const res = await fetch('/api/v1/recordings/run-lifecycle-policy', { method: 'POST' });
    const data = await res.json();
    alert(`Política S3 Lifecycle ejecutada con éxito.\nTransiciones aplicadas: ${data.transitions_executed}\nAhorro mensual estimado: $${data.financial_impact.monthly_savings_usd} USD (${data.financial_impact.savings_percentage}%)`);
    loadRecordings();
  } catch (err) {
    alert("Error al ejecutar política de ciclo de vida");
  }
}

// ----------------------------------------------------
// 3. SECURITY ALERTS
// ----------------------------------------------------
async function loadAlerts() {
  try {
    const res = await fetch('/api/v1/alerts/');
    const alerts = await res.json();

    const activeCount = alerts.filter(a => a.status === 'NEW').length;
    document.getElementById('alerts-count-badge').innerText = activeCount;

    const tbody = document.getElementById('alerts-table-body');
    tbody.innerHTML = '';

    alerts.forEach(al => {
      const tr = document.createElement('tr');
      const sevBadge = al.severity === 'CRITICAL' ? '<span class="badge-tier badge-crit">CRÍTICO</span>' :
                       al.severity === 'HIGH' ? '<span class="badge-tier badge-high">ALTO</span>' :
                       '<span class="badge-tier badge-med">MEDIO</span>';
      
      const timeStr = new Date(al.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      tr.innerHTML = `
        <td>${timeStr}</td>
        <td>${sevBadge}</td>
        <td><strong>${al.alert_type}</strong></td>
        <td>${al.camera_name}</td>
        <td>${al.description}</td>
        <td style="font-family: monospace; font-size: 0.75rem; color: var(--accent-cyan);">${al.s3_clip_key || 'N/A'}</td>
        <td>
          <span style="font-weight: 700; color: ${al.status === 'NEW' ? '#ef4444' : al.status === 'ACKNOWLEDGED' ? '#f59e0b' : '#10b981'};">
            ${al.status}
          </span>
        </td>
        <td>
          ${al.status === 'NEW' ? `
            <button class="btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.72rem;" onclick="updateAlertStatus(${al.id}, 'ACKNOWLEDGED')">Reconocer</button>
          ` : al.status === 'ACKNOWLEDGED' ? `
            <button class="btn-primary" style="padding: 0.2rem 0.5rem; font-size: 0.72rem;" onclick="updateAlertStatus(${al.id}, 'RESOLVED')">Resolver</button>
          ` : '<span style="color: var(--accent-green);">Resuelto ✓</span>'}
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading alerts:", err);
  }
}

async function simulateAlert() {
  try {
    const res = await fetch(`/api/v1/alerts/simulate?camera_id=${currentCameraId}`, { method: 'POST' });
    const data = await res.json();
    alert(`🚨 ALERTA GENERADA EN TIEMPO REAL:\nTipo: ${data.alert_type}\nCámara: ${data.camera_name}\nDescripción: ${data.description}`);
    loadAlerts();
  } catch (err) {
    alert("Error al simular alerta");
  }
}

async function updateAlertStatus(alertId, newStatus) {
  try {
    await fetch(`/api/v1/alerts/${alertId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    loadAlerts();
  } catch (err) {
    alert("Error al actualizar estado de alerta");
  }
}

// ----------------------------------------------------
// 4. AWS INFRASTRUCTURE & SSM
// ----------------------------------------------------
async function loadAWSInfrastructure() {
  try {
    const res = await fetch('/api/v1/aws/ec2-fleet');
    const nodes = await res.json();

    document.getElementById('ec2-fleet-count').innerText = `${nodes.length} Nodos Activos`;
    const avgCpu = (nodes.reduce((acc, curr) => acc + curr.cpu_utilization, 0) / nodes.length).toFixed(1);
    document.getElementById('ec2-avg-cpu').innerText = `${avgCpu}%`;

    const tbody = document.getElementById('ec2-fleet-table-body');
    tbody.innerHTML = '';

    nodes.forEach(node => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-family: monospace; color: var(--accent-cyan);">${node.instance_id}</td>
        <td><strong>${node.instance_type}</strong> (Graviton 3)</td>
        <td>${node.availability_zone}</td>
        <td><span style="color: var(--accent-green);">● ${node.state}</span></td>
        <td>${node.cpu_utilization}%</td>
        <td>${node.current_streams} cámaras</td>
        <td><span class="badge-tier badge-standard">${node.lifecycle_type}</span></td>
        <td><span class="badge-status" style="display: inline-flex;"><span class="status-dot"></span> ${node.ssm_agent_status}</span></td>
      `;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("Error loading AWS infra:", err);
  }
}

async function evaluateAutoScaling() {
  try {
    const res = await fetch('/api/v1/aws/ec2-autoscaling/evaluate', { method: 'POST' });
    const data = await res.json();
    alert(`Evaluación de Auto Scaling AWS:\nEstado: ${data.fleet_status}\nAcción: ${data.action_taken}\nNodos en cluster: ${data.total_worker_instances}\nPromedio CPU: ${data.average_cpu_percent}%`);
    loadAWSInfrastructure();
  } catch (err) {
    alert("Error al evaluar auto scaling");
  }
}

async function runQuickSSM(cmd) {
  document.getElementById('ssm-cmd-input').value = cmd;
  await executeSSMCommand();
}

async function executeSSMCommand() {
  const input = document.getElementById('ssm-cmd-input');
  const command = input.value.trim();
  if (!command) return;

  const terminal = document.getElementById('ssm-terminal-output');
  terminal.innerHTML += `\n\n\x1b[36m> Enviando comando a AWS Systems Manager: "${command}"...\x1b[0m`;
  terminal.scrollTop = terminal.scrollHeight;

  try {
    const res = await fetch('/api/v1/aws/ssm/run-command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: command, instance_ids: ["i-08a9f4c3b2e1001", "i-08a9f4c3b2e1002"] })
    });
    const data = await res.json();

    terminal.innerHTML += `\n[SSM Command ID: ${data.command_id}] Canal: ${data.delivery_channel}\nResultado (Status: ${data.status}):\n${data.output}`;
    terminal.scrollTop = terminal.scrollHeight;
    input.value = '';
  } catch (err) {
    terminal.innerHTML += `\nError al ejecutar comando en AWS Systems Manager.`;
  }
}

// ----------------------------------------------------
// 5. COST ANALYSIS & ROI
// ----------------------------------------------------
async function loadCostAnalysis() {
  try {
    const res = await fetch('/api/v1/cost-analysis/history');
    const history = await res.json();

    const tbody = document.getElementById('cost-history-table-body');
    tbody.innerHTML = '';

    history.forEach(item => {
      const tr = document.createElement('tr');
      const isOptimized = item.architecture_type.includes('Optimizado');

      tr.innerHTML = `
        <td><strong>${item.period_name}</strong></td>
        <td>
          <span class="badge-tier ${isOptimized ? 'badge-standard' : 'badge-crit'}">
            ${item.architecture_type}
          </span>
        </td>
        <td>$${item.ec2_cost_usd.toFixed(2)}</td>
        <td>$${item.s3_cost_usd.toFixed(2)}</td>
        <td>$${item.rds_cost_usd.toFixed(2)}</td>
        <td>$${item.data_transfer_usd.toFixed(2)}</td>
        <td><strong style="color: ${isOptimized ? 'var(--accent-green)' : 'var(--accent-red)'}; font-size: 1.05rem;">$${item.total_cost_usd.toFixed(2)}</strong></td>
        <td>${item.active_cameras_count} cámaras</td>
      `;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("Error loading cost analysis:", err);
  }
}

// Initial Boot
document.addEventListener('DOMContentLoaded', () => {
  loadCameras();
  loadAlerts();
});

