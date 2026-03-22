// ── Office ─────────────────────────────────────────────────────────────────
function buildOffice(){
  document.getElementById('OFF_MAP').src=DAY_MAP;
  const spr=document.getElementById('OFF_SPR');spr.innerHTML='';
  const SX=640/1400,SY=384/840;
  const allA=[{id:'ceo',name:'You',status:'working',hue:'planning'},...AGENTS];
  allA.forEach(a=>{
    const pos=POSITIONS[a.id];if(!pos)return;
    const wrap=mk('div','off-agent');
    wrap.style.left=(pos.x*SX/640*100).toFixed(2)+'%';
    wrap.style.top=(pos.y*SY/384*100).toFixed(2)+'%';
    wrap.setAttribute('data-id',a.id);
    wrap.title=`${a.name} · ${(pos.zone||'').replace(/_/g,' ')} · ${a.status||'working'}`;
    wrap.onclick=()=>{const ag=AGENTS.find(x=>x.id===a.id);alert(`${a.name}\n${ag?ag.role:'CEO'}\nZone: ${(pos.zone||'').replace(/_/g,' ')}\nStatus: ${a.status||'working'}\nTask: ${ag?ag.task:'Management'}`);};
    const spDiv=mk('div','off-sp');
    const pose={working:'seated',blocked:'talking',validating:'talking',idle:'idle'}[a.status||'idle']||'idle';
    spDiv.classList.add(pose);
    const spId=agentSprites[a.id]||(a.id==='ceo'?ceoSprite:a.id);
    if(a.id==='ceo'&&ceoPhoto){spDiv.style.backgroundImage='url('+ceoPhoto+')';spDiv.style.backgroundSize='cover';spDiv.style.backgroundPosition='center top';}
    else spDiv.style.backgroundImage='url('+(SPR[spId]||SPR[a.id]||SPR['ceo'])+')';
    const dot=mk('div','off-dot '+{working:'spw',blocked:'spb',validating:'spv',idle:'spi'}[a.status||'idle']);
    const nm=txt('div','off-name',a.name);
    wrap.appendChild(spDiv);wrap.appendChild(dot);wrap.appendChild(nm);
    spr.appendChild(wrap);
  });
  const scrum=document.getElementById('SCRUM');scrum.innerHTML='';
  [{id:'violet',t:'8AM briefing (T-206)'},{id:'charlie',t:'Blocked — deploy secret (T-209)'},{id:'orion',t:'Routing morning ops'},{id:'codex',t:'Board filters (T-203)'},{id:'ralph',t:'Validation sweep (T-201)'},{id:'pixel',t:'Office polish (T-204)'}].forEach(s=>{
    const item=mk('div','scrum-item');
    item.appendChild(mkFaceAv(s.id,''));
    item.appendChild(txt('span','',AGENTS.find(a=>a.id===s.id)?.name+': '+s.t));
    scrum.appendChild(item);
  });
}
function setScene(s){
  document.getElementById('OFF_MAP').src=s==='day'?DAY_MAP:NIGHT_MAP;
  document.getElementById('SCN_DAY').classList.toggle('on',s==='day');
  document.getElementById('SCN_NIGHT').classList.toggle('on',s==='night');
}
function updateOfficeAgentSprite(agentId){
  const spDiv=document.querySelector(`.off-agent[data-id="${agentId}"] .off-sp`);
  if(!spDiv)return;
  const spId=agentId==='ceo'?ceoSprite:(agentSprites[agentId]||agentId);
  if(agentId==='ceo'&&ceoPhoto){spDiv.style.backgroundImage='url('+ceoPhoto+')';spDiv.style.backgroundSize='cover';}
  else{spDiv.style.backgroundImage='url('+(SPR[spId]||SPR[agentId]||'')+')';spDiv.style.backgroundSize='500% auto';}
}

