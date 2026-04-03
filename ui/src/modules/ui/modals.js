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
  const typeIcon={'bug':'🐛','story':'📖','spike':'⚡','epic':'🗺','task':'🔧'}[t.type||'task']||'🔧';
  const depsOn=(t.depends_on||[]).map(did=>{const dt=TASKS.find(x=>x.id===did)||{id:did,title:did,status:'?'};
    const dsc={backlog:'chip',ready:'chip in',in_progress:'chip ac',validation:'chip wn',done:'chip ok',blocked:'chip dn'}[dt.status]||'chip';
    return `<span class="${dsc}" style="cursor:pointer" onclick="closeMo();setTimeout(()=>openTask(TASKS.find(x=>x.id==='${did}')||{id:'${did}',title:'${did}',status:'?'}),50)" title="Open ${did}">${did}: ${(dt.title||did).slice(0,30)}</span>`;
  }).join('');
  const blocking=(t.blocking||[]).map(bid=>{const bt=TASKS.find(x=>x.id===bid)||{id:bid,title:bid,status:'?'};
    return `<span class="chip wn" style="cursor:pointer" onclick="closeMo();setTimeout(()=>openTask(TASKS.find(x=>x.id==='${bid}')||{id:'${bid}',title:'${bid}',status:'?'}),50)" title="Opens ${bid}">${bid}: ${(bt.title||bid).slice(0,30)}</span>`;
  }).join('');
  const linkTypeIcon={'blocks':'🚫','is-blocked-by':'⛔','relates-to':'🔗','duplicates':'📋','child-of':'↳','parent-of':'↑'};
  const linkedIssuesHtml=(t.links||[]).map(l=>{const lt=TASKS.find(x=>x.id===l.target_id);
    return `<span class="chip" style="cursor:pointer" onclick="closeMo();setTimeout(()=>openTask(TASKS.find(x=>x.id==='${l.target_id}')||{id:'${l.target_id}',title:'${l.title||l.target_id}',status:'?'}),50)">${linkTypeIcon[l.type]||'🔗'} ${l.type} · ${l.target_id}: ${(l.title||l.target_id).slice(0,28)}</span>`;
  }).join('');
  const acItems=(t.acceptance_criteria||[]);
  const activityHtml=(t.activity||[]).slice(-8).reverse().map(a=>`<div style="font-size:.68rem;color:var(--mut);padding:3px 0;border-bottom:1px solid rgba(255,255,255,.04)"><span style="color:var(--txs)">${a.author}</span> changed <span style="color:var(--ac)">${a.field}</span>: <span style="text-decoration:line-through">${a.from||'—'}</span> → <span style="color:var(--txs)">${a.to||'—'}</span> <span style="float:right">${(a.timestamp||'').slice(0,16).replace('T',' ')}</span></div>`).join('');
  box.innerHTML=`
    <div class="mo-head">
      <div>
        <div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:4px;font-family:'JetBrains Mono',monospace">${t.id} · ${t.project_name}${t.reporter?` · filed by ${t.reporter}`:''}</div>
        <div class="mo-title">${typeIcon} ${t.title}</div>
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
      ${(t.links||[]).length?`<div><div class="mo-st">Linked issues</div><div style="display:flex;gap:5px;flex-wrap:wrap">${linkedIssuesHtml}</div></div>`:''}
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
      ${acItems.length?`<div><div class="mo-st">Acceptance Criteria</div><div class="mo-cb">${acItems.map(item=>`<div class="mo-ci"><div class="chk">${isDone?'✓':''}</div><span>${item}</span></div>`).join('')}</div></div>`:''}
      <div><div class="mo-st">Validation steps</div><div class="mo-cb">${vsteps.map(item=>{const d=isVal;return`<div class="mo-ci"><div class="chk ${d?'done':''}">${d?'✓':''}</div><span>${item}</span></div>`;}).join('')}</div></div>
      <div class="mo-div"></div>
      ${(t.artifacts&&t.artifacts.length)?`<div class="mo-st">Artifacts</div><div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:8px">${t.artifacts.map(a=>`<a href="${a.startsWith('http')?a:'#'}" target="${a.startsWith('http')?'_blank':'_self'}" class="chip" style="text-decoration:none;cursor:pointer;font-size:.68rem" title="${a}">${a.length>45?a.slice(0,43)+'…':a}</a>`).join('')}</div>`:''}
      <div>
        <div class="mo-st">Comments (${(t.comments||[]).length})</div>
        ${(t.comments||[]).map(c=>`<div style="background:rgba(94,232,210,.05);border:1px solid rgba(94,232,210,.12);border-radius:6px;padding:8px 10px;margin-bottom:6px"><div style="display:flex;justify-content:space-between;margin-bottom:3px"><span style="font-size:.68rem;font-weight:700;color:var(--ac)">${c.author}</span><span style="font-size:.62rem;color:var(--mut)">${(c.timestamp||'').slice(0,16).replace('T',' ')}</span></div><div style="font-size:.76rem;color:var(--tx)">${c.text}</div></div>`).join('')}
        <div style="display:flex;gap:6px;margin-top:6px">
          <input id="CMT_INPUT_${t.id}" class="ai" placeholder="Add a comment…" style="flex:1;font-size:.75rem">
          <button class="sbb p" style="padding:4px 12px;font-size:.72rem" onclick="submitTaskComment('${t.id}')">Post</button>
        </div>
      </div>
      ${activityHtml?`<div style="margin-top:8px"><div class="mo-st">Activity</div>${activityHtml}</div>`:''}
      <div style="display:flex;gap:8px;margin-top:8px">
        <button class="sbb" style="font-size:.68rem;padding:4px 10px" onclick="closeMo();openTaskEdit('${t.id}')">✎ Edit</button>
        <button class="sbb" style="font-size:.68rem;padding:4px 10px;border-color:var(--dn);color:var(--dn)" onclick="closeMo();deleteTaskFromModal('${t.id}')">× Delete</button>
      </div>
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
  apiPost('/api/tasks/update',{id,owner:agentId});
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
    <div class="mo-head"><span class="mo-title">New task ticket</span><div style="display:flex;gap:8px;align-items:center"><button class="sbb" onclick="openTemplateChooser()" style="font-size:.6rem;padding:2px 8px">📋 Use template</button><button class="mo-x" onclick="closeMo()">×</button></div></div>
    <div id="NT_AC_WARN" style="display:none;align-items:center;gap:6px;padding:5px 10px;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);border-radius:var(--rsm);font-size:.68rem;color:#f87171;margin:0 0 4px">⚠ Acceptance criteria recommended before advancing to ready or beyond</div>
    <div style="display:grid;gap:12px;padding:0 0 10px;max-height:75vh;overflow-y:auto">
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Title *</label>
        <input id="NT_TITLE" class="ai" placeholder="What needs to be done?" style="width:100%"></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Description</label>
        <textarea id="NT_DESC" class="ai" rows="2" placeholder="Brief description of the work..." style="width:100%;resize:vertical"></textarea></div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Type</label>
          <select id="NT_TYPE" class="ai"><option value="task" selected>🔧 Task</option><option value="bug">🐛 Bug</option><option value="story">📖 Story</option><option value="spike">⚡ Spike</option><option value="epic">🗺 Epic</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Priority</label>
          <select id="NT_PRI" class="ai"><option value="P0">🔴 P0 Critical</option><option value="P1" selected>🟠 P1 High</option><option value="P2">🟡 P2 Medium</option><option value="P3">⚪ P3 Low</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Story points</label>
          <select id="NT_PTS" class="ai"><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option><option value="5">5</option><option value="8">8</option><option value="13">13</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Status</label>
          <select id="NT_STATUS" class="ai"><option value="backlog" selected>Backlog</option><option value="ready">Ready</option><option value="in_progress">In Progress</option></select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Assignee</label>
          <select id="NT_OWNER" class="ai"><option value="">— Unassigned —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Validator</label>
          <select id="NT_VALIDATOR" class="ai"><option value="">— None —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Horizon</label>
          <select id="NT_HORIZON" class="ai"><option value="Today">Today</option><option value="This Week" selected>This Week</option><option value="This Month">This Month</option><option value="Later">Later</option></select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Epic / Project</label>
          <select id="NT_PROJ" class="ai"><option value="">— No project —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Mission link</label>
          <select id="NT_MISSION" class="ai"><option value="">— No mission —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Sprint</label>
          <select id="NT_SPRINT" class="ai"><option value="">— No sprint —</option></select></div>
      </div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Labels <span style="color:var(--mut);font-weight:400">(comma-separated)</span></label>
        <input id="NT_LABELS" class="ai" placeholder="e.g. frontend, performance, v2" style="width:100%"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Definition of Done</label>
          <textarea id="NT_DOD" class="ai" rows="3" placeholder="One criterion per line:&#10;Implementation complete&#10;Tests passing&#10;Reviewed and approved" style="width:100%;resize:vertical"></textarea></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Acceptance Criteria</label>
          <textarea id="NT_AC" class="ai" rows="3" placeholder="One criterion per line:&#10;Given X when Y then Z" style="width:100%;resize:vertical"></textarea></div>
      </div>
      <button class="sbb p" onclick="submitNewTaskModal()">Create ticket</button>
    </div>`;
  const ownerSel=document.getElementById('NT_OWNER');
  const valSel=document.getElementById('NT_VALIDATOR');
  AGENTS.forEach(a=>{
    const o=mk('option','');o.value=a.id;o.textContent=a.name;ownerSel.appendChild(o);
    const v=mk('option','');v.value=a.id;v.textContent=a.name;valSel.appendChild(v);
  });
  const projSel=document.getElementById('NT_PROJ');
  (typeof PROJECTS!=='undefined'?PROJECTS:[]).forEach(p=>{const o=mk('option','');o.value=p.id;o.textContent=p.name||p.id;projSel.appendChild(o);});
  if(!projSel.options.length){
    Object.keys(AM||{}).forEach(p=>{const o=mk('option','');o.value=p.toLowerCase().replace(/\s+/g,'-');o.textContent=p;projSel.appendChild(o);});
  }
  const missSel=document.getElementById('NT_MISSION');
  (typeof missionsLocal!=='undefined'?missionsLocal:[]).forEach(m=>{const o=mk('option','');o.value=m.id;o.textContent=m.title;missSel.appendChild(o);});
  const sprintSel=document.getElementById('NT_SPRINT');
  (typeof SPRINTS!=='undefined'?SPRINTS:[]).forEach(s=>{const o=mk('option','');o.value=s.id;o.textContent=s.name||s.id;sprintSel.appendChild(o);});
  const ntStatus=document.getElementById('NT_STATUS');
  const ntWarn=document.getElementById('NT_AC_WARN');
  if(ntStatus&&ntWarn){ntStatus.addEventListener('change',function(){const adv=['ready','in_progress','validation'].includes(this.value);const hasAC=(document.getElementById('NT_AC')?.value.trim().length||0)>0;ntWarn.style.display=(adv&&!hasAC)?'flex':'none';});}
}

async function submitNewTaskModal(){
  const title=document.getElementById('NT_TITLE').value.trim();
  if(!title){alert('Title is required');return;}
  const ownerId=document.getElementById('NT_OWNER').value;
  const owner=AGENTS.find(a=>a.id===ownerId);
  const projId=document.getElementById('NT_PROJ').value;
  const dodText=document.getElementById('NT_DOD').value.trim();
  const acText=document.getElementById('NT_AC')?.value.trim()||'';
  const labelsText=document.getElementById('NT_LABELS')?.value.trim()||'';
  const dod=dodText?dodText.split('\n').map(s=>s.trim()).filter(Boolean):['Implementation complete','Tests passing','Reviewed'];
  const ac=acText?acText.split('\n').map(s=>s.trim()).filter(Boolean):[];
  const labels=labelsText?labelsText.split(',').map(s=>s.trim()).filter(Boolean):[];
  const body={
    title,
    description:document.getElementById('NT_DESC').value.trim()||title,
    status:document.getElementById('NT_STATUS').value||'backlog',
    project_id:projId,
    owner:ownerId,
    priority:document.getElementById('NT_PRI').value,
    story_points:parseInt(document.getElementById('NT_PTS').value)||3,
    mission_id:document.getElementById('NT_MISSION').value||'',
    sprint_id:document.getElementById('NT_SPRINT')?.value||'',
    type:document.getElementById('NT_TYPE')?.value||'task',
    validation_owner:document.getElementById('NT_VALIDATOR')?.value||'',
    horizon:document.getElementById('NT_HORIZON')?.value||'This Week',
    labels,
    definition_of_done:dod,
    acceptance_criteria:ac,
    validation_steps:['QA review passed'],
    reporter:'ceo',
  };
  try{
    const res=await apiPost('/api/tasks/create',body);
    if(res&&res.task){
      TASKS.unshift(res.task);
    } else {
      // optimistic local insert
      const id='T-'+(++taskCounter);
      TASKS.unshift({...body,id,owner_name:owner?owner.name:(ownerId||'Unassigned'),
        project_name:projId?projId.replace(/-/g,' ').replace(/\b\w/g,c=>c.toUpperCase()):'',
        comments:[],blocked:false,progress:0,labels:[],artifacts:[],
        depends_on:[],blocking:[],collaborators:[],story_points:body.story_points,
        routing_mismatch:false,updated_at:new Date().toISOString()});
    }
  }catch(e){
    const id='T-'+(++taskCounter);
    TASKS.unshift({...body,id,owner_name:owner?owner.name:(ownerId||'Unassigned'),
      project_name:projId?projId.replace(/-/g,' ').replace(/\b\w/g,c=>c.toUpperCase()):'',
      comments:[],blocked:false,progress:0,labels:[],artifacts:[],
      depends_on:[],blocking:[],collaborators:[],routing_mismatch:false,updated_at:new Date().toISOString()});
  }
  closeMo();renderBoard();refreshCounters();
  if(document.getElementById('V_pipeline')&&document.getElementById('V_pipeline').classList.contains('on'))renderPipeline();
}

// ── Task edit modal ─────────────────────────────────────────────────────
function openTaskEdit(taskId){
  const t=TASKS.find(x=>x.id===taskId);if(!t)return;
  closeMo();
  const mo=document.getElementById('MO');mo.style.display='flex';
  const mc=document.getElementById('MC');
  const curLabels=(t.labels||[]).join(', ');
  const esc=s=>(s||'').replace(/"/g,'&quot;').replace(/</g,'&lt;');
  mc.innerHTML=`
    <div class="mo-head"><span class="mo-title">Edit ${t.id}</span><button class="mo-x" onclick="closeMo()">×</button></div>
    <div style="display:grid;gap:10px;padding:0 0 10px;max-height:75vh;overflow-y:auto">
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Title</label>
        <input id="TE_TITLE" class="ai" value="${esc(t.title)}" style="width:100%"></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Description</label>
        <textarea id="TE_DESC" class="ai" rows="2" style="width:100%;resize:vertical">${esc(t.description)}</textarea></div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Type</label>
          <select id="TE_TYPE" class="ai">
            <option value="task" ${(t.type||'task')==='task'?'selected':''}>🔧 Task</option>
            <option value="bug" ${t.type==='bug'?'selected':''}>🐛 Bug</option>
            <option value="story" ${t.type==='story'?'selected':''}>📖 Story</option>
            <option value="spike" ${t.type==='spike'?'selected':''}>⚡ Spike</option>
            <option value="epic" ${t.type==='epic'?'selected':''}>🗺 Epic</option>
          </select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Status</label>
          <select id="TE_STATUS" class="ai"><option value="backlog" ${t.status==='backlog'?'selected':''}>Backlog</option><option value="ready" ${t.status==='ready'?'selected':''}>Ready</option><option value="in_progress" ${t.status==='in_progress'?'selected':''}>In Progress</option><option value="validation" ${t.status==='validation'?'selected':''}>Validation</option><option value="done" ${t.status==='done'?'selected':''}>Done</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Priority</label>
          <select id="TE_PRI" class="ai"><option value="P0" ${t.priority==='P0'?'selected':''}>🔴 P0</option><option value="P1" ${t.priority==='P1'?'selected':''}>🟠 P1</option><option value="P2" ${t.priority==='P2'?'selected':''}>🟡 P2</option><option value="P3" ${t.priority==='P3'?'selected':''}>⚪ P3</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Points</label>
          <select id="TE_PTS" class="ai"><option value="1" ${t.story_points==1?'selected':''}>1</option><option value="2" ${t.story_points==2?'selected':''}>2</option><option value="3" ${t.story_points==3?'selected':''}>3</option><option value="5" ${t.story_points==5?'selected':''}>5</option><option value="8" ${t.story_points==8?'selected':''}>8</option><option value="13" ${t.story_points==13?'selected':''}>13</option></select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Assignee</label>
          <select id="TE_OWNER" class="ai"><option value="">— Unassigned —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Validator</label>
          <select id="TE_VALIDATOR" class="ai"><option value="">— None —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Horizon</label>
          <select id="TE_HORIZON" class="ai">
            <option value="Today" ${t.horizon==='Today'?'selected':''}>Today</option>
            <option value="This Week" ${(!t.horizon||t.horizon==='This Week')?'selected':''}>This Week</option>
            <option value="This Month" ${t.horizon==='This Month'?'selected':''}>This Month</option>
            <option value="Later" ${t.horizon==='Later'?'selected':''}>Later</option>
          </select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Mission</label>
          <select id="TE_MISSION" class="ai"><option value="">— No mission —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Sprint</label>
          <select id="TE_SPRINT" class="ai"><option value="">— No sprint —</option></select></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr;gap:8px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Labels <span style="font-weight:400">(comma-separated)</span></label>
          <input id="TE_LABELS" class="ai" value="${esc(curLabels)}" placeholder="e.g. frontend, bug, v2" style="width:100%"></div>
      </div>
      <div style="display:flex;align-items:center;gap:8px;padding:6px 0">
        <input type="checkbox" id="TE_BLOCKED" ${t.blocked?'checked':''}>
        <label for="TE_BLOCKED" style="font-size:.72rem;color:var(--mut);cursor:pointer">Mark as blocked</label>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Definition of Done</label>
          <textarea id="TE_DOD" class="ai" rows="3" style="width:100%;resize:vertical">${esc((t.definition_of_done||[]).join('\n'))}</textarea></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Acceptance Criteria</label>
          <textarea id="TE_AC" class="ai" rows="3" style="width:100%;resize:vertical">${esc((t.acceptance_criteria||[]).join('\n'))}</textarea></div>
      </div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Artifacts <span style="font-weight:400">(one per line: file paths, URLs, doc names)</span></label>
        <textarea id="TE_ARTIFACTS" class="ai" rows="2" placeholder="e.g. workspace/myproject/docs/spec.md&#10;https://docs.example.com" style="width:100%;resize:vertical">${esc((t.artifacts||[]).join('\n'))}</textarea></div>
      <button class="sbb p" onclick="submitTaskEdit('${t.id}')">Save changes</button>
    </div>`;
  const sel=document.getElementById('TE_OWNER');
  const valSel=document.getElementById('TE_VALIDATOR');
  AGENTS.forEach(a=>{
    const o=mk('option','');o.value=a.id;o.textContent=a.name;
    if(a.id===(t.owner_id||t.owner))o.selected=true;
    sel.appendChild(o);
    const v=mk('option','');v.value=a.id;v.textContent=a.name;
    if(a.id===t.validation_owner)v.selected=true;
    valSel.appendChild(v);
  });
  const missSel=document.getElementById('TE_MISSION');
  (typeof missionsLocal!=='undefined'?missionsLocal:[]).forEach(m=>{const o=mk('option','');o.value=m.id;o.textContent=m.title;if(m.id===t.mission_id)o.selected=true;missSel.appendChild(o);});
  const sprintSel=document.getElementById('TE_SPRINT');
  (typeof SPRINTS!=='undefined'?SPRINTS:[]).forEach(s=>{const o=mk('option','');o.value=s.id;o.textContent=s.name||s.id;if(s.id===t.sprint_id)o.selected=true;sprintSel.appendChild(o);});
}

function submitTaskEdit(id){
  const t=TASKS.find(x=>x.id===id);if(!t)return;
  t.title=document.getElementById('TE_TITLE').value.trim()||t.title;
  t.description=document.getElementById('TE_DESC').value.trim();
  t.status=document.getElementById('TE_STATUS').value;
  t.priority=document.getElementById('TE_PRI').value;
  t.story_points=parseInt(document.getElementById('TE_PTS').value)||3;
  t.type=document.getElementById('TE_TYPE')?.value||t.type||'task';
  t.horizon=document.getElementById('TE_HORIZON')?.value||t.horizon||'This Week';
  t.blocked=document.getElementById('TE_BLOCKED')?.checked||false;
  t.mission_id=document.getElementById('TE_MISSION')?.value||'';
  t.sprint_id=document.getElementById('TE_SPRINT')?.value||null;
  const ownerId=document.getElementById('TE_OWNER').value;
  t.owner_id=ownerId;t.owner=ownerId;
  const owner=AGENTS.find(a=>a.id===ownerId);
  t.owner_name=owner?owner.name:ownerId;
  t.validation_owner=document.getElementById('TE_VALIDATOR')?.value||t.validation_owner;
  const labelsText=document.getElementById('TE_LABELS')?.value.trim()||'';
  t.labels=labelsText?labelsText.split(',').map(s=>s.trim()).filter(Boolean):t.labels;
  const dod=document.getElementById('TE_DOD').value.trim();
  t.definition_of_done=dod?dod.split('\n').map(s=>s.trim()).filter(Boolean):t.definition_of_done;
  const acText=document.getElementById('TE_AC')?.value.trim()||'';
  t.acceptance_criteria=acText?acText.split('\n').map(s=>s.trim()).filter(Boolean):t.acceptance_criteria;
  const artText=document.getElementById('TE_ARTIFACTS')?.value.trim()||'';
  t.artifacts=artText?artText.split('\n').map(s=>s.trim()).filter(Boolean):t.artifacts||[];
  apiPost('/api/tasks/update',{
    id, title:t.title, description:t.description, status:t.status,
    priority:t.priority, story_points:t.story_points, owner:ownerId,
    type:t.type, horizon:t.horizon, blocked:t.blocked,
    mission_id:t.mission_id, sprint_id:t.sprint_id,
    validation_owner:t.validation_owner, labels:t.labels,
    definition_of_done:t.definition_of_done, acceptance_criteria:t.acceptance_criteria,
    artifacts:t.artifacts,
  });
  closeMo();renderBoard();refreshCounters();
  if(document.getElementById('V_pipeline')&&document.getElementById('V_pipeline').classList.contains('on'))renderPipeline();
  if(document.getElementById('V_approvals')&&document.getElementById('V_approvals').classList.contains('on'))buildApprovals();
}

// ── Shared API helper ─────────────────────────────────────────────────────────
function apiPost(path,body){
  const tok=typeof API_TOKEN!=='undefined'?API_TOKEN:'';
  return fetch(path,{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+tok},
    body:JSON.stringify(body)}).then(r=>r.ok?r.json():r.json().then(e=>{
      const msg=e.error||'Server error';
      if(typeof showToast==='function') showToast('Error: '+msg,'error');
      throw new Error(msg);
    })).catch(err=>{
      if(typeof showToast==='function') showToast('Request failed: '+(err.message||'network error'),'error');
      throw err;
    });
}

// ── Task comment ──────────────────────────────────────────────────────────────
async function submitTaskComment(taskId){
  const inp=document.getElementById('CMT_INPUT_'+taskId);
  if(!inp)return;
  const text=inp.value.trim();if(!text)return;
  const t=TASKS.find(x=>x.id===taskId);if(!t)return;
  inp.value='';
  try{
    const res=await apiPost('/api/tasks/comment',{task_id:taskId,text,author:'ceo'});
    if(res&&res.comment){
      t.comments=t.comments||[];t.comments.push(res.comment);
    }
  }catch(e){
    t.comments=t.comments||[];
    t.comments.push({id:'cm-local-'+Date.now(),author:'ceo',text,timestamp:new Date().toISOString()});
  }
  openTask(t);
}

// ── Task delete from modal ────────────────────────────────────────────────────
async function deleteTaskFromModal(taskId){
  if(!confirm('Delete task '+taskId+'?'))return;
  const idx=TASKS.findIndex(t=>t.id===taskId);
  if(idx>=0)TASKS.splice(idx,1);
  try{await apiPost('/api/tasks/delete',{task_id:taskId});}catch(e){}
  renderPipeline();renderBoard();refreshCounters();
}

// ── Task templates ────────────────────────────────────────────────────────────
async function openTemplateChooser(){
  let templates=[];
  try{const res=await fetch('/api/tasks/templates',{headers:{'Authorization':'Bearer '+(typeof API_TOKEN!=='undefined'?API_TOKEN:'')}});if(res.ok)templates=(await res.json()).templates||[];}catch(_){}
  if(!templates.length){alert('No templates available (server offline)');return;}
  const mo=document.getElementById('MO');mo.style.display='flex';
  const mc=document.getElementById('MC');
  mc.innerHTML=`<div class="mo-head"><span class="mo-title">Choose a template</span><button class="mo-x" onclick="closeMo()">×</button></div><div style="display:grid;gap:8px;padding:0 0 10px">${templates.map((tpl,i)=>`<div style="padding:10px 12px;border:1px solid var(--bd);border-radius:var(--rsm);cursor:pointer;background:var(--bg3)" onclick="applyTemplate(${i})"><div style="font-weight:700;color:var(--txs);font-size:.8rem">${tpl.name}</div><div style="font-size:.68rem;color:var(--mut);margin-top:2px">${tpl.specialist} · ${tpl.type} · ${tpl.priority}</div></div>`).join('')}</div>`;
  mc._tplCache=templates;
}

function applyTemplate(idx){
  const mc=document.getElementById('MC');
  const tpl=(mc._tplCache||[])[idx];if(!tpl)return;
  closeMo();openNewTaskForm();
  requestAnimationFrame(()=>{
    const setVal=(id,val)=>{const el=document.getElementById(id);if(el&&val!=null)el.value=val;};
    setVal('NT_DESC',tpl.description||'');
    setVal('NT_PRI',tpl.priority||'P1');
    setVal('NT_TYPE',tpl.type||'task');
    const acEl=document.getElementById('NT_AC');
    const dodEl=document.getElementById('NT_DOD');
    const labEl=document.getElementById('NT_LABELS');
    if(acEl&&tpl.acceptance_criteria)acEl.value=tpl.acceptance_criteria.join('\n');
    if(dodEl&&tpl.definition_of_done)dodEl.value=tpl.definition_of_done.join('\n');
    if(labEl&&tpl.labels)labEl.value=tpl.labels.join(', ');
  });
}
