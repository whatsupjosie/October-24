"""Exercise getUserMedia -> floor socket -> listener WebAudio with a fake test mic."""
import json
import pytest
from tests.test_world_walk_host_integration import host, owner


def test_real_browser_capture_reaches_listener_and_stops_on_dismiss(host,owner):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(args=['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
        context=browser.new_context(permissions=['microphone'])
        context.add_init_script('sessionStorage.setItem("pubcast_token",'+json.dumps(owner['access_token'])+');')
        context.add_init_script('''
          window.__floorAudioStarts=0;window.__floorMaxSample=0;
          const start=AudioBufferSourceNode.prototype.start;
          AudioBufferSourceNode.prototype.start=function(...args){
            window.__floorAudioStarts++;
            if(this.buffer){for(const v of this.buffer.getChannelData(0))window.__floorMaxSample=Math.max(window.__floorMaxSample,Math.abs(v));}
            return start.apply(this,args);
          };
          if(navigator.mediaDevices){const get=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
          navigator.mediaDevices.getUserMedia=async(...args)=>{const s=await get(...args);window.__testFloorStream=s;return s;};}
        ''')
        try:
            director=context.new_page();director.goto(host+'/director-console')
            director.locator('#pubcast-slate-open:not([hidden])').click()
            director.locator('[data-action=standby]').click()
            director.wait_for_function("document.querySelector('[data-phase]').textContent.includes('ROLL CALL')")
            listener=context.new_page();listener.goto(host+'/static/safe_console.html')
            listener.locator('#pubcast-slate-floor:not([hidden])').wait_for()
            listener.click('[data-action=listen]')
            director.click('[data-action=mic]')
            director.wait_for_function("document.querySelector('[data-action=mic]').textContent.includes('Stop')",timeout=10000)
            listener.wait_for_function('window.__floorAudioStarts>0 && window.__floorMaxSample>.001',timeout=20000)
            director.click('[data-action=hide]')
            director.wait_for_function('window.__testFloorStream.getTracks().every(t=>t.readyState==="ended")')
        finally:
            context.close();browser.close()
