"""Release requirements tests for ClawTasker CEO Console v1.0.5.

These tests verify that:
- All versioned docs exist for the current VERSION string
- All vendored assets are present (v9 only - v4/brick-edition removed in v1.0.5)
- ui/src source files exist (ui/dist is gitignored and not checked)
- web/ (legacy static serving layer) exists
- README reflects current version and all key feature phrases
- openclaw companion files are present and well-formed
- docs/ARCHITECTURE.md is present (new in v1.0.5)
- Sprint, dependency, notification, and directive features are covered
"""
import json
import unittest
from pathlib import Path

import server


class ReleaseRequirementsTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(server.__file__).resolve().parent
        self.version = (self.root / 'VERSION').read_text(encoding='utf-8').strip()
        self.version_tag = self.version.replace('.', '_').replace('-', '_')

    # ------------------------------------------------------------------
    # Version consistency
    # ------------------------------------------------------------------

    def test_version_file_matches_server_constant(self):
        """VERSION file and server.APP_VERSION must be identical."""
        self.assertEqual(self.version, server.APP_VERSION)

    def test_version_is_1_0_5(self):
        """This release is v1.0.5."""
        self.assertEqual(self.version, '1.0.5')

    def test_readme_declares_correct_version(self):
        readme = (self.root / 'README.md').read_text(encoding='utf-8')
        self.assertIn('**Version:** 1.0.5', readme)

    def test_package_metadata_version_is_current(self):
        pkg = json.loads((self.root / 'ui' / 'package.json').read_text(encoding='utf-8'))
        self.assertEqual(pkg['dependencies']['vite'], '8.0.0')
        self.assertEqual(pkg['dependencies']['lit'], '^3.3.2')

    # ------------------------------------------------------------------
    # Versioned documentation
    # ------------------------------------------------------------------

    def test_requirement_docs_exist(self):
        tag = self.version_tag
        self.assertTrue((self.root / 'docs' / f'REQUIREMENTS_v{tag}.md').exists())
        self.assertTrue((self.root / 'docs' / f'TEST_TRACEABILITY_v{tag}.md').exists())

    def test_regression_and_test_results_exist(self):
        tag = self.version_tag
        self.assertTrue((self.root / 'docs' / f'REGRESSION_REPORT_v{tag}.md').exists())
        self.assertTrue((self.root / 'docs' / f'TEST_RESULTS_v{tag}.txt').exists())

    def test_pocket_office_mapping_manifest_exists(self):
        tag = self.version_tag
        self.assertTrue((self.root / 'docs' / f'POCKET_OFFICE_MAPPING_v{tag}.json').exists())

    def test_build_render_artifacts_exist(self):
        docs = self.root / 'docs'
        tag = self.version_tag
        for name in [
            f'render_app_layout_v{tag}.png',
            f'render_office_v{tag}.png',
            f'render_office_night_v{tag}.png',
            f'render_office_floor_v{tag}.png',
            f'render_avatars_v{tag}.png',
            f'render_palette_v{tag}.png',
            f'render_team_v{tag}.png',
            f'ClawTasker_CEO_Console_Guide_v{tag}.pdf',
        ]:
            self.assertTrue((docs / name).exists(), f'Missing: {name}')

    # ------------------------------------------------------------------
    # Evergreen docs (new in v1.0.5 structure)
    # ------------------------------------------------------------------

    def test_architecture_doc_exists(self):
        """ARCHITECTURE.md is a new evergreen doc added in v1.0.5."""
        self.assertTrue((self.root / 'docs' / 'ARCHITECTURE.md').exists())

    def test_agent_api_docs_and_schema_exist(self):
        self.assertTrue((self.root / 'docs' / 'AGENT_API_GUIDE.md').exists())
        self.assertTrue((self.root / 'docs' / 'AGENT_PROMPTS.md').exists())
        self.assertTrue((self.root / 'schemas' / 'agent_register.schema.json').exists())
        guide = (self.root / 'docs' / 'AGENT_API_GUIDE.md').read_text(encoding='utf-8').lower()
        self.assertIn('/api/agents/register', guide)
        self.assertIn('name, role, and skills', guide)
        self.assertIn('company chart', guide)

    def test_mission_plan_schema_and_agent_guide_references_exist(self):
        self.assertTrue((self.root / 'schemas' / 'mission_plan.schema.json').exists())
        guide = (self.root / 'docs' / 'AGENT_API_GUIDE.md').read_text(encoding='utf-8').lower()
        self.assertIn('/api/missions/plan', guide)
        self.assertIn('/api/schema/mission-plan', guide)
        self.assertIn('shared mission brief', guide)

    # ------------------------------------------------------------------
    # Vendor assets — v9 only (v4 and brick-edition removed in v1.0.5)
    # ------------------------------------------------------------------

    def test_vendor_v9_pack_is_complete(self):
        v9 = self.root / 'third_party' / 'pocket-office-quest-v9'
        self.assertTrue((v9 / 'assets' / 'avatars' / 'aria-portrait.png').exists())
        self.assertTrue((v9 / 'src' / 'engine.js').exists())
        self.assertTrue((v9 / 'src' / 'render.js').exists())
        self.assertTrue((v9 / 'compat' / 'office-layout-day.png').exists())
        self.assertTrue((v9 / 'compat' / 'office-layout-night.png').exists())

    def test_vendor_v9_only_in_third_party(self):
        """Only pocket-office-quest-v9 is kept in third_party/.
        v4 and brick-edition have been removed: v9 is the active version and
        the only one whose characters are used by the office renderer.
        """
        self.assertTrue((self.root / 'third_party' / 'pocket-office-quest-v9').exists(),
                        'pocket-office-quest-v9 must be present')
        self.assertFalse((self.root / 'third_party' / 'pocket-office-quest-v4').exists(),
                         'pocket-office-quest-v4 must be removed — v9 supersedes it')
        self.assertFalse((self.root / 'third_party' / 'pocket-office-quest-brick-edition').exists(),
                         'pocket-office-quest-brick-edition must be removed — v9 is the active version')

    def test_avatar_mapping_has_no_duplicate_values(self):
        """Every app agent should map to a unique v9 character where possible.
        v9 has 12 characters for 14 agents, so exactly 2 sharing pairs are
        unavoidable. The allowed pairs are:
          - iris + ledger → mina  (both back-office / people-ops roles)
          - scout + mercury → zara (both analyst / research-domain roles)
        No other duplicates are permitted.
        """
        state = server.default_state()
        mapping = state['asset_library']['avatar_mapping']
        # Remove the _note metadata key if present
        char_map = {k: v for k, v in mapping.items() if not k.startswith('_')}

        from collections import Counter
        counts = Counter(char_map.values())
        duplicates = {char: count for char, count in counts.items() if count > 1}

        # Only the two sanctioned sharing pairs are allowed
        self.assertIn('mina', duplicates,
            'mina should be shared between iris and ledger')
        self.assertIn('zara', duplicates,
            'zara should be shared between scout and mercury')
        self.assertEqual(len(duplicates), 2,
            f'Exactly 2 shared characters allowed, found: {duplicates}')

        # Verify the correct agents share the correct characters
        mina_agents = sorted(k for k, v in char_map.items() if v == 'mina')
        zara_agents = sorted(k for k, v in char_map.items() if v == 'zara')
        self.assertEqual(mina_agents, ['iris', 'ledger'],
            f'mina should be shared by iris+ledger, got {mina_agents}')
        self.assertEqual(zara_agents, ['mercury', 'scout'],
            f'zara should be shared by scout+mercury, got {zara_agents}')

    def test_avatar_mapping_all_characters_exist_in_v9(self):
        """Every v9 character referenced in avatar_mapping must have
        both a portrait and a sprite sheet in third_party/pocket-office-quest-v9/.
        """
        state = server.default_state()
        mapping = state['asset_library']['avatar_mapping']
        v9_avatars = self.root / 'third_party' / 'pocket-office-quest-v9' / 'assets' / 'avatars'
        for agent, char in mapping.items():
            if agent.startswith('_'):
                continue
            self.assertTrue((v9_avatars / f'{char}-portrait.png').exists(),
                f'Missing v9 portrait for {agent} → {char}')
            self.assertTrue((v9_avatars / f'{char}-sheet.png').exists(),
                f'Missing v9 sprite sheet for {agent} → {char}')

    # ------------------------------------------------------------------
    # UI source files (ui/src — ui/dist is gitignored)
    # ------------------------------------------------------------------

    def test_ui_source_files_exist(self):
        self.assertTrue((self.root / 'ui' / 'src' / 'main.ts').exists())
        self.assertTrue((self.root / 'ui' / 'src' / 'ui' / 'app.ts').exists())
        self.assertTrue((self.root / 'ui' / 'vite.config.ts').exists())
        self.assertTrue((self.root / 'ui' / 'src' / 'styles' / 'layout.mobile.css').exists())

    def test_web_legacy_serving_layer_exists(self):
        """web/ is the committed static bundle served by server.py."""
        self.assertTrue((self.root / 'web' / 'index.html').exists())
        self.assertTrue((self.root / 'web' / 'app.js').exists())

    # ------------------------------------------------------------------
    # data/ — only .gitkeep, no live state
    # ------------------------------------------------------------------

    def test_data_state_file_is_absent_from_repo(self):
        """state.json must not be committed — it is in .gitignore.

        Note: importing server.py during this test run creates state.json as a
        side-effect of server initialisation.  We therefore verify the policy
        via .gitignore rather than requiring physical absence at test time.
        """
        gi = (self.root / '.gitignore').read_text(encoding='utf-8')
        self.assertIn('data/state.json', gi,
            'data/state.json must be listed in .gitignore')

    def test_gitignore_covers_state_and_dist(self):
        gi = (self.root / '.gitignore').read_text(encoding='utf-8')
        self.assertIn('data/state.json', gi)
        self.assertIn('ui/dist/', gi)

    # ------------------------------------------------------------------
    # GitHub / repo hygiene files
    # ------------------------------------------------------------------

    def test_github_ready_files_exist(self):
        self.assertTrue((self.root / '.github' / 'PULL_REQUEST_TEMPLATE.md').exists())
        self.assertTrue((self.root / '.github' / 'workflows' / 'regression.yml').exists())
        self.assertTrue((self.root / 'LICENSE').exists())
        self.assertTrue((self.root / 'README.md').exists())
        self.assertTrue((self.root / 'CHANGELOG.md').exists())

    # ------------------------------------------------------------------
    # Server state shape
    # ------------------------------------------------------------------

    def test_state_includes_workspace_asset_library_platform_and_office_contract(self):
        state = server.default_state()
        self.assertIn('company', state)
        self.assertIn('ceo', state['company'])
        self.assertGreaterEqual(len(state['access_matrix']), 1)
        self.assertIn('github_flow', state)
        self.assertIn('asset_library', state)
        self.assertIn('platform_contract', state)
        self.assertIn('office_layout', state)
        self.assertTrue(state['platform_contract']['visualization_only'])

    def test_default_ui_settings_and_office_policy(self):
        state = server.default_state()
        self.assertEqual(state['ui_defaults']['theme_preset'], 'ceo')
        self.assertEqual(state['ui_defaults']['theme_mode'], 'dark')
        self.assertEqual(state['office_layout']['movement_policy']['cross_zone_behavior'], 'snap')
        self.assertTrue(state['office_layout']['movement_policy']['respect_protected_bounds'])
        self.assertGreaterEqual(len(state['office_layout']['object_bounds']), 10)

    # ------------------------------------------------------------------
    # v1.0.5 new features — sprint, dependency, notification, directive
    # ------------------------------------------------------------------

    def test_sprints_key_in_default_state(self):
        """Sprint system added in v1.0.5 — default state must include sprints key."""
        state = server.default_state()
        self.assertIn('sprints', state)
        self.assertIsInstance(state['sprints'], list)

    def test_notifications_key_in_default_state(self):
        """Notification inbox added in v1.0.5."""
        state = server.default_state()
        self.assertIn('notifications', state)
        self.assertIsInstance(state['notifications'], list)

    def test_task_has_depends_on_and_story_points_fields(self):
        """Tasks now carry depends_on and story_points added in v1.0.5."""
        state = server.default_state()
        tasks = state.get('tasks', [])
        self.assertGreater(len(tasks), 0, 'default_state should include at least one task')
        t = tasks[0]
        self.assertIn('depends_on', t)
        self.assertIn('story_points', t)

    def test_project_has_type_field(self):
        """Project type system added in v1.0.5."""
        state = server.default_state()
        projects = state.get('projects', [])
        self.assertGreater(len(projects), 0)
        self.assertIn('type', projects[0])

    # ------------------------------------------------------------------
    # Requirements document phrase coverage
    # ------------------------------------------------------------------

    def test_requirements_document_mentions_core_platform_phrases(self):
        req = (self.root / 'docs' / f'REQUIREMENTS_v{self.version_tag}.md').read_text(encoding='utf-8')
        for phrase in [
            'Visualization-first role',
            'OpenClaw subagent boundary alignment',
            'Restart-safe behavior',
            'Error handling and degraded recovery',
            'System health and recovery center',
            'Agent publish contract visibility',
            'OpenClaw latest release compatibility',
            'OpenClaw publish ingress',
            'Live update channel',
            'Ticket lifecycle integrity',
            'Deterministic task ordering',
            'Idempotent OpenClaw publish dedupe',
            'Ticket system health visibility',
            'Agent roster scalability',
            'OpenClaw roster synchronization',
            'Flexible organisation templates',
            'Core-skill-aligned routing',
            'Scale-aware office rendering',
            'Manager-linked company chart',
            'Multiple managers and reporting relationships',
            'Manager and team metadata in OpenClaw roster sync',
            'Large virtual company scaling',
            'Pocket Office v9 compatibility pack',
            'Visible-face roster cards',
            'Office seat and depth mechanics',
            'Office scene toggle',
            'Office area catalog',
            'Collision-safe office placement',
            'Layout-respecting office movement',
            'Conversation source badges',
            'Official channel handoff',
            'Directive versus discussion split',
            'Subagent summaries by default',
            'Audit-safe transcript linking',
            'Default CEO Console palette',
            'Protected office object bounds',
            'Object-safe office movement policy',
            'agent self-registration contract',
            'Company-chart identity visibility',
            'Mission Control prompt pack',
            'Agent API guide',
        ]:
            self.assertIn(phrase, req, f'Missing phrase in requirements: {phrase!r}')

    def test_requirements_document_mentions_mission_planning_surfaces(self):
        req = (self.root / 'docs' / f'REQUIREMENTS_v{self.version_tag}.md').read_text(encoding='utf-8')
        for phrase in [
            'Mission-plan contract',
            'Shared mission brief',
            'Staffing and coverage',
            'Risk and dependency radar',
            'Mission-linked task management',
        ]:
            self.assertIn(phrase, req, f'Missing mission phrase: {phrase!r}')

    def test_requirements_document_mentions_v1_0_5_features(self):
        """New v1.0.5 features must appear in the requirements document."""
        req = (self.root / 'docs' / f'REQUIREMENTS_v{self.version_tag}.md').read_text(encoding='utf-8')
        for phrase in [
            'Sprint',
            'story point',
            'dependency',
            'notification',
            'directive',
            'project type',
            'workload',
        ]:
            self.assertIn(phrase.lower(), req.lower(), f'Missing v1.0.5 phrase: {phrase!r}')

    def test_requirements_mentions_official_channels_and_summary_mode(self):
        req = (self.root / 'docs' / f'REQUIREMENTS_v{self.version_tag}.md').read_text(encoding='utf-8').lower()
        self.assertIn('official channels', req)
        self.assertIn('summaries only', req)
        self.assertIn('transcript linking', req)

    # ------------------------------------------------------------------
    # README phrase coverage
    # ------------------------------------------------------------------

    def test_readme_mentions_key_features(self):
        readme = (self.root / 'README.md').read_text(encoding='utf-8').lower()
        for phrase in [
            'roster-sync bridge',
            'day / night office scene',
            'collision-safe',
            'which manager coordinates which team',
            'source badges',
            'directive vs discussion',
            'summaries only',
            'ceo console palette',
            'object bounds',
            'agent self-registration',
            '/api/agents/register',
            'agent api guide',
            'mission control onboarding prompt pack',
            '/api/missions/plan',
            'mission brief',
            'staffing and coverage',
            'openclaw/update_mission_plan.py',
        ]:
            self.assertIn(phrase, readme, f'README missing phrase: {phrase!r}')

    def test_readme_mentions_v1_0_5_features(self):
        readme = (self.root / 'README.md').read_text(encoding='utf-8').lower()
        for phrase in [
            'sprint',
            'story point',
            'depend',
            'notification',
            'directive',
            'project type',
            'workload',
        ]:
            self.assertIn(phrase, readme, f'README missing v1.0.5 phrase: {phrase!r}')

    def test_readme_mentions_repository_layout_section(self):
        """README now documents the repo structure (new in v1.0.5)."""
        readme = (self.root / 'README.md').read_text(encoding='utf-8')
        self.assertIn('Repository layout', readme)

    # ------------------------------------------------------------------
    # OpenClaw companion files
    # ------------------------------------------------------------------

    def test_openclaw_companion_files_exist(self):
        oc = self.root / 'openclaw'
        self.assertTrue((oc / 'publish_status.py').exists())
        self.assertTrue((oc / 'publish_roster.py').exists())
        self.assertTrue((oc / 'register_agent.py').exists())
        self.assertTrue((oc / 'update_mission_plan.py').exists())
        self.assertTrue((oc / 'skills' / 'clawtasker-publish' / 'SKILL.md').exists())
        self.assertTrue((oc / 'skills' / 'clawtasker-roster-sync' / 'SKILL.md').exists())
        self.assertTrue((oc / 'skills' / 'clawtasker-register' / 'SKILL.md').exists())
        self.assertTrue((oc / 'skills' / 'clawtasker-mission-plan' / 'SKILL.md').exists())
        self.assertTrue((oc / 'prompts' / 'mission-control' / 'README.md').exists())
        self.assertTrue((oc / 'prompts' / 'mission-control' / '01-existing-sub-agents-prompt.md').exists())
        self.assertTrue((oc / 'prompts' / 'mission-control' / '02-new-sub-agents-prompt.md').exists())
        self.assertTrue((oc / 'prompts' / 'mission-control' / '03-mission-control-orchestrator-agent-prompt.md').exists())

    def test_openclaw_config_example_has_required_fields(self):
        config = (self.root / 'openclaw' / 'openclaw.json5.example').read_text(encoding='utf-8')
        self.assertIn('defaultSessionKey: "hook:clawtasker"', config)
        self.assertIn('allowRequestSessionKey: false', config)
        self.assertIn('allowedAgentIds', config)
        self.assertIn('visibility: "tree"', config)
        self.assertIn('agentToAgent', config)
        self.assertIn('cron:', config)

    def test_openclaw_readme_mentions_current_release(self):
        readme = (self.root / 'openclaw' / 'README.md').read_text(encoding='utf-8')
        self.assertIn('2026.3.13', readme)
        self.assertIn('v2026.3.13-1', readme)

    def test_openclaw_readme_mentions_helpers_and_prompt_pack(self):
        readme = (self.root / 'openclaw' / 'README.md').read_text(encoding='utf-8').lower()
        self.assertIn('register_agent.py', readme)
        self.assertIn('name, role, and skills', readme)
        self.assertIn('prompts/mission-control', readme)
        self.assertIn('docs/agent_api_guide.md', readme)
        self.assertIn('update_mission_plan.py', readme)
        self.assertIn('shared mission brief', readme)
        self.assertIn('mission-planning', readme)

    def test_openclaw_roster_helper_references_correct_endpoint(self):
        helper = (self.root / 'openclaw' / 'publish_roster.py').read_text(encoding='utf-8')
        self.assertIn('/api/openclaw/roster_sync', helper)
        self.assertIn('openclaw-agents-list', helper)


if __name__ == '__main__':
    unittest.main()
