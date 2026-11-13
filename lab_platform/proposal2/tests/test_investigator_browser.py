"""Optional real-browser regression checks; no additional runtime dependencies."""
import json
import os
import shutil
import threading
from unittest.mock import Mock

import pytest
from lab_platform.app import create_app
from lab_platform.proposal2.poisoning_registry import REGISTRY


@pytest.fixture
def browser_lab(tmp_path):
    pw = pytest.importorskip('playwright.sync_api')
    from werkzeug.serving import make_server
    model = Mock()
    model.chat.return_value = 'The approved policy is two years [LK-005].'
    app = create_app({'TESTING': True, 'DATABASE_PATH': str(tmp_path / 'p1.sqlite3')}, client=model)
    server = make_server('127.0.0.1', 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with pw.sync_playwright() as play:
        executable = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
        try:
            browser = play.chromium.launch(executable_path=executable, headless=True)
        except pw.Error as exc:
            server.shutdown()
            pytest.skip(f'Chromium unavailable: {exc}')
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://127.0.0.1:{server.server_port}/proposal-02/poisoning')
        page.wait_for_function("() => document.querySelector('#status').textContent.startsWith('Ready.')")
        try:
            yield page, app, model
        finally:
            browser.close()
            server.shutdown()
            thread.join(timeout=5)
        assert errors == []


def api(page, path):
    return page.evaluate("async path => (await fetch('/proposal-02/poisoning/api/' + path)).json()", path)


def ready(page):
    page.wait_for_function("() => !document.querySelector('#scenario').disabled")


@pytest.mark.parametrize('ident', REGISTRY)
def test_scenario_independent_hints_and_guided_examples(browser_lab, ident):
    page, _, _ = browser_lab
    page.select_option('#scenario', ident)
    ready(page)
    assert page.input_value('#learning-mode') == 'investigator'
    assert page.input_value('#answer') == ''
    assert page.input_value('#question') == ''
    assert page.input_value('#rating') == '3'
    assert page.locator('#investigation-scope').inner_text().startswith('Configured investigation scope: ' + REGISTRY[ident]['target_id'])
    assert not page.locator('#reference').is_visible()
    assert page.locator('#hints li').count() == 0
    for n in range(1, 4):
        page.click('#hint-next')
        assert page.locator('#hints li').count() == n
        assert f'{n} of 3' in page.locator('#hint-count').inner_text()
    if ident == 'DP-004':
        assert 'starlight mode' in page.locator('#hints').inner_text()
    page.fill('#answer', '<img src=x onerror=alert(1)> fictional draft')
    before = api(page, 'state')
    evidence = api(page, 'export')
    page.select_option('#learning-mode', 'guided')
    assert page.locator('#reference').is_visible()
    assert page.input_value('#answer').endswith('fictional draft')
    assert api(page, 'state') == before
    assert api(page, 'export') == evidence
    page.once('dialog', lambda dialog: dialog.dismiss())
    page.click('#use-example')
    assert page.input_value('#answer').endswith('fictional draft')
    page.once('dialog', lambda dialog: dialog.accept())
    page.click('#use-example')
    assert page.input_value('#answer') == REGISTRY[ident]['sample']
    assert page.input_value('#question') == REGISTRY[ident]['target_question']
    page.select_option('#learning-mode', 'investigator')
    page.select_option('#mode', 'hardened')
    ready(page)
    assert '3 of 3' in page.locator('#hint-count').inner_text()
    assert page.input_value('#answer') == REGISTRY[ident]['sample']
    page.reload()
    ready(page)
    assert page.input_value('#mode') == 'hardened'
    assert page.input_value('#answer') == REGISTRY[ident]['sample']
    assert '3 of 3' in page.locator('#hint-count').inner_text()


def test_manual_experiment_notes_export_and_replay(browser_lab, tmp_path):
    page, app, model = browser_lab
    clean_kb = app.extensions['proposal2_kb'].info()
    p1_before = open(app.config['DATABASE_PATH'], 'rb').read()
    page.fill('#question', 'How long is the warranty?')
    page.fill('#answer', 'Fictional warranty claim for three years.')
    page.select_option('#account', 'new')
    page.fill('#rating', '2')
    page.fill('#source', 'student-source')
    page.click('#clean'); ready(page)
    page.locator('#inject button:not([type="button"])').click(); ready(page)
    page.click('#current'); ready(page)
    assert 'Manual review required' in page.locator('#evidence-summary').inner_text()
    vulnerable = api(page, 'state')
    assert vulnerable['records'][0]['answer'] == 'Fictional warranty claim for three years.'
    page.select_option('#mode', 'hardened'); ready(page)
    page.locator('#inject button:not([type="button"])').click(); ready(page)
    page.click('#current'); ready(page)
    assert api(page, 'state')['records'][0]['disposition'] == 'quarantined'
    page.locator('#worksheet-details summary').click()
    notes = '<script>window.untrusted=true</script> & evidence reflection'
    before = api(page, 'export')
    for field in ['hypothesis', 'attack_design', 'observed_evidence', 'defensive_comparison', 'conclusion']:
        page.fill('#note-' + field, notes)
    page.select_option('#learning-mode', 'guided')
    page.select_option('#learning-mode', 'investigator')
    assert page.input_value('#mode') == 'hardened'
    assert api(page, 'export') == before
    assert page.evaluate('window.untrusted') is None
    for selector, suffix in [('#worksheet-json', '.json'), ('#worksheet-export', '.md')]:
        with page.expect_download() as info:
            page.click(selector)
        download = info.value
        path = tmp_path / ('worksheet' + suffix)
        download.save_as(path)
        content = path.read_text()
        if suffix == '.md':
            assert '&lt;script&gt;' in content and '<script>' not in content
        if suffix == '.json':
            doc = json.loads(content)
            assert doc['scenario_id'] == 'DP-001'
            assert doc['guidance_mode'] == 'investigator'
            assert doc['hypothesis'] == notes
            assert len(doc['experiment_identifiers']) == 3
            assert 'account_id' not in content and 'session_id' not in content
    assert notes not in str(model.chat.call_args_list)
    page.reload(); ready(page)
    assert page.input_value('#note-hypothesis') == notes
    page.select_option('#scenario', 'DP-002'); ready(page)
    assert page.input_value('#note-hypothesis') == ''
    page.select_option('#scenario', 'DP-001'); ready(page)
    assert page.input_value('#note-hypothesis') == notes
    page.click('#replay'); ready(page)
    assert page.locator('#comparison table').count() == 1
    assert model.chat.call_count == 6
    page.click('#reset'); ready(page)
    assert api(page, 'state')['records'] == []
    assert page.input_value('#note-hypothesis') == notes
    page.locator('#worksheet-details summary').click()
    page.once('dialog', lambda dialog: dialog.accept())
    page.click('#learning-restart')
    assert page.input_value('#note-hypothesis') == ''
    assert page.input_value('#answer') == 'Fictional warranty claim for three years.'
    assert app.extensions['proposal2_kb'].info() == clean_kb
    assert open(app.config['DATABASE_PATH'], 'rb').read() == p1_before
    page.set_viewport_size({'width': 390, 'height': 1000})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


def test_new_browser_context_isolation(browser_lab):
    page, _, _ = browser_lab
    page.select_option('#learning-mode', 'guided')
    page.select_option('#scenario', 'DP-002'); ready(page)
    assert page.input_value('#answer') == REGISTRY['DP-002']['sample']
    context = page.context.browser.new_context()
    other = context.new_page()
    other.goto(page.url)
    other.wait_for_function("() => document.querySelector('#status').textContent.startsWith('Ready.')")
    assert other.input_value('#learning-mode') == 'investigator'
    assert other.input_value('#answer') == ''
    assert other.input_value('#note-hypothesis') == ''
    assert api(other, 'state')['session_id'] != api(page, 'state')['session_id']
    context.close()
    # A new server session in the same tab also gets the Investigator default.
    page.context.clear_cookies()
    page.reload(); ready(page)
    assert page.input_value('#learning-mode') == 'investigator'
    assert page.input_value('#answer') == ''


def test_storage_failure_keeps_editing_and_exports(browser_lab):
    page, _, _ = browser_lab
    page.add_init_script("Object.defineProperty(window, 'sessionStorage', {get() { throw new Error('disabled'); }});")
    page.reload(); ready(page)
    assert page.locator('#storage-warning').is_visible()
    page.locator('#worksheet-details summary').click()
    page.fill('#note-hypothesis', 'Export this in-memory reflection')
    page.click('#hint-next')
    assert '1 of 3' in page.locator('#hint-count').inner_text()
    with page.expect_download():
        page.click('#worksheet-json')
    assert page.input_value('#note-hypothesis') == 'Export this in-memory reflection'


def test_shared_cookie_tabs_keep_local_worksheets_scoped(browser_lab):
    page, _, _ = browser_lab
    page.locator('#worksheet-details summary').click()
    page.fill('#note-hypothesis', 'Only DP-001 in first tab')
    page.fill('#answer', 'First tab warranty draft')
    other = page.context.new_page()
    other.goto(page.url)
    other.wait_for_function("() => document.querySelector('#status').textContent.startsWith('Ready.')")
    other.select_option('#scenario', 'DP-002'); ready(other)
    other.locator('#worksheet-details summary').click()
    other.fill('#note-hypothesis', 'Only DP-002 in second tab')
    page.click('#refresh'); ready(page)
    assert page.input_value('#scenario') == 'DP-002'
    assert page.input_value('#answer') == ''
    assert page.input_value('#note-hypothesis') == ''
    page.select_option('#scenario', 'DP-001'); ready(page)
    assert page.input_value('#note-hypothesis') == 'Only DP-001 in first tab'
    assert page.input_value('#answer') == 'First tab warranty draft'
    other.close()
