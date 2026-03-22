// ── Task modal ─────────────────────────────────────────────────────────────
function openTask(t){
  const box=document.getElementById('MB');
  const sc={backlog:'chip',ready:'chip in',in_progress:'chip ac',validation:'chip wn',done:'chip ok'}[t.status]||'chip';
  const pColor=HUE[t.specialist]||'#14b8a6';
  const isDone=t.status==='done',isVal=t.status==='validation'||isDone;
  const dod=t.definition_of_done||[];const vsteps=t.validation_steps||[];
  const collabs=t.collaborators||[];
  const nextState=LIFECYCLE[t.status];
  const agentOptions=AGENTS.map(a=>`<option value="${a.id}"${a.id===t.owner?' selected':''}>${a.name}</option>`).join('');
  const spBadge=t.story_points?`<span class="chip ac" style="font-family:'JetBrains Mono',monospace">${t.story_points} pts</span>`:`<span class="chip" style="font-family:'JetBrains Mono',monospace">? pts</span>`;
  const sprintName=t.sprint_id?(SPRINTS.find(s=>s.id===t.sprint_id)||{name:t.sprint_id}).name:'';
  const sprintBadge=sprintName?`<span class="chip in">📅 ${sprintName}</span>`:'';
  // Dependencies
  const depsOn=(t.depends_on||[]).map(did=>{const dt=TASKS.find(x=>x.id===did)||{id:did,title:did,status:'?'};
    const dsc={backlog:'chip',ready:'chip in',in_progress:'chip ac',validation:'chip wn',done:'chip ok',blocked:'chip dn'}[dt.status]||'chip';
    return `<span class="${dsc}" style="cursor:pointer" onclick="closeMo();setTimeout(()=>openTask(TASKS.find(x=>x.id==='${did}')||{id:'${did}',title:'${did}',status:'?'}),50)" title="Open ${did}">${did}: ${(dt.title||did).slice(0,30)}</span>`;
  }).join('');
  const blocking=(t.blocking||[]).map(bid=>{const bt=TASKS.find(x=>x.id===bid)||{id:bid,title:bid,status:'?'};
    return `<span class="chip wn" style="cursor:pointer" onclick="closeMo();setTimeout(()=>openTask(TASKS.find(x=>x.id==='${bid}')||{id:'${bid}',title:'${bid}',status:'?'}),50)" title="Opens ${bid}">${bid}: ${(bt.title||bid).slice(0,30)}</span>`;
  }).join('');
  box.innerHTML=`
    <div class="mo-head">
      <div>
        <div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:4px;font-family:'JetBrains Mono',monospace">${t.id} · ${t.project_name}</div>
        <div class="mo-title">${t.title}</div>
      </div>
      <button class="mo-close" onclick="closeMo()">×</button>
    </div>
    <div class="mo-body">
      <div class="mo-meta">
        <span class="${sc}">${t.status.replace(/_/g,' ')}</span>
        ${t.blocked?'<span class="chip dn">blocked</span>':''}
        ${t.routing_mismatch?'<span class="chip wn">mismatch</span>':''}
        <span class="chip">${t.priority}</span><span class="chip">${t.horizon}</span><span class="chip">${t.specialist}</span>
        ${spBadge}${sprintBadge}
        ${(t.labels||[]).map(l=>`<span class="chip">${l}</span>`).join('')}
        ${nextState?`<button class="sbb" style="margin-left:auto;padding:3px 10px;font-size:.68rem;font-weight:700;border:1px solid var(--ac);color:var(--ac);background:rgba(94,232,210,.08);border-radius:20px;cursor:pointer" onclick="advanceTask('${t.id}','${nextState}');closeMo();goV('board',document.querySelector('.nv.on'))">→ Advance to ${nextState.replace(/_/g,' ')}</button>`:''}
      </div>
      ${(t.depends_on||[]).length?`<div><div class="mo-st">Depends on</div><div style="display:flex;gap:5px;flex-wrap:wrap">${depsOn}</div></div>`:''}
      ${(t.blocking||[]).length?`<div><div class="mo-st">Blocking</div><div style="display:flex;gap:5px;flex-wrap:wrap">${blocking}</div></div>`:''}
      <div class="mo-div"></div>
      <div><div class="mo-st">Description</div><div class="mo-desc">${t.description}</div></div>
      <div class="mo-fl">
        <div class="mo-f">
          <div class="mo-fl2">Assign to</div>
          <select class="mo-sel" onchange="reassignTask('${t.id}',this.value)">${agentOptions}</select>
        </div>
        <div class="mo-f"><div class="mo-fl2">Validation owner</div><div class="mo-fv">${t.validation_owner_name}</div></div>
        <div class="mo-f"><div class="mo-fl2">Due date</div><div class="mo-fv">${t.due_date}</div></div>
        <div class="mo-f"><div class="mo-fl2">Issue</div><div class="mo-fv">${t.issue_ref}</div></div>
        <div class="mo-f" style="grid-column:1/-1"><div class="mo-fl2">Branch</div><div class="mo-fv" style="font-family:'JetBrains Mono',monospace;font-size:.7rem;word-break:break-all">${t.branch_name}</div></div>
      </div>
      <div class="pw"><div style="display:flex;justify-content:space-between;font-size:.75rem;font-weight:600;color:var(--txs)"><span>Progress</span><span>${t.progress}%</span></div><div class="pbl"><div class="pbfl" style="width:${t.progress}%;background:${pColor}"></div></div></div>
      ${collabs.length?`<div><div class="mo-st">Collaborators</div><div class="mo-cbs">${collabs.map(c=>{const a=AGENTS.find(x=>x.id===c);return`<div class="co-tag"><img src="${PT[c]||''}" class="card-portrait sm" style="width:24px;height:24px"><span>${a?a.name:c}</span></div>`;}).join('')}</div></div>`:''}
      <div class="mo-div"></div>
      <div><div class="mo-st">Definition of Done</div><div class="mo-cb">${dod.map((item,i)=>{const d=isDone||(t.progress>=(i+1)/dod.length*100&&t.progress>0);return`<div class="mo-ci"><div class="chk ${d?'done':''}">${d?'✓':''}</div><span>${item}</span></div>`;}).join('')}</div></div>
      <div><div class="mo-st">Validation steps</div><div class="mo-cb">${vsteps.map(item=>{const d=isVal;return`<div class="mo-ci"><div class="chk ${d?'done':''}">${d?'✓':''}</div><span>${item}</span></div>`;}).join('')}</div></div>
    </div>`;
  document.getElementById('MO').style.display='flex';
}

function reassignTask(id,agentId){
  const t=TASKS.find(t=>t.id===id);if(!t)return;
  const ag=AGENTS.find(a=>a.id===agentId);
  if(!ag)return;
  t.owner=agentId;t.owner_name=ag.name;
  if(t.routing_mismatch&&agentId===t.recommended_owner)t.routing_mismatch=false;
  renderBoard();
}

function closeMo(){document.getElementById('MO').style.display='none';}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMo();});

// ── Task creation ────────────────────────────────────────────────────────────
let taskCounter=300;
function openNewTaskForm(){
  const f=document.getElementById('TASK_FORM');if(!f)return;
  f.classList.add('open');
  const sel=document.getElementById('NTF_OWN');
  if(sel&&sel.options.length===0)AGENTS.forEach(a=>{const o=mk('option','');o.value=a.id;o.textContent=a.name;sel.appendChild(o);});
  f.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function closeTaskForm(){const f=document.getElementById('TASK_FORM');if(f)f.classList.remove('open');}
function submitNewTask(){
  const title=document.getElementById('NTF_TITLE').value.trim();if(!title){alert('Title required');return;}
  const ownerId=document.getElementById('NTF_OWN').value;
  const ownerAg=AGENTS.find(a=>a.id===ownerId);
  const spec=document.getElementById('NTF_SPEC').value;
  const pri=document.getElementById('NTF_PRI').value;
  const projId=document.getElementById('NTF_PROJ').value;
  const desc=document.getElementById('NTF_DESC').value.trim();
  const id='T-'+taskCounter++;
  const newTask={
    id,title,description:desc||title,status:'backlog',
    project_id:projId,project_name:projId.replace(/-/g,' ').replace(/\b\w/g,c=>c.toUpperCase()),
    specialist:spec,owner:ownerId,owner_name:ownerAg?ownerAg.name:ownerId,
    priority:pri,horizon:'This Week',progress:0,blocked:false,routing_mismatch:false,
    recommended_owner:ownerId,validation_owner:'ralph',validation_owner_name:'Ralph',
    due_date:'2026-03-27',branch_name:'agent/'+ownerId+'/'+id.toLowerCase()+'-'+title.toLowerCase().replace(/\s+/g,'-').slice(0,25),
    issue_ref:'GH-'+taskCounter,pr_status:'',labels:[],
    definition_of_done:['Implementation complete','Tests passing','Reviewed'],
    validation_steps:['QA review passed','No regressions'],
    collaborators:[],mission_id:'',
  };
  TASKS.unshift(newTask);
  closeTaskForm();renderBoard();refreshCounters();
  document.getElementById('NTF_TITLE').value='';
  document.getElementById('NTF_DESC').value='';
}


// ── Enhanced task creation via modal (GUI + API compatible) ─────────────────
// Overrides openNewTaskForm to provide full task ticket fields:
// title, description, DoD, epic/project link, assignee, priority, story points, comments

function openNewTaskForm(){
  const mo=document.getElementById('MO');mo.style.display='flex';
  const mc=document.getElementById('MC');
  mc.innerHTML=`
    <div class="mo-head"><span class="mo-title">New task ticket</span><button class="mo-x" onclick="closeMo()">×</button></div>
    <div style="display:grid;gap:12px;padding:0 0 10px;max-height:70vh;overflow-y:auto">
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Title *</label>
        <input id="NT_TITLE" class="ai" placeholder="What needs to be done?" style="width:100%"></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Description</label>
        <textarea id="NT_DESC" class="ai" rows="2" placeholder="Brief description of the work..." style="width:100%;resize:vertical"></textarea></div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Assignee</label>
          <select id="NT_OWNER" class="ai"><option value="">— Unassigned —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Priority</label>
          <select id="NT_PRI" class="ai"><option value="P0">P0 — Critical</option><option value="P1" selected>P1 — High</option><option value="P2">P2 — Medium</option><option value="P3">P3 — Low</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Story points</label>
          <select id="NT_PTS" class="ai"><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option><option value="5">5</option><option value="8">8</option><option value="13">13</option></select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Epic / Project</label>
          <select id="NT_PROJ" class="ai"><option value="">— No project —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Status</label>
          <select id="NT_STATUS" class="ai"><option value="backlog" selected>Backlog</option><option value="ready">Ready</option><option value="in_progress">In Progress</option></select></div>
      </div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Definition of Done</label>
        <textarea id="NT_DOD" class="ai" rows="2" placeholder="One criterion per line:&#10;Implementation complete&#10;Tests passing&#10;Reviewed and approved" style="width:100%;resize:vertical"></textarea></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Mission link (optional)</label>
        <select id="NT_MISSION" class="ai"><option value="">— No mission —</option></select></div>
      <div style="background:rgba(94,232,210,.06);border:1px solid rgba(94,232,210,.15);border-radius:8px;padding:10px;font-size:.72rem;color:var(--mut)">
        AI agents can create tasks via <code>POST /api/tasks/create</code> with the same fields.
      </div>
      <button class="sbb p" onclick="submitNewTaskModal()">Create ticket</button>
    </div>`;
  // Populate dropdowns
  const ownerSel=document.getElementById('NT_OWNER');
  AGENTS.forEach(a=>{const o=mk('option','');o.value=a.id;o.textContent=a.name;ownerSel.appendChild(o);});
  const projSel=document.getElementById('NT_PROJ');
  Object.keys(AM).forEach(p=>{const o=mk('option','');o.value=p.toLowerCase().replace(/\\s+/g,'-');o.textContent=p;projSel.appendChild(o);});
  const missSel=document.getElementById('NT_MISSION');
  (typeof missionsLocal!=='undefined'?missionsLocal:[]).forEach(m=>{const o=mk('option','');o.value=m.id;o.textContent=m.title;missSel.appendChild(o);});
}

function submitNewTaskModal(){
  const title=document.getElementById('NT_TITLE').value.trim();
  if(!title){alert('Title is required');return;}
  const id='T-'+(++taskCounter);
  const ownerId=document.getElementById('NT_OWNER').value;
  const owner=AGENTS.find(a=>a.id===ownerId);
  const projId=document.getElementById('NT_PROJ').value;
  const dodText=document.getElementById('NT_DOD').value.trim();
  const dod=dodText?dodText.split('\\n').map(s=>s.trim()).filter(Boolean):['Implementation complete','Tests passing','Reviewed'];
  
  const task={
    id, title,
    description:document.getElementById('NT_DESC').value.trim()||title,
    status:document.getElementById('NT_STATUS').value||'backlog',
    project_id:projId,
    project_name:projId?projId.replace(/-/g,' ').replace(/\\b\\w/g,c=>c.toUpperCase()):'',
    owner_id:ownerId,
    owner_name:owner?owner.name:(ownerId||'Unassigned'),
    priority:document.getElementById('NT_PRI').value,
    story_points:parseInt(document.getElementById('NT_PTS').value)||3,
    mission_id:document.getElementById('NT_MISSION').value||'',
    definition_of_done:dod,
    validation_steps:['QA review passed'],
    comments:[],
    blocked:false,
    due_date:'',
    created_at:new Date().toISOString()
  };
  TASKS.unshift(task);
  
  // POST to server
  fetch('/api/tasks/create',{
    method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+(typeof API_TOKEN!=='undefined'?API_TOKEN:'')},
    body:JSON.stringify(task)
  }).catch(()=>{});
  
  closeMo();renderBoard();refreshCounters();
  // Re-render pipeline if visible
  if(document.getElementById('V_pipeline')&&document.getElementById('V_pipeline').classList.contains('on'))renderPipeline();
}

// ── Task edit modal ─────────────────────────────────────────────────────
function openTaskEdit(taskId){
  const t=TASKS.find(x=>x.id===taskId);if(!t)return;
  closeMo();
  const mo=document.getElementById('MO');mo.style.display='flex';
  const mc=document.getElementById('MC');
  mc.innerHTML=`
    <div class="mo-head"><span class="mo-title">Edit ${t.id}</span><button class="mo-x" onclick="closeMo()">×</button></div>
    <div style="display:grid;gap:10px;padding:0 0 10px;max-height:70vh;overflow-y:auto">
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Title</label>
        <input id="TE_TITLE" class="ai" value="${(t.title||'').replace(/"/g,'&quot;')}" style="width:100%"></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Description</label>
        <textarea id="TE_DESC" class="ai" rows="2" style="width:100%;resize:vertical">${t.description||''}</textarea></div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Status</label>
          <select id="TE_STATUS" class="ai"><option value="backlog" ${t.status==='backlog'?'selected':''}>Backlog</option><option value="ready" ${t.status==='ready'?'selected':''}>Ready</option><option value="in_progress" ${t.status==='in_progress'?'selected':''}>In Progress</option><option value="validation" ${t.status==='validation'?'selected':''}>Validation</option><option value="done" ${t.status==='done'?'selected':''}>Done</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Priority</label>
          <select id="TE_PRI" class="ai"><option value="P0" ${t.priority==='P0'?'selected':''}>P0</option><option value="P1" ${t.priority==='P1'?'selected':''}>P1</option><option value="P2" ${t.priority==='P2'?'selected':''}>P2</option><option value="P3" ${t.priority==='P3'?'selected':''}>P3</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Points</label>
          <select id="TE_PTS" class="ai"><option value="1" ${t.story_points==1?'selected':''}>1</option><option value="2" ${t.story_points==2?'selected':''}>2</option><option value="3" ${t.story_points==3?'selected':''}>3</option><option value="5" ${t.story_points==5?'selected':''}>5</option><option value="8" ${t.story_points==8?'selected':''}>8</option><option value="13" ${t.story_points==13?'selected':''}>13</option></select></div>
      </div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Assignee</label>
        <select id="TE_OWNER" class="ai"><option value="">— Unassigned —</option></select></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Definition of Done</label>
        <textarea id="TE_DOD" class="ai" rows="2" style="width:100%;resize:vertical">${(t.definition_of_done||[]).join('\\n')}</textarea></div>
      <button class="sbb p" onclick="submitTaskEdit('${t.id}')">Save changes</button>
    </div>`;
  const sel=document.getElementById('TE_OWNER');
  AGENTS.forEach(a=>{const o=mk('option','');o.value=a.id;o.textContent=a.name;if(a.id===(t.owner_id||t.owner))o.selected=true;sel.appendChild(o);});
}

function submitTaskEdit(id){
  const t=TASKS.find(x=>x.id===id);if(!t)return;
  t.title=document.getElementById('TE_TITLE').value.trim()||t.title;
  t.description=document.getElementById('TE_DESC').value.trim();
  t.status=document.getElementById('TE_STATUS').value;
  t.priority=document.getElementById('TE_PRI').value;
  t.story_points=parseInt(document.getElementById('TE_PTS').value)||3;
  const ownerId=document.getElementById('TE_OWNER').value;
  t.owner_id=ownerId;t.owner=ownerId;
  const owner=AGENTS.find(a=>a.id===ownerId);
  t.owner_name=owner?owner.name:ownerId;
  const dod=document.getElementById('TE_DOD').value.trim();
  t.definition_of_done=dod?dod.split('\n').map(s=>s.trim()).filter(Boolean):t.definition_of_done;
  closeMo();renderBoard();refreshCounters();
  if(document.getElementById('V_pipeline')&&document.getElementById('V_pipeline').classList.contains('on'))renderPipeline();
  if(document.getElementById('V_approvals')&&document.getElementById('V_approvals').classList.contains('on'))buildApprovals();
}
