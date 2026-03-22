#!/usr/bin/env python3
"""
ClawTasker v1.5.0 Build Verification & Regression Test Suite
Runs all BOM, structural, and functional checks.
Exit code 0 = all pass, 1 = failures detected.
"""
import os, re, sys, json

PASS = 0
FAIL = 0
TOTAL = 0

def check(name, condition):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")

def read_file(path):
    with open(path) as f:
        return f.read()

def main():
    global PASS, FAIL, TOTAL

    print("=" * 60)
    print("ClawTasker CEO Console — Build Verification")
    print("=" * 60)

    # Load built HTML
    html = read_file('ui/dist/index.html')
    version = read_file('VERSION').strip()
    
    print(f"\nVersion: {version}")
    print(f"Build size: {len(html):,} bytes")

    # === CRITICAL PATH FILES ===
    print("\n--- Critical Path Files ---")
    check("server.py exists", os.path.exists('server.py'))
    check("ui/dist/index.html exists", os.path.exists('ui/dist/index.html'))
    check("VERSION exists", os.path.exists('VERSION'))
    check("ui/dist/assets/styles.css exists", os.path.exists('ui/dist/assets/styles.css'))
    check("ui/dist/logo.svg exists", os.path.exists('ui/dist/logo.svg'))
    check(".gitignore exists", os.path.exists('.gitignore'))
    check("No stale web/ directory", not os.path.exists('web'))
    check("ui/dist/GENERATED.md exists", os.path.exists('ui/dist/GENERATED.md'))
    
    # === VERSION ALIGNMENT ===
    print("\n--- Version Alignment ---")
    check(f"VERSION file = {version}", version == '1.5.0')
    check(f"index.html title contains v{version}", f'v{version}' in html)
    
    # Server version
    server = read_file('server.py')
    # Check server has version reference
    check("server.py references APP_VERSION", 'APP_VERSION' in server)
    
    # WEB_DIR
    check("server.py WEB_DIR → ui/dist", "WEB_DIR = ROOT / 'ui' / 'dist'" in server)

    # === BUILD PIPELINE ===
    print("\n--- Build Pipeline ---")
    check("scripts/build_ui.py exists", os.path.exists('scripts/build_ui.py'))
    manifest_path = 'ui/src/build-manifest.json'
    check("build-manifest.json exists", os.path.exists(manifest_path))
    
    manifest = json.loads(read_file(manifest_path))
    check(f"manifest version = {version}", manifest['version'] == version)
    check(f"manifest has {len(manifest['js_modules'])} modules", len(manifest['js_modules']) == 22)
    check("main.js is last module", manifest['js_modules'][-1] == 'main.js')
    
    # === MODULES ===
    print("\n--- JS Modules ---")
    modules_dir = os.path.join('ui/src/modules', manifest.get('js_modules_dir', ''))
    for mod in manifest['js_modules']:
        mod_path = os.path.join('ui/src/modules', mod)
        check(f"module {mod}", os.path.exists(mod_path))
    
    # === ASSETS ===
    print("\n--- Portraits ---")
    agents = ['ceo','charlie','codex','echo','iris','ledger','mercury','orion','pixel','quill','ralph','scout','shield','violet']
    for a in agents:
        check(f"portrait {a}", os.path.exists(f'ui/dist/assets/portraits/{a}.png'))
    
    print("\n--- Sprites ---")
    for a in agents:
        check(f"sprite {a}", os.path.exists(f'ui/dist/assets/sprites/{a}.png'))
    
    print("\n--- Textures ---")
    textures = os.listdir('ui/dist/assets/textures/')
    check(f"textures count ≥ 23 (got {len(textures)})", len(textures) >= 23)
    
    print("\n--- Vendor ---")
    vendor_count = sum(1 for _ in _walk_files('ui/dist/assets/vendor/pocket-office-quest-v9'))
    check(f"vendor files ≥ 50 (got {vendor_count})", vendor_count >= 50)
    
    # === CSS VERIFICATION ===
    print("\n--- CSS Checks ---")
    css = read_file('ui/dist/assets/styles.css')
    check("sprite-avatar-frame in styles.css", 'sprite-avatar-frame' in css)
    check("--sprite-url in styles.css", '--sprite-url' in css)
    
    # === BUILT HTML STRUCTURAL CHECKS ===
    print("\n--- HTML Structure ---")
    funcs = re.findall(r'^function (\w+)', html, re.MULTILINE)
    check(f"functions >= 120 (got {len(funcs)})", len(funcs) >= 120)
    
    # View containers
    print("\n--- View Containers ---")
    views = ['V_dash','V_team','V_council','V_cal','V_board','V_pipeline','V_approvals','V_miss','V_conv','V_off','V_acc','V_req','V_tc','V_app']
    for v in views:
        check(f"container {v}", v in html)
    
    # Key constants
    print("\n--- Key Constants ---")
    for c in ['GAME_W','GAME_ZONES','FURNITURE_RECTS','STATUS_DOT','HOME_ZONE','AGENTS','TASKS','PT','SPR','HEADS','DAY_MAP','NIGHT_MAP','META']:
        check(f"const/let {c}", c in html)
    
    # Key functions
    print("\n--- Key Functions ---")
    key_fns = ['goV','buildDashboard','buildOrg','buildRoster','renderBoard','buildMissions',
               'renderThread','renderCal','buildOffice','initCanvasOffice','offTick',
               '_drawSprite','_pickNextDestination','buildAccess','applyMode','openTask',
               'confirmDecommission','exportSnapshot','buildCouncil','renderPipeline','buildApprovals','openAddAgentForm','submitNewTaskModal','openTaskEdit','editCouncilEntry','deleteCalEvent','deleteMission','refreshCounters']
    for fn in key_fns:
        check(f"function {fn}()", f'function {fn}(' in html)
    
    # Dependency ordering
    print("\n--- Dependency Order ---")
    check("AGENTS before buildDashboard", html.find('const AGENTS=[') < html.find('function buildDashboard'))
    check("META before goV", html.find('const META=') < html.find('function goV'))
    check("GAME_W before initCanvasOffice", html.find('const GAME_W') < html.find('function initCanvasOffice'))
    check("main.js documentation present", 'main.js' in html)
    
    # === PROJECT DIRECTORIES ===
    print("\n--- Project Directories ---")
    for d in ['scripts','tests','schemas','openclaw','docs','third_party','ui/src','ui/public','ui/tests']:
        count = sum(1 for _ in _walk_files(d))
        check(f"{d}/ ({count} files)", count > 0)
    
    # === CLEANUP VERIFICATION ===
    print("")
    print("--- Cleanup Verification ---")
    check("No {data,schemas}/ stray dir", not os.path.exists('{data,schemas}'))
    check("No .DS_Store files", not any(f.endswith('.DS_Store') for f in _all_files('.')))
    check("No stale ui/src/main.ts", not os.path.exists('ui/src/main.ts'))
    check("No stale ui/src/legacy/", not os.path.exists('ui/src/legacy'))
    check("No stale ui/src/lib/ (outside modules)", not os.path.exists('ui/src/lib'))
    check("No stale ui/src/views/ (outside modules)", not os.path.exists('ui/src/views'))
    check("No stale ui/src/ui/ (outside modules)", not os.path.exists('ui/src/ui'))
    check("No stale ui/src/data/ (outside modules)", not os.path.exists('ui/src/data'))
    check("No stale ui/src/state/ (outside modules)", not os.path.exists('ui/src/state'))
    check("Single canonical source: ui/src/modules/", os.path.exists('ui/src/modules/main.js'))
    check("schemas/database.sql exists", os.path.exists('schemas/database.sql'))

    # === v1.3.0 FEATURE CHECKS ===
    print("\n--- v1.3.0 Features ---")
    check("FURNITURE_RECTS defined", 'FURNITURE_RECTS' in html)
    check("kitchen zone", '"kitchen"' in html)
    check("conference zone", '"conference"' in html)
    check("Enhanced labels (statusText)", 'statusText' in html)
    check("Missing agent detection (isStale)", 'isStale' in html)
    check("Face-av CSS fix (center 15%)", 'center 15%' in html)
    check("Speech bubbles all statuses", 'Focused' in html and 'Break' in html)
    
    # === SUMMARY ===
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS}/{TOTAL} passed, {FAIL} failed")
    print("=" * 60)
    
    return 0 if FAIL == 0 else 1

def _all_files(directory):
    result = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            result.append(os.path.join(root, f))
    return result

def _walk_files(directory):
    """Walk directory yielding file paths"""
    for root, dirs, files in os.walk(directory):
        for f in files:
            yield os.path.join(root, f)

if __name__ == '__main__':
    sys.exit(main())
