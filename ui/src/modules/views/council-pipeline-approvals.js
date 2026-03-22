// ── Council view — full CRUD ──────────────────────────────────────────────
let councilEntries = [];

function buildCouncil(){
  const el=document.getElementById('COUNCIL_LIST');if(!el)return;
  el.innerHTML='';
  if(councilEntries.length===0){
    el.innerHTML='<div style="padding:30px;text-align:center;color:var(--mut);font-size:.82rem"><div style="font-size:1.5rem;margin-bottom:8px">📋</div><div style="font-weight:600;color:var(--txs);margin-bottom:4px">No council decisions yet</div><div>Click <b>+ New decision</b> to record your first executive decision.<br><span style="font-size:.72rem;margin-top:4px;display:inline-block">AI agents: <code>POST /api/council/decisions</code></span></div></div>';
    return;
  }
  councilEntries.forEach(c=>{
    const card=mk('div','card');
    card.style.cssText='padding:16px;border-radius:var(--rsm);background:var(--card);border:1px solid var(--bd)';
    const statusColor={decided:'var(--ok)','action-required':'var(--wn)',pending:'var(--mut)'}[c.status]||'var(--mut)';
    card.innerHTML=`
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div style="font-weight:700;color:var(--txs)">${c.title}</div>
        <div style="display:flex;gap:6px;align-items:center">
          <span class="chip">${c.priority||'P1'}</span>
          <span style="color:${statusColor};font-weight:700;font-size:.68rem;text-transform:uppercase">${c.status}</span>
          <button class="sbb" onclick="editCouncilEntry('${c.id}')" style="font-size:.6rem;padding:2px 6px">✎</button><button class="sbb" onclick="deleteCouncilEntry('${c.id}')" style="font-size:.6rem;padding:2px 6px;border-color:var(--dn);color:var(--dn)">×</button>
        </div>
      </div>
      <div style="color:var(--tx);font-size:.78rem;margin-bottom:8px">${c.summary||''}</div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;gap:4px">${(c.participants||[]).map(p=>{try{return mkFaceAv(p,'sm').outerHTML}catch(e){return ''}}).join('')}</div>
        <div style="color:var(--mut);font-size:.65rem">${c.id} · ${c.date||new Date().toISOString().slice(0,10)}</div>
      </div>`;
    el.appendChild(card);
  });
}

function openCouncilEntry(){
  const mo=document.getElementById('MO');mo.style.display='flex';
  const mc=document.getElementById('MC');
  mc.innerHTML=`
    <div class="mo-head"><span class="mo-title">New council decision</span><button class="mo-x" onclick="closeMo()">×</button></div>
    <div style="display:grid;gap:12px;padding:0 0 10px">
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Title</label>
        <input id="CD_TITLE" class="ai" placeholder="e.g. Sprint scope approved, Budget allocation" style="width:100%"></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Summary</label>
        <textarea id="CD_SUMMARY" class="ai" rows="3" placeholder="What was decided and why..." style="width:100%;resize:vertical"></textarea></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Status</label>
          <select id="CD_STATUS" class="ai"><option value="decided">Decided</option><option value="action-required">Action Required</option><option value="pending">Pending</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Priority</label>
          <select id="CD_PRI" class="ai"><option value="P0">P0</option><option value="P1" selected>P1</option><option value="P2">P2</option><option value="P3">P3</option></select></div>
      </div>
      <button class="sbb p" onclick="submitCouncilEntry()">Save decision</button>
    </div>`;
}

function submitCouncilEntry(){
  const title=document.getElementById('CD_TITLE').value.trim();
  if(!title){alert('Title required');return;}
  const id='C-'+String(councilEntries.length+1).padStart(3,'0');
  councilEntries.push({
    id, title,
    summary:document.getElementById('CD_SUMMARY').value.trim(),
    status:document.getElementById('CD_STATUS').value,
    priority:document.getElementById('CD_PRI').value,
    date:new Date().toISOString().slice(0,10),
    participants:['ceo']
  });
  closeMo();buildCouncil();
}

function deleteCouncilEntry(id){
  if(!confirm('Delete council decision '+id+'?'))return;
  councilEntries=councilEntries.filter(c=>c.id!==id);
  buildCouncil();
}

// ── Pipeline view — full task backlog ──────────────────────────────────────

function renderPipeline(){
  const el=document.getElementById('PIPE_TABLE');if(!el)return;
  const projFilter=(document.getElementById('PIPE_PROJ')||{}).value||'';
  const statusFilter=(document.getElementById('PIPE_STATUS')||{}).value||'';
  
  const projSel=document.getElementById('PIPE_PROJ');
  if(projSel&&projSel.options.length<=1){
    const projects=[...new Set(TASKS.map(t=>t.project_name).filter(Boolean))];
    projects.forEach(p=>{const o=mk('option','');o.value=p;o.textContent=p;projSel.appendChild(o);});
  }
  
  let filtered=TASKS.slice();
  if(projFilter) filtered=filtered.filter(t=>t.project_name===projFilter);
  if(statusFilter) filtered=filtered.filter(t=>t.status===statusFilter);
  
  const ORDER={in_progress:0,validation:1,ready:2,backlog:3,done:4};
  filtered.sort((a,b)=>(ORDER[a.status]||5)-(ORDER[b.status]||5));
  
  el.innerHTML='';
  if(filtered.length===0){
    el.innerHTML='<div style="padding:30px;text-align:center;color:var(--mut);font-size:.82rem"><div style="font-size:1.5rem;margin-bottom:8px">📝</div><div style="font-weight:600;color:var(--txs);margin-bottom:4px">No tickets yet</div><div>Click <b>+ New ticket</b> to create your first task.<br>Link tasks to projects/EPICs for full traceability.<br><span style="font-size:.72rem;margin-top:4px;display:inline-block">AI agents: <code>POST /api/tasks/create</code></span></div></div>';
    return;
  }
  
  const tbl=mk('table','');tbl.style.cssText='width:100%;border-collapse:collapse;font-size:.76rem';
  tbl.innerHTML='<thead><tr style="text-align:left;color:var(--mut);border-bottom:1px solid var(--bd)"><th style="padding:8px">ID</th><th style="padding:8px">Title</th><th style="padding:8px">Status</th><th style="padding:8px">Owner</th><th style="padding:8px">Project</th><th style="padding:8px">Pts</th><th style="padding:8px">Pri</th><th style="padding:8px"></th></tr></thead>';
  const tbody=mk('tbody','');
  filtered.forEach(t=>{
    const sc={backlog:'bi',ready:'bi',in_progress:'bw',validation:'bv',done:'bw'}[t.status]||'bi';
    const owner=AGENTS.find(a=>a.id===t.owner_id);
    const tr=mk('tr','');tr.style.cssText='border-bottom:1px solid var(--bd);cursor:pointer';
    tr.onclick=()=>openTask(t);
    tr.innerHTML=`
      <td style="padding:8px;color:var(--mut)">${t.id}</td>
      <td style="padding:8px;color:var(--txs);font-weight:600">${t.title}</td>
      <td style="padding:8px"><span class="badge ${sc}">${t.status}</span></td>
      <td style="padding:8px">${owner?owner.name:'—'}</td>
      <td style="padding:8px;color:var(--mut)">${t.project_name||'—'}</td>
      <td style="padding:8px;text-align:center">${t.story_points||'—'}</td>
      <td style="padding:8px">${t.priority||'—'}</td>
      <td style="padding:8px"><button class="sbb" onclick="event.stopPropagation();deleteTask('${t.id}')" style="font-size:.6rem;padding:2px 6px;border-color:var(--dn);color:var(--dn)">×</button></td>`;
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  el.appendChild(tbl);
  refreshCounters();
}

function deleteTask(id){
  if(!confirm('Delete task '+id+'?'))return;
  const idx=TASKS.findIndex(t=>t.id===id);
  if(idx>=0)TASKS.splice(idx,1);
  renderPipeline();renderBoard();refreshCounters();
}

// ── Approvals view ──────────────────────────────────────────────────────────

function buildApprovals(){
  const el=document.getElementById('APPR_LIST');if(!el)return;
  el.innerHTML='';
  
  const pending=TASKS.filter(t=>t.status==='validation'||t.status==='validating');
  const countEl=document.getElementById('APPR_COUNT');
  if(countEl) countEl.textContent=pending.length+' pending';
  
  if(pending.length===0){
    el.innerHTML='<div style="padding:30px;text-align:center;color:var(--mut);font-size:.82rem"><div style="font-size:1.5rem;margin-bottom:8px">✅</div><div style="font-weight:600;color:var(--txs);margin-bottom:4px">No approvals pending</div><div>Tasks in <b>validation</b> status will appear here for CEO review.</div></div>';
    return;
  }
  
  pending.forEach(t=>{
    const owner=AGENTS.find(a=>a.id===t.owner_id);
    const card=mk('div','card');
    card.style.cssText='padding:16px;border-radius:var(--rsm);background:var(--card);border:1px solid var(--bd);cursor:pointer';
    card.onclick=()=>openTask(t);
    card.innerHTML=`
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
        <div>
          <div style="font-weight:700;color:var(--txs)">${t.title}</div>
          <div style="color:var(--mut);font-size:.68rem;margin-top:2px">${t.id} · ${t.project_name||'No project'}</div>
        </div>
        <span class="badge bv">${t.status}</span>
      </div>
      <div style="color:var(--tx);font-size:.76rem;margin-bottom:10px">${t.description||'No description'}</div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;align-items:center;gap:6px">
          ${owner?mkFaceAv(owner.id,'sm').outerHTML:''}
          <span style="font-size:.72rem;color:var(--mut)">${owner?owner.name:'Unassigned'}</span>
        </div>
        <div style="display:flex;gap:6px">
          <button class="mc-edit" onclick="event.stopPropagation();advanceTask('${t.id}','done');buildApprovals();">Approve</button>
          <button class="fix-rt" style="font-size:.6rem" onclick="event.stopPropagation();advanceTask('${t.id}','in_progress');buildApprovals();">Return</button>
        </div>
      </div>`;
    el.appendChild(card);
  });
}

// ── Council edit ────────────────────────────────────────────────────────
function editCouncilEntry(id){
  const c=councilEntries.find(x=>x.id===id);if(!c)return;
  const mo=document.getElementById('MO');mo.style.display='flex';
  const mc=document.getElementById('MC');
  mc.innerHTML=`
    <div class="mo-head"><span class="mo-title">Edit decision ${c.id}</span><button class="mo-x" onclick="closeMo()">×</button></div>
    <div style="display:grid;gap:12px;padding:0 0 10px">
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Title</label>
        <input id="CD_TITLE" class="ai" value="${c.title}" style="width:100%"></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Summary</label>
        <textarea id="CD_SUMMARY" class="ai" rows="3" style="width:100%;resize:vertical">${c.summary||''}</textarea></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Status</label>
          <select id="CD_STATUS" class="ai"><option value="decided" ${c.status==='decided'?'selected':''}>Decided</option><option value="action-required" ${c.status==='action-required'?'selected':''}>Action Required</option><option value="pending" ${c.status==='pending'?'selected':''}>Pending</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Priority</label>
          <select id="CD_PRI" class="ai"><option value="P0" ${c.priority==='P0'?'selected':''}>P0</option><option value="P1" ${c.priority==='P1'?'selected':''}>P1</option><option value="P2" ${c.priority==='P2'?'selected':''}>P2</option><option value="P3" ${c.priority==='P3'?'selected':''}>P3</option></select></div>
      </div>
      <button class="sbb p" onclick="updateCouncilEntry('${c.id}')">Update decision</button>
    </div>`;
}

function updateCouncilEntry(id){
  const c=councilEntries.find(x=>x.id===id);if(!c)return;
  c.title=document.getElementById('CD_TITLE').value.trim()||c.title;
  c.summary=document.getElementById('CD_SUMMARY').value.trim();
  c.status=document.getElementById('CD_STATUS').value;
  c.priority=document.getElementById('CD_PRI').value;
  closeMo();buildCouncil();
}

// ── Mission delete ──────────────────────────────────────────────────────
function deleteMission(id){
  if(!confirm('Delete mission '+id+'?'))return;
  missionsLocal=missionsLocal.filter(m=>m.id!==id);
  buildMissions();
}
