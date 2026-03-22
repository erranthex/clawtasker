import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { APP_TEMPLATE } from '../src/ui/app-template.js';

test('RQ-001 shell uses the OpenClaw-style shell structure and grouped navigation', () => {
  assert.match(APP_TEMPLATE, /class="shell shell--clawtasker"/);
  assert.match(APP_TEMPLATE, /class="shell-nav"/);
  assert.match(APP_TEMPLATE, /class="sidebar-shell"/);
  assert.match(APP_TEMPLATE, /class="topbar"/);
  assert.match(APP_TEMPLATE, /Operate/);
  assert.match(APP_TEMPLATE, /Work/);
  assert.match(APP_TEMPLATE, /Observe/);
  assert.match(APP_TEMPLATE, /Theme: Dark \/ Light \/ System/);
  assert.match(APP_TEMPLATE, /data-view="appearance"/);
});

test('RQ-002 shell includes Appearance controls, theme cycle, and quick find', () => {
  assert.match(APP_TEMPLATE, /id="theme-cycle"/);
  assert.match(APP_TEMPLATE, /id="focus-search"/);
  assert.match(APP_TEMPLATE, /Palette family/);
  assert.match(APP_TEMPLATE, /Mode/);
  assert.match(APP_TEMPLATE, /Write token stays in your browser only/);
});

test('RQ-003 template includes CEO profile controls and upload input', () => {
  assert.match(APP_TEMPLATE, /ceo-avatar-mode/);
  assert.match(APP_TEMPLATE, /ceo-avatar-upload/);
  assert.match(APP_TEMPLATE, /ceo-profile-preview/);
});

test('RQ-005 template includes Pocket Office v9 office canvas and scene controls', () => {
  assert.match(APP_TEMPLATE, /Pocket Office v9 office scene/);
  assert.match(APP_TEMPLATE, /office-canvas/);
  assert.match(APP_TEMPLATE, /sync table/);
  assert.match(APP_TEMPLATE, /id="office-scene-day"/);
  assert.match(APP_TEMPLATE, /id="office-scene-night"/);
});

test('RQ-011 style entry imports official-like layout mobile sheet', () => {
  const styles = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');
  assert.match(styles, /layout\.mobile\.css/);
});

test('RQ-012 access view states visualization-only contract and restart-safe boundary', () => {
  assert.match(APP_TEMPLATE, /Visualization contract/);
  assert.match(APP_TEMPLATE, /visualization only/i);
  assert.match(APP_TEMPLATE, /OpenClaw keeps routing, sessions, and workspaces/i);
  assert.match(APP_TEMPLATE, /Agents publish heartbeats, status, validation updates, and conversation notes/i);
  assert.match(APP_TEMPLATE, /If ClawTasker restarts, agents continue working/i);
});

test('RQ-016 dashboard includes system health and recovery playbook surfaces', () => {
  assert.match(APP_TEMPLATE, /System health/);
  assert.match(APP_TEMPLATE, /id="system-health"/);
  assert.match(APP_TEMPLATE, /Recovery playbook/);
  assert.match(APP_TEMPLATE, /id="recovery-playbook"/);
});

test('RQ-017 access view includes agent publish contract and recovery center', () => {
  assert.match(APP_TEMPLATE, /Agent publish contract/);
  assert.match(APP_TEMPLATE, /id="agent-api-contract"/);
  assert.match(APP_TEMPLATE, /Recovery center/);
  assert.match(APP_TEMPLATE, /id="recovery-facts"/);
  assert.match(APP_TEMPLATE, /Boundary reminders/);
});

test('RQ-020 access view includes OpenClaw team bridge and live sync channel surfaces', () => {
  assert.match(APP_TEMPLATE, /OpenClaw team bridge/);
  assert.match(APP_TEMPLATE, /id="openclaw-bridge"/);
  assert.match(APP_TEMPLATE, /Live sync channel/);
  assert.match(APP_TEMPLATE, /id="live-sync-facts"/);
});

test('RQ-028 dashboard includes ticket system health surface', () => {
  assert.match(APP_TEMPLATE, /Ticket system health/);
  assert.match(APP_TEMPLATE, /id="ticket-system-health"/);
});

test('RQ-030 team view includes capability matrix and roster sync surfaces', () => {
  assert.match(APP_TEMPLATE, /Capability matrix/);
  assert.match(APP_TEMPLATE, /id="org-capabilities"/);
  assert.match(APP_TEMPLATE, /OpenClaw roster sync/);
  assert.match(APP_TEMPLATE, /id="roster-sync-status"/);
});

test('RQ-054 dashboard copy matches the command-center layout refresh', () => {
  assert.match(APP_TEMPLATE, /Command Center/);
  assert.match(APP_TEMPLATE, /Run a virtual AI company with a human CEO, a chief agent, and specialist sub-agents that stay in sync/);
  assert.match(APP_TEMPLATE, /Slice the company by agent, project, specialist, status, horizon, or search/);
  assert.match(APP_TEMPLATE, /Fast chief \/ specialist alignment/);
});

test('RQ-035 team view includes manager relationship surface and reporting-line language', () => {
  assert.match(APP_TEMPLATE, /Manager relationships/);
  assert.match(APP_TEMPLATE, /id="manager-grid"/);
  assert.match(APP_TEMPLATE, /Which manager coordinates which team/);
});

test('RQ-042 appearance view includes office scene selector', () => {
  assert.match(APP_TEMPLATE, /id="appearance-office-scene"/);
  assert.match(APP_TEMPLATE, /Office scene/);
  assert.match(APP_TEMPLATE, /Day office/);
  assert.match(APP_TEMPLATE, /Night office/);
});

test('RQ-046 conversation view includes source badge and official channel language', () => {
  assert.match(APP_TEMPLATE, /Source badges show whether the latest context came from browser chat, Telegram, Discord, a webhook, or an internal OpenClaw session/);
  assert.match(APP_TEMPLATE, /Open official channel/);
});

test('RQ-048 conversation composer separates directive and discussion messages', () => {
  assert.match(APP_TEMPLATE, /id="message-classification"/);
  assert.match(APP_TEMPLATE, /Directive/);
  assert.match(APP_TEMPLATE, /Discussion/);
});

test('RQ-050 conversation view includes the subagent summary toggle', () => {
  assert.match(APP_TEMPLATE, /id="show-subagent-detail"/);
  assert.match(APP_TEMPLATE, /Show internal subagent discussion instead of summaries only/);
});

test('RQ-051 conversation context exposes transcript and channel references', () => {
  assert.match(APP_TEMPLATE, /Current task, channel, and transcript refs/);
  assert.match(APP_TEMPLATE, /OpenClaw remains the runtime communication layer/);
});


test('RQ-053 appearance view exposes CEO Console as the default palette family', () => {
  assert.match(APP_TEMPLATE, /<option value="ceo">CEO Console<\/option>/);
  assert.match(APP_TEMPLATE, /Reset to CEO Console default/);
});


test('RQ-055 dashboard includes mission brief and staffing surfaces', () => {
  assert.match(APP_TEMPLATE, /Mission brief/);
  assert.match(APP_TEMPLATE, /id="mission-brief"/);
  assert.match(APP_TEMPLATE, /Shared mission plan for the current operating slice/);
  assert.match(APP_TEMPLATE, /Staffing and coverage/);
  assert.match(APP_TEMPLATE, /id="mission-staffing"/);
  assert.match(APP_TEMPLATE, /Who is staffed, what skills are covered, and where the gaps are/);
});

test('RQ-056 dashboard includes mission risk and dependency radar', () => {
  assert.match(APP_TEMPLATE, /Risk and dependency radar/);
  assert.match(APP_TEMPLATE, /id="mission-radar"/);
  assert.match(APP_TEMPLATE, /What could block the mission and which dependencies still need attention/);
});
