// ── Access matrix ─────────────────────────────────────────────────────────
function buildAccess(){
  const tbl=document.getElementById('ACC_TBL');
  const projs=['CEO Console','Market Radar','Atlas Core'];
  const mx={CEO:['rw','rw','rw'],Orion:['rw','rw','rw'],Codex:['rw','none','rw'],Violet:['none','rw','none'],Scout:['none','rw','none'],Charlie:['rw','none','rw'],Ralph:['rw','none','rw'],Shield:['none','none','rw'],Quill:['rw','rw','none'],Pixel:['rw','none','none'],Echo:['none','rw','none'],Iris:['ro','none','none'],Ledger:['none','none','ro'],Mercury:['none','ro','none']};
  // Override with real AM data
  Object.keys(mx).forEach(agCap=>{
    const aid=agCap.toLowerCase();
    projs.forEach((pname,pi)=>{
      if(AM[pname]&&AM[pname][aid])mx[agCap][pi]=AM[pname][aid]==='none'?'none':AM[pname][aid];
    });
  });
  tbl.innerHTML=`<thead><tr><th>Agent</th>${projs.map(p=>`<th>${p}</th>`).join('')}</tr></thead>`;
  const tb=mk('tbody','');
  Object.entries(mx).forEach(([ag,ac])=>{
    const aid=ag.toLowerCase();
    const tr=mk('tr','');
    const imgEl=PT[aid]?`<img src="${PT[aid]}" class="card-portrait sm" style="width:28px;height:28px">`:'' ;
    tr.innerHTML=`<td style="display:flex;align-items:center;gap:7px">${imgEl}${ag}</td>`+ac.map(a=>`<td class="${a==='none'?'no':a}">${a==='none'?'—':a}</td>`).join('');
    tb.appendChild(tr);
  });
  tbl.appendChild(tb);
}

