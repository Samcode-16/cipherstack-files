'use strict';
 
let currentMode = 'encrypt';
let selectedFile = null;
 
const $ = id => document.getElementById(id);
 
function setMode(mode) {
  currentMode = mode;
  const eBtn = $('encryptBtn'), dBtn = $('decryptBtn');
  const aBtn = $('actionBtn'), bTxt = $('btnText');
 
  if (mode === 'encrypt') {
    eBtn.classList.add('active'); eBtn.classList.remove('decrypt-active');
    eBtn.setAttribute('aria-pressed', 'true');
    dBtn.classList.remove('active', 'decrypt-active');
    dBtn.setAttribute('aria-pressed', 'false');
    aBtn.classList.remove('decrypt-mode');
    bTxt.textContent = 'Encrypt File';
    updateBtnIcon('lock');
  } else {
    dBtn.classList.add('active', 'decrypt-active');
    dBtn.setAttribute('aria-pressed', 'true');
    eBtn.classList.remove('active');
    eBtn.setAttribute('aria-pressed', 'false');
    aBtn.classList.add('decrypt-mode');
    bTxt.textContent = 'Decrypt File';
    updateBtnIcon('unlock');
  }
  hideOutput(); hideError();
}
 
function updateBtnIcon(type) {
  const icon = $('btnIcon');
  if (!icon) return;
  if (type === 'lock') {
    icon.innerHTML = `<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>`;
  } else {
    icon.innerHTML = `<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/><line x1="3" y1="3" x2="7" y2="7"/>`;
  }
}
 
function triggerFilePicker() {
  $('filePicker').value = '';
  $('filePicker').click();
}
 
function onFilePicked(input) {
  if (input.files && input.files[0]) attachFile(input.files[0]);
}
 
function onDragOver(e) { e.preventDefault(); $('dropzone').classList.add('drag-over'); }
function onDragLeave()  { $('dropzone').classList.remove('drag-over'); }
function onDrop(e) {
  e.preventDefault(); $('dropzone').classList.remove('drag-over');
  const files = e.dataTransfer?.files;
  if (files && files[0]) attachFile(files[0]);
}
 
function attachFile(file) {
  selectedFile = file;
  const bytes = file.size;
  const size = bytes >= 1_048_576 ? (bytes/1_048_576).toFixed(1)+' MB'
             : bytes >= 1024      ? (bytes/1024).toFixed(0)+' KB'
             : bytes + ' B';
  const ext = file.name.split('.').pop().toLowerCase();
 
  $('fileRow').innerHTML = `
    <div class="file-ico">${getFileIcon(ext)}</div>
    <div class="file-meta">
      <div class="file-name" title="${escHtml(file.name)}">${escHtml(file.name)}</div>
      <div class="file-size">${size}</div>
    </div>
    <button class="remove-btn" type="button" onclick="removeFile()">Remove</button>
  `;
  $('fileRow').classList.add('visible');
  $('dropzone').style.display = 'none';
  hideOutput(); hideError();
}
 
function removeFile() {
  selectedFile = null;
  $('fileRow').classList.remove('visible');
  $('fileRow').innerHTML = '';
  $('dropzone').style.display = '';
  $('filePicker').value = '';
  hideOutput(); hideError();
}
 
function getFileIcon(ext) {
  const map = { pdf:'document', doc:'document', docx:'document',
                xls:'spreadsheet', xlsx:'spreadsheet',
                jpg:'image', jpeg:'image', png:'image', gif:'image',
                zip:'archive', rar:'archive', encrypted:'lock' };
  const type = map[ext] || 'file';
  const icons = {
    document: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
    image:    `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`,
    archive:  `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>`,
    lock:     `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
    file:     `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>`,
  };
  return icons[type] || icons.file;
}
 
async function handleSubmit() {
  hideOutput(); hideError();
  if (!selectedFile) { showError('Please select a file first.'); return; }
 
  const formData = new FormData();
  formData.append('file', selectedFile);
 
  const btn = $('actionBtn');
  btn.disabled = true;
  showProgress();
 
  try {
    const resp = await fetch(`/process?mode=${encodeURIComponent(currentMode)}`, {
      method: 'POST', body: formData,
    });
    const data = await resp.json();
    finishProgress();
    await delay(350);
    hideProgress();
    if (data.success) {
      showOutput(data.filename);
    } else {
      showError(data.error || 'Something went wrong. Please try again.');
    }
  } catch (err) {
    finishProgress(); hideProgress();
    showError('Network error — could not reach the server.');
  } finally {
    btn.disabled = false;
  }
}
 
const STEPS = [
  { id: 'd1', label: 'Layer 1 — Playfair substitution…',    pct: 25 },
  { id: 'd2', label: 'Layer 2 — Columnar transposition…',   pct: 55 },
  { id: 'd3', label: 'Layer 3 — DES block cipher…',         pct: 82 },
  { id: 'd4', label: 'Saving output file…',                 pct: 97 },
];
 
let progressTimer = null;
 
function showProgress() {
  ['d1','d2','d3','d4'].forEach(id => $(id).className = 's-dot');
  $('progressFill').style.width = '0%';
  $('progressPct').textContent = '0%';
  $('progressLabel').textContent = 'Starting…';
  $('progressBlock').classList.add('visible');
  let step = 0;
  function tick() {
    if (step < STEPS.length) {
      if (step > 0) $(STEPS[step-1].id).className = 's-dot done';
      const s = STEPS[step];
      $(s.id).className = 's-dot active';
      $('progressLabel').textContent = s.label;
      $('progressPct').textContent = s.pct + '%';
      $('progressFill').style.width = s.pct + '%';
      step++;
      progressTimer = setTimeout(tick, 500 + Math.random() * 400);
    }
  }
  tick();
}
 
function finishProgress() {
  clearTimeout(progressTimer);
  ['d1','d2','d3','d4'].forEach(id => $(id).className = 's-dot done');
  $('progressFill').style.width = '100%';
  $('progressPct').textContent = '100%';
  $('progressLabel').textContent = 'Done!';
}
 
function hideProgress() { $('progressBlock').classList.remove('visible'); }
 
function showOutput(filename) {
  const block = $('outputBlock'), link = $('downloadLink'), label = $('outputLabel');
  label.textContent = currentMode === 'encrypt' ? 'Encryption complete' : 'Decryption complete';
  link.href = `/download/${encodeURIComponent(filename)}`;
  link.download = filename;
  block.classList.add('visible');
  block.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function hideOutput() { $('outputBlock').classList.remove('visible'); }
 
function showError(msg) {
  $('errorMsg').textContent = msg;
  $('errorBlock').classList.add('visible');
  $('errorBlock').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function hideError() { $('errorBlock').classList.remove('visible'); }
 
function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}