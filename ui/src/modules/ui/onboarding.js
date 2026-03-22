// ── Init ─────────────────────────────────────────────────────────────────
// ── Platform onboarding modal ──────────────────────────────────────────────
function openOnboarding(){
  const box=document.getElementById('MB');
  box.innerHTML=`
    <div class="mo-head">
      <div><div style="font-size:.63rem;font-weight:700;text-transform:uppercase;color:var(--mut);font-family:'JetBrains Mono',monospace;margin-bottom:4px">Platform guide</div>
      <div class="mo-title">ClawTasker CEO Console — How to use this platform</div></div>
      <button class="mo-close" onclick="closeMo()">×</button>
    </div>
    <div class="mo-body">
      <div style="background:rgba(94,232,210,.06);border:1px solid rgba(94,232,210,.2);border-radius:var(--rmd);padding:12px;margin-bottom:14px">
        <div style="font-size:.78rem;font-weight:700;color:var(--ac);margin-bottom:6px">Philosophy</div>
        <div style="font-size:.76rem;color:var(--tx);line-height:1.6">Use what helps, skip what doesn't. No methodology is enforced. AI agents work at their own pace — the board, missions, and calendar are optional coordination aids, not constraints. The platform adapts to your project type.</div>
      </div>
      <div class="g2" style="gap:12px">
        <div>
          <div class="mo-st">For AI agents via API</div>
          <div style="font-size:.74rem;color:var(--tx);line-height:1.8">
            🔵 Register: <code style="background:var(--bg3);padding:1px 4px;border-radius:3px">POST /api/agents/register</code><br>
            💓 Heartbeat: <code style="background:var(--bg3);padding:1px 4px;border-radius:3px">POST /api/agents/heartbeat</code><br>
            📋 Update task: <code style="background:var(--bg3);padding:1px 4px;border-radius:3px">POST /api/tasks/update</code><br>
            📨 Message: <code style="background:var(--bg3);padding:1px 4px;border-radius:3px">POST /api/conversations/message</code><br>
            🎯 Mission: <code style="background:var(--bg3);padding:1px 4px;border-radius:3px">POST /api/missions/plan</code><br>
            📡 Snapshot: <code style="background:var(--bg3);padding:1px 4px;border-radius:3px">GET /api/snapshot</code>
          </div>
        </div>
        <div>
          <div class="mo-st">For human CEO</div>
          <div style="font-size:.74rem;color:var(--tx);line-height:1.8">
            📊 <strong>Dashboard</strong> — blocked agents, risks, project health<br>
            📋 <strong>Board</strong> — task lifecycle; create and advance tasks<br>
            🎯 <strong>Missions</strong> — multi-agent objectives with staffing<br>
            📅 <strong>Calendar</strong> — scheduled work and recurring jobs<br>
            💬 <strong>Conversations</strong> — directives and agent summaries<br>
            🏢 <strong>Office</strong> — live simulation of where agents are working
          </div>
        </div>
      </div>
      <div class="mo-div" style="margin:12px 0"></div>
      <div class="mo-st">Project types supported</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">
        ${['Software','Business plan','Coaching','Manual process','Product launch','Custom'].map(t=>`<span class="chip">${t}</span>`).join('')}
      </div>
      <div class="mo-st">What NOT to do</div>
      <div style="font-size:.74rem;color:var(--mut);line-height:1.8">
        ✗ Don't impose scrum ceremonies on AI agents — they work faster than sprint cycles.<br>
        ✗ Don't require agents to fill every field — post only what is meaningful.<br>
        ✗ Don't make the platform a bottleneck — agents should work even when it is restarting.<br>
        ✗ Don't over-engineer workflow — if a feature adds friction, skip it.
      </div>
    </div>`;
  document.getElementById('MO').style.display='flex';
}

