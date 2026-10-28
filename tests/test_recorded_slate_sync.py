"""Decode actual media and verify offsets in both directions, preserving originals."""
import hashlib
import shutil
import subprocess
import wave
from pathlib import Path
import numpy as np
import pytest
from modules.recorded_slate_sync import measure, align, SyncError


def fixture_media(folder: Path, offset: float, *, cue=True):
    if not shutil.which('ffmpeg'):pytest.skip('FFmpeg unavailable')
    rate=48000;samples=np.zeros(rate*3,dtype=np.float32)
    if cue:
        start=round((1+offset)*rate);t=np.arange(1440)/rate
        samples[start:start+1440]=.3*np.sin(2*np.pi*1500*t)*np.exp(np.log(.001/.3)*t/.03)
    with wave.open(str(folder/'audio.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((samples*32767).astype('<i2').tobytes())
    path=folder/'input.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=black:s=320x240:r=30:d=3','-i',str(folder/'audio.wav'),
        '-vf',"drawbox=x=0:y=0:w=64:h=64:color=white:t=fill:enable='between(t,1,1.1)'",'-c:v','libx264','-c:a','aac','-y',str(path)],check=True)
    return path


@pytest.mark.parametrize('offset',[.20,-.16,0.0])
def test_encoded_artifacts_are_measured_and_corrected(tmp_path,offset):
    source=fixture_media(tmp_path,offset);digest=hashlib.sha256(source.read_bytes()).hexdigest()
    measured=measure(source)
    assert abs(measured['audio_minus_video_ms']-offset*1000)<15
    report=align(source,tmp_path/'aligned.mp4')
    assert report['status']=='verified_recorded_cue'
    assert report['after']['within_tolerance']
    assert abs(report['after']['audio_minus_video_ms'])<40
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest


def test_missing_audio_mark_cannot_be_certified(tmp_path):
    source=fixture_media(tmp_path,0,cue=False)
    with pytest.raises(SyncError,match='cue'):
        align(source,tmp_path/'aligned.mp4')
    assert not (tmp_path/'aligned.mp4').exists()


def test_section_render_handles_silent_preroll_and_keeps_reference_out_of_mix(tmp_path):
    import json
    from modules.recorded_slate_sync import render_edits
    source=fixture_media(tmp_path,0)
    shutil.copyfile(source,tmp_path/'aligned.mp4')
    rate=48000;tracks=[]
    for name in ['dialogue','music','sfx','ui','vtr','room','floor','reference']:
        channels=1 if name in {'floor','reference'} else 2
        data=np.zeros((rate*3,channels))
        if name in {'music','reference'}:
            freq=440 if name=='music' else 1500;t=np.arange(rate*2)/rate
            data[rate//2:rate//2+rate*2,:]=(.1*np.sin(2*np.pi*freq*t))[:,None]
        with wave.open(str(tmp_path/('stem-'+name+'.wav')),'wb') as w:
            w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes((data*32767).astype('<i2').tobytes())
        tracks.append({'name':name,'channels':channels,'sample_rate':rate,'sample_frames':rate*3})
    (tmp_path/'stems.json').write_text(json.dumps({'tracks':tracks,'audio_to_video_offset_seconds':.1,'timeline_origin_seconds':.04}))
    (tmp_path/'edits.json').write_text(json.dumps({'sections':{'0':{'music':.005}},'enabled_tracks':['music']}))
    report=render_edits(tmp_path)
    assert report['reference_in_program_mix'] is False and report['video_stream_copied'] is True
    samples=subprocess.check_output(['ffmpeg','-v','error','-i',str(tmp_path/'final.mp4'),'-map','0:a:0','-ac','1','-ar',str(rate),'-f','f32le','-'])
    data=np.frombuffer(samples,dtype='<f4');window=data[rate:rate*2];spec=np.abs(np.fft.rfft(window));freq=np.fft.rfftfreq(len(window),1/rate)
    assert abs(freq[int(np.argmax(spec))]-440)<2
    assert spec[np.argmin(abs(freq-1500))]<spec.max()*.01
