from tests.test_studio_slate import floor, headers, post
from tests.test_recorded_slate_sync import fixture_media


def test_take_analysis_download_and_permissions(floor,tmp_path):
    client,_=floor;post(client,'create');post(client,'standby');post(client,'clap')
    slate=client.get('/api/studio/slate',headers=headers()).json()['slate']
    url='/api/studio/slate/takes/'+slate['id'];source=fixture_media(tmp_path,.2)
    assert client.post(url,content=source.read_bytes(),headers={**headers('intruder','owner'),'Content-Type':'video/mp4'}).status_code==403
    response=client.post(url,content=source.read_bytes(),headers={**headers(),'Content-Type':'video/mp4'})
    assert response.status_code==200,response.text
    report=response.json();assert report['status']=='verified_recorded_cue'
    assert client.get(report['original_url'],headers=headers()).content==source.read_bytes()
    assert client.get(report['aligned_url'],headers=headers()).status_code==200
    assert client.get(report['aligned_url'],headers=headers('intruder','owner')).status_code==403
    assert client.get(url,headers=headers()).json()['takes'][0]['take_id']==report['take_id']


def test_bad_media_never_claims_verified_and_keeps_original(floor):
    client,_=floor;post(client,'create')
    s=client.get('/api/studio/slate',headers=headers()).json()['slate']
    url='/api/studio/slate/takes/'+s['id']
    assert client.post(url,content=b'x',headers={**headers(),'Content-Type':'text/html'}).status_code==415
    response=client.post(url,content=b'not media',headers={**headers(),'Content-Type':'video/webm'})
    assert response.json()['status']=='unverified'
    assert client.get(response.json()['original_url'],headers=headers()).content==b'not media'
    assert client.get(url+'/../../escape/original',headers=headers()).status_code==404
