import test from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_THEME_SETTINGS,
  OPENCLAW_BASE_TOKENS,
  THEME_PRESETS,
  applyThemeState,
  normalizeThemeSettings,
  paletteFor,
  resolveTheme,
} from '../src/lib/theme.js';
import {
  OFFICE_AREA_REQUIREMENTS,
  OFFICE_MOVEMENT_POLICY,
  OFFICE_OBJECT_BOUNDS,
  OFFICE_ZONE_SLOTS,
  bubbleOffset,
  movementShouldSnap,
  normalizeOfficeScene,
  pathIntersectsProtectedBounds,
  slotInsideProtectedBounds,
  reserveOfficePlacements,
  seatAtRectTable,
  sortSpritesByDepth,
  validateOfficePlacements,
} from '../src/lib/office.js';

test('RQ-002 resolveTheme keeps dark, light, and system modes deterministic', () => {
  assert.equal(resolveTheme('dark', true), 'dark');
  assert.equal(resolveTheme('light', false), 'light');
  assert.equal(resolveTheme('system', true), 'light');
  assert.equal(resolveTheme('system', false), 'dark');
});

test('RQ-002 theme presets include official palette families and custom mode', () => {
  assert.ok(THEME_PRESETS.claw);
  assert.ok(THEME_PRESETS.openknot);
  assert.ok(THEME_PRESETS.dash);
  assert.ok(THEME_PRESETS.custom);
  assert.equal(normalizeThemeSettings({ mode: 'oops', preset: 'unknown' }).mode, DEFAULT_THEME_SETTINGS.mode);
});

test('RQ-002 applyThemeState writes theme dataset and accent tokens', () => {
  const styleMap = new Map();
  const doc = {
    documentElement: {
      dataset: {},
      style: { setProperty(name, value) { styleMap.set(name, value); } },
    },
  };
  const result = applyThemeState(doc, { mode: 'light', preset: 'dash', customAccent: '#ff5c5c', customAccent2: '#14b8a6' }, false);
  assert.equal(result.resolved, 'light');
  assert.equal(doc.documentElement.dataset.themeMode, 'light');
  assert.equal(doc.documentElement.dataset.themePalette, 'dash');
  assert.equal(styleMap.get('--accent'), paletteFor({ preset: 'dash' }).accent);
});

test('RQ-002 official base palette matches OpenClaw control-ui tokens', () => {
  assert.equal(OPENCLAW_BASE_TOKENS.dark.bg, '#0e1015');
  assert.equal(OPENCLAW_BASE_TOKENS.dark.accent, '#ff5c5c');
  assert.equal(OPENCLAW_BASE_TOKENS.dark.accent2, '#14b8a6');
  assert.equal(OPENCLAW_BASE_TOKENS.light.bg, '#f8f9fa');
  assert.equal(OPENCLAW_BASE_TOKENS.light.accent, '#dc2626');
});

test('RQ-006 office helper keeps table seats and bubble offsets stable', () => {
  const slots = [{ x: 10, y: 20 }, { x: 20, y: 10 }];
  assert.deepEqual(seatAtRectTable(0, slots), { x: 10, y: 20 });
  assert.deepEqual(seatAtRectTable(2, slots), { x: 10, y: 20 });
  assert.deepEqual(sortSpritesByDepth([{ y: 30 }, { y: 10 }, { y: 20 }]).map((item) => item.y), [10, 20, 30]);
  assert.deepEqual(bubbleOffset('scrum_table', 1), { x: -10, y: -94 });
});

test('RQ-042 office scene toggle normalizes to day/night only', () => {
  assert.equal(normalizeOfficeScene('day'), 'day');
  assert.equal(normalizeOfficeScene('night'), 'night');
  assert.equal(normalizeOfficeScene('weird'), 'day');
});

test('RQ-043 office area catalog includes the required zones', () => {
  const required = ['ceo_strip', 'chief_desk', 'code_pod', 'research_pod', 'ops_pod', 'qa_pod', 'studio_pod', 'scrum_table', 'review_rail', 'board_wall', 'lounge'];
  for (const id of required) {
    assert.ok(OFFICE_AREA_REQUIREMENTS[id], id);
    assert.ok(Array.isArray(OFFICE_ZONE_SLOTS[id]), `${id} slots`);
    assert.ok(OFFICE_ZONE_SLOTS[id].length >= 1, `${id} seat count`);
  }
});

test('RQ-044 collision-safe office placement returns unique non-overlapping seat anchors', () => {
  const agents = [
    { id: 'ceo', target_zone: 'ceo_strip' },
    { id: 'orion', target_zone: 'chief_desk' },
    { id: 'codex', target_zone: 'code_pod' },
    { id: 'violet', target_zone: 'scrum_table' },
    { id: 'charlie', target_zone: 'ops_pod' },
    { id: 'ralph', target_zone: 'review_rail' },
  ];
  const placements = reserveOfficePlacements(agents, OFFICE_ZONE_SLOTS);
  assert.equal(placements.length, agents.length);
  assert.equal(validateOfficePlacements(placements).ok, true);
  const ids = new Set(placements.map((item) => `${item.target.x}:${item.target.y}`));
  assert.equal(ids.size, placements.length);
});



test('RQ-053 CEO Console preset is the default first-run appearance', () => {
  assert.equal(DEFAULT_THEME_SETTINGS.mode, 'dark');
  assert.equal(DEFAULT_THEME_SETTINGS.preset, 'ceo');
  assert.ok(THEME_PRESETS.ceo);
  assert.equal(paletteFor(DEFAULT_THEME_SETTINGS).accent, '#67e8d7');
});

test('RQ-054 office protected bounds keep anchors away from furniture footprints', () => {
  assert.ok(Array.isArray(OFFICE_OBJECT_BOUNDS));
  assert.ok(OFFICE_OBJECT_BOUNDS.length >= 10);
  assert.equal(slotInsideProtectedBounds({ x: 640, y: 250 }), true);
  assert.equal(slotInsideProtectedBounds(OFFICE_ZONE_SLOTS.code_pod[0]), false);
  const placements = reserveOfficePlacements([
    { id: 'ceo', target_zone: 'ceo_strip' },
    { id: 'orion', target_zone: 'chief_desk' },
    { id: 'codex', target_zone: 'code_pod' },
    { id: 'violet', target_zone: 'research_pod' },
  ], OFFICE_ZONE_SLOTS);
  assert.equal(validateOfficePlacements(placements).insideBounds.length, 0);
});

test('RQ-055 office movement policy snaps cross-zone moves and unsafe paths', () => {
  assert.equal(OFFICE_MOVEMENT_POLICY.crossZoneBehavior, 'snap');
  assert.equal(movementShouldSnap('code_pod', 'scrum_table', { x: 188, y: 262 }, { x: 510, y: 214 }), true);
  assert.equal(pathIntersectsProtectedBounds({ x: 430, y: 240 }, { x: 760, y: 240 }), true);
  assert.equal(movementShouldSnap('code_pod', 'code_pod', { x: 188, y: 262 }, { x: 292, y: 262 }), false);
});
