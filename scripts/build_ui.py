#!/usr/bin/env python3
"""
ClawTasker UI Build Script v3
Assembles ui/dist/index.html from modular ui/src/ files.
Supports both legacy sections/ and new modules/ structure.
Python-only, no Node.js dependency.
"""
import json, os, re, sys

SRC_DIR = 'ui/src'
DIST_DIR = 'ui/dist'
OUTPUT = os.path.join(DIST_DIR, 'index.html')

def read_file(path):
    with open(path) as f:
        return f.read()

def build(version_override=None):
    manifest = json.loads(read_file(os.path.join(SRC_DIR, 'build-manifest.json')))
    version = version_override or manifest['version']
    
    print(f"Building ClawTasker CEO Console v{version}")
    
    # 1. Head
    head = read_file(os.path.join(SRC_DIR, manifest['html']['head']))
    head = re.sub(r'v\d+\.\d+\.\d+', f'v{version}', head)
    
    # 2. CSS
    css_parts = []
    for css_file in manifest['css']:
        css_parts.append(read_file(os.path.join(SRC_DIR, css_file)))
    css = ''.join(css_parts)
    
    # 3. Body
    body = read_file(os.path.join(SRC_DIR, manifest['html']['body']))
    body = re.sub(r'v\d+\.\d+\.\d+', f'v{version}', body)
    
    # 4. JS — support both sections (legacy) and modules (new)
    js_parts = []
    
    modules_dir = manifest.get('js_modules_dir', 'modules')
    for js_file in manifest['js_modules']:
        js_path = os.path.join(SRC_DIR, modules_dir, js_file)
        if os.path.exists(js_path):
            js_parts.append(read_file(js_path))
        else:
            print(f"  WARNING: {js_path} missing!")
    print(f"  Loaded {len(manifest['js_modules'])} JS modules from {modules_dir}/")
    
    js = ''.join(js_parts)
    
    # 5. Tail
    tail = read_file(os.path.join(SRC_DIR, manifest['html']['tail']))
    
    # 6. Assemble
    output = head + '<style>\n' + css + '</style>\n' + body + '<script>\n' + js + '</script>\n' + tail
    
    os.makedirs(DIST_DIR, exist_ok=True)
    with open(OUTPUT, 'w') as f:
        f.write(output)
    
    lines = output.count('\n') + 1
    funcs = len(re.findall(r'^function ', output, re.MULTILINE))
    print(f"Built: {OUTPUT} ({len(output):,} bytes, {lines} lines, {funcs} functions)")
    return OUTPUT

if __name__ == '__main__':
    version = sys.argv[1] if len(sys.argv) > 1 else None
    build(version)
