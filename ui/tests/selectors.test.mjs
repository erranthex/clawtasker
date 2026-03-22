import test from 'node:test';
import assert from 'node:assert/strict';
import { filterTasks, attentionKinds, sortTasks, matchAgentsToSkill, groupAgentsByDepartment, groupAgentsByManager } from '../src/lib/selectors.js';

const tasks = [
  { title: 'Adapt Pocket Office avatars', description: 'UI pass', project_id: 'ceo-console', project_name: 'CEO Console', owner: 'codex', owner_name: 'Codex', specialist: 'code', status: 'in_progress', horizon: 'Today', labels: ['ui'], collaborators: ['quill'], progress: 35, blocked: false },
  { title: 'Review sync table depth ordering', description: 'QA review', project_id: 'atlas-core', project_name: 'Atlas Core', owner: 'ralph', owner_name: 'Ralph', specialist: 'qa', status: 'validation', horizon: 'This Week', labels: ['qa'], collaborators: [], progress: 80, blocked: false },
  { title: 'Blocked GitHub sync', description: 'Token missing', project_id: 'market-radar', project_name: 'Market Radar', owner: 'charlie', owner_name: 'Charlie', specialist: 'ops', status: 'ready', horizon: 'Later', labels: ['ops'], collaborators: [], progress: 0, blocked: true },
];

test('RQ-004 filterTasks supports agent and specialist filtering', () => {
  assert.equal(filterTasks(tasks, { agent: 'codex', specialist: 'code' }).length, 1);
  assert.equal(filterTasks(tasks, { agent: 'quill' }).length, 1);
  assert.equal(filterTasks(tasks, { specialist: 'qa' }).length, 1);
});

test('RQ-004 filterTasks supports project, status, horizon, and search', () => {
  assert.equal(filterTasks(tasks, { project: 'atlas-core' }).length, 1);
  assert.equal(filterTasks(tasks, { status: 'validation' }).length, 1);
  assert.equal(filterTasks(tasks, { horizon: 'Later' }).length, 1);
  assert.equal(filterTasks(tasks, { search: 'github' }).length, 1);
});

test('RQ-004 attentionKinds flags blocked, validation, and active work', () => {
  assert.deepEqual(attentionKinds(tasks), ['blocked', 'validation', 'active']);
});


test('RQ-026 sortTasks orders blocked first, then status and due date', () => {
  const ordered = sortTasks(tasks);
  assert.equal(ordered[0].title, 'Blocked GitHub sync');
  assert.equal(ordered[1].title, 'Adapt Pocket Office avatars');
  assert.equal(ordered[2].title, 'Review sync table depth ordering');
});


const agents = [
  { id: 'orion', name: 'Orion', department: 'Leadership', home_specialist: 'planning', core_skills: ['planning', 'triage'] },
  { id: 'iris', name: 'Iris', department: 'People', home_specialist: 'hr', core_skills: ['hr', 'people', 'policy'] },
  { id: 'mercury', name: 'Mercury', department: 'Intelligence', home_specialist: 'media', core_skills: ['media', 'coverage', 'signals'] },
];

test('RQ-033 matchAgentsToSkill finds agents by core skill and home specialist', () => {
  assert.deepEqual(matchAgentsToSkill(agents, 'hr').map((agent) => agent.id), ['iris']);
  assert.deepEqual(matchAgentsToSkill(agents, 'media').map((agent) => agent.id), ['mercury']);
});

test('RQ-032 groupAgentsByDepartment groups flexible org roles', () => {
  const grouped = groupAgentsByDepartment(agents);
  assert.equal(grouped.People[0].id, 'iris');
  assert.equal(grouped.Intelligence[0].id, 'mercury');
});


test('RQ-036 groupAgentsByManager exposes reporting relationships for multiple managers', () => {
  const grouped = groupAgentsByManager([
    { id: 'ralph', name: 'Ralph', manager: 'codex' },
    { id: 'pixel', name: 'Pixel', manager: 'codex' },
    { id: 'mercury', name: 'Mercury', manager: 'violet' },
  ]);
  assert.deepEqual(grouped.codex.map((agent) => agent.id), ['pixel', 'ralph']);
  assert.deepEqual(grouped.violet.map((agent) => agent.id), ['mercury']);
});
