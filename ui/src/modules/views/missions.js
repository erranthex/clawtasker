// ── Mission planner ────────────────────────────────────────────────────────
let missionsLocal=[...MISSIONS_DATA];

function buildMissions(){
  const el=document.getElementById('MISSIONS_LIST');el.innerHTML='';
  // Populate owner dropdown in form
  const ownerSel=document.getElementById('MF_OWN');
  if(ownerSel&&ownerSel.options.length===1){
    AGENTS.forEach(a=>{const o=document.createElement('option');o.value=a.id;o.textContent=a.name;ownerSel.appendChild(o);});
  }
  missionsLocal.forEach(m=>el.appendChild(mkMissionCard(m)));
}

function mkMissionCard(m){
  const card=mk('div','mc '+(m.status||'active'));
  const staffing=m.staffing||{coverage_percent:0,gaps:[]};
  const prog=m.progress_percent||0;
  const progColor=m.status==='blocked'?'var(--dn)':prog>=80?'var(--ok)':'var(--ac)';
  const sevColor={critical:'var(--dn)',high:'var(--wn)',medium:'var(--wn)',low:'var(--mut)'};

  // Head
  const head=mk('div','mc-head');
  const title=txt('div','mc-t',m.title);
  const headR=mk('div','mc-head-r');
  const editBtn=txt('button','mc-edit','Edit');editBtn.onclick=()=>openMissionForm(m);const delBtn=txt('button','fix-rt','\u00d7');delBtn.style.cssText='font-size:.65rem;padding:3px 8px';delBtn.onclick=(e)=>{e.stopPropagation();deleteMission(m.id);};
  const statusChip=mk('span','chip '+(m.status==='blocked'?'dn':m.status==='active'?'ok':'in'));
  statusChip.textContent=m.status;
  headR.appendChild(editBtn);headR.appendChild(delBtn);headR.appendChild(statusChip);
  head.appendChild(title);head.appendChild(headR);card.appendChild(head);

  // Objective
  const obj=txt('div','mc-obj',m.objective);card.appendChild(obj);

  // Meta
  const meta=mk('div','mc-meta');
  [{t:`${m.priority}`,c:'chip'},{t:m.horizon,c:'chip'},{t:`${m.owner_name||m.owner||'—'}`,c:'chip in'}].forEach(({t,c})=>{const s=mk('span',c);s.textContent=t;meta.appendChild(s);});
  card.appendChild(meta);

  // Staffing coverage
  const stRow=mk('div','mc-staffing');
  const covPct=staffing.coverage_percent;
  const covColor=covPct>=80?'var(--ok)':covPct>=50?'var(--wn)':'var(--dn)';
  stRow.innerHTML=`<span style="color:${covColor};font-weight:700">${covPct}% staffed</span>`;
  if(staffing.gaps&&staffing.gaps.length)stRow.innerHTML+=`<span style="color:var(--dn);font-size:.68rem">⚠ gaps: ${staffing.gaps.join(', ')}</span>`;
  (m.assigned_agents||[]).forEach(aid=>{
    const ag=AGENTS.find(a=>a.id===aid);
    if(ag){const av=mkFaceAv(aid,'sm');av.title=ag.name;stRow.appendChild(av);}
  });
  card.appendChild(stRow);

  // Progress bar
  const progRow=mk('div','mc-prog-row');
  const progBar=mk('div','mc-prog-bar');
  const progFill=mk('div','mc-prog-fill');
  progFill.style.width=prog+'%';progFill.style.background=progColor;
  progBar.appendChild(progFill);
  progRow.innerHTML=`<span>${prog}%</span>`;progRow.appendChild(progBar);
  progRow.innerHTML+=`<span>${m.open_task_count||0}/${m.task_count||0} open tasks</span>`;
  card.appendChild(progRow);

  // Linked task chips
  if(m.task_ids&&m.task_ids.length){
    const chips=mk('div','mc-task-chips');
    m.task_ids.forEach(tid=>{
      const chip=txt('div','mc-task-chip',tid);
      chip.onclick=()=>{const t=TASKS.find(t=>t.id===tid);if(t)openTask(t);};
      chips.appendChild(chip);
    });
    card.appendChild(chips);
  }

  // Risks
  if(m.risks&&m.risks.length){
    const sec=mk('div','mc-section');
    sec.appendChild(txt('div','mc-section-title','Risks'));
    m.risks.slice(0,3).forEach(r=>{
      const row=mk('div','mc-risk');
      const sev=mk('span','chip '+(r.severity==='critical'||r.severity==='high'?'dn':'wn'));
      sev.textContent=r.severity||'risk';
      row.innerHTML=`<span class="mc-risk-title">${r.title}</span>`;
      row.prepend(sev);
      card.appendChild(row);
    });
    card.appendChild(sec);
  }

  // Dependencies
  if(m.dependencies&&m.dependencies.length){
    const sec=mk('div','mc-section');
    sec.appendChild(txt('div','mc-section-title','Dependencies'));
    m.dependencies.slice(0,3).forEach(d=>{
      const row=mk('div','mc-dep');
      const dot=mk('div','mc-dep-status');
      dot.style.background=d.status==='blocked'?'var(--dn)':d.status==='done'?'var(--ok)':'var(--wn)';
      row.appendChild(dot);row.appendChild(txt('span','',d.title));
      const statusLbl=txt('span','chip '+(d.status==='blocked'?'dn':d.status==='done'?'ok':'wn'),d.status||'pending');
      row.appendChild(statusLbl);sec.appendChild(row);
    });
    card.appendChild(sec);
  }

  // Next actions / success criteria (expandable)
  const hasExtra=(m.next_actions&&m.next_actions.length)||(m.success_criteria&&m.success_criteria.length);
  if(hasExtra){
    const expandBtn=mk('button','mc-expand-btn');
    const expandId='mc-exp-'+m.id;
    expandBtn.innerHTML='▶ Next actions &amp; success criteria';
    expandBtn.onclick=()=>{
      const exp=document.getElementById(expandId);
      const open=exp.classList.toggle('open');
      expandBtn.innerHTML=(open?'▼':'▶')+' Next actions &amp; success criteria';
    };
    const expandable=mk('div','mc-expandable');expandable.id=expandId;
    if(m.next_actions&&m.next_actions.length){
      expandable.appendChild(txt('div','mc-section-title','Next actions'));
      m.next_actions.forEach(a=>{
        const row=mk('div','mc-action-item');
        row.appendChild(mk('div','mc-ac-dot'));row.appendChild(txt('span','',a));
        expandable.appendChild(row);
      });
    }
    if(m.success_criteria&&m.success_criteria.length){
      expandable.appendChild(txt('div','mc-section-title','Success criteria'));
      m.success_criteria.forEach(s=>{
        const row=mk('div','mc-action-item');
        row.appendChild(mk('div','mc-ac-dot'));row.appendChild(txt('span','',s));
        expandable.appendChild(row);
      });
    }
    card.appendChild(expandBtn);card.appendChild(expandable);
  }
  return card;
}

function openMissionForm(mission){
  editingMissionId=mission?mission.id:null;
  document.getElementById('MF_TITLE').textContent=mission?'Edit mission':'New mission';
  document.getElementById('MF_TITLE_IN').value=mission?mission.title:'';
  document.getElementById('MF_OBJ').value=mission?mission.objective:'';
  document.getElementById('MF_PRI').value=mission?mission.priority:'P1';
  if(document.getElementById('MF_STATUS'))document.getElementById('MF_STATUS').value=mission?mission.status||'active':'active';
  document.getElementById('MF_HOR').value=mission?mission.horizon:'Today';
  document.getElementById('MF_OWN').value=mission?mission.owner:'';
  document.getElementById('MF_PROJ').value=mission?(mission.project_ids||[])[0]||'':'';
  document.getElementById('MF_ACT').value=mission?(mission.next_actions||[]).join('\n'):'';
  if(document.getElementById('MF_SC'))document.getElementById('MF_SC').value=mission?(mission.success_criteria||[]).join('\n'):'';
  const form=document.getElementById('MISS_FORM');
  form.classList.add('open');form.scrollIntoView({behavior:'smooth',block:'nearest'});
  // Switch to missions view if not there
  if(!document.getElementById('V_miss').classList.contains('on')){
    goV('miss',document.getElementById('NV_MISS'));
  }
}
function closeMissionForm(){document.getElementById('MISS_FORM').classList.remove('open');editingMissionId=null;}
function submitMissionForm(){
  const title=document.getElementById('MF_TITLE_IN').value.trim();
  const obj=document.getElementById('MF_OBJ').value.trim();
  if(!title||!obj){alert('Title and objective are required.');return;}
  const actions=document.getElementById('MF_ACT').value.split('\n').map(s=>s.trim()).filter(Boolean);
  const sc=(document.getElementById('MF_SC')?.value||'').split('\n').map(s=>s.trim()).filter(Boolean);
  const projId=document.getElementById('MF_PROJ').value;
  const ownerId=document.getElementById('MF_OWN').value;
  const ownerAg=AGENTS.find(a=>a.id===ownerId);
  const mStatus=document.getElementById('MF_STATUS')?.value||'active';
  const newMission={
    id:editingMissionId||('M-'+Date.now()),
    title,objective:obj,
    status:mStatus,priority:document.getElementById('MF_PRI').value,
    horizon:document.getElementById('MF_HOR').value,
    owner:ownerId,owner_name:ownerAg?ownerAg.name:ownerId,
    project_ids:projId?[projId]:[],
    task_ids:[],assigned_agents:ownerId?[ownerId]:[],required_specialists:[],
    next_actions:actions,success_criteria:sc,risks:[],dependencies:[],
    progress_percent:0,task_count:0,open_task_count:0,blocked_task_count:0,
    staffing:{coverage_percent:100,gaps:[]},health_label:'active',
  };
  if(editingMissionId){
    const idx=missionsLocal.findIndex(m=>m.id===editingMissionId);
    if(idx>=0)missionsLocal[idx]={...missionsLocal[idx],...newMission};
  } else {
    missionsLocal.unshift(newMission);
    const nvMiss=document.getElementById('NV_MISS');
    const badge=mk('span','');badge.style.cssText='width:8px;height:8px;border-radius:50%;background:var(--ac);animation:pu 2s infinite;display:inline-block;margin-left:6px';
    nvMiss.appendChild(badge);setTimeout(()=>badge.remove(),10000);
  }
  // Persist via API
  const missionPayload={
    agent_id:ownerId,title:newMission.title,objective:newMission.objective,
    status:newMission.status,priority:newMission.priority,horizon:newMission.horizon,
    project_ids:newMission.project_ids,next_actions:newMission.next_actions,
    success_criteria:newMission.success_criteria,assigned_agents:newMission.assigned_agents,
  };
  if(editingMissionId)missionPayload.mission_id=editingMissionId;
  apiPost('/api/missions/plan',missionPayload).then(res=>{
    if(res&&res.mission&&!editingMissionId){
      // Replace optimistic entry with server ID
      const idx=missionsLocal.findIndex(m=>m.id===newMission.id);
      if(idx>=0)missionsLocal[idx]={...missionsLocal[idx],...res.mission};
      buildMissions();
    }
  }).catch(()=>{});
  closeMissionForm();buildMissions();
}

