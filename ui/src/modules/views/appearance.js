// ── Appearance ────────────────────────────────────────────────────────────
function buildAppearance(){
  const gr=document.getElementById('PR_GRID');
  Object.entries(PRESETS).forEach(([key,p])=>{
    const card=mk('div','pr-card'+(key===activePreset?' on':''));
    card.innerHTML=`<div class="pr-sw" style="background:linear-gradient(135deg,${p.a},${p.a2})"></div><div class="pr-nm">${p.n}</div>`;
    card.onclick=()=>{activePreset=key;document.querySelectorAll('.pr-card').forEach(c=>c.classList.remove('on'));card.classList.add('on');updatePreviewStrip(p);};
    gr.appendChild(card);
  });
  updatePreviewStrip(PRESETS.ceo);
  refreshCEODisplay();
  buildPickers();
}
function updatePreviewStrip(p){
  const el=document.getElementById('PVS');
  el.innerHTML=`<div class="pvsw" style="background:${p.a};color:#080b11">Primary</div><div class="pvsw" style="background:${p.a2};color:#080b11">Secondary</div><div class="pvsw" style="background:var(--card);border:1px solid var(--bd);color:var(--tx)">Panel</div>`;
}
function applyTheme(){
  const p=activePreset==='custom'?{a:document.getElementById('ACC1').value,a2:document.getElementById('ACC2').value}:PRESETS[activePreset];
  document.documentElement.style.setProperty('--ac',p.a);
  document.documentElement.style.setProperty('--ach',p.a);
  document.documentElement.style.setProperty('--ac2',p.a2);
}
function resetTheme(){
  activePreset='ceo';
  ['--ac','--ach'].forEach(v=>document.documentElement.style.setProperty(v,'#5ee8d2'));
  document.documentElement.style.setProperty('--ac2','#6ba3ff');
  document.querySelectorAll('.pr-card').forEach((c,i)=>c.classList.toggle('on',i===0));
  updatePreviewStrip(PRESETS.ceo);
}
function refreshCEODisplay(){
  const ptEl=document.getElementById('CEO_PT');if(ptEl)ptEl.src=ceoPhoto||PT[ceoPortrait]||PT['ceo'];
  const spEl=document.getElementById('CEO_SP');
  if(spEl){
    if(ceoPhoto){spEl.style.backgroundImage='url('+ceoPhoto+')';spEl.style.backgroundSize='cover';spEl.style.backgroundPosition='center top';}
    else{spEl.style.backgroundImage='url('+(SPR[ceoSprite]||SPR['ceo'])+')';spEl.style.backgroundSize='500% auto';spEl.style.backgroundPosition='0% top';}
  }
}
function buildPickers(){
  const pp=document.getElementById('PT_PICKER');pp.innerHTML='';
  IDS.forEach(id=>{
    const img=mk('img','pt-thumb'+(id===ceoPortrait?' on':''));
    img.src=PT[id]||'';img.alt=id;img.title=id;
    img.onclick=()=>{ceoPortrait=id;ceoPhoto=null;refreshCEODisplay();updatePickers();};
    pp.appendChild(img);
  });
  const sp=document.getElementById('SP_PICKER');sp.innerHTML='';
  IDS.forEach(id=>{
    const div=mk('div','sp-thumb'+(id===ceoSprite?' on':''));
    div.setAttribute('data-id',id);div.title=id;div.style.backgroundImage='url('+(SPR[id]||'')+')';
    div.onclick=()=>{ceoSprite=id;refreshCEODisplay();updatePickers();updateOfficeAgentSprite('ceo');};
    sp.appendChild(div);
  });
}
function updatePickers(){
  document.querySelectorAll('#PT_PICKER img').forEach(img=>img.className='pt-thumb'+(img.alt===ceoPortrait?' on':''));
  document.querySelectorAll('#SP_PICKER .sp-thumb').forEach(div=>div.className='sp-thumb'+(div.dataset.id===ceoSprite?' on':''));
  document.querySelectorAll('.org-ceo img').forEach(img=>img.src=ceoPhoto||PT[ceoPortrait]||PT['ceo']);
  buildRoster();
}
function uploadPT(e){
  const f=e.target.files[0];if(!f)return;
  const r=new FileReader();
  r.onload=ev=>{ceoPhoto=ev.target.result;refreshCEODisplay();updatePickers();updateOfficeAgentSprite('ceo');};
  r.readAsDataURL(f);
}
function saveCEO(){alert(`Profile saved: ${document.getElementById('CEO_NAME').value} · ${document.getElementById('CEO_ROLE').value}`);}

