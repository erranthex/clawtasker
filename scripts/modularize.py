#!/usr/bin/env python3
"""
ClawTasker Modularization Script - Phase 4+
Extracts the monolith ui/dist/index.html into modular source files
in ui/src/ and creates a build pipeline to reassemble.
"""
import os, re, sys

MONOLITH = 'ui/dist/index.html'
SRC_DIR = 'ui/src'

def read_monolith():
    with open(MONOLITH) as f:
        return f.readlines()

def extract_range(lines, start, end):
    """Extract lines[start-1:end-1] (1-indexed, inclusive)"""
    return lines[start-1:end]

def find_boundaries(lines):
    """Find CSS, HTML body, and JS boundaries"""
    bounds = {}
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s == '<style>': bounds['css_start'] = i
        elif s == '</style>': bounds['css_end'] = i
        elif s == '<script>': bounds['js_start'] = i
        elif s == '</script>': bounds['js_end'] = i
    bounds['html_start'] = bounds['css_end'] + 1
    bounds['html_end'] = bounds['js_start'] - 1
    return bounds

def find_js_sections(lines, js_start, js_end):
    """Find all // ── Section ── markers"""
    sections = []
    for i in range(js_start, js_end):
        line = lines[i-1]
        if line.startswith('// ── '):
            name = line.strip()
            # Clean name
            name = re.sub(r'^// ── ', '', name)
            name = re.sub(r' ─+$', '', name)
            name = name.strip()
            sections.append((i, name))
    # Add end boundary
    sections.append((js_end, '__END__'))
    return sections

def get_section_content(lines, sections, name):
    """Get content of a named section"""
    for idx, (line_num, sec_name) in enumerate(sections):
        if sec_name == name:
            next_line = sections[idx+1][0]
            return ''.join(lines[line_num:next_line-1])
    return ''

def get_section_range(sections, name):
    """Get (start, end) line numbers for a section"""
    for idx, (line_num, sec_name) in enumerate(sections):
        if sec_name == name:
            next_line = sections[idx+1][0]
            return (line_num, next_line - 1)
    return None

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f'  Created: {path} ({len(content)} bytes)')

def extract_modules():
    lines = read_monolith()
    bounds = find_boundaries(lines)
    sections = find_js_sections(lines, bounds['js_start'], bounds['js_end'])
    
    print(f"Monolith: {len(lines)} lines")
    print(f"CSS:  {bounds['css_start']}-{bounds['css_end']}")
    print(f"HTML: {bounds['html_start']}-{bounds['html_end']}")
    print(f"JS:   {bounds['js_start']}-{bounds['js_end']}")
    print(f"Sections found: {len(sections)-1}")
    print()
    
    # === EXTRACT CSS ===
    print("=== Extracting CSS ===")
    css_content = ''.join(lines[bounds['css_start']:bounds['css_end']-1])
    write_file(f'{SRC_DIR}/styles/monolith.css', css_content)
    
    # === EXTRACT HTML TEMPLATE ===
    print("\n=== Extracting HTML template ===")
    # Head (before <style>)
    head = ''.join(lines[0:bounds['css_start']-1])
    # Body (between </style> and <script>)
    body = ''.join(lines[bounds['css_end']:bounds['js_start']-1])
    # Tail (after </script>)
    tail = ''.join(lines[bounds['js_end']:])
    write_file(f'{SRC_DIR}/templates/head.html', head)
    write_file(f'{SRC_DIR}/templates/body.html', body)
    write_file(f'{SRC_DIR}/templates/tail.html', tail)
    
    # === EXTRACT JS MODULES ===
    # Map section names to target module files
    module_map = {
        # data/
        'data/constants.js': ['Data'],
        # state/
        'state/store.js': ['State'],
        # lib/
        'lib/router.js': ['Nav'],
        'lib/dom.js': ['Util'],
        'lib/theme.js': ['Mode'],
        'lib/office-engine.js': [
            'Helper: pick a free slot from a list',
            'initCanvasOffice',
            'Main game tick',
            'Pick next destination for an agent',
            'Draw a sprite',
            'Draw speech bubble above agent',
            'Tooltip on click',
            'Public controls',
        ],
        # views/
        'views/dashboard.js': [
            'Dashboard',
            'Capability matrix',
            'Project health',
            'Export snapshot',
            'Active focus period dashboard card',
            'Directives trail',
            'Notifications',
        ],
        'views/team.js': [
            'Org chart',
            'Agent roster',
            'Sprite modal',
            'Org config',
        ],
        'views/board.js': [
            'Board',
            'Sprint management',
        ],
        'views/missions.js': ['Mission planner'],
        'views/conversations.js': ['Conversations'],
        'views/calendar.js': ['Calendar'],
        'views/office.js': ['Office'],
        'views/access.js': ['Access matrix'],
        'views/appearance.js': ['Appearance'],
        'views/requirements.js': ['Requirements & Test Cases (v1.2.0)'],
        # ui/
        'ui/modals.js': [
            'Task modal',
            'Task creation',
        ],
        'ui/onboarding.js': ['Platform onboarding modal'],
        'ui/api.js': ['Live API wiring (Option A)'],
        # init
        'init.js': ['Init'],
    }
    
    print("\n=== Extracting JS modules ===")
    extracted_sections = set()
    for module_path, section_names in module_map.items():
        content_parts = []
        for sec_name in section_names:
            sec_content = get_section_content(lines, sections, sec_name)
            if sec_content:
                content_parts.append(sec_content)
                extracted_sections.add(sec_name)
            else:
                print(f'  WARNING: Section "{sec_name}" not found!')
        
        if content_parts:
            full_content = '\n'.join(content_parts)
            write_file(f'{SRC_DIR}/{module_path}', full_content)
    
    # Check for unextracted sections
    all_sections = set(name for _, name in sections if name != '__END__')
    missed = all_sections - extracted_sections
    if missed:
        print(f"\n  WARNING: Unextracted sections: {missed}")
    
    # === CREATE BUILD MANIFEST ===
    print("\n=== Creating build manifest ===")
    # The order matters for concatenation!
    build_order = [
        'data/constants.js',
        'state/store.js',
        'lib/router.js',
        'lib/dom.js',
        'lib/theme.js',
        'views/dashboard.js',
        'views/team.js',
        'views/board.js',
        'ui/modals.js',
        'views/missions.js',
        'views/conversations.js',
        'views/calendar.js',
        'views/office.js',
        'views/access.js',
        'views/appearance.js',
        'views/requirements.js',
        'lib/office-engine.js',
        'ui/onboarding.js',
        'ui/api.js',
        'init.js',
    ]
    
    manifest = {
        'version': '1.4.0',
        'css': ['styles/monolith.css'],
        'html': {
            'head': 'templates/head.html',
            'body': 'templates/body.html', 
            'tail': 'templates/tail.html',
        },
        'js_order': build_order,
    }
    
    import json
    write_file(f'{SRC_DIR}/build-manifest.json', json.dumps(manifest, indent=2))
    
    print("\nExtraction complete!")
    return bounds, sections

if __name__ == '__main__':
    extract_modules()
