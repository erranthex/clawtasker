#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
VTAG = VERSION.replace('.', '_').replace('-', '_')
OUT = DOCS / f'ClawTasker_CEO_Console_Guide_v{VTAG}.pdf'
IMG_APP = DOCS / f'render_app_layout_v{VTAG}.png'
IMG_OFFICE = DOCS / f'render_office_v{VTAG}.png'
IMG_OFFICE_NIGHT = DOCS / f'render_office_night_v{VTAG}.png'
IMG_FLOOR = DOCS / f'render_office_floor_v{VTAG}.png'
IMG_AVATARS = DOCS / f'render_avatars_v{VTAG}.png'
IMG_PALETTE = DOCS / f'render_palette_v{VTAG}.png'
IMG_TEAM = DOCS / f'render_team_v{VTAG}.png'

PALETTE = {
    'night': colors.HexColor('#0e1015'),
    'deck': colors.HexColor('#171b24'),
    'paper': colors.HexColor('#f8f9fa'),
    'ink': colors.HexColor('#111827'),
    'muted': colors.HexColor('#64748b'),
    'line': colors.HexColor('#d6d9df'),
    'line_dark': colors.HexColor('#2e3040'),
    'accent': colors.HexColor('#ff5c5c'),
    'mint': colors.HexColor('#14b8a6'),
    'gold': colors.HexColor('#f59e0b'),
}

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='GuideTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=28, leading=31, textColor=PALETTE['paper'], alignment=TA_LEFT, spaceAfter=8))
styles.add(ParagraphStyle(name='GuideSubtitle', parent=styles['BodyText'], fontName='Helvetica', fontSize=11, leading=15, textColor=colors.HexColor('#c7d4e6'), spaceAfter=10))
styles.add(ParagraphStyle(name='SectionTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=17, leading=21, textColor=PALETTE['ink'], spaceBefore=10, spaceAfter=8))
styles.add(ParagraphStyle(name='Body', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.1, leading=14.2, textColor=PALETTE['ink'], spaceAfter=7))
styles.add(ParagraphStyle(name='BodyDark', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.0, leading=14.0, textColor=PALETTE['paper'], spaceAfter=7))
styles.add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontName='Helvetica', fontSize=8.4, leading=11.6, textColor=PALETTE['muted'], spaceAfter=4))
styles.add(ParagraphStyle(name='CodeBlock', parent=styles['Code'], fontName='Courier', fontSize=8.3, leading=10.6, textColor=PALETTE['ink']))


def bullets(lines: list[str], style_name: str = 'Body'):
    return [Paragraph(f'- {line}', styles[style_name]) for line in lines]


def caption(text: str) -> Paragraph:
    return Paragraph(text, styles['Small'])


def code_block(text: str) -> Preformatted:
    return Preformatted(text.strip('\n'), styles['CodeBlock'], maxLineLength=96)


def scaled_image(path: Path, width: float, max_height: float) -> RLImage:
    img = RLImage(str(path))
    img.drawWidth = width
    ratio = img.imageHeight / float(img.imageWidth)
    img.drawHeight = width * ratio
    if img.drawHeight > max_height:
        img.drawHeight = max_height
        img.drawWidth = max_height / ratio
    return img


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PALETTE['muted'])
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 10 * mm, f'ClawTasker CEO Console {VERSION} - Page {canvas.getPageNumber()}')
    canvas.restoreState()


def header_card(doc_width: float) -> Table:
    title = Paragraph('ClawTasker CEO Console', styles['GuideTitle'])
    subtitle = Paragraph('Release candidate focused on a modernized CEO Console shell, mission planning for shared briefs and staffing/risk visibility, agent self-registration for the company chart, Pocket Office Quest v9 day/night office scenes, protected office-object bounds, and a thin operator conversation rail aligned to OpenClaw channels and transcripts.', styles['GuideSubtitle'])
    meta = Table([[Paragraph(f'<b>Release</b><br/>{VERSION}', styles['BodyDark']), Paragraph('<b>OpenClaw target</b><br/>2026.3.13 / v2026.3.13-1', styles['BodyDark']), Paragraph('<b>Runtime role</b><br/>Visualization companion with restart-safe local recovery', styles['BodyDark'])]], colWidths=[doc_width/3]*3)
    meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#13151b')),
        ('BOX', (0, 0), (-1, -1), 1, PALETTE['line_dark']),
        ('INNERGRID', (0, 0), (-1, -1), 1, PALETTE['line_dark']),
        ('LEFTPADDING', (0, 0), (-1, -1), 12), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    card = Table([[title], [subtitle], [Spacer(1, 4)], [meta]], colWidths=[doc_width])
    card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PALETTE['night']),
        ('LEFTPADDING', (0, 0), (-1, -1), 18), ('RIGHTPADDING', (0, 0), (-1, -1), 18),
        ('TOPPADDING', (0, 0), (-1, -1), 14), ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
    ]))
    return card


def build() -> None:
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=14*mm, bottomMargin=16*mm, title='ClawTasker CEO Console Guide', author='OpenAI')
    story = []
    story.append(header_card(doc.width))
    story.append(Spacer(1, 10))
    story.append(scaled_image(IMG_APP, doc.width, 104 * mm))
    story.append(Spacer(1, 4))
    story.append(caption('Figure 1. OpenClaw-style shell with grouped navigation, Appearance controls, system health, and CEO-facing workflow views.'))

    story.append(PageBreak())
    story.append(Paragraph('1. Executive summary', styles['SectionTitle']))
    story.extend(bullets([
        'ClawTasker remains a standalone local-first product: one Python server plus a prebuilt static frontend bundle, with no runtime cloning or migrations.',
        'This release candidate focuses on a screenshot-aligned CEO Console shell, first-class mission planning, Pocket Office Quest v9 character integration, visible-face roster cards, agent self-registration for company-chart visibility, deterministic office-area placement, protected office-object bounds, day/night office scenes, and a thin operator conversation rail built on top of OpenClaw-native channels/transcripts.',
        'The platform boundary remains explicit: ClawTasker is a visualization and collaboration companion, while OpenClaw keeps routing, sessions, subagents, and workspaces.',
        'The office is deterministic and token-free: task state drives desk, sync-table, and review-rail placement without using an LLM for animation, and movement now respects protected furniture bounds.',
        'The release package includes updated requirements, traceability, regression tests, raw results, renders, a PDF guide, a mission-planning assessment, an agent API guide, a Mission Control prompt pack, and an OpenClaw companion pack with explicit conversation-source/channel metadata plus inspectable office layout rules.',
    ]))

    story.append(Spacer(1, 8))
    story.append(Paragraph('2. Pocket Office Quest v9 integration', styles['SectionTitle']))
    story.append(Paragraph('The supplied Pocket Office Quest v9 character pack is vendored directly into the release, while the shell now boots into the CEO Console palette by default. ClawTasker adapts the portraits for roster/profile views, builds office sprite strips from the supplied sheets, and generates compatible day/night office layouts so the runtime can expose office-scene switching even though the supplied archive does not include standalone office background bitmaps.', styles['Body']))
    story.append(scaled_image(IMG_OFFICE, doc.width, 86 * mm))
    story.append(Spacer(1, 4))
    story.append(caption('Figure 2. Day office scene with deterministic zone placement, visible status labels, and manager/specialist presence.'))
    if IMG_OFFICE_NIGHT.exists():
        story.append(Spacer(1, 10))
        story.append(scaled_image(IMG_OFFICE_NIGHT, doc.width, 86 * mm))
        story.append(Spacer(1, 4))
        story.append(caption('Figure 3. Night office scene using the same roster state and office-area layout with alternate lighting.'))

    story.append(PageBreak())
    story.append(Paragraph('3. Office areas and movement rules', styles['SectionTitle']))
    story.extend(bullets([
        'The office is organized into explicit zones and protected object bounds: CEO strip, chief desk, engineering pod, research pod, ops pod, QA pod, studio pod, sync table, review rail, board wall, and lounge.',
        'Working agents stay in desk pods, coordination moves agents to the sync table, and validation moves agents to the review rail.',
        'Placement is collision-safe: visible agents receive unique seat anchors, protected furniture bounds are exposed in the snapshot, and the regression suite validates that office placements do not overlap or spawn inside office objects.',
        'The office engine respects layout intent rather than freeform wandering, keeping the view readable for a human operator.',
    ]))
    story.append(scaled_image(IMG_FLOOR, doc.width, 86 * mm))
    story.append(Spacer(1, 4))
    story.append(caption('Figure 4. Full office floor showing day/night layout compatibility assets and named office areas.'))

    story.append(PageBreak())
    story.append(Paragraph('4. Visible-face roster and company structure', styles['SectionTitle']))
    story.append(Paragraph('Portraits and office sprites come from the Pocket Office Quest v9 adaptation pipeline. The roster render emphasizes readable faces, larger hero poses, and directional rows, while the company chart supports the human CEO, the chief agent, multiple managers, and synced specialist roles such as HR, Purchasing, or Media Analysis.', styles['Body']))
    story.append(scaled_image(IMG_AVATARS, doc.width, 92 * mm))
    story.append(Spacer(1, 4))
    story.append(caption('Figure 5. Visible-face roster cards with readable portraits, hero poses, and directional sprite strips derived from the v9 pack.'))
    story.append(Spacer(1, 8))
    story.append(scaled_image(IMG_TEAM, doc.width, 82 * mm))
    story.append(Spacer(1, 4))
    story.append(caption('Figure 6. CEO -> chief agent -> manager lanes -> specialist teams using the integrated Pocket Office v9 avatar family.'))

    story.append(PageBreak())
    story.append(Paragraph('5. OpenClaw alignment and operator boundary', styles['SectionTitle']))
    story.extend(bullets([
        'OpenClaw remains the source of truth for agent creation through agents.list-style infrastructure; ClawTasker receives roster sync envelopes and lightweight self-registration payloads over a dedicated local API.',
        'The OpenClaw bridge is local-first and restart-safe: if ClawTasker restarts, agents continue working and can republish status later.',
        'Task lifecycle guardrails remain in place: deterministic ordering, validator enforcement, owner validation, retry-safe publish dedupe, and mission-linked task tracking.',
        'The office view is intentionally bounded for readability and performance; the Team view remains authoritative for larger rosters.',
    ]))
    matrix = Table([
        ['Metric', 'Meaning'],
        ['Open items', 'All tasks not yet in done'],
        ['Mission coverage', 'Coverage of required specialists on the focus mission'],
        ['Open risks', 'Current mission risks that are still open or unmitigated'],
        ['Assignment drift', 'Active tasks whose owner is not currently aligned in the roster'],
        ['Missing validators', 'Validation/done tasks lacking a validator'],
        ['Roster sync', 'Last synced roster metadata published from OpenClaw infrastructure'],
        ['Office overflow', 'Agents beyond the office visual capacity that remain visible through Team filters'],
        ['Publish dedupe', 'Seconds during which an identical OpenClaw publish envelope is treated as a retry'],
    ], colWidths=[48 * mm, doc.width - 48 * mm])
    matrix.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PALETTE['night']), ('TEXTCOLOR', (0, 0), (-1, 0), PALETTE['paper']),
        ('GRID', (0, 0), (-1, -1), 0.7, PALETTE['line']),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(matrix)

    story.append(Spacer(1, 8))
    story.append(Paragraph('6. Conversation rail and official channels', styles['SectionTitle']))
    story.extend(bullets([
        'Conversation source badges show whether a thread or message came from browser chat, Telegram, Discord, a webhook, or an internal OpenClaw session.',
        'The conversation surface is intentionally thin: directives and discussion are separated, and subagent-to-subagent threads default to summaries only unless a human chooses to reveal more detail.',
        'Where available, each thread exposes official-channel handoff links plus session key, run ID, transcript path, and transcript URL references so audit trails stay tied to OpenClaw rather than being duplicated here.',
        'This keeps Mission Control focused on human visibility and collaboration while OpenClaw remains the runtime communication engine for agent work.',
    ]))

    story.append(Spacer(1, 8))
    story.append(Paragraph('7. Appearance, palette, and office scenes', styles['SectionTitle']))
    story.append(Paragraph('The shell follows the OpenClaw palette direction and grouped shell proportions while refreshing the dashboard to match the supplied command-center reference more closely. The Appearance view includes mode, palette family, accent tuning, CEO profile controls, and a persistent office scene selector.', styles['Body']))
    story.append(scaled_image(IMG_PALETTE, doc.width, 72 * mm))
    story.append(Spacer(1, 4))
    story.append(caption('Figure 7. OpenClaw-style shell palette tokens plus office day/night scene switching.'))

    story.append(Spacer(1, 8))
    story.append(Paragraph('8. Run and validate', styles['SectionTitle']))
    story.append(Paragraph('Start the app with one command, then open the loopback URL in a browser.', styles['Body']))
    story.append(code_block('''
export CLAWTASKER_API_TOKEN="replace-this-with-a-strong-local-token"
python3 server.py
'''))
    story.append(Spacer(1, 6))
    story.append(Paragraph('Open:', styles['Body']))
    story.append(code_block('''
http://127.0.0.1:3000
'''))
    story.append(Spacer(1, 8))
    story.append(Paragraph('Validation commands:', styles['Body']))
    story.append(code_block('''
python3 scripts/adapt_pocket_office_release.py
python3 scripts/build_static_ui.py
python3 docs/build_guide.py
python3 -m py_compile server.py
python3 -m unittest discover -s tests -v
node --test ui/tests/*.test.mjs
bash scripts/smoke_test.sh
'''))

    story.append(Spacer(1, 8))
    story.append(Paragraph('9. Publication package', styles['SectionTitle']))
    story.extend(bullets([
        'The repo includes README, MIT license, changelog, security policy, contributing guide, support notes, and GitHub issue/PR templates.',
        'The release ZIP includes the OpenClaw companion pack, the vendored Pocket Office Quest v9 character library, the Mission Control prompt pack, the agent API guide, requirements, traceability, renders, the regression report, and raw test results.',
        'This release candidate is intended for validation of the v9 office/roster integration while staying compatible with the latest stable OpenClaw line.',
    ]))

    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)


if __name__ == '__main__':
    build()
