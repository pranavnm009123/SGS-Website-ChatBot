const ADMIN_KEY = 'localdev123';

const dropZone   = document.getElementById('drop-zone');
const fileInput  = document.getElementById('file-input');
const statusEl   = document.getElementById('upload-status');
const tbody      = document.getElementById('docs-tbody');
const reindexBtn = document.getElementById('reindex-btn');

let selectedFiles = [];

// ── Drag & Drop ──────────────────────────────────────────────────────────────
dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', e => handleFiles(e.target.files));

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  handleFiles(e.dataTransfer.files);
});

function handleFiles(fileList) {
  const files = Array.from(fileList).filter(f => f.name.toLowerCase().endsWith('.pdf'));
  if (!files.length) {
    setStatus('Please select valid PDF files.', 'var(--danger)');
    return;
  }
  selectedFiles = files;
  const list = files.map(f =>
    `<div style="display:flex;align-items:center;gap:.5rem;padding:.15rem 0;">` +
    `<span>📄 ${esc(f.name)} <span style="color:var(--text-muted)">(${(f.size/1024).toFixed(1)} KB)</span></span>` +
    `</div>`
  ).join('');
  setStatus(`
    ${list}
    <button class="btn btn-primary btn-sm" id="upload-btn" style="margin-top:.5rem;">
      Upload ${files.length > 1 ? files.length + ' files' : ''}
    </button>
  `);
  document.getElementById('upload-btn').addEventListener('click', uploadFiles);
}

async function uploadFiles() {
  if (!selectedFiles.length) return;
  const btn = document.getElementById('upload-btn');
  btn.disabled = true;
  btn.textContent = 'Uploading…';

  let successes = 0;
  let errors = [];

  for (const file of selectedFiles) {
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch('/upload', { method: 'POST', body: form });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Upload failed');
      }
      successes++;
    } catch (err) {
      errors.push(`${file.name}: ${err.message}`);
    }
  }

  if (errors.length) {
    setStatus(`✓ ${successes} uploaded. Errors: ${errors.join(', ')}`, errors.length === selectedFiles.length ? 'var(--danger)' : 'var(--success)');
  } else {
    setStatus(`✓ ${successes} file${successes > 1 ? 's' : ''} uploaded — pending approval.`, 'var(--success)');
  }
  selectedFiles = [];
  fetchDocs();
}

function setStatus(html, color) {
  statusEl.style.color = color || 'var(--text)';
  statusEl.innerHTML = html;
}

// ── Document library ─────────────────────────────────────────────────────────
async function fetchDocs() {
  try {
    const res  = await fetch('/documents');
    const docs = await res.json();
    renderTable(docs);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--danger)">Failed to load documents.</td></tr>`;
  }
}

function renderTable(docs) {
  if (!docs.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--text-muted);text-align:center;">No documents yet.</td></tr>`;
    return;
  }

  docs.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
  tbody.innerHTML = docs.map(doc => `
    <tr>
      <td title="${esc(doc.filename)}">${esc(doc.filename)}</td>
      <td>${doc.page_count}</td>
      <td>${doc.chunk_count || 0}</td>
      <td><span class="badge badge-${doc.status}">${doc.status}</span></td>
      <td class="table-actions" id="actions-${doc.doc_id}">
        ${renderActions(doc)}
      </td>
    </tr>
  `).join('');
}

function renderActions(doc) {
  if (doc.status === 'pending') {
    return `
      <button class="btn btn-primary btn-sm" onclick="approveDoc('${doc.doc_id}')">Approve</button>
      <button class="btn btn-outline btn-sm" style="border-color:#7f1d1d;color:#fca5a5;" onclick="rejectDoc('${doc.doc_id}')">Reject</button>
    `;
  }
  return `<button class="btn btn-danger btn-sm" onclick="deleteDoc('${doc.doc_id}')">${doc.status === 'approved' ? 'Remove' : 'Delete'}</button>`;
}

async function approveDoc(docId) {
  const cell = document.getElementById(`actions-${docId}`);
  if (cell) cell.innerHTML = '<span style="color:var(--text-muted);font-size:.85rem;">Ingesting…</span>';
  try {
    const res = await fetch(`/documents/${docId}/approve`, {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY }
    });
    if (!res.ok) throw new Error('Approval failed');
    fetchDocs();
  } catch (err) {
    alert(err.message);
    fetchDocs();
  }
}

async function rejectDoc(docId) {
  if (!confirm('Reject and delete this document?')) return;
  try {
    await fetch(`/documents/${docId}/reject`, {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY }
    });
    fetchDocs();
  } catch (err) { alert(err.message); }
}

async function deleteDoc(docId) {
  if (!confirm('Permanently remove this document and its vectors?')) return;
  try {
    await fetch(`/documents/${docId}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Key': ADMIN_KEY }
    });
    fetchDocs();
  } catch (err) { alert(err.message); }
}

// ── Re-index website ─────────────────────────────────────────────────────────
reindexBtn.addEventListener('click', async () => {
  reindexBtn.disabled = true;
  reindexBtn.textContent = 'Re-indexing…';
  try {
    const res = await fetch('/reindex-site', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY }
    });
    if (!res.ok) throw new Error('Re-index failed');
    reindexBtn.textContent = '✓ Done';
    setTimeout(() => { reindexBtn.textContent = '↺ Re-index Website'; reindexBtn.disabled = false; }, 2000);
  } catch (err) {
    alert(err.message);
    reindexBtn.textContent = '↺ Re-index Website';
    reindexBtn.disabled = false;
  }
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Init ──────────────────────────────────────────────────────────────────────
fetchDocs();
setInterval(fetchDocs, 5000);
