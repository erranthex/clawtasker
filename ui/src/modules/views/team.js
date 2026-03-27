// ── Org chart ──────────────────────────────────────────────────────────────
function buildOrg(){
  const el=document.getElementById('ORG');el.innerHTML='';
  // CEO row
  const cl=mk('div','org-ceo');
  cl.appendChild(mkOrgCard({id:'ceo',name:'You',role:'CEO / Human operator',hue:'planning',skills:['priorities','approvals','exceptions']},true));
  el.appendChild(cl);
  // Chief row
  const chief=AGENTS.find(a=>a.org_level==='chief')||AGENTS.find(a=>a.id==='orion')||AGENTS[0];
  if(chief&&chief.status!=='offline'){
    const ch=mk('div','org-chief');ch.appendChild(mkOrgCard(chief,true));el.appendChild(ch);
  }
  const ln=mk('div','org-hline');el.appendChild(ln);
  // Manager lanes (active only)
  const mgrs=AGENTS.filter(a=>a.org_level==='manager'&&a.status!=='offline');
  if(mgrs.length){
    const gr=mk('div','org-grid');
    mgrs.forEach(mgr=>{
      const rpts=AGENTS.filter(a=>a.mgr===mgr.name&&a.status!=='offline');
      gr.appendChild(mkOrgCard(mgr,false,rpts));
    });
    el.appendChild(gr);
  }
  // Offline / decommissioned agents pool
  const offline=AGENTS.filter(a=>a.status==='offline'||a.derived_status==='offline');
  if(offline.length){
    const pool=mk('div','');
    pool.style.cssText='margin-top:14px;padding-top:12px;border-top:1px dashed var(--bd)';
    const lbl=mk('div','ey');lbl.textContent='Offline / Decommissioned';lbl.style.marginBottom='8px';
    pool.appendChild(lbl);
    const row=mk('div','');row.style.cssText='display:flex;flex-wrap:wrap;gap:8px';
    offline.forEach(ag=>{
      const card=mk('div','');
      card.style.cssText='display:flex;align-items:center;gap:8px;padding:8px 12px;'+
        'background:var(--bg3);border:1px solid var(--bd);border-radius:var(--rmd);opacity:.5;position:relative';
      card.appendChild(mkPortrait(ag.id,'sm'));
      const info=mk('div','');
      info.innerHTML=`<div style="font-size:.78rem;font-weight:600;color:var(--mut)">${ag.name}</div>`+
        `<div style="font-size:.65rem;color:var(--mut)">${ag.role}</div>`+
        `<span class="chip" style="font-size:.6rem;background:var(--dns);color:var(--dn);border-color:rgba(255,77,106,.3)">offline</span>`;
      card.appendChild(info);
      // Permanent delete button
      const del=mk('button','');del.textContent='✕ Remove';
      del.style.cssText='position:absolute;top:4px;right:6px;font-size:.6rem;color:var(--dn);'+
        'background:transparent;border:none;cursor:pointer;padding:2px 6px;'+
        'border-radius:4px;transition:background .12s';
      del.onmouseenter=()=>del.style.background='var(--dns)';
      del.onmouseleave=()=>del.style.background='transparent';
      del.onclick=()=>{
        if(!confirm('Permanently remove '+ag.name+' from the roster? This cannot be undone.'))return;
        apiPost('/api/agents/delete',{agent_id:ag.id}).then(()=>{
          const idx=AGENTS.findIndex(a=>a.id===ag.id);
          if(idx>=0)AGENTS.splice(idx,1);
          buildOrg();buildRoster();
        }).catch(err=>alert('Delete failed: '+(err.message||err)));
      };
      card.appendChild(del);
      row.appendChild(card);
    });
    pool.appendChild(row);
    el.appendChild(pool);
  }
}
function mkOrgCard(agent,big,rpts){
  const c=mk('div','org-card'+(big?' big':''));
  c.style.borderTopColor=HUE[agent.hue]||'#14b8a6';
  c.appendChild(mkPortrait(agent.id,big?'lg':''));
  const nameEl=txt('div','org-name',agent.name);
  nameEl.style.cursor='pointer';nameEl.title='Click to edit';
  nameEl.onclick=()=>openOrgEdit(agent,'name',nameEl);
  c.appendChild(nameEl);
  const roleEl=txt('div','org-role',agent.role);
  roleEl.style.cursor='pointer';roleEl.title='Click to edit role';
  roleEl.onclick=()=>openOrgEdit(agent,'role',roleEl);
  c.appendChild(roleEl);
  if(agent.skills){const sk=mk('div','org-sk');agent.skills.slice(0,3).forEach(s=>{const ch=mk('span','chip');ch.textContent=s;sk.appendChild(ch);});c.appendChild(sk);}
  if(rpts&&rpts.length){const rw=mk('div','org-reps');rpts.forEach(r=>{rw.appendChild(mkPortrait(r.id,'sm'));});c.appendChild(rw);}
  if(agent.id&&agent.id!=='ceo'){
    const ctrl=mk('div','');ctrl.style.cssText='display:flex;gap:4px;margin-top:6px;justify-content:center';
    const editBtn=txt('button','mc-edit','Edit');editBtn.onclick=e=>{e.stopPropagation();openFullOrgEdit(agent);};
    const dcBtn=txt('button','fix-rt','Decommission');dcBtn.style.fontSize='.55rem';
    dcBtn.onclick=e=>{e.stopPropagation();confirmDecommission(agent);};
    ctrl.appendChild(editBtn);ctrl.appendChild(dcBtn);c.appendChild(ctrl);
  }
  return c;
}

// ── Agent roster ──────────────────────────────────────────────────────────
function buildRoster(){
  const gr=document.getElementById('AG_GRID');gr.innerHTML='';
  AGENTS.forEach(a=>{
    const card=mk('div','ag-card');card.style.borderLeftColor=HUE[a.hue]||'#14b8a6';
    const faceAv=mkFaceAv(a.id,'lg');
    faceAv.style.cursor='pointer';faceAv.title='Click to set as CEO portrait';
    faceAv.onclick=()=>{ceoPortrait=a.id;ceoPhoto=null;refreshCEODisplay();updatePickers();};
    card.appendChild(faceAv);
    const info=mk('div','ag-info');
    const st=a.derived_status||a.status;
    const sc={working:'bw',blocked:'bb',validation:'bv',validating:'bv',idle:'bi'}[st]||'bi';
    const wl_active=a.workload_active||0;
    const wl_pts=a.workload_points||0;
    const overloaded=a.overloaded||false;
    const wl_bar_pct=Math.min(100,wl_active/5*100);
    const wl_color=overloaded?'var(--dn)':wl_active>=3?'var(--wn)':'var(--ok)';
    // Check if agent heartbeat is stale (>10 min in demo, would be configurable)
    const hbAge=a.last_heartbeat?Math.floor((Date.now()-new Date(a.last_heartbeat))/1000):99999;
    const isStale=hbAge>600; // 10 minutes = likely disconnected
    const isMissing=st==='offline'||isStale;
    info.innerHTML=`<div class="ag-name">${a.name}${isMissing?' <span style="color:var(--dn);font-size:.6rem;font-weight:700;letter-spacing:.04em">⚠ MISSING</span>':''}</div><div class="ag-role">${a.role}</div><div class="badge ${sc}">${st}</div><div class="ag-task">${a.task}</div>
      <div style="margin-top:5px">
        <div style="display:flex;justify-content:space-between;font-size:.6rem;color:var(--mut);margin-bottom:2px">
          <span>Workload</span><span style="color:${wl_color};font-weight:700">${wl_active} active · ${wl_pts}pts${overloaded?' ⚠ OVERLOADED':''}</span>
        </div>
        <div style="height:4px;background:var(--bds);border-radius:2px;overflow:hidden">
          <div style="height:100%;width:${wl_bar_pct}%;background:${wl_color};border-radius:2px;transition:width .4s"></div>
        </div>
      </div>
      <div class="ag-hb">⏱ ${relTime(a.last_heartbeat)}${isStale?' — <span style="color:var(--wn)">heartbeat stale</span>':''}</div>
      ${isMissing?'<div style="margin-top:5px"><button class="fix-rt" style="font-size:.6rem;padding:3px 8px" onclick="confirmDecommission({id:\''+a.id+'\',name:\''+a.name+'\'})">🗑 Remove agent</button></div>':''}`;
    const spRow=mk('div','');spRow.style.cssText='display:flex;align-items:center;gap:6px;margin-top:6px';
    const spThumb=mkSprite(a.id,'idle','sm');
    spThumb.style.cursor='pointer';spThumb.title='Change sprite';
    spThumb.onclick=()=>openSpriteModal(a.id);
    const spLbl=txt('span','','Change sprite');spLbl.style.cssText='font-size:.62rem;color:var(--mut);cursor:pointer';
    spLbl.onclick=()=>openSpriteModal(a.id);
    spRow.appendChild(spThumb);spRow.appendChild(spLbl);info.appendChild(spRow);
    card.appendChild(info);gr.appendChild(card);
  });
}

// ── Sprite modal ──────────────────────────────────────────────────────────
function openSpriteModal(agentId){
  const agent=AGENTS.find(a=>a.id===agentId);
  const box=document.getElementById('MB');
  const cur=agentSprites[agentId]||agentId;
  box.innerHTML=`
    <div class="mo-head">
      <div>
        <div style="font-size:.63rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin-bottom:4px;font-family:'JetBrains Mono',monospace">Character sprite</div>
        <div class="mo-title">Choose sprite for ${agent?agent.name:agentId}</div>
      </div>
      <button class="mo-close" onclick="closeMo()">×</button>
    </div>
    <div class="mo-body">
      <p style="font-size:.8rem;color:var(--mut);margin-bottom:12px">Select a character. Idle agents face the camera (frame 0). Working agents display seated pose.</p>
      <div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:center" id="SP_MOD_GRID"></div>
    </div>`;
  document.getElementById('MO').style.display='flex';
  const gr=document.getElementById('SP_MOD_GRID');
  IDS.forEach(id=>{
    const wrap=mk('div','');
    wrap.style.cssText=`display:flex;flex-direction:column;align-items:center;gap:5px;cursor:pointer;padding:10px;border-radius:10px;border:2px solid ${id===cur?'var(--ac)':'var(--bd)'};background:var(--bg3);transition:all .12s;min-width:72px`;
    wrap.onmouseenter=()=>{if(id!==cur)wrap.style.borderColor='var(--bds)';};
    wrap.onmouseleave=()=>{if(id!==cur)wrap.style.borderColor='var(--bd)';};
    const idleDiv=mkSprite(id,'idle','');
    const lbl=txt('div','',id);lbl.style.cssText='font-size:.62rem;color:var(--mut)';
    wrap.appendChild(idleDiv);wrap.appendChild(lbl);
    wrap.onclick=()=>{agentSprites[agentId]=id;closeMo();refreshOfficeSprite(agentId);buildRoster();};
    gr.appendChild(wrap);
  });
}

// ── Org config ─────────────────────────────────────────────────────────────
let API_TOKEN='change-me-local';
function openOrgConfig(){
  const f=document.getElementById('ORG_CONFIG');
  if(!f)return;
  const sel=document.getElementById('OC_CHIEF');
  if(sel&&sel.options.length<=1)AGENTS.forEach(a=>{const o=mk('option','');o.value=a.id;o.textContent=a.name;sel.appendChild(o);});
  f.classList.add('open');
}
function closeOrgConfig(){const f=document.getElementById('ORG_CONFIG');if(f)f.classList.remove('open');}
function saveOrgConfig(){
  const ceoName=document.getElementById('OC_CEO_NAME').value.trim();
  const ceoRole=document.getElementById('OC_CEO_ROLE').value.trim();
  const coName=document.getElementById('OC_CO_NAME').value.trim();
  const chief=document.getElementById('OC_CHIEF').value;
  const token=document.getElementById('OC_TOKEN').value.trim();
  if(token)API_TOKEN=token;
  const payload={};
  if(ceoName)payload.ceo_name=ceoName;
  if(ceoRole)payload.ceo_role=ceoRole;
  if(coName)payload.company_name=coName;
  if(chief)payload.chief_agent_id=chief;
  if(!Object.keys(payload).length){closeOrgConfig();return;}
  fetch('/api/org/configure',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},body:JSON.stringify(payload)})
    .then(r=>r.json()).then(d=>{if(d.ok){closeOrgConfig();buildOrg();alert(d.message);}else alert('Error: '+d.error);})
    .catch(()=>{closeOrgConfig();});
}
function openOrgEdit(agent,field,el){
  const cur=el.textContent;
  const inp=mk('input','mf-in');inp.value=cur;inp.style.cssText='width:100%;font-size:.8rem;padding:3px 6px;margin:2px 0';
  el.replaceWith(inp);inp.focus();inp.select();
  const save=()=>{
    const v=inp.value.trim();if(!v){inp.replaceWith(el);return;}
    el.textContent=v;inp.replaceWith(el);
    const ag=AGENTS.find(a=>a.id===agent.id);if(ag)ag[field]=v;
    fetch('/api/agents/register',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},
      body:JSON.stringify({source:'org-edit',agent:{id:agent.id,name:ag?ag.name:agent.name,role:ag?ag.role:agent.role,specialist:ag?ag.hue:'planning',skills:ag?ag.skills||[]:[]}}),
    }).then(r=>r.json()).then(d=>console.log('[OrgEdit]',d.message||d.error)).catch(()=>{});
  };
  inp.onblur=save;inp.onkeydown=e=>{if(e.key==='Enter')save();if(e.key==='Escape')inp.replaceWith(el);};
}
function openFullOrgEdit(agent){
  const ag=AGENTS.find(a=>a.id===agent.id)||agent;
  const box=document.getElementById('MB');
  const agentOpts=AGENTS.map(a=>`<option value="${a.id}"${a.id===ag.manager?' selected':''}>${a.name}</option>`).join('');
  box.innerHTML=`
    <div class="mo-head">
      <div><div style="font-size:.63rem;font-weight:700;text-transform:uppercase;color:var(--mut);margin-bottom:4px;font-family:'JetBrains Mono',monospace">Edit agent</div>
      <div class="mo-title">${ag.name}</div></div>
      <button class="mo-close" onclick="closeMo()">×</button>
    </div>
    <div class="mo-body">
      <div class="mf-grid">
        <div><label class="mf-lbl">Display name</label><input class="mf-in" id="OE_NAME" value="${ag.name}"></div>
        <div><label class="mf-lbl">Role title</label><input class="mf-in" id="OE_ROLE" value="${ag.role}"></div>
        <div><label class="mf-lbl">Reports to</label><select class="mf-in" id="OE_MGR"><option value="ceo">CEO (You)</option>${agentOpts}</select></div>
        <div><label class="mf-lbl">Department</label><input class="mf-in" id="OE_DEPT" value="${ag.department||''}"></div>
        <div style="grid-column:1/-1"><label class="mf-lbl">Skills (comma-separated)</label><input class="mf-in" id="OE_SKILLS" value="${(ag.skills||[]).join(', ')}"></div>
      </div>
      <div class="mf-actions">
        <button class="mf-save" onclick="saveFullOrgEdit('${ag.id}')">Save changes</button>
        <button class="mf-cancel" onclick="closeMo()">Cancel</button>
      </div>
      <div style="margin-top:12px;border-top:1px solid var(--bd);padding-top:10px">
        <button class="fix-rt" style="font-size:.72rem;padding:5px 12px" onclick="confirmDecommission({id:'${ag.id}',name:'${ag.name}'})">⚠ Decommission agent</button>
      </div>
    </div>`;
  document.getElementById('MO').style.display='flex';
}
function saveFullOrgEdit(agentId){
  const name=document.getElementById('OE_NAME').value.trim();
  const role=document.getElementById('OE_ROLE').value.trim();
  const mgr=document.getElementById('OE_MGR').value;
  const dept=document.getElementById('OE_DEPT').value.trim();
  const skills=document.getElementById('OE_SKILLS').value.split(',').map(s=>s.trim()).filter(Boolean);
  if(!name||!role){alert('Name and role required');return;}
  const ag=AGENTS.find(a=>a.id===agentId);
  if(ag){ag.name=name;ag.role=role;ag.manager=mgr;ag.department=dept;ag.skills=skills;}
  fetch('/api/agents/register',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},
    body:JSON.stringify({source:'org-edit',agent:{id:agentId,name,role,manager:mgr,department:dept,skills,specialist:ag?ag.hue:'planning'}}),
  }).then(r=>r.json()).then(d=>{closeMo();buildOrg();buildRoster();}).catch(()=>{closeMo();buildOrg();buildRoster();});
}
function confirmDecommission(agent){
  if(!confirm('Decommission '+agent.name+'?\n\nMarks offline, unassigns tasks. Audit trail preserved.'))return;
  fetch('/api/agents/decommission',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},
    body:JSON.stringify({agent_id:agent.id,reason:'Decommissioned by CEO via org chart'}),
  }).then(r=>r.json()).then(d=>{
    if(d.ok){const ag=AGENTS.find(a=>a.id===agent.id);if(ag){ag.status='offline';ag.derived_status='offline';}
      decommissionOfficeAgent(agent.id);
      closeMo();buildOrg();buildRoster();renderBoard();}
    else alert('Error: '+(d.error||'unknown'));
  }).catch(()=>{const ag=AGENTS.find(a=>a.id===agent.id);if(ag){ag.status='offline';ag.derived_status='offline';}
    decommissionOfficeAgent(agent.id);
    closeMo();buildOrg();buildRoster();});
}


// ── Add agent via GUI — mirrors POST /api/agents/register ──────────────────
function openAddAgentForm(){
  const mo=document.getElementById('MO');mo.style.display='flex';
  const mc=document.getElementById('MC');
  mc.innerHTML=`
    <div class="mo-head"><span class="mo-title">Register new AI agent</span><button class="mo-x" onclick="closeMo()">×</button></div>
    <div style="display:grid;gap:12px;padding:0 0 10px">
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Agent name</label>
        <input id="NA_NAME" class="ai" placeholder="e.g. Atlas, Nova, Sage..." style="width:100%"></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Role / specialty</label>
        <input id="NA_ROLE" class="ai" placeholder="e.g. Frontend engineer, Research analyst, Content writer..." style="width:100%"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Team / manager</label>
          <select id="NA_MGR" class="ai"><option value="">— No manager —</option></select></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Hue (theme color)</label>
          <select id="NA_HUE" class="ai"><option value="planning">Planning (teal)</option><option value="code">Code (blue)</option><option value="research">Research (purple)</option><option value="ops">Ops (orange)</option><option value="qa">QA (green)</option><option value="security">Security (red)</option><option value="design">Design (pink)</option><option value="docs">Docs (cyan)</option></select></div>
      </div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Appearance</label><div style="display:flex;gap:8px;flex-wrap:wrap" id="NA_SPRITES"></div><input type="hidden" id="NA_SPRITE" value="ceo"></div>
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Skills (comma-separated)</label>
        <input id="NA_SKILLS" class="ai" placeholder="e.g. python, writing, analysis, design..." style="width:100%"></div>
      <div style="background:rgba(94,232,210,.06);border:1px solid rgba(94,232,210,.15);border-radius:8px;padding:10px;font-size:.72rem;color:var(--mut)">
        AI agents can self-register via <code>POST /api/agents/register</code> with the same fields.
      </div>
      <button class="sbb p" onclick="submitAddAgent()">Register agent</button>
    </div>`;
  // Populate sprite picker
  const sprDiv=document.getElementById("NA_SPRITES");
  IDS.forEach(id=>{
    if(id==="ceo")return;
    const d=mk("div","");d.style.cssText="cursor:pointer;border:2px solid transparent;border-radius:50%;padding:2px";
    d.onclick=()=>{document.getElementById("NA_SPRITE").value=id;document.querySelectorAll("#NA_SPRITES>div").forEach(x=>x.style.borderColor="transparent");d.style.borderColor="var(--ac)";};
    d.appendChild(mkFaceAv(id,"sm"));
    sprDiv.appendChild(d);
  });
  // Populate manager dropdown
  const sel=document.getElementById('NA_MGR');
  AGENTS.forEach(a=>{
    if(a.id==='ceo')return;
    const o=document.createElement('option');o.value=a.id;o.textContent=a.name+' ('+a.role+')';sel.appendChild(o);
  });
}

function submitAddAgent(){
  const name=document.getElementById('NA_NAME').value.trim();
  if(!name){alert('Agent name is required');return;}
  const role=document.getElementById('NA_ROLE').value.trim()||'Agent';
  const mgr=document.getElementById('NA_MGR').value;
  const hue=document.getElementById('NA_HUE').value;
  const skills=document.getElementById('NA_SKILLS').value.split(',').map(s=>s.trim()).filter(Boolean);
  
  const id=name.toLowerCase().replace(/[^a-z0-9]/g,'');
  
  // Check for duplicate
  if(AGENTS.find(a=>a.id===id)){alert('Agent "'+id+'" already exists');return;}
  
  const agent={
    id, name, role, hue, status:'idle', derived_status:'idle',
    task:'Awaiting first assignment', mgr:mgr||'orion',
    skills, workload_active:0, workload_points:0, overloaded:false,
    last_heartbeat:new Date().toISOString()
  };
  AGENTS.push(agent);
  
  // Also POST to server
  fetch('/api/agents/register',{
    method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+(typeof API_TOKEN!=='undefined'?API_TOKEN:'')},
    body:JSON.stringify({id,name,role,manager:mgr,hue,skills})
  }).catch(()=>{});
  
  closeMo();buildOrg();buildRoster();buildCapabilityMatrix();refreshCounters();
}
