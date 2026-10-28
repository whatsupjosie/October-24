"""The actual host and real Chromium: mini-camera motion and floor slate."""
import httpx
from tests.test_world_walk_host_integration import host, owner, browser, page, signed_in


def test_mini_console_changes_actual_stage_camera(host, signed_in):
    p=signed_in
    p.goto(host+'/static/mini_console.html')
    p.wait_for_function("window.PubCastControlRoom?.client.state?.cameras?.length>0")
    p.select_option('#mini-camera','wide_shot')
    frame=p.frame_locator('#mini-screen')
    frame.locator('canvas').wait_for(timeout=30000)
    p.wait_for_function("document.getElementById('mini-screen').contentWindow.PubCastStageCamera?.getPose().name==='wide'")
    before=p.evaluate("document.getElementById('mini-screen').contentWindow.PubCastStageCamera.getPose()")
    p.locator('#mini-stick').focus();p.keyboard.press('ArrowRight')
    p.wait_for_function("document.getElementById('mini-status').textContent.includes('confirmed')")
    p.wait_for_function("document.getElementById('mini-screen').contentWindow.PubCastStageCamera.getPose().rotation[1] !== "+str(before['rotation'][1]))
    assert not p.problems,p.problems


def test_shared_floor_raised_roll_call_and_editor_controls(host,signed_in,browser,owner):
    p=signed_in
    auth={'Authorization':'Bearer '+owner['access_token']}
    p.goto(host+'/director-console')
    p.wait_for_selector('#pubcast-slate-open:not([hidden])')
    p.click('#pubcast-slate-open')
    p.wait_for_selector('#pubcast-slate-floor:not([hidden])')
    p.fill('#pubcast-slate-floor input[name=scene]','14')
    p.click('[data-action=save]')
    p.wait_for_function("document.querySelector('#pubcast-slate-floor .status').textContent.includes('Saved')")
    p.click('[data-action=standby]')
    p.wait_for_function("document.querySelector('[data-phase]').textContent.includes('ROLL CALL')")
    assert 'closed' not in p.locator('.clacker').get_attribute('class')
    # A second independent screen sees the same raised slate, via global HTML injection.
    q=browser.new_page()
    import json
    q.add_init_script('sessionStorage.setItem("pubcast_token",'+json.dumps(owner['access_token'])+');')
    q.goto(host+'/static/safe_console.html')
    q.wait_for_selector('#pubcast-slate-floor:not([hidden])')
    assert q.input_value('[name=scene]')=='14'
    assert 'closed' not in q.locator('.clacker').get_attribute('class')
    q.close()
    p.click('[data-action=clap]')
    p.wait_for_selector('.clacker.closed')
    r=httpx.get(host+'/api/studio/slate',headers=auth).json()
    assert r['slate']['phase']=='take' and r['slate']['sync_status']=='media_alignment_unverified'
    p.once('dialog',lambda d:d.accept())
    p.click('[data-action=end]')
    p.wait_for_selector('#pubcast-slate-floor[hidden]',state='attached')
    assert not p.problems,p.problems
