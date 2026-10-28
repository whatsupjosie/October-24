"""A real browser records the real stage, then FFmpeg verifies the encoded take."""
from tests.test_world_walk_host_integration import host, owner, browser, page, signed_in


def test_stage_take_roundtrip_is_measured_from_actual_recording(host,signed_in,owner,tmp_path):
    p=signed_in;p.goto(host+'/director-console')
    p.frame_locator('iframe[title="Program stage recording source"]').locator('canvas').wait_for()
    p.locator('#pubcast-slate-open:not([hidden])').click()
    p.click('[data-action=standby]')
    p.wait_for_function("document.querySelector('[data-phase]').textContent.includes('ROLL CALL')")
    p.click('[data-action=record-take]')
    p.locator('#pubcast-stop-take:not([hidden])').wait_for()
    p.evaluate('''() => {
      const runtime=document.querySelector('iframe[title="Program stage recording source"]').contentWindow.PubcastProgramAudio;
      for(const [bus,freq] of [['music',440],['dialogue',660],['sfx',880]]){
        const context=runtime.ensureContext(),source=context.createOscillator(),gain=context.createGain();
        source.frequency.value=freq;gain.gain.value=.025;source.connect(gain).connect(runtime.buses.get(bus).gain);source.start();source.stop(context.currentTime+3);
      }
    }''')
    p.click('[data-action=clap]');p.wait_for_selector('.clacker.closed');p.click('[data-action=hide]')
    p.wait_for_function('window.PubCastSlate.getTiming()?.checkpoints.length>=2',timeout=25000)
    with p.expect_download() as original:
        p.click('#pubcast-stop-take')
    assert original.value.suggested_filename.endswith('.webm')
    p.wait_for_function('window.PubCastSlate.getTakeResult()!==null',timeout=90000)
    report=p.evaluate('window.PubCastSlate.getTakeResult()')
    assert report['status']=='verified_recorded_cue',report
    assert report['after']['within_tolerance'],report
    assert report['aligned_url'] and report['original_sha256']
    p.get_by_role('link',name='Open take timeline',exact=True).wait_for(timeout=90000)
    import httpx,json,subprocess,wave
    auth={'Authorization':'Bearer '+owner['access_token']}
    prefix=host+report['original_url'].rsplit('/',1)[0]
    timing=httpx.get(prefix+'/timing',headers=auth).json()
    assert timing['cadence_seconds']==15 and len(timing['checkpoints'])>=2
    assert timing['periodic_audio_added'] is False
    assert timing['cadence_seconds']==15
    edit=tmp_path/'editing.mp4';edit.write_bytes(httpx.get(prefix+'/editing',headers=auth).content)
    streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(edit)]))['streams']
    audio=[s for s in streams if s['codec_type']=='audio']
    assert len(audio)==9 and audio[0]['disposition']['default']==1 and all(s['disposition']['default']==0 for s in audio[1:])
    reference=tmp_path/'reference.wav';reference.write_bytes(httpx.get(prefix+'/stem-reference',headers=auth).content)
    import numpy as np
    with wave.open(str(reference)) as wav:
        rate=wav.getframerate();samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2')
    point=timing['checkpoints'][1]
    stems=httpx.get(prefix+'/stems',headers=auth).json()
    at=15+stems['reference_cue_seconds']-timing['clap_audio_seconds']
    assert np.max(np.abs(samples[max(0,int((at-.05)*rate)):int((at+.05)*rate)]))>1000
    at=15+stems['timeline_origin_seconds']
    program=subprocess.check_output(['ffmpeg','-v','error','-i',str(edit),'-map','0:a:0','-af',f'atrim=start={at-.05}:end={at+.05}','-f','f32le','-'])
    assert np.max(np.abs(np.frombuffer(program,dtype='<f4')))<.001  # no recurring blip in the program mix

    p.get_by_role('link',name='Open take timeline',exact=True).wait_for(timeout=90000)
    stems=httpx.get(prefix+'/stems',headers=auth).json()
    assert stems['shared_sample_clock'] is True and len(stems['tracks'])==8
    assert len({(t['sample_rate'],t['sample_frames']) for t in stems['tracks']})==1
    assert stems['markers_in_picture'] is False
    for name,frequency in [('music',440),('dialogue',660),('sfx',880)]:
        file=tmp_path/(name+'.wav');file.write_bytes(httpx.get(prefix+'/stem-'+name,headers=auth).content)
        with wave.open(str(file)) as wav:
            sample_rate=wav.getframerate();data=np.frombuffer(wav.readframes(sample_rate*2),dtype='<i2').reshape(-1,2)[:,0]
        spectrum=np.abs(np.fft.rfft(data));peak=np.fft.rfftfreq(len(data),1/sample_rate)[int(np.argmax(spectrum))]
        assert abs(peak-frequency)<3,(name,peak)

    p.get_by_role('link',name='Open take timeline',exact=True).click()
    p.wait_for_function('document.querySelectorAll(".track").length===8')
    assert not p.get_by_role('checkbox',name='Enable Sync Reference',exact=True).is_checked()
    p.wait_for_function('document.querySelectorAll("#lanes .tick").length>=2')
    music=p.locator('.track').filter(has=p.get_by_text('Music',exact=True))
    music.get_by_role('button',name='+5 ms',exact=True).click()
    p.click('#save');p.wait_for_function('document.getElementById("status").textContent.includes("decisions saved")')
    assert httpx.get(prefix+'/edits',headers=auth).json()['sections']['0']['music']==.005
    with p.expect_download(timeout=90000) as final:
        p.click('#render')
    assert final.value.suggested_filename.endswith('-final.mp4')
    assert p.problems==[],p.problems
