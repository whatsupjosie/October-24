"""Measure and align a recorded slate's reserved visual and 1500 Hz audio marks.

Verification applies to this encoded artifact, not the latency of other devices.
Original recordings are never overwritten. Missing/ambiguous marks fail closed.
"""
from __future__ import annotations
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
import numpy as np


class SyncError(ValueError):
    pass


def run(args, *, timeout=90):
    try:
        result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise SyncError('Media analysis unavailable or timed out') from exc
    if result.returncode:
        raise SyncError('Media could not be decoded or aligned')
    return result


def measure(path: Path, *, limit=120):
    ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        raise SyncError('FFmpeg and ffprobe are required for recorded sync verification')
    safe_input=['-protocol_whitelist','file,pipe','-format_whitelist','matroska,webm,mov,mp4,m4a,3gp,3g2,mj2']
    probe=json.loads(run([ffprobe,'-v','error',*safe_input,'-show_streams','-of','json',str(path)]).stdout)
    videos=[s for s in probe['streams'] if s['codec_type']=='video']
    audios=[s for s in probe['streams'] if s['codec_type']=='audio']
    if len(videos)!=1 or len(audios)!=1 or min(videos[0]['width'],videos[0]['height'])<64:
        raise SyncError('One video and one audio stream, with a reserved 64px marker, are required')
    rate=videos[0].get('avg_frame_rate','30/1')
    num,den=map(float,rate.split('/'));fps=num/den if den else 0
    if not math.isfinite(fps) or not 1<=fps<=120:
        fps = 0
    # The recorder reserves this corner as black except for the clap. Metadata
    # retains decoded frame timestamps; it does not infer timing from wall time.
    video=run([ffmpeg,'-v','error',*safe_input,'-copyts','-i',str(path),'-t',str(limit),'-an',
        '-vf','crop=64:64:0:0,signalstats,metadata=print:file=-','-f','null','-']).stdout.decode(errors='replace')
    frames=[];at=None
    for line in video.splitlines():
        m=re.search(r'pts_time:([0-9.eE+\-]+)',line)
        if m:at=float(m[1])
        if 'lavfi.signalstats.YAVG=' in line and at is not None:
            frames.append((at,float(line.rsplit('=',1)[1])))
    if not fps:
        intervals=np.diff([at for at,_ in frames]);intervals=intervals[intervals>0]
        if not len(intervals):raise SyncError('No measurable video frame cadence')
        fps=float(1/np.median(intervals))
        if not 1<=fps<=120:raise SyncError('Unsupported video frame cadence')
    marks=[];previous=False
    for at,value in frames:
        bright=value>180
        if bright and not previous:marks.append(at)
        previous=bright
    if not marks or not frames or frames[0][1]>40:
        raise SyncError('Expected an initial white clap marker after a black lead-in')
    sample_rate=48000
    raw=run([ffmpeg,'-v','error',*safe_input,'-copyts','-i',str(path),'-t',str(limit),'-vn',
        '-af','aresample=async=1:first_pts=0','-ac','1','-ar',str(sample_rate),'-f','f32le','-']).stdout
    samples=np.frombuffer(raw,dtype='<f4')
    if not len(samples) or not np.all(np.isfinite(samples)):
        raise SyncError('No decodable audio')
    # Correlate the known exponentially decaying cue near the visual mark.
    # Phase-independent quadrature handles codec phase shifts and rejects speech.
    count=1440;t=np.arange(count)/sample_rate;envelope=np.exp(np.log(.001/.3)*t/.03)
    sin=np.sin(2*np.pi*1500*t)*envelope;cos=np.cos(2*np.pi*1500*t)*envelope
    start=max(0,int((marks[0]-2)*sample_rate));end=min(len(samples),int((marks[0]+2)*sample_rate))
    window=samples[start:end]
    if len(window)<count:raise SyncError('Audio cue search window is too short')
    real=np.correlate(window,sin,'valid');imag=np.correlate(window,cos,'valid')
    score=np.hypot(real,imag);index=int(np.argmax(score));power=float(np.dot(window[index:index+count],window[index:index+count]))
    confidence=float(score[index]/math.sqrt(max(power,1e-12)*float(np.dot(sin,sin))))
    if confidence<.65 or float(score[index])<1:
        raise SyncError('A distinct 1500 Hz slate cue was not found')
    audio_at=(start+index)/sample_rate;offset=audio_at-marks[0]
    return {'video_marker_seconds':marks[0],'audio_marker_seconds':audio_at,
        'audio_minus_video_ms':round(offset*1000,3),'confidence':round(confidence,4),
        'frame_rate':fps,'tolerance_ms':round(1000/fps+5,3),
        'within_tolerance':abs(offset)*1000<=1000/fps+5}


def align(original: Path, output: Path):
    if original.resolve()==output.resolve() or output.exists():
        raise SyncError('An unused output path is required; originals are preserved')
    before=measure(original);offset=before['audio_minus_video_ms']/1000
    if abs(offset)>2:raise SyncError('Offset is outside the supported correction window')
    video_delay=max(0,offset);audio_delay=max(0,-offset)
    ffmpeg=shutil.which('ffmpeg')
    try:
        run([ffmpeg,'-v','error','-protocol_whitelist','file,pipe','-format_whitelist','matroska,webm,mov,mp4,m4a,3gp,3g2,mj2','-copyts','-i',str(original),'-map','0:v:0','-map','0:a:0',
            '-vf',f'setpts=PTS+{video_delay:.9f}/TB',
            '-af',f'adelay={round(audio_delay*48000)}S:all=1',
            '-fps_mode','cfr','-r','30','-c:v','libx264','-preset','veryfast','-crf','18','-c:a','aac','-b:a','192k',
            '-movflags','+faststart','-n',str(output)])
        after=measure(output)
        if not after['within_tolerance']:
            raise SyncError('Corrected artifact failed measured sync tolerance')
        return {'status':'verified_recorded_cue','scope':'this_artifact_only','before':before,'after':after,
                'correction':{'video_delay_ms':round(video_delay*1000,3),'audio_delay_ms':round(audio_delay*1000,3)}}
    except Exception:
        output.unlink(missing_ok=True)
        raise


def stem_manifest(folder: Path):
    """All PCM stems share sample frames; anchor them using the captured sync cue."""
    import wave
    names=['dialogue','music','sfx','ui','vtr','room','floor','reference']
    tracks=[];reference=None;layout=None
    for name in names:
        file=folder/('stem-'+name+'.wav')
        if not file.is_file():raise SyncError('Missing captured stem: '+name)
        with wave.open(str(file)) as wav:
            shape=(wav.getframerate(),wav.getnframes())
            if layout is not None and shape!=layout:raise SyncError('Audio stems do not share the same sample clock and length')
            layout=shape
            if name=='reference':reference=np.frombuffer(wav.readframes(min(wav.getnframes(),wav.getframerate()*120)),dtype='<i2').astype(float)/32768
            tracks.append({'name':name,'channels':wav.getnchannels(),'sample_rate':shape[0],'sample_frames':shape[1],
                           'default_muted':name=='reference'})
    report=json.loads((folder/'sync.json').read_text());timing=json.loads((folder/'timing.json').read_text())
    hint=timing.get('clap_audio_seconds')
    if reference is None or not isinstance(hint,(float,int)) or not math.isfinite(hint):raise SyncError('No captured reference cue')
    rate=layout[0];count=round(rate*.03);t=np.arange(count)/rate;env=np.exp(np.log(.001/.3)*t/.03)
    sin=np.sin(2*np.pi*1500*t)*env;cos=np.cos(2*np.pi*1500*t)*env
    start=max(0,round((hint-1)*rate));window=reference[start:min(len(reference),round((hint+1)*rate))]
    if len(window)<count:raise SyncError('Captured reference cue is incomplete')
    score=np.hypot(np.correlate(window,sin,'valid'),np.correlate(window,cos,'valid'));index=int(np.argmax(score))
    if score[index]<1:raise SyncError('Captured sync-reference track is silent')
    reference_at=(start+index)/rate
    if not report.get('after'):raise SyncError('Video cue has not passed encoded-file verification')
    offset=report['after']['audio_marker_seconds']-reference_at
    return {'schema':'pubcast.stems.v1','tracks':tracks,'shared_sample_clock':True,
            'audio_to_video_offset_seconds':offset,'reference_cue_seconds':reference_at,
            'timeline_origin_seconds':report['after']['audio_marker_seconds']-hint,
            'cadence_seconds':15,'timeline_marker_color':'red','markers_in_picture':False,
            'scope':'Captured stems share sample frames; initial cue anchors them to the verified video. Checkpoints do not certify unrelated devices.'}


def build_stem_edit_copy(folder: Path, manifest: dict):
    args=[shutil.which('ffmpeg'),'-v','error','-i',str(folder/'aligned.mp4')]
    tracks=manifest['tracks']
    for track in tracks:args += ['-i',str(folder/('stem-'+track['name']+'.wav'))]
    filters=[];offset=manifest['audio_to_video_offset_seconds']
    for index,track in enumerate(tracks,1):
        if offset>=0:
            chain=f'adelay={round(offset*track["sample_rate"])}S:all=1'
        else:
            chain=f'atrim=start={-offset:.9f},asetpts=PTS-STARTPTS'
        filters.append(f'[{index}:a:0]{chain}[stem{index}]')
    args += ['-filter_complex',';'.join(filters),'-map','0:v:0','-map','0:a:0']
    for index in range(1,len(tracks)+1):args += ['-map',f'[stem{index}]']
    args += ['-c:v','copy','-c:a','aac','-c:a:0','copy','-disposition:a:0','default']
    labels={'dialogue':'Vocals and Dialogue','music':'Music','sfx':'Sound Effects','floor':'Director Floor','reference':'Sync Reference - mute in final mix'}
    for index,track in enumerate(tracks,1):
        label=labels.get(track['name'],track['name'].upper())
        args += [f'-disposition:a:{index}','0',f'-metadata:s:a:{index}',f'handler_name={label}']
    args += ['-movflags','+faststart','-y',str(folder/'editing.pending.mp4')]
    try:
        run(args)
        (folder/'editing.pending.mp4').replace(folder/'editing.mp4')
        run([shutil.which('ffmpeg'),'-v','error','-copyts','-i',str(folder/'aligned.mp4'),'-an',
             '-c:v','libvpx','-deadline','realtime','-cpu-used','8','-b:v','2M','-y',str(folder/'preview.pending.webm')])
        (folder/'preview.pending.webm').replace(folder/'preview.webm')
    except Exception:
        (folder/'editing.pending.mp4').unlink(missing_ok=True)
        raise


def render_edits(folder: Path):
    """Render per-section track offsets into a mix; picture is stream-copied."""
    manifest=json.loads((folder/'stems.json').read_text())
    edits=json.loads((folder/'edits.json').read_text()) if (folder/'edits.json').exists() else {'sections':{}}
    probe=json.loads(run([shutil.which('ffprobe'),'-v','error','-show_format','-of','json',str(folder/'aligned.mp4')]).stdout)
    duration=float(probe['format']['duration']);origin=manifest.get('timeline_origin_seconds',0)
    boundaries=sorted(set([0.,duration]+[origin+i*15 for i in range(501) if 0<origin+i*15<duration]))
    tracks=manifest['tracks'];enabled=set(edits.get('enabled_tracks',[t['name'] for t in tracks if t['name']!='reference']))-{'reference'}
    args=[shutil.which('ffmpeg'),'-v','error','-i',str(folder/'aligned.mp4')]
    for track in tracks:args += ['-i',str(folder/('stem-'+track['name']+'.wav'))]
    filters=[];outputs=[];mix=[]
    for index,track in enumerate(tracks,1):
        segments=len(boundaries)-1;labels=''.join(f'[i{index}s{s}]' for s in range(segments))
        filters.append(f'[{index}:a:0]asplit={segments}{labels}')
        for segment,(left,right) in enumerate(zip(boundaries,boundaries[1:])):
            section=max(0,math.floor(((left+right)/2-origin)/15));delta=float(edits.get('sections',{}).get(str(section),{}).get(track['name'],0))
            start=left-manifest['audio_to_video_offset_seconds']-delta;length=right-left;end=start+length
            if end<=0 or start>=track['sample_frames']/track['sample_rate']:
                filters.append(f'[i{index}s{segment}]anullsink')
                layout='stereo' if track['channels']==2 else 'mono'
                filters.append(f'anullsrc=r={track["sample_rate"]}:cl={layout},atrim=duration={length:.9f},asetpts=PTS-STARTPTS[t{index}s{segment}]')
                continue
            else:
                chain=f'atrim=start={max(0,start):.9f}:end={max(0,end):.9f},asetpts=PTS-STARTPTS'
                if start<0:chain+=f',adelay={round(-start*track["sample_rate"])}S:all=1'
                chain+=f',apad=whole_dur={length:.9f},atrim=duration={length:.9f}'
            filters.append(f'[i{index}s{segment}]{chain}[t{index}s{segment}]')
        labels=''.join(f'[t{index}s{s}]' for s in range(segments))
        filters.append(f'{labels}concat=n={segments}:v=0:a=1[t{index}]')
        if track['name'] in enabled:
            filters.append(f'[t{index}]asplit=2[e{index}][m{index}]');mix.append(f'[m{index}]')
        else:filters.append(f'[t{index}]anull[e{index}]')
        outputs.append(f'[e{index}]')
    if mix:filters.append(''.join(mix)+f'amix=inputs={len(mix)}:duration=longest:normalize=0[program]')
    else:filters.append(f'anullsrc=r=48000:cl=stereo,atrim=duration={duration:.9f}[program]')
    args += ['-filter_complex',';'.join(filters),'-map','0:v:0','-map','[program]']
    for output in outputs:args += ['-map',output]
    args += ['-c:v','copy','-c:a','aac','-b:a','192k','-disposition:a:0','default']
    for index,track in enumerate(tracks,1):args += [f'-disposition:a:{index}','0',f'-metadata:s:a:{index}',f'handler_name={track["name"]}']
    args += ['-movflags','+faststart','-y',str(folder/'final.pending.mp4')]
    try:
        run(args,timeout=180)
        (folder/'final.pending.mp4').replace(folder/'final.mp4')
    except Exception:
        (folder/'final.pending.mp4').unlink(missing_ok=True)
        raise
    return {'rendered':True,'section_count':len(boundaries)-1,'enabled_tracks':sorted(enabled),'reference_in_program_mix':False,'video_stream_copied':True}
