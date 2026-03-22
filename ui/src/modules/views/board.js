// ── Board ─────────────────────────────────────────────────────────────────
const LIFECYCLE={backlog:'ready',ready:'in_progress',in_progress:'validation',validation:'done',done:null};
// renderBoard defined in sprint section below

function advanceTask(id,nextStatus){
  const t=TASKS.find(t=>t.id===id);if(!t)return;
  t.status=nextStatus;
  if(nextStatus==='in_progress')t.progress=Math.max(t.progress||0,10);
  if(nextStatus==='validation')t.progress=80;
  if(nextStatus==='done')t.progress=100;
  renderBoard();
}
function fixRouting(id,recommended){
  const t=TASKS.find(t=>t.id===id);if(!t)return;
  const ag=AGENTS.find(a=>a.id===recommended);
  t.owner=recommended;t.owner_name=ag?ag.name:recommended;t.routing_mismatch=false;
  renderBoard();
}

// ── Sprint management ──────────────────────────────────────────────────────
function openSprintForm(){
  const f=document.getElementById('SPRINT_FORM');if(!f)return;
  f.classList.add('open');f.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function closeSprintForm(){const f=document.getElementById('SPRINT_FORM');if(f)f.classList.remove('open');}
function submitSprintForm(){
  const name=document.getElementById('SF_NAME').value.trim();if(!name){alert('Sprint name required');return;}
  const proj=document.getElementById('SF_PROJ').value;
  const start=document.getElementById('SF_START').value;
  const end  =document.getElementById('SF_END').value;
  const goal =document.getElementById('SF_GOAL').value.trim();
  const id   ='SPR-'+(SPRINTS.length+101);
  SPRINTS.unshift({id,name,project_id:proj,goal,start_date:start,end_date:end,status:'planning',velocity:0,_burndown:{total:0,done:0,remaining:0,pct:0}});
  closeSprintForm();buildSprintSelector();
  fetch('/api/sprints/create',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},
    body:JSON.stringify({name,project_id:proj,goal,start_date:start,end_date:end})}).catch(()=>{});
}
function buildSprintSelector(){
  const sel=document.getElementById('BF_SPRINT');if(!sel)return;
  const cur=sel.value;
  // Clear all except "All tasks"
  while(sel.options.length>1)sel.remove(1);
  SPRINTS.forEach(s=>{const o=document.createElement('option');o.value=s.id;o.textContent=`${s.name} (${s.status})`;sel.appendChild(o);});
  if(cur)sel.value=cur;
}
function updateSprintBurndown(sprintId){
  const bd=document.getElementById('SPRINT_BURNDOWN');
  if(!sprintId||!bd){if(bd)bd.style.display='none';return;}
  const sp=SPRINTS.find(s=>s.id===sprintId);if(!sp){bd.style.display='none';return;}
  const spTasks=TASKS.filter(t=>t.sprint_id===sprintId);
  const total=spTasks.reduce((sum,t)=>(t.story_points||1)+sum,0);
  const done=spTasks.filter(t=>t.status==='done').reduce((sum,t)=>(t.story_points||1)+sum,0);
  const pct=total?Math.round(done/total*100):0;
  document.getElementById('SB_LABEL').textContent=sp.goal||sp.name;
  document.getElementById('SB_PTS').textContent=`${done}/${total} pts · ${pct}%`;
  document.getElementById('SB_BAR').style.width=pct+'%';
  bd.style.display='flex';
}

