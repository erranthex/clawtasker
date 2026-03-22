// ═══════════════════════════════════════════════════════════════════════
// CLAWTASKER POCKET OFFICE v10 — Self-contained canvas 2D simulation
// No CDN. Works offline. requestAnimationFrame game loop.
//
// Spritesheet 480×128: frame 0=idle/front  1=walk-A  2=walk-B
//                       frame 3=seated      4=talk/point
//
// Behaviour zones (status → zone):
//   working    → specialist pod (seated at desk)
//   blocked    → ceo_strip / scrum_table (escalate, talk)
//   validation → review_rail (talk)
//   idle       → lounge / kitchen (wander, idle)
//   speaking   → scrum_table (discussion with peers)
// ═══════════════════════════════════════════════════════════════════════

const GAME_W = 640, GAME_H = 384;
const MIN_AGENT_DIST = 18;   // px — minimum separation between any two agents
const SPRITE_DW = 26, SPRITE_DH = 34;   // display size of each sprite on canvas
const WALK_FPS  = 5;   // animation frames per second for walk cycle

// Zone slots (game coords 640×384)
const GAME_ZONES = {"ceo_strip": [{"x": 297, "y": 316}, {"x": 340, "y": 316}], "chief_desk": [{"x": 238, "y": 317}, {"x": 268, "y": 317}], "code_pod": [{"x": 86, "y": 120}, {"x": 133, "y": 120}, {"x": 86, "y": 186}, {"x": 133, "y": 186}], "research_pod": [{"x": 451, "y": 120}, {"x": 501, "y": 120}, {"x": 451, "y": 186}, {"x": 501, "y": 186}], "ops_pod": [{"x": 86, "y": 266}, {"x": 133, "y": 266}, {"x": 86, "y": 312}, {"x": 133, "y": 312}], "qa_pod": [{"x": 452, "y": 266}, {"x": 501, "y": 266}], "studio_pod": [{"x": 470, "y": 309}, {"x": 511, "y": 309}, {"x": 552, "y": 309}, {"x": 593, "y": 309}], "scrum_table": [{"x": 233, "y": 98}, {"x": 293, "y": 89}, {"x": 352, "y": 98}, {"x": 233, "y": 152}, {"x": 293, "y": 160}, {"x": 352, "y": 152}], "review_rail": [{"x": 416, "y": 238}, {"x": 464, "y": 238}, {"x": 511, "y": 238}, {"x": 559, "y": 238}], "board_wall": [{"x": 293, "y": 45}], "lounge": [{"x": 197, "y": 311}, {"x": 238, "y": 311}, {"x": 357, "y": 311}, {"x": 398, "y": 311}], "kitchen": [{"x": 560, "y": 100}, {"x": 590, "y": 100}, {"x": 575, "y": 130}], "conference": [{"x": 180, "y": 200}, {"x": 210, "y": 200}, {"x": 240, "y": 200}, {"x": 180, "y": 230}, {"x": 210, "y": 230}, {"x": 240, "y": 230}]};

// Furniture collision rectangles — agents cannot walk through these
const FURNITURE_RECTS = [
  {x:80,y:100,w:70,h:20},    // code pod desks
  {x:80,y:170,w:70,h:20},
  {x:445,y:100,w:70,h:20},   // research pod desks
  {x:445,y:170,w:70,h:20},
  {x:80,y:250,w:70,h:20},    // ops pod desks
  {x:80,y:296,w:70,h:20},
  {x:446,y:250,w:70,h:20},   // qa pod desk
  {x:220,y:80,w:150,h:15},   // scrum table top
  {x:220,y:145,w:150,h:15},  // scrum table bottom
  {x:285,y:300,w:50,h:28},   // CEO desk
  {x:410,y:222,w:160,h:14},  // review rail
  {x:170,y:188,w:85,h:14},   // conference table
  {x:170,y:218,w:85,h:14},
  {x:555,y:86,w:50,h:18},    // kitchen counter
];

// Additional semantic zones for behaviour routing
const KITCHEN_SLOTS = [
  {x:197,y:311},{x:238,y:311},{x:357,y:311},{x:398,y:311}  // lounge == kitchen/break area
];
const DISCUSSION_SLOTS = [  // scrum table slots for speaking/blocked agents
  {x:233,y:98},{x:293,y:89},{x:352,y:98},
  {x:233,y:152},{x:293,y:160},{x:352,y:152}
];
const CEO_AREA_SLOTS = [    // ceo strip + chief desk for blocked escalation
  {x:297,y:316},{x:238,y:317},{x:280,y:316}
];

// Status → behaviour routing
const STATUS_ZONE = {
  working:    null,          // use agent's home specialist zone
  blocked:    'scrum_table', // go to discussion table / CEO area
  validation: 'review_rail', // go to review rail
  validating: 'review_rail',
  idle:       'lounge',      // go to lounge/kitchen
  offline:    null,          // stay put, grayed out
};

// Status → sprite frame when stationary
const STATUS_FRAME = {
  working:    3,  // seated
  blocked:    4,  // talk/point
  validation: 4,
  validating: 4,
  idle:       0,  // frontal
  offline:    0,
};

// Status → dot colour
const STATUS_DOT = {
  working:'#22d160', blocked:'#ff4d6a',
  validation:'#f5a623', validating:'#f5a623',
  idle:'#525870', offline:'#333344',
};

// Agent home zones based on role/specialist
const HOME_ZONE = {
  ceo:'ceo_strip', orion:'chief_desk',
  codex:'code_pod', pixel:'code_pod',
  violet:'research_pod', scout:'research_pod', mercury:'research_pod',
  charlie:'ops_pod', shield:'ops_pod', ledger:'ops_pod',
  ralph:'qa_pod',
  quill:'studio_pod', iris:'studio_pod',
  echo:'lounge',
};

let offCanvas=null, offCtx=null, offImgDay=null, offImgNight=null;
let offAgents={}, offScene='day', offInited=false;
let offLastTs=0;
const offSpeechBubbles={};   // agentId → {text, timer}

// ── Helper: pick a free slot from a list ────────────────────────────────
function pickFreeSlot(slotList, occupiedPositions, excludeSelf){
  // Shuffle for variety
  const shuffled=[...slotList].sort(()=>Math.random()-0.5);
  for(const s of shuffled){
    const conflict=occupiedPositions.some(p=>{
      if(p.id===excludeSelf)return false;
      return Math.hypot(p.x-s.x,p.y-s.y)<MIN_AGENT_DIST;
    });
    if(!conflict)return s;
  }
  // All slots occupied — offset slightly to avoid exact stack
  const base=slotList[Math.floor(Math.random()*slotList.length)];
  return {x:base.x+(Math.random()-0.5)*MIN_AGENT_DIST*0.8,
          y:base.y+(Math.random()-0.5)*MIN_AGENT_DIST*0.8};
}

// ── initCanvasOffice ────────────────────────────────────────────────────
function initCanvasOffice(){
  if(offInited)return;
  const container=document.getElementById('OFF_CANVAS_CONTAINER');
  if(!container)return;

  offCanvas=document.createElement('canvas');
  offCanvas.width=GAME_W; offCanvas.height=GAME_H;
  offCanvas.style.cssText='width:100%;height:100%;display:block;image-rendering:pixelated;cursor:crosshair';
  container.appendChild(offCanvas);
  offCtx=offCanvas.getContext('2d');

  offImgDay=new Image();   offImgDay.src=DAY_MAP;
  offImgNight=new Image(); offImgNight.src=NIGHT_MAP;

  const allA=[{id:'ceo',name:'You',status:'working',hue:'planning',role:'CEO',task:'Management'},...AGENTS];

  // First pass: assign positions ensuring no overlaps from start
  const reserved=[];
  allA.forEach(a=>{
    if(a.derived_status==='offline'||a.status==='offline')return;
    const homeZone  = HOME_ZONE[a.id]||'lounge';
    const destZone  = STATUS_ZONE[a.status||'idle']||homeZone;
    const slotList  = GAME_ZONES[destZone]||GAME_ZONES['lounge'];
    const slot      = pickFreeSlot(slotList, reserved, a.id);
    reserved.push({id:a.id, x:slot.x, y:slot.y});
  });

  allA.forEach((a,i)=>{
    const spriteSrc = (a.id==='ceo'&&ceoPhoto)?ceoPhoto
                      : (SPR[agentSprites[a.id]]||SPR[a.id]||SPR['ceo']);
    const img=new Image(); img.src=spriteSrc;
    const reserved_pos = reserved.find(p=>p.id===a.id);
    const x = reserved_pos ? reserved_pos.x : 320;
    const y = reserved_pos ? reserved_pos.y : 200;
    const offline = (a.derived_status==='offline'||a.status==='offline');
    offAgents[a.id]={
      id:a.id, name:a.name, status:a.status||'idle',
      role:a.role||'', task:a.task||'',
      x, y, tx:x, ty:y,
      img, frame:offline?0:STATUS_FRAME[a.status]||0,
      walkFrame:0, walkTimer:0,
      waitTimer:1000+Math.random()*3000,
      moving:false, flipX:false, offline,
      homeZone: HOME_ZONE[a.id]||'lounge',
    };
  });

  // Click to inspect agent
  offCanvas.onclick=function(e){
    const rect=offCanvas.getBoundingClientRect();
    const sx=GAME_W/rect.width, sy=GAME_H/rect.height;
    const mx=(e.clientX-rect.left)*sx, my=(e.clientY-rect.top)*sy;
    let hit=null, hitDist=999;
    Object.values(offAgents).forEach(ag=>{
      const d=Math.hypot(mx-ag.x, my-ag.y);
      if(d<SPRITE_DW&&d<hitDist){hit=ag;hitDist=d;}
    });
    if(hit){
      const agent=AGENTS.find(a=>a.id===hit.id)||hit;
      showOfficeTooltip(hit, agent, e);
    } else { hideOfficeTooltip(); }
  };

  offInited=true;
  requestAnimationFrame(offTick);
  buildScrumList();
}

// ── Main game tick ───────────────────────────────────────────────────────
function offTick(ts){
  requestAnimationFrame(offTick);
  const dt=Math.min(ts-offLastTs, 50); // cap at 50ms (20fps min)
  offLastTs=ts;
  const ctx=offCtx;

  // Draw map
  const mapImg=offScene==='day'?offImgDay:offImgNight;
  if(mapImg&&mapImg.complete&&mapImg.naturalWidth>0){
    ctx.drawImage(mapImg,0,0,GAME_W,GAME_H);
  } else {
    ctx.fillStyle='#0a0d14';ctx.fillRect(0,0,GAME_W,GAME_H);
  }

  // Gather current positions for collision checks
  const positions=Object.values(offAgents).map(ag=>({id:ag.id,x:ag.x,y:ag.y}));

  // Depth-sort by Y so agents lower on screen draw on top
  const sorted=Object.values(offAgents).sort((a,b)=>a.y-b.y);

  sorted.forEach(ag=>{
    if(ag.offline){
      // Draw greyed-out offline agent (stationary, desaturated)
      _drawSprite(ctx, ag, true);
      return;
    }

    // ── Movement update ──────────────────────────────────────────────
    if(ag.moving){
      const dx=ag.tx-ag.x, dy=ag.ty-ag.y, dist=Math.hypot(dx,dy);
      if(dist<2){
        ag.x=ag.tx; ag.y=ag.ty;
        ag.moving=false;
        ag.frame=STATUS_FRAME[ag.status]||0;
        ag.waitTimer=3000+Math.random()*6000;
      } else {
        // Speed based on status (blocked agents rush, idle agents stroll)
        const spd=({blocked:1.1,validation:0.9,validating:0.9,working:0.7,idle:0.55}[ag.status]||0.7)*dt/16;
        ag.x+=dx/dist*spd; ag.y+=dy/dist*spd;
        ag.flipX=(dx<0);

        // Collision push — separate from other agents
        positions.forEach(other=>{
          if(other.id===ag.id)return;
          const od=Math.hypot(ag.x-other.x, ag.y-other.y);
          if(od<MIN_AGENT_DIST&&od>0){
            // Push this agent away
            const push=(MIN_AGENT_DIST-od)/MIN_AGENT_DIST*0.5;
            ag.x+=(ag.x-other.x)/od*push;
            ag.y+=(ag.y-other.y)/od*push;
          }
        });

        // Furniture collision — push agents out of furniture rectangles
        FURNITURE_RECTS.forEach(r=>{
          const pad=4; // agent radius padding
          if(ag.x>r.x-pad&&ag.x<r.x+r.w+pad&&ag.y>r.y-pad&&ag.y<r.y+r.h+pad){
            // Find nearest edge to push toward
            const dLeft=ag.x-(r.x-pad), dRight=(r.x+r.w+pad)-ag.x;
            const dTop=ag.y-(r.y-pad), dBottom=(r.y+r.h+pad)-ag.y;
            const minD=Math.min(dLeft,dRight,dTop,dBottom);
            if(minD===dLeft) ag.x=r.x-pad;
            else if(minD===dRight) ag.x=r.x+r.w+pad;
            else if(minD===dTop) ag.y=r.y-pad;
            else ag.y=r.y+r.h+pad;
          }
        });

        // Walk frame animation
        ag.walkTimer+=dt;
        if(ag.walkTimer>1000/WALK_FPS){
          ag.walkFrame=(ag.walkFrame+1)%2;
          ag.walkTimer=0;
        }
        ag.frame=ag.walkFrame===0?1:2;
      }
    } else {
      // ── Idle countdown → pick next destination ───────────────────
      ag.waitTimer-=dt;
      if(ag.waitTimer<=0){
        _pickNextDestination(ag, positions);
      }
      ag.frame=STATUS_FRAME[ag.status]||0;
    }

    // Keep within canvas bounds
    ag.x=Math.max(4,Math.min(GAME_W-4,ag.x));
    ag.y=Math.max(8,Math.min(GAME_H-4,ag.y));

    _drawSprite(ctx, ag, false);
  });

  // Draw speech bubbles
  Object.entries(offSpeechBubbles).forEach(([id,b])=>{
    const ag=offAgents[id];
    if(!ag||ag.offline)return;
    b.timer-=dt;
    if(b.timer<=0){delete offSpeechBubbles[id];return;}
    _drawSpeechBubble(ctx, ag, b.text);
  });

  // Night tint overlay
  if(offScene==='night'){
    ctx.fillStyle='rgba(0,20,60,0.35)';
    ctx.fillRect(0,0,GAME_W,GAME_H);
  }
}

// ── Pick next destination for an agent ──────────────────────────────────
function _pickNextDestination(ag, positions){
  const status=ag.status||'idle';

  // Determine target zone based on behaviour
  let targetZone=STATUS_ZONE[status];
  if(!targetZone) targetZone=ag.homeZone;

  // Blocked agents sometimes head to CEO area, sometimes scrum table
  if(status==='blocked'){
    targetZone=Math.random()<0.5?'scrum_table':'ceo_strip';
  }

  // Idle agents: coffee break in kitchen (30%), wander lounge (30%), or home (40%)
  if(status==='idle'){
    const r=Math.random();
    if(r<0.3) targetZone='kitchen';
    else if(r<0.6) targetZone='lounge';
    else targetZone=ag.homeZone;
  }

  // Working agents: mostly stay at desk, sometimes visit scrum table or conference
  if(status==='working'){
    const r=Math.random();
    if(r<0.15) targetZone='scrum_table';
    else if(r<0.25) targetZone='conference';
    else if(r<0.35) targetZone=ag.homeZone;
    // else stay at current zone
  }

  // Validation agents visit review rail or conference
  if(status==='validation'||status==='validating'){
    if(Math.random()<0.4) targetZone='review_rail';
    else if(Math.random()<0.3) targetZone='conference';
  }

  const slotList=GAME_ZONES[targetZone]||GAME_ZONES['lounge'];
  const slot=pickFreeSlot(slotList, positions, ag.id);

  ag.tx=slot.x; ag.ty=slot.y; ag.moving=true;

  // Occasionally emit a speech bubble
  if(Math.random()<0.18){
    const msgs={
      blocked:['Need help!','Escalating…','Waiting for CEO','🚫 Stuck'],
      validation:['Reviewing…','Checking…','Approving?','🔍 QA pass'],
      working:['On it…','Building…','Shipping…','📝 Focused'],
      idle:['☕ Break','Thinking…','Ready','Available'],
    };
    const pool=msgs[status]||['…'];
    offSpeechBubbles[ag.id]={
      text:pool[Math.floor(Math.random()*pool.length)],
      timer:3500,
    };
  }
}

// ── Draw a sprite ────────────────────────────────────────────────────────
function _drawSprite(ctx, ag, offline){
  const fw=96, fh=128, dw=SPRITE_DW, dh=SPRITE_DH;
  const sx=ag.frame*fw;
  const drawY=ag.y-dh+4;  // anchor at feet (ag.y is feet position)

  ctx.save();
  if(offline) ctx.globalAlpha=0.35;

  if(ag.img&&ag.img.complete&&ag.img.naturalWidth>0){
    if(ag.flipX){
      ctx.translate(ag.x+dw/2, drawY);
      ctx.scale(-1,1);
      ctx.drawImage(ag.img, sx,0, fw,fh, -dw,0, dw,dh);
    } else {
      ctx.drawImage(ag.img, sx,0, fw,fh, ag.x-dw/2, drawY, dw,dh);
    }
  } else {
    // Fallback circle while sprite loads
    ctx.beginPath();
    ctx.arc(ag.x, ag.y-dh/2, dw/2, 0, Math.PI*2);
    ctx.fillStyle=offline?'#333':'#5ee8d2';
    ctx.fill();
  }

  // Status dot (top-right of sprite)
  if(!offline){
    const dotCol=STATUS_DOT[ag.status]||'#525870';
    ctx.beginPath();
    ctx.arc(ag.x+dw/2-2, drawY+2, 3, 0, Math.PI*2);
    ctx.fillStyle='#0a0d14'; ctx.fill();
    ctx.beginPath();
    ctx.arc(ag.x+dw/2-2, drawY+2, 2.2, 0, Math.PI*2);
    ctx.fillStyle=dotCol; ctx.fill();
  }

  ctx.restore();

  // ── Enhanced label: Name + Status ──
  ctx.save();
  const statusText=offline?'OFFLINE':ag.status.toUpperCase();
  const dotCol=STATUS_DOT[ag.status]||'#525870';

  // Name label
  ctx.font='600 5.5px "JetBrains Mono",monospace';
  ctx.textAlign='center';
  const nameW=ctx.measureText(ag.name).width;

  // Status label
  ctx.font='500 4.2px "JetBrains Mono",monospace';
  const statW=ctx.measureText(statusText).width;

  const maxW=Math.max(nameW,statW+8);
  const lx=ag.x, ly=ag.y+3;

  // Background pill
  ctx.fillStyle='rgba(8,11,17,0.88)';
  const bw=maxW+8, bh=15;
  ctx.beginPath();
  ctx.roundRect(lx-bw/2, ly-6, bw, bh, 3);
  ctx.fill();

  // Name
  ctx.font='600 5.5px "JetBrains Mono",monospace';
  ctx.fillStyle=offline?'#555':ag.moving?'#5ee8d2':'#eef0f6';
  ctx.fillText(ag.name, lx, ly);

  // Status text with dot
  ctx.font='500 4.2px "JetBrains Mono",monospace';
  const sly=ly+6.5;
  // Status dot
  ctx.beginPath();
  ctx.arc(lx-statW/2-3, sly-1.5, 1.8, 0, Math.PI*2);
  ctx.fillStyle=offline?'#333344':dotCol;
  ctx.fill();
  // Status text
  ctx.fillStyle=offline?'#555':dotCol;
  ctx.fillText(statusText, lx+2, sly);

  ctx.restore();
}

// ── Draw speech bubble above agent ──────────────────────────────────────
function _drawSpeechBubble(ctx, ag, text){
  const dh=SPRITE_DH;
  const bx=ag.x, by=ag.y-dh-8;
  ctx.save();
  ctx.font='bold 5px sans-serif';
  ctx.textAlign='center';
  const tw=ctx.measureText(text).width;
  const bw=tw+10, bh=12, br=4;
  const bxl=bx-bw/2;
  ctx.fillStyle='rgba(94,232,210,0.92)';
  ctx.beginPath();
  ctx.roundRect(bxl,by-bh,bw,bh,br);
  ctx.fill();
  // Tail
  ctx.beginPath();
  ctx.moveTo(bx-3,by);ctx.lineTo(bx+3,by);ctx.lineTo(bx,by+4);
  ctx.fillStyle='rgba(94,232,210,0.92)';ctx.fill();
  ctx.fillStyle='#080b11';
  ctx.fillText(text,bx,by-bh/2+2);
  ctx.restore();
}

// ── Tooltip on click ────────────────────────────────────────────────────
function showOfficeTooltip(agData, agent, evt){
  let tip=document.getElementById('OFF_TIP');
  if(!tip){
    tip=document.createElement('div');tip.id='OFF_TIP';
    tip.style.cssText='position:fixed;z-index:9999;pointer-events:none;max-width:220px;'+
      'background:var(--card);border:1px solid var(--bds);border-radius:10px;'+
      'padding:10px 14px;font-size:.74rem;color:var(--tx);'+
      'box-shadow:0 8px 24px rgba(0,0,0,.55)';
    document.body.appendChild(tip);
  }
  const col=STATUS_DOT[agData.status]||'#555';
  tip.innerHTML=
    `<div style="font-weight:700;color:var(--txs);margin-bottom:3px">${agent.name||agData.name}</div>`+
    `<div style="color:var(--mut);font-size:.67rem;margin-bottom:6px">${agent.role||''}</div>`+
    `<div style="color:var(--tx);font-size:.7rem;margin-bottom:5px">⚙ ${(agent.task||'No task').slice(0,52)}</div>`+
    `<div style="display:flex;align-items:center;gap:5px">`+
      `<span style="width:7px;height:7px;border-radius:50%;background:${col};display:inline-block"></span>`+
      `<span style="color:${col};font-weight:700;font-size:.68rem;text-transform:uppercase">${agData.status}</span>`+
    `</div>`;
  tip.style.left=(evt.clientX+14)+'px';
  tip.style.top =(evt.clientY-24)+'px';
  tip.style.display='block';
  clearTimeout(tip._t);tip._t=setTimeout(hideOfficeTooltip,5000);
}
function hideOfficeTooltip(){
  const t=document.getElementById('OFF_TIP');
  if(t)t.style.display='none';
}

// ── Public controls ──────────────────────────────────────────────────────
function setGameScene(mode){
  offScene=mode;
  document.getElementById('SCN_DAY').classList.toggle('on',mode==='day');
  document.getElementById('SCN_NIGHT').classList.toggle('on',mode==='night');
}

function randomiseAgents(){
  if(!offInited)return;
  const zones=Object.keys(GAME_ZONES);
  const positions=Object.values(offAgents).map(ag=>({id:ag.id,x:ag.x,y:ag.y}));
  Object.values(offAgents).forEach(ag=>{
    if(ag.offline)return;
    const zone=zones[Math.floor(Math.random()*zones.length)];
    const slot=pickFreeSlot(GAME_ZONES[zone]||GAME_ZONES['lounge'],positions,ag.id);
    ag.tx=slot.x; ag.ty=slot.y; ag.moving=true;
    const pos=positions.find(p=>p.id===ag.id);
    if(pos){pos.x=slot.x;pos.y=slot.y;}
  });
}

function resetAgents(){
  if(!offInited)return;
  const positions=[];
  Object.entries(POSITIONS).forEach(([id,pos])=>{
    const ag=offAgents[id];if(!ag)return;
    const gx=pos.x*GAME_W/1400, gy=pos.y*GAME_H/840;
    const slot=pickFreeSlot([{x:gx,y:gy}],positions,id);
    ag.tx=slot.x; ag.ty=slot.y; ag.moving=true;
    positions.push({id,x:slot.x,y:slot.y});
  });
}

// Refresh sprite image for an agent (called after sprite change in picker)
function refreshOfficeSprite(agentId){
  const ag=offAgents[agentId];if(!ag)return;
  const src=(agentId==='ceo'&&ceoPhoto)?ceoPhoto
            :(SPR[agentSprites[agentId]]||SPR[agentId]||SPR['ceo']);
  const img=new Image();img.src=src;
  ag.img=img;
}

// Called from org decommission — grey out and stop in place
function decommissionOfficeAgent(agentId){
  const ag=offAgents[agentId];if(!ag)return;
  ag.offline=true;ag.moving=false;ag.status='offline';ag.frame=0;
}

function buildScrumList(){
  const scrum=document.getElementById('SCRUM');if(!scrum)return;
  scrum.innerHTML='';
  [{id:'violet',t:'8AM briefing (T-206)'},
   {id:'charlie',t:'Blocked — deploy secret (T-209)'},
   {id:'orion',t:'Routing morning ops'},
   {id:'codex',t:'Board filters (T-203)'},
   {id:'ralph',t:'Validation sweep (T-201)'},
   {id:'pixel',t:'Office engine polish (T-204)'}
  ].forEach(s=>{
    const item=document.createElement('div');item.className='scrum-item';
    item.appendChild(mkFaceAv(s.id,''));
    const ag=AGENTS.find(a=>a.id===s.id)||{name:s.id};
    const sp=document.createElement('span');sp.textContent=ag.name+': '+s.t;
    item.appendChild(sp);scrum.appendChild(item);
  });
}



