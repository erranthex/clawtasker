// ── Dashboard ──────────────────────────────────────────────────────────────
function buildDashboard(){
  // Metrics
  const mr=document.getElementById('METRICS_ROW');
  const m=METRICS_DATA;
  const throughput=m.throughput||'2/15 done';
  const blocked=m.blocked||'1';
  const valq=m.validation_queue||'1';
  const util=m.agent_utilization||'13/13 active';
  mr.innerHTML=`
    <div class="met ok"><div class="met-v">${throughput}</div><div class="met-l">Done</div></div>
    <div class="met dn"><div class="met-v">${blocked}</div><div class="met-l">Blocked</div></div>
    <div class="met wn"><div class="met-v">${valq}</div><div class="met-l">Validation Q</div></div>
    <div class="met ac"><div class="met-v">${util.split('/')[0]||'13'}</div><div class="met-l">Active agents</div></div>`;

  // Attention queue
  const aql=document.getElementById('AQ_LIST');aql.innerHTML='';
  const kindColor={blocked:'var(--dn)',routing_mismatch:'var(--wn)',validation:'var(--wn)',mission_risk:'var(--dn)',dependency_blocked:'var(--dn)',staffing_gap:'var(--pu)'};
  (AQ_DATA||[]).forEach(item=>{
    const d=mk('div','attn');
    const dot=mk('div','attn-dot');dot.style.background=kindColor[item.kind]||'var(--mut)';
    const info=mk('div','');
    info.innerHTML=`<strong>${item.title}</strong><span>${item.owner||''} — ${item.detail||''}</span>`;
    d.appendChild(dot);d.appendChild(info);aql.appendChild(d);
  });

  // Projects
  const pl=document.getElementById('PROJ_LIST');pl.innerHTML='';
  (PROJECTS_DATA||[]).forEach(p=>{
    const d=mk('div','');d.style.cssText='padding:6px 0;border-bottom:1px solid var(--bd)';
    d.innerHTML=`<div style="font-size:.8rem;font-weight:600;color:var(--txs)">${p.name||p.id}</div><div style="font-size:.67rem;color:var(--mut)">${p.id} · ${(p.specialist_teams||[]).join(', ')||'shared'}</div>`;
    pl.appendChild(d);
  });

  // Mission feed
  const mf=document.getElementById('MISS_FEED');mf.innerHTML='';
  [{t:'47m ago',txt:'Ralph moved T-201 → Validation'},{t:'32m ago',txt:'Charlie flagged deploy secret blocker'},{t:'20m ago',txt:'Violet started 8AM briefing'},{t:'8m ago',txt:'Orion updated mission M-302 plan'}]
    .forEach(e=>{const d=mk('div','ev');d.innerHTML=`<span class="ev-t">${e.t}</span><span>${e.txt}</span>`;mf.appendChild(d);});
}

// ── Capability matrix ─────────────────────────────────────────────────────────
function buildCapabilityMatrix(){
  const el=document.getElementById('CAP_MATRIX');if(!el)return;
  const skills={
    orion:['planning','coordination','prioritization','chief-of-staff'],
    codex:['code','engineering','architecture','typescript','python'],
    violet:['research','intelligence','briefings','trend-analysis'],
    charlie:['ops','operations','github','deploy','workflow'],
    quill:['docs','knowledge','writing','guides','onboarding'],
    ralph:['qa','testing','validation','acceptance'],
    pixel:['design','ux','pixel-art','office-sim'],
    scout:['research','trend-radar','signals'],
    mercury:['media','coverage','press-monitoring'],
    echo:['distribution','publishing','channel-handoff'],
    shield:['security','threat-review','secret-rotation'],
    ledger:['procurement','vendor','purchasing'],
    iris:['hr','people-ops','policy','onboarding'],
  };
  let t='<table style="font-size:.74rem;width:100%;border-collapse:collapse"><thead><tr>';
  ['Agent','Role','Specialist','Skills','Status'].forEach(c=>t+=`<th style="padding:7px 10px;text-align:left;border-bottom:1px solid var(--bd);font-size:.6rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--mut);background:var(--bg3);font-family:'JetBrains Mono',monospace">${c}</th>`);
  t+='</tr></thead><tbody>';
  AGENTS.forEach(a=>{
    const st={working:'bw',blocked:'bb',validation:'bv',validating:'bv',idle:'bi'}[a.derived_status||a.status]||'bi';
    const sk=(skills[a.id]||[]).slice(0,4).map(s=>`<span class="chip" style="font-size:.58rem;padding:1px 6px">${s}</span>`).join(' ');
    const av=document.createElement('div');av.appendChild(mkFaceAv(a.id,'sm'));
    t+=`<tr onmouseover="this.style.background='var(--bgh)'" onmouseout="this.style.background=''">
      <td style="padding:7px 10px"><div style="display:flex;align-items:center;gap:7px">${av.innerHTML}<strong style="color:var(--txs)">${a.name}</strong></div></td>
      <td style="padding:7px 10px;color:var(--mut)">${a.role}</td>
      <td style="padding:7px 10px"><span class="chip ac">${a.hue}</span></td>
      <td style="padding:7px 10px">${sk}</td>
      <td style="padding:7px 10px"><span class="badge ${st}">${a.derived_status||a.status}</span></td>
    </tr>`;
  });
  t+='</tbody></table>';
  el.innerHTML=t;
}

// ── Project health ─────────────────────────────────────────────────────────────
function buildProjectHealth(){
  const el=document.getElementById('PROJ_HEALTH');if(!el)return;
  [{id:'ceo-console',name:'CEO Console',color:'#5ee8d2'},
   {id:'market-radar',name:'Market Radar',color:'#a78bfa'},
   {id:'atlas-core',name:'Atlas Core',color:'#f5a623'}].forEach(p=>{
    const tasks=TASKS.filter(t=>t.project_id===p.id);
    const done=tasks.filter(t=>t.status==='done').length;
    const blocked=tasks.filter(t=>t.blocked).length;
    const total=tasks.length;
    const pct=total?Math.round(done/total*100):0;
    const card=mk('div','');
    card.style.cssText='background:var(--bg3);border:1px solid var(--bd);border-radius:var(--rmd);padding:12px;border-top:3px solid '+p.color;
    card.innerHTML=`<div style="font-size:.82rem;font-weight:700;color:var(--txs);margin-bottom:6px">${p.name}</div>
      <div style="font-size:.7rem;color:var(--mut);margin-bottom:8px">${total} tasks · ${tasks.filter(t=>t.status==='in_progress').length} active${blocked?' · <span style="color:var(--dn)">⛔ '+blocked+' blocked</span>':''}</div>
      <div style="height:5px;background:var(--bds);border-radius:3px;overflow:hidden;margin-bottom:4px">
        <div style="height:100%;background:${p.color};width:${pct}%;border-radius:3px;transition:width .5s"></div>
      </div>
      <div style="font-size:.68rem;color:var(--mut)">${pct}% complete</div>`;
    el.appendChild(card);
  });
}

// ── Export snapshot ─────────────────────────────────────────────────────────────
function exportSnapshot(){
  const snap={version:'1.0.3',exported_at:new Date().toISOString(),agents:AGENTS,tasks:TASKS,missions:missionsLocal,positions:POSITIONS,calendar:CAL,access_matrix:AM,metrics:METRICS_DATA,attention_queue:AQ_DATA};
  const blob=new Blob([JSON.stringify(snap,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download='clawtasker-snapshot-'+Date.now()+'.json';a.click();URL.revokeObjectURL(url);
}

// ── Notifications ───────────────────────────────────────────────────────────
let notifOpen=false;
const localNotifications=[];
function toggleNotifDrawer(){
  notifOpen=!notifOpen;
  const d=document.getElementById('NOTIF_DRAWER');
  if(d){d.style.display=notifOpen?'block':'none';}
  if(notifOpen)renderNotifications();
}
function renderNotifications(){
  const el=document.getElementById('NOTIF_LIST');if(!el)return;
  const kindIcon={task_blocked:'⛔',task_completed:'✅',mission_risk:'⚠',agent_offline:'👤',
    sprint_ending:'📅',dependency_cleared:'🔗',directive_delivered:'📨',routing_mismatch:'↻',overloaded:'🔥'};
  if(!localNotifications.length){el.innerHTML='<div style="padding:16px;text-align:center;color:var(--mut);font-size:.78rem">No notifications</div>';return;}
  el.innerHTML=localNotifications.filter(n=>!n.dismissed).map(n=>`
    <div style="padding:10px 14px;border-bottom:1px solid var(--bd);display:flex;gap:10px;align-items:flex-start;${!n.read?'background:rgba(94,232,210,.04)':''}">
      <span style="font-size:1rem;flex-shrink:0;margin-top:1px">${kindIcon[n.kind]||'●'}</span>
      <div style="flex:1;min-width:0">
        <div style="font-size:.78rem;font-weight:600;color:var(--txs)">${n.title}</div>
        <div style="font-size:.68rem;color:var(--mut);margin-top:2px">${n.detail}</div>
      </div>
      <button onclick="dismissNotif('${n.id}')" style="flex-shrink:0;font-size:.65rem;color:var(--mut);background:transparent;border:none;cursor:pointer;padding:2px 6px;border-radius:4px;border:1px solid var(--bd)">Dismiss</button>
    </div>`).join('');
}
function addNotification(kind,title,detail,agentId){
  const n={id:'N-'+(localNotifications.length+1),kind,title,detail,agent_id:agentId||'',created_at:new Date().toISOString(),read:false,dismissed:false};
  localNotifications.unshift(n);
  updateNotifBadge();
  fetch('/api/notifications/dismiss',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},
    body:JSON.stringify({id:'placeholder'})}).catch(()=>{});
}
function dismissNotif(id){
  const n=localNotifications.find(x=>x.id===id);if(n){n.dismissed=true;n.read=true;}
  renderNotifications();updateNotifBadge();
  fetch('/api/notifications/dismiss',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},
    body:JSON.stringify({id})}).catch(()=>{});
}
function dismissAllNotifications(){
  localNotifications.forEach(n=>{n.dismissed=true;n.read=true;});
  renderNotifications();updateNotifBadge();toggleNotifDrawer();
  fetch('/api/notifications/dismiss',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},
    body:JSON.stringify({all:true})}).catch(()=>{});
}
function updateNotifBadge(){
  const badge=document.getElementById('NOTIF_BADGE');
  const bell=document.getElementById('NOTIF_BELL');
  const count=localNotifications.filter(n=>!n.dismissed&&!n.read).length;
  if(badge){
    badge.textContent=count>9?'9+':count;
    badge.style.display=count>0?'flex':'none';
  }
  if(bell)bell.style.borderColor=count>0?'var(--dn)':'var(--bd)';
}
function seedNotifications(){
  // Seed with initial notifications from current state
  const blocked=AGENTS.filter(a=>a.status==='blocked');
  blocked.forEach(a=>addNotification('task_blocked',`${a.name} blocked`,a.task||'',a.id));
  const overloaded=AGENTS.filter(a=>a.overloaded);
  overloaded.forEach(a=>addNotification('overloaded',`${a.name} overloaded`,`${a.workload_active||0} active tasks`,a.id));
  // Active focus period ending check
  const activeSp=SPRINTS.find(s=>s.status==='active');
  if(activeSp&&activeSp.end_date){
    const days=Math.round((new Date(activeSp.end_date)-new Date())/86400000);
    if(days<=3&&days>=0) addNotification('sprint_ending',`Sprint ending in ${days}d`,activeSp.name);
  }
}

// ── Active focus period dashboard card ─────────────────────────────────────────────
function buildActiveSprintCard(){
  const activeSp=SPRINTS.find(s=>s.status==='active');
  const card=document.getElementById('ACTIVE_SPRINT_CARD');
  if(!card)return;
  if(!activeSp){card.style.display='none';return;}
  const spTasks=TASKS.filter(t=>t.sprint_id===activeSp.id);
  const total=spTasks.reduce((sum,t)=>(t.story_points||1)+sum,0);
  const done=spTasks.filter(t=>t.status==='done').reduce((sum,t)=>(t.story_points||1)+sum,0);
  const pct=total?Math.round(done/total*100):0;
  const inprog=spTasks.filter(t=>t.status==='in_progress').length;
  const blocked=spTasks.filter(t=>t.blocked).length;
  document.getElementById('ASC_NAME').textContent=activeSp.name;
  document.getElementById('ASC_GOAL').textContent=activeSp.goal||'';
  document.getElementById('ASC_BAR').style.width=pct+'%';
  const metrics=document.getElementById('ASC_METRICS');
  if(metrics)metrics.innerHTML=[
    {v:spTasks.length,l:'Total tasks',c:''},
    {v:inprog,l:'In progress',c:'ac'},
    {v:`${done}/${total}`,l:'Points done',c:'ok'},
    {v:blocked||'0',l:'Blocked',c:blocked?'dn':''},
  ].map(m=>`<div class="met ${m.c}"><div class="met-v">${m.v}</div><div class="met-l">${m.l}</div></div>`).join('');
  card.style.display='block';
}

// ── Directives trail ──────────────────────────────────────────────────────────
const localDirectives=[];
function openDirectiveForm(){
  const f=document.getElementById('DIRECTIVE_FORM');if(!f)return;
  const sel=document.getElementById('DIR_TARGET');
  if(sel&&sel.options.length===0)AGENTS.forEach(a=>{const o=document.createElement('option');o.value=a.id;o.textContent=a.name;sel.appendChild(o);});
  f.classList.add('open');
}
function closeDirectiveForm(){const f=document.getElementById('DIRECTIVE_FORM');if(f)f.classList.remove('open');}
function submitDirective(){
  const text=document.getElementById('DIR_TEXT').value.trim();if(!text){alert('Directive text required');return;}
  const target=document.getElementById('DIR_TARGET').value;
  const ctx=document.getElementById('DIR_CTX').value.trim();
  const ag=AGENTS.find(a=>a.id===target);
  const d={id:'D-'+(localDirectives.length+1),text,context:ctx,target_agent:target,
    target_name:ag?ag.name:target,created_at:new Date().toISOString(),status:'delivered'};
  localDirectives.unshift(d);
  closeDirectiveForm();renderDirectiveTrail();
  addNotification('directive_delivered',`Directive to ${d.target_name}`,text.slice(0,60),target);
  fetch('/api/ceo/directive',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},
    body:JSON.stringify({directive:text,context:ctx,target_agent:target})}).catch(()=>{});
  document.getElementById('DIR_TEXT').value='';document.getElementById('DIR_CTX').value='';
}
function renderDirectiveTrail(){
  const el=document.getElementById('DIRECTIVE_TRAIL');if(!el)return;
  if(!localDirectives.length){el.innerHTML='<div style="padding:12px;color:var(--mut);font-size:.78rem;text-align:center">No directives sent yet</div>';return;}
  el.innerHTML=localDirectives.map(d=>`
    <div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid var(--bd)">
      ${mkFaceAv(d.target_agent||'ceo','').outerHTML}
      <div style="flex:1;min-width:0">
        <div style="font-size:.8rem;font-weight:600;color:var(--txs)">${d.text}</div>
        <div style="font-size:.67rem;color:var(--mut);margin-top:2px">${d.target_name||''} ${d.context?'· '+d.context:''}</div>
        <div style="font-size:.62rem;color:var(--mut);margin-top:2px;font-family:'JetBrains Mono',monospace">${new Date(d.created_at).toLocaleTimeString()}</div>
      </div>
      <span class="chip ok" style="align-self:flex-start">${d.status}</span>
    </div>`).join('');
}

// renderBoard is defined below with full sprint filter support
let _sprintFilter=null;
function renderBoard(){
  const spSel=document.getElementById('BF_SPRINT');
  const sid=spSel?spSel.value:'';
  updateSprintBurndown(sid);
  if(spSel&&spSel.options.length<=1)buildSprintSelector();
  const board=document.getElementById('BOARD');if(!board)return;board.innerHTML='';
  const fpEl=document.getElementById('BF_PROJ');
  const fsEl=document.getElementById('BF_SPEC');
  const fp=fpEl?fpEl.value:''; const fs=fsEl?fsEl.value:'';
  let tasks=TASKS.filter(t=>{
    if(fp&&t.project_id!==fp)return false;
    if(fs&&t.specialist!==fs)return false;
    if(sid&&t.sprint_id!==sid)return false;
    return true;
  });
  const bcEl=document.getElementById('BOARD_COUNT');
  if(bcEl)bcEl.textContent=tasks.length+' tasks';
  [{key:'backlog',l:'Backlog',c:'bl'},{key:'ready',l:'Ready',c:'rd'},
   {key:'in_progress',l:'In Progress',c:'ip'},{key:'validation',l:'Validation',c:'vl'},
   {key:'done',l:'Done',c:'dn'}].forEach(col=>{
    const colTasks=tasks.filter(t=>t.status===col.key);
    const kol=mk('div','kol');
    const kh=mk('div','kh '+col.c);
    const ptsBadge=colTasks.reduce((s,t)=>(t.story_points||0)+s,0);
    kh.innerHTML=`${col.l}<span class="chip">${colTasks.length}${ptsBadge?' · '+ptsBadge+'p':''}</span>`;
    kol.appendChild(kh);
    const body=mk('div','kbody');
    if(!colTasks.length){
      const empty=mk('div','k-empty');
      const msgs={backlog:'No backlog items',ready:'Nothing ready',in_progress:'No work in progress',validation:'Nothing in validation',done:'No completed tasks'};
      empty.textContent=msgs[col.key]||'Empty';body.appendChild(empty);
    } else {
      colTasks.forEach(t=>{
        const card=mk('div','tc');card.style.borderLeftColor=HUE[t.specialist]||'#14b8a6';
        const nextState=LIFECYCLE[t.status];
        const badges=(t.blocked?'<span class="chip dn">blocked</span>':'')+(t.routing_mismatch?'<span class="chip wn">mismatch</span>':'');
        const fixBtn=t.routing_mismatch&&t.recommended_owner?`<button class="fix-rt" onclick="event.stopPropagation();fixRouting('${t.id}','${t.recommended_owner}')">Fix routing</button>`:'';
        const tc_sprint=t.sprint_id?(SPRINTS.find(s=>s.id===t.sprint_id)||{}).name||'':'';
        const depWarn=(t.depends_on||[]).length?`<div style="font-size:.62rem;color:var(--mut)">⛓ ${t.depends_on.join(', ')}</div>`:'';
        card.innerHTML=`
          <div class="tc-id"><span>${t.id}</span>${badges}${fixBtn}${t.story_points?`<span class="chip ac" style="font-size:.58rem;font-family:'JetBrains Mono',monospace;padding:1px 5px">${t.story_points}p</span>`:''}</div>
          <div class="tc-t">${t.title}</div>
          ${t.blocked&&t.labels&&t.labels.length?`<div class="tc-blk">⛔ ${t.labels.slice(0,2).join(', ')}</div>`:''}
          ${depWarn}
          <div class="tc-m"><span>${t.owner_name}</span><span>${t.progress}%</span></div>
          ${t.progress>0?`<div class="pb"><div class="pbf" style="width:${t.progress}%;background:${HUE[t.specialist]}"></div></div>`:''}
          ${nextState?`<button class="tc-adv" onclick="event.stopPropagation();advanceTask('${t.id}','${nextState}')">→ ${nextState.replace(/_/g,' ')}</button>`:''}`;
        card.onclick=()=>openTask(t);
        body.appendChild(card);
      });
    }
    kol.appendChild(body);board.appendChild(kol);
  });
}

