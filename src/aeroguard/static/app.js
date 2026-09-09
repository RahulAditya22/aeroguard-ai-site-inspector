const form = document.getElementById('inspectionForm');
const input = document.getElementById('imageInput');
const dropzone = document.getElementById('dropzone');
const preview = document.getElementById('preview');
const uploadPrompt = document.getElementById('uploadPrompt');
const selectedFile = document.getElementById('selectedFile');
const button = document.getElementById('inspectButton');
const message = document.getElementById('message');

input.addEventListener('change', () => setSelectedFile(input.files[0]));
['dragenter','dragover'].forEach(event => dropzone.addEventListener(event, e => { e.preventDefault(); dropzone.classList.add('drag'); }));
['dragleave','drop'].forEach(event => dropzone.addEventListener(event, e => { e.preventDefault(); dropzone.classList.remove('drag'); }));
dropzone.addEventListener('drop', e => { const file = e.dataTransfer.files[0]; if (file) { input.files = e.dataTransfer.files; setSelectedFile(file); } });

function setSelectedFile(file) {
  if (!file) return;
  selectedFile.hidden = false;
  selectedFile.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  uploadPrompt.hidden = true;
  clearMessage();
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const file = input.files[0];
  if (!file) return showMessage('Please select an image first.');
  button.disabled = true;
  button.innerHTML = 'Analyzing image… <span>⟳</span>';
  clearMessage();
  try {
    const body = new FormData(); body.append('image', file);
    const response = await fetch('/api/inspect', { method: 'POST', body });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Inspection failed.');
    renderResult(data); loadHistory();
  } catch (error) { showMessage(error.message); }
  finally { button.disabled = false; button.innerHTML = 'Run AI Inspection <span>→</span>'; }
});

document.getElementById('refreshButton').addEventListener('click', loadHistory);

function renderResult(data) {
  document.getElementById('emptyState').hidden = true;
  document.getElementById('resultBody').hidden = false;
  document.getElementById('resultTitle').textContent = data.threat_detected ? 'Threat detected' : 'No threat detected';
  const severity = document.getElementById('severity');
  severity.textContent = data.severity.toUpperCase(); severity.className = `severity ${data.severity}`;
  document.getElementById('threat').textContent = formatThreat(data.threat_type);
  document.getElementById('confidence').textContent = `${Math.round(data.confidence * 100)}%`;
  document.getElementById('action').textContent = formatThreat(data.automated_action);
  document.getElementById('description').textContent = data.description;
  document.getElementById('recommendedAction').textContent = data.recommended_action;
  fillList('observations', data.observations); fillList('uncertainties', data.uncertainties);
}

function fillList(id, items) { const el = document.getElementById(id); el.innerHTML = ''; (items || []).forEach(item => { const li = document.createElement('li'); li.textContent = item; el.appendChild(li); }); if (!items?.length) { const li = document.createElement('li'); li.textContent = 'None reported'; el.appendChild(li); } }
function formatThreat(value) { return String(value || '—').replaceAll('_',' '); }
function showMessage(text) { message.hidden = false; message.textContent = text; }
function clearMessage() { message.hidden = true; message.textContent = ''; }

async function loadHistory() {
  try {
    const response = await fetch('/api/incidents');
    const rows = await response.json();
    const body = document.getElementById('historyBody'); body.innerHTML = '';
    if (!rows.length) { body.innerHTML = '<tr><td colspan="6" class="empty-row">No inspections recorded yet.</td></tr>'; return; }
    rows.slice(0, 20).forEach(row => {
      const tr = document.createElement('tr');
      const values = [new Date(row.timestamp_utc).toLocaleString(), row.image_name, formatThreat(row.threat_type), row.severity, `${Math.round(Number(row.confidence) * 100)}%`, formatThreat(row.automated_action)];
      values.forEach((value, index) => { const td = document.createElement('td'); td.textContent = value; if (index === 3) td.className = `severity ${row.severity}`; tr.appendChild(td); });
      body.appendChild(tr);
    });
  } catch { /* History is supplementary; inspection remains usable. */ }
}

loadHistory();
fetch('/api/health').then(r => r.ok).catch(() => { document.getElementById('systemStatus').textContent = 'SYSTEM OFFLINE'; });
