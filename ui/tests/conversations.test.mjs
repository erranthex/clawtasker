import test from 'node:test';
import assert from 'node:assert/strict';
import {
  categoryBadgeLabel,
  hiddenConversationCount,
  latestTranscriptReference,
  normalizeConversationCategory,
  normalizeConversationSource,
  officialChannelHref,
  sourceBadgeLabel,
  threadPolicyLabel,
  threadSummaryOnly,
  visibleConversationMessages,
} from '../src/lib/conversations.js';

test('RQ-046 source badges normalize official conversation channels', () => {
  assert.equal(normalizeConversationSource('browser_chat'), 'browser');
  assert.equal(normalizeConversationSource('tg'), 'telegram');
  assert.equal(normalizeConversationSource('session'), 'internal_session');
  assert.equal(sourceBadgeLabel('discord'), 'Discord');
});

test('RQ-048 directive and discussion categories stay separate in the UI model', () => {
  assert.equal(normalizeConversationCategory('message'), 'discussion');
  assert.equal(normalizeConversationCategory('directive'), 'directive');
  assert.equal(categoryBadgeLabel('summary'), 'Summary');
});

test('RQ-049 official channel links prefer explicit urls and otherwise fall back to OpenClaw-style routes', () => {
  assert.equal(officialChannelHref({ official_channel_url: 'https://example.test/thread/42' }), 'https://example.test/thread/42');
  assert.equal(officialChannelHref({ official_channel_source: 'telegram', session_key: 'tg:ops' }), 'http://127.0.0.1:18789/#/channels/telegram?sessionKey=tg:ops');
});

test('RQ-050 subagent threads default to summaries only and hide raw internal discussion until requested', () => {
  const thread = {
    mode: 'chief-specialist',
    participants: ['orion', 'codex'],
    messages: [
      { id: '1', source: 'internal_session', category: 'directive', text: 'Do the work' },
      { id: '2', source: 'internal_session', category: 'discussion', text: 'Raw details', hidden_by_default: true },
      { id: '3', source: 'internal_session', category: 'summary', text: 'Outcome summary' },
    ],
  };
  assert.equal(threadSummaryOnly(thread), true);
  assert.equal(visibleConversationMessages(thread).length, 2);
  assert.equal(hiddenConversationCount(thread), 1);
  assert.equal(threadPolicyLabel(thread), 'Subagent summaries only');
});

test('RQ-051 transcript references surface session, run, and path from the latest relevant message', () => {
  const ref = latestTranscriptReference({
    official_channel_url: 'http://127.0.0.1:18789/#/sessions?sessionKey=session:codex',
    messages: [
      { id: '1', source: 'browser', category: 'discussion', text: 'Hi' },
      { id: '2', source: 'internal_session', category: 'summary', text: 'Done', session_key: 'session:codex', run_id: 'run-22', transcript_path: '~/.openclaw/sessions/session-codex.jsonl', transcript_url: 'http://127.0.0.1:18789/#/sessions?sessionKey=session:codex' },
    ],
  });
  assert.equal(ref.session_key, 'session:codex');
  assert.equal(ref.run_id, 'run-22');
  assert.match(ref.transcript_path, /session-codex/);
  assert.match(ref.transcript_url, /sessionKey=session:codex/);
});
