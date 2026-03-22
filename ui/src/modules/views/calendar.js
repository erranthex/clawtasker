// ── Calendar ───────────────────────────────────────────────────────────────
function getISOWeek(d){const j4=new Date(d.getFullYear(),0,4);const s=new Date(j4);s.setDate(j4.getDate()-((j4.getDay()||7)-1));return Math.ceil(((d-s)/86400000+1)/7);}
function weekStart(d){const day=d.getDay();const diff=(day===0?-6:1)-day;const s=new Date(d);s.setDate(d.getDate()+diff);s.setHours(0,0,0,0);return s;}
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
const DAYS=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

function setCalV(v,btn){
  calView=v;
  document.querySelectorAll('.cal-vtab').forEach(b=>b.classList.remove('on'));
  if(btn)btn.classList.add('on');
  document.getElementById('CAL_TITLE').textContent={week:'Week schedule',month:'Month schedule',year:'Year overview'}[v];
  const wt=document.getElementById('CAL_WEEK_TABS');
  const al=document.getElementById('CAL_ALWAYS');
  if(wt)wt.style.display=v==='week'?'flex':'none';
  if(al)al.style.display=v==='week'?'flex':'none';
  renderCal();
}
function calNav(d){
  if(calView==='week')calDate.setDate(calDate.getDate()+d*7);
  else if(calView==='month')calDate.setMonth(calDate.getMonth()+d);
  else calDate.setFullYear(calDate.getFullYear()+d);
  renderCal();
}
function calToday(){calDate=new Date(TODAY);renderCal();}

function renderCal(){
  if(calView==='week')renderWeek();
  else if(calView==='month')renderMonth();
  else renderYear();
}

function renderWeek(){
  const ws=weekStart(calDate);
  const we=new Date(ws);we.setDate(ws.getDate()+6);
  const wn=getISOWeek(ws);
  document.getElementById('CAL_PER').innerHTML=
    `${ws.toLocaleDateString('en-GB',{day:'2-digit',month:'short'})} – ${we.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})}<span class="wbadge">W${wn}</span>`;

  // Day tabs - highlight today
  const tabs=document.getElementById('CAL_WEEK_TABS');tabs.innerHTML='';
  DAYS.forEach((d,i)=>{
    const dd=new Date(ws);dd.setDate(ws.getDate()+i);
    const isT=dd.toDateString()===TODAY.toDateString();
    const b=mk('button','cal-tab'+(d===curDay?' on':'')+(isT?' today-tab':''));
    b.innerHTML=`${d}<br><span style="font-size:.6rem;font-weight:400">${dd.getDate()}</span>`;
    b.style.lineHeight='1.3';
    b.onclick=()=>{curDay=d;renderWeek();};
    tabs.appendChild(b);
  });
  renderWeekPanel();
}

function renderWeekPanel(){
  const el=document.getElementById('CAL_PANEL');el.innerHTML='';
  const allEvents=(CAL[curDay]||[]).sort((a,b)=>a.t.localeCompare(b.t));
  if(!allEvents.length){el.innerHTML='<div style="padding:20px;color:var(--mut);text-align:center">No tasks scheduled</div>';return;}

  // Group by agent for lane separation
  const byAgent={};
  allEvents.forEach(ev=>{
    const agKey=ev.ag||'Team';
    if(!byAgent[agKey])byAgent[agKey]=[];
    byAgent[agKey].push(ev);
  });

  Object.entries(byAgent).forEach(([agName,evts])=>{
    const ag=AGENTS.find(a=>a.name===agName);
    const lane=mk('div','cal-lane');
    // Agent lane header
    const hd=mk('div','cal-lane-hd');
    if(ag){hd.appendChild(mkFaceAv(ag.id,'sm'));}
    hd.appendChild(txt('span','',agName));
    lane.appendChild(hd);
    evts.forEach(ev=>{
      const row=mk('div','cal-row '+(ev.h||''));
      row.setAttribute('title',`${ev.ti} — ${agName} @ ${ev.t}`);
      row.innerHTML=`<div class="cal-tc"><span class="cal-tl">${ev.t}</span><span class="cal-td"></span></div><div class="cal-bc"><div class="cal-et">${ev.ti}</div><div class="cal-ea">${agName}</div></div>`;
      lane.appendChild(row);
    });
    el.appendChild(lane);
  });
}

function renderMonth(){
  const y=calDate.getFullYear(),m=calDate.getMonth();
  document.getElementById('CAL_PER').innerHTML=`${MONTHS[m]} ${y}<span class="wbadge">W${getISOWeek(new Date(y,m,1))}</span>`;
  const el=document.getElementById('CAL_PANEL');el.innerHTML='';
  const taskDates={};TASKS.forEach(t=>{if(t.due_date){if(!taskDates[t.due_date])taskDates[t.due_date]=[];taskDates[t.due_date].push(t);}});
  const fd=new Date(y,m,1),sdow=(fd.getDay()||7)-1;
  const gs=new Date(fd);gs.setDate(1-sdow);
  const grid=mk('div','mgrid');
  const wh=mk('div','mghead');wh.textContent='Wk';grid.appendChild(wh);
  ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].forEach(d=>{const h=mk('div','mghead');h.textContent=d;grid.appendChild(h);});
  let cur=new Date(gs),lastWk=-1;
  while(cur.getMonth()<=m||cur<gs){
    if(cur.getDay()===1||cur.getTime()===gs.getTime()){
      const wn=getISOWeek(cur);
      if(wn!==lastWk){const wc=mk('div','mwnum');wc.textContent='W'+wn;grid.appendChild(wc);lastWk=wn;}
    }
    const cell=mk('div','mday'+(cur.toDateString()===TODAY.toDateString()?' today':'')+(cur.getMonth()!==m?' dim':''));
    const dn=mk('div','mday-n');dn.textContent=cur.getDate();cell.appendChild(dn);
    const dk=`${cur.getFullYear()}-${String(cur.getMonth()+1).padStart(2,'0')}-${String(cur.getDate()).padStart(2,'0')}`;
    (taskDates[dk]||[]).slice(0,2).forEach(t=>{
      const ev=mk('div','mev');ev.style.background=HUE[t.specialist]||'#14b8a6';ev.textContent=t.title;
      ev.title=`${t.title} — ${t.owner_name} @ ${dk}`;
      ev.onclick=e=>{e.stopPropagation();openTask(t);};cell.appendChild(ev);
    });
    if((taskDates[dk]||[]).length>2){const more=txt('div','',`+${taskDates[dk].length-2}`);more.style.cssText='font-size:.58rem;color:var(--mut)';cell.appendChild(more);}
    grid.appendChild(cell);
    cur.setDate(cur.getDate()+1);
    if(cur.getMonth()>m&&cur.getDay()===1)break;
  }
  el.appendChild(grid);
}

function renderYear(){
  const y=calDate.getFullYear();
  document.getElementById('CAL_PER').textContent=y;
  const el=document.getElementById('CAL_PANEL');el.innerHTML='';
  const taskDates={};TASKS.forEach(t=>{if(t.due_date)taskDates[t.due_date]=(taskDates[t.due_date]||0)+1;});
  const ygr=mk('div','ygrid');
  for(let m=0;m<12;m++){
    const ym=mk('div','ym');
    const yt=mk('div','ym-title');
    yt.innerHTML=`${MONTHS[m]} <span class="wbadge" style="${(y===2026&&m===2)?'':'opacity:.5'}">W${getISOWeek(new Date(y,m,1))}</span>`;
    ym.appendChild(yt);
    const mg=mk('div','ymini');
    ['M','T','W','T','F','S','S'].forEach(d=>{const h=mk('div','ymini-h');h.textContent=d;mg.appendChild(h);});
    const fd=new Date(y,m,1),sdow=(fd.getDay()||7)-1;
    for(let i=0;i<sdow;i++)mg.appendChild(mk('div',''));
    const dim=new Date(y,m+1,0).getDate();
    for(let d=1;d<=dim;d++){
      const cell=mk('div','ymini-d');
      const dk=`${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
      const isT=new Date(y,m,d).toDateString()===TODAY.toDateString();
      if(isT)cell.classList.add('today');
      else if(taskDates[dk])cell.classList.add('ht');
      cell.textContent=d;cell.title=taskDates[dk]?`${taskDates[dk]} task(s) due`:'';
      cell.onclick=()=>{calDate=new Date(y,m,d);setCalV('month',null);document.querySelectorAll('.cal-vtab').forEach((b,i2)=>b.classList.toggle('on',i2===1));};
      mg.appendChild(cell);
    }
    ym.appendChild(mg);ygr.appendChild(ym);
  }
  el.appendChild(ygr);
}


// ── Calendar event creation (GUI + API compatible) ─────────────────────────
// Events can be created by:
//   1. Human user via GUI (openCalEventForm)
//   2. AI agent via POST /api/calendar/events
//   3. AI agent via POST /api/tasks/create (tasks auto-appear on their due date)

function openCalEventForm(){
  const mo=document.getElementById('MO');
  mo.style.display='flex';
  const mc=document.getElementById('MC');
  mc.innerHTML=`
    <div class="mo-head">
      <span class="mo-title">Add calendar event</span>
      <button class="mo-x" onclick="closeMo()">×</button>
    </div>
    <div style="display:grid;gap:12px;padding:0 0 10px">
      <div>
        <label style="font-size:.68rem;color:var(--mut);margin-bottom:3px;display:block">Title</label>
        <input id="CE_TITLE" class="ai" placeholder="e.g. Sprint review, Client meeting, Daily standup" style="width:100%">
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
        <div>
          <label style="font-size:.68rem;color:var(--mut);margin-bottom:3px;display:block">Day</label>
          <select id="CE_DAY" class="ai">
            <option>Mon</option><option>Tue</option><option>Wed</option><option>Thu</option><option>Fri</option><option>Sat</option><option>Sun</option>
          </select>
        </div>
        <div>
          <label style="font-size:.68rem;color:var(--mut);margin-bottom:3px;display:block">Time</label>
          <input id="CE_TIME" class="ai" type="time" value="09:00">
        </div>
        <div>
          <label style="font-size:.68rem;color:var(--mut);margin-bottom:3px;display:block">Category</label>
          <select id="CE_CAT" class="ai">
            <option value="hl-plan">Planning</option>
            <option value="hl-code">Code</option>
            <option value="hl-res">Research</option>
            <option value="hl-ops">Ops</option>
            <option value="hl-qa">QA</option>
            <option value="hl-sec">Security</option>
            <option value="hl-des">Design</option>
            <option value="hl-doc">Docs</option>
          </select>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div>
          <label style="font-size:.68rem;color:var(--mut);margin-bottom:3px;display:block">Assigned to</label>
          <select id="CE_AGENT" class="ai">
            <option value="">— Unassigned —</option>
          </select>
        </div>
        <div>
          <label style="font-size:.68rem;color:var(--mut);margin-bottom:3px;display:block">Type</label>
          <select id="CE_TYPE" class="ai">
            <option value="false">One-time</option>
            <option value="true">Recurring (weekly)</option>
          </select>
        </div>
      </div>
      <button class="sbb p" onclick="submitCalEvent()" style="margin-top:6px">Add to calendar</button>
    </div>`;
  // Populate agent selector
  const sel=document.getElementById('CE_AGENT');
  AGENTS.forEach(a=>{
    if(a.id==='ceo')return;
    const o=document.createElement('option');o.value=a.name;o.textContent=a.name;
    sel.appendChild(o);
  });
  // Default day to current calendar day
  const dayNames=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  document.getElementById('CE_DAY').value=dayNames[calDate.getDay()]||'Mon';
}

function submitCalEvent(){
  const title=document.getElementById('CE_TITLE').value.trim();
  if(!title){alert('Title is required');return;}
  const day=document.getElementById('CE_DAY').value;
  const time=document.getElementById('CE_TIME').value;
  const cat=document.getElementById('CE_CAT').value;
  const agent=document.getElementById('CE_AGENT').value||'CEO';
  const recurring=document.getElementById('CE_TYPE').value==='true';

  const event={t:time, ti:title, ag:agent, h:cat, recurring:recurring};

  // Add to local calendar data
  if(!CAL[day])CAL[day]=[];
  CAL[day].push(event);
  // Sort by time
  CAL[day].sort((a,b)=>a.t.localeCompare(b.t));

  // Also try to push to server API
  fetch('/api/calendar/events',{
    method:'POST',
    headers:{'Content-Type':'application/json','Authorization':'Bearer '+(typeof API_TOKEN!=='undefined'?API_TOKEN:'')},
    body:JSON.stringify({day:day, time:time, title:title, agent:agent, category:cat, recurring:recurring})
  }).catch(()=>{/* offline mode — event is in local state */});

  closeMo();
  renderCal();
}

// API-compatible event creation (called by server when AI agent creates event)
function addCalendarEvent(day, time, title, agent, category, recurring){
  const event={t:time, ti:title, ag:agent||'CEO', h:category||'hl-plan', recurring:!!recurring};
  if(!CAL[day])CAL[day]=[];
  CAL[day].push(event);
  CAL[day].sort((a,b)=>a.t.localeCompare(b.t));
  // Re-render if calendar is visible
  const calView=document.getElementById('V_cal');
  if(calView&&calView.classList.contains('on'))renderCal();
}

// ── Calendar event edit/delete ─────────────────────────────────────────────
function deleteCalEvent(day, idx){
  if(!confirm('Delete this event?'))return;
  if(CAL[day]) CAL[day].splice(idx, 1);
  renderCal();
}

function editCalEvent(day, idx){
  const ev=CAL[day]&&CAL[day][idx];if(!ev)return;
  const mo=document.getElementById('MO');mo.style.display='flex';
  const mc=document.getElementById('MC');
  mc.innerHTML=`
    <div class="mo-head"><span class="mo-title">Edit event</span><button class="mo-x" onclick="closeMo()">×</button></div>
    <div style="display:grid;gap:12px;padding:0 0 10px">
      <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Title</label>
        <input id="CE_TITLE" class="ai" value="${(ev.ti||'').replace(/"/g,'&quot;')}" style="width:100%"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Time</label>
          <input id="CE_TIME" class="ai" type="time" value="${ev.t||'09:00'}"></div>
        <div><label style="font-size:.68rem;color:var(--mut);display:block;margin-bottom:3px">Agent</label>
          <input id="CE_AG" class="ai" value="${ev.ag||''}" style="width:100%"></div>
      </div>
      <div style="display:flex;gap:8px">
        <button class="sbb p" onclick="updateCalEvent('${day}',${idx})">Save</button>
        <button class="sbb" onclick="deleteCalEvent('${day}',${idx});closeMo()" style="border-color:var(--dn);color:var(--dn)">Delete</button>
      </div>
    </div>`;
}

function updateCalEvent(day, idx){
  const ev=CAL[day]&&CAL[day][idx];if(!ev)return;
  ev.ti=document.getElementById('CE_TITLE').value.trim()||ev.ti;
  ev.t=document.getElementById('CE_TIME').value||ev.t;
  ev.ag=document.getElementById('CE_AG').value.trim()||ev.ag;
  CAL[day].sort((a,b)=>a.t.localeCompare(b.t));
  closeMo();renderCal();
}
