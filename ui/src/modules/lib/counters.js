// ── Dynamic counters — update all hardcoded values on data change ──────────
function refreshCounters(){
  const ac=AGENTS.length;
  const tc=TASKS.length;
  const pc=Object.keys(AM).length;
  
  // Topbar pill
  const pill=document.getElementById('AGENT_COUNT_PILL');
  if(pill) pill.textContent=ac;
  
  // Team chip
  const chip=document.getElementById('AGENT_COUNT_CHIP');
  if(chip) chip.textContent=ac+' agents';
  
  // Capability chip
  const cap=document.getElementById('CAP_AGENT_COUNT');
  if(cap) cap.textContent=ac+' agents';
  
  // Board count
  const bc=document.getElementById('BOARD_COUNT');
  if(bc) bc.textContent=tc+' tasks';
  
  // Access chip
  const acc=document.getElementById('ACC_CHIP');
  if(acc) acc.textContent=pc+' projects · '+ac+' entities';
}
