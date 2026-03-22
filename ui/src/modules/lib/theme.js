// ── Mode ───────────────────────────────────────────────────────────────────
function toggleMode(){darkMode=!darkMode;document.getElementById('APP_MODE').value=darkMode?'dark':'light';applyMode();}
function applyMode(){
  darkMode=document.getElementById('APP_MODE').value==='dark';
  const t=darkMode
    ?{bg:'#080b11',bg2:'#0c0f17',bg3:'#10141e',bgh:'#161c28',card:'#111520',tx:'#c8ccd8',txs:'#eef0f6',mut:'#525870',bd:'#1a1f2e',bds:'#252c40'}
    :{bg:'#f0f2f8',bg2:'#e8eaf2',bg3:'#e2e4ef',bgh:'#dde0ec',card:'#ffffff',tx:'#3c3d4d',txs:'#1a1b26',mut:'#7c7e94',bd:'#d5d7e8',bds:'#c0c3d8'};
  Object.entries(t).forEach(([k,v])=>document.documentElement.style.setProperty('--'+k,v));
  document.getElementById('MODE_P').textContent=darkMode?'Dark':'Light';
}

