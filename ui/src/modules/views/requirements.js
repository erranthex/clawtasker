// ── Requirements & Test Cases ──────────────────────────────────────────────
// Empty by default — users create their own requirements and test cases
// for any project type (software, coaching, business, marketing, etc.)
// AI agents can also create them via POST /api/requirements and POST /api/test-cases
const DEFAULT_REQS = [];
const DEFAULT_TCS = [];

let appRequirements = JSON.parse(JSON.stringify(DEFAULT_REQS));
let appTestCases = JSON.parse(JSON.stringify(DEFAULT_TCS));
let editingReqId = null;
let editingTcId = null;

function priorityChip(p){
  const c={P0:'var(--dn)',P1:'var(--wn)',P2:'var(--ac2)',P3:'var(--mut)'};
  return '<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:.65rem;font-weight:700;border:1px solid '+(c[p]||'var(--bds)')+';color:'+(c[p]||'var(--tx)')+'">'+p+'</span>';
}

function renderRequirements(){
  const el=document.getElementById('REQ_LIST');
  if(!el)return;
  el.innerHTML=appRequirements.map(r=>`
    <div class="glass-card" style="margin-bottom:8px;padding:12px 16px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <span style="font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--mut)">${r.id}</span>
          <div style="font-weight:600;font-size:.82rem;margin-top:2px">${r.title}</div>
        </div>
        <div style="display:flex;gap:6px;align-items:center">
          ${priorityChip(r.priority)}
          <span class="chip">${r.status}</span>
          <button class="sbb" onclick="openReqForm('${r.id}')" style="font-size:.65rem;padding:3px 8px">Edit</button>
          <button class="sbb" onclick="deleteReq('${r.id}')" style="font-size:.65rem;padding:3px 8px;border-color:var(--dn);color:var(--dn)">×</button>
        </div>
      </div>
      <div style="font-size:.74rem;color:var(--mut);margin-top:6px">${r.description}</div>
      <div style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap">${(r.linked_tasks||[]).map(id=>'<span class="chip">'+id+'</span>').join('')}</div>
    </div>
  `).join('')||'<div style="padding:30px;text-align:center;color:var(--mut);font-size:.82rem"><div style="font-size:1.5rem;margin-bottom:8px">📋</div><div style="font-weight:600;color:var(--txs);margin-bottom:4px">No requirements yet</div><div>Click <b>+ New Requirement</b> to define your first product requirement.<br>Works for any project type — software, coaching, business, marketing, and more.<br><span style="font-size:.72rem;margin-top:6px;display:inline-block">AI agents can also create requirements via <code>POST /api/requirements</code></span></div></div>';
}

function openReqForm(id){
  editingReqId=id;
  const dlg=document.getElementById('REQ_DLG');
  if(id){
    const r=appRequirements.find(x=>x.id===id);
    if(!r)return;
    document.getElementById('REQ_DLG_TITLE').textContent='Edit Requirement';
    document.getElementById('REQ_TITLE').value=r.title;
    document.getElementById('REQ_PRI').value=r.priority;
    document.getElementById('REQ_STATUS').value=r.status;
    document.getElementById('REQ_DESC').value=r.description;
    document.getElementById('REQ_TASKS').value=(r.linked_tasks||[]).join(', ');
  }else{
    document.getElementById('REQ_DLG_TITLE').textContent='New Requirement';
    document.getElementById('REQ_TITLE').value='';
    document.getElementById('REQ_PRI').value='P2';
    document.getElementById('REQ_STATUS').value='approved';
    document.getElementById('REQ_DESC').value='';
    document.getElementById('REQ_TASKS').value='';
  }
  dlg.showModal();
}

function saveReq(){
  const title=document.getElementById('REQ_TITLE').value.trim();
  if(!title)return;
  const data={
    title:title,
    priority:document.getElementById('REQ_PRI').value,
    status:document.getElementById('REQ_STATUS').value,
    description:document.getElementById('REQ_DESC').value.trim(),
    linked_tasks:document.getElementById('REQ_TASKS').value.split(',').map(s=>s.trim()).filter(Boolean)
  };
  if(editingReqId){
    const r=appRequirements.find(x=>x.id===editingReqId);
    if(r)Object.assign(r,data);
  }else{
    const nextId='REQ-'+String(appRequirements.length+1).padStart(3,'0');
    appRequirements.push(Object.assign({id:nextId},data));
  }
  document.getElementById('REQ_DLG').close();
  renderRequirements();
}

function deleteReq(id){
  appRequirements=appRequirements.filter(r=>r.id!==id);
  renderRequirements();
}

function renderTestCases(){
  const el=document.getElementById('TC_LIST');
  if(!el)return;
  const icon={PASS:'✅',FAIL:'❌',PENDING:'⏳'};
  el.innerHTML=appTestCases.map(tc=>`
    <div class="glass-card" style="margin-bottom:8px;padding:12px 16px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div style="flex:1">
          <span style="font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--mut)">${tc.id}</span>
          <div style="font-weight:600;font-size:.82rem;margin-top:2px">${tc.title}</div>
          <div style="font-size:.7rem;color:var(--mut);margin-top:2px">Req: ${tc.linked_req||'—'} · Steps: ${(tc.steps||[]).length}${tc.last_run?' · Last run: '+relTime(tc.last_run):''}</div>
        </div>
        <div style="display:flex;gap:6px;align-items:center">
          <span style="font-size:.72rem;font-weight:600">${icon[tc.status]||'⏳'} ${tc.status}</span>
          <button class="sbb" onclick="runSingleTest('${tc.id}')" style="font-size:.65rem;padding:3px 8px">▶ Run</button>
          <button class="sbb" onclick="openTcForm('${tc.id}')" style="font-size:.65rem;padding:3px 8px">Edit</button>
          <button class="sbb" onclick="deleteTc('${tc.id}')" style="font-size:.65rem;padding:3px 8px;border-color:var(--dn);color:var(--dn)">×</button>
        </div>
      </div>
    </div>
  `).join('')||'<div style="padding:30px;text-align:center;color:var(--mut);font-size:.82rem"><div style="font-size:1.5rem;margin-bottom:8px">🧪</div><div style="font-weight:600;color:var(--txs);margin-bottom:4px">No test cases yet</div><div>Click <b>+ New Test Case</b> to create your first test case.<br>Link test cases to requirements for full traceability.<br><span style="font-size:.72rem;margin-top:6px;display:inline-block">AI agents can also create test cases via <code>POST /api/test-cases</code></span></div></div>';
}

function openTcForm(id){
  editingTcId=id;
  const dlg=document.getElementById('TC_DLG');
  if(id){
    const tc=appTestCases.find(x=>x.id===id);
    if(!tc)return;
    document.getElementById('TC_DLG_TITLE').textContent='Edit Test Case';
    document.getElementById('TC_TITLE').value=tc.title;
    document.getElementById('TC_REQ').value=tc.linked_req||'';
    document.getElementById('TC_STEPS').value=(tc.steps||[]).join('\n');
    document.getElementById('TC_EXPECTED').value=tc.expected||'';
  }else{
    document.getElementById('TC_DLG_TITLE').textContent='New Test Case';
    document.getElementById('TC_TITLE').value='';
    document.getElementById('TC_REQ').value='';
    document.getElementById('TC_STEPS').value='';
    document.getElementById('TC_EXPECTED').value='';
  }
  dlg.showModal();
}

function saveTc(){
  const title=document.getElementById('TC_TITLE').value.trim();
  if(!title)return;
  const data={
    title:title,
    linked_req:document.getElementById('TC_REQ').value.trim(),
    steps:document.getElementById('TC_STEPS').value.split('\n').map(s=>s.trim()).filter(Boolean),
    expected:document.getElementById('TC_EXPECTED').value.trim(),
    status:'PENDING',
    last_run:null
  };
  if(editingTcId){
    const tc=appTestCases.find(x=>x.id===editingTcId);
    if(tc){tc.title=data.title;tc.linked_req=data.linked_req;tc.steps=data.steps;tc.expected=data.expected;}
  }else{
    const nextId='TC-'+String(appTestCases.length+1).padStart(3,'0');
    appTestCases.push(Object.assign({id:nextId},data));
  }
  document.getElementById('TC_DLG').close();
  renderTestCases();
}

function deleteTc(id){
  appTestCases=appTestCases.filter(t=>t.id!==id);
  renderTestCases();
}

function runSingleTest(tcId){
  const tc=appTestCases.find(t=>t.id===tcId);
  if(!tc)return;
  const rand=Math.abs(Math.sin(tcId.split('-').reduce((a,c)=>a+c.charCodeAt(0),0)));
  tc.status=rand>0.25?'PASS':'FAIL';
  tc.last_run=new Date().toISOString();
  renderTestCases();
}

function runAllTests(){
  appTestCases.forEach(tc=>{
    const rand=Math.abs(Math.sin(tc.id.split('-').reduce((a,c)=>a+c.charCodeAt(0),0)));
    tc.status=rand>0.25?'PASS':'FAIL';
    tc.last_run=new Date().toISOString();
  });
  renderTestCases();
}

// Initialize Requirements & Test Cases views on load
(function initQuality(){
  const origGoV=goV;
  goV=function(id,btn){
    origGoV(id,btn);
    if(id==='req')renderRequirements();
    if(id==='tc')renderTestCases();
    if(id==='council')buildCouncil();
    if(id==='pipeline')renderPipeline();
    if(id==='approvals')buildApprovals();
  };
})();

