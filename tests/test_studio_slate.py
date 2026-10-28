"""Production-floor permissions, shared state, persistence and actual voice relay."""
import json
import pytest
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from modules.auth import create_access_token, WS_SESSION_COOKIE
from modules.studio_slate import create_slate_router, SlateOverlayMiddleware


def headers(user='director', role='mod'):
    return {'Authorization': 'Bearer '+create_access_token({'sub':user,'role':role})}


@pytest.fixture
def floor(tmp_path):
    app=FastAPI()
    router=create_slate_router(tmp_path/'slates.sqlite3')
    app.include_router(router)
    app.add_middleware(SlateOverlayMiddleware)
    @app.get('/')
    def home():
        return HTMLResponse('<!doctype html><html><head><title>Studio</title></head><body>Screen</body></html>')
    return TestClient(app), router.slate_store


def post(client,action,data=None,user='director',role='mod'):
    state=client.get('/api/studio/slate',headers=headers(user,role)).json()
    return client.post('/api/studio/slate',headers=headers(user,role),json={'action':action,'data':data or {},'revision':state['slate']['revision'] if state['slate'] else None})


def test_director_ownership_delegation_and_revision(floor):
    c,store=floor
    assert c.get('/api/studio/slate').status_code==401
    assert post(c,'create',user='viewer',role='viewer').status_code==403
    assert post(c,'create').status_code==200
    assert post(c,'create',user='other',role='owner').status_code==409
    assert post(c,'edit',{'fields':{'scene':'14'}},user='other',role='owner').status_code==403
    assert post(c,'delegate',{'editors':['assistant']}).status_code==200
    assert post(c,'edit',{'fields':{'scene':'14'}},user='assistant',role='viewer').status_code==200
    assert post(c,'delegate',{'editors':['other']},user='assistant',role='owner').status_code==403
    assert post(c,'end',user='assistant',role='owner').status_code==403
    assert post(c,'delegate',{'editors':[]}).status_code==200
    assert post(c,'edit',{'fields':{'take':'9'}},user='assistant').status_code==403
    stale=c.post('/api/studio/slate',headers=headers(),json={'action':'hide','revision':1})
    assert stale.status_code==409
    assert store.current()['fields']['scene']=='14'


def test_roll_call_everyone_reads_only_self_checks_in(floor):
    c,store=floor
    post(c,'create');post(c,'departments',{'departments':{'Camera':'cam','Sound':'sound'}})
    post(c,'standby')
    viewer=c.get('/api/studio/slate',headers=headers('cam','viewer')).json()
    assert viewer['slate']['visible'] and viewer['slate']['clap_at'] is None
    assert viewer['can_edit'] is False
    assert post(c,'ready',{'department':'Sound','ready':True},user='cam',role='viewer').status_code==403
    assert post(c,'clap').status_code==409
    assert post(c,'ready',{'department':'Camera','ready':True},user='cam',role='viewer').status_code==200
    assert post(c,'ready',{'department':'Sound','ready':True},user='sound',role='viewer').status_code==200
    take=post(c,'clap').json()['slate']
    assert take['phase']=='take' and take['clap_at']>take['updated_at']
    assert take['sync_status']=='media_alignment_unverified'
    assert post(c,'ready',{'department':'Camera','ready':False},user='cam').status_code==409
    post(c,'edit',{'fields':{'notes':'Later take notes'}})
    from modules.studio_slate import SlateStore
    reopened=SlateStore(store.path)
    assert reopened.current()['fields']['notes']=='Later take notes'
    post(c,'standby')
    assert all(not e['ready'] for e in store.current()['departments'].values())


def test_crew_stays_session_local_and_bad_fields_rejected(floor):
    c,store=floor;post(c,'create')
    crew=[{'label':'Pete','role':'camera operator','profile':'local','instructions':'Underwater scene','flight_pattern':'slow orbit','enabled':True}]
    assert post(c,'crew',{'crew':crew}).status_code==200
    assert store.current()['crew']==crew
    assert post(c,'edit',{'fields':{'director_id':'imposter'}}).status_code==422
    assert post(c,'departments',{'departments':{'Camera':5}}).status_code==422
    assert post(c,'crew',{'crew':[{'enabled':'yes'}]}).status_code==422
    post(c,'end');post(c,'create',user='next',role='mod')
    assert store.current()['crew']==[] and store.current()['director_id']=='next'


def test_overlay_on_html_not_json_and_head(floor):
    c,_=floor
    assert c.get('/').text.count('/static/studio_slate.js')==1
    assert '/static/studio_slate.js' not in c.get('/api/studio/slate',headers=headers()).text


def test_live_voice_only_verified_director_can_transmit(floor):
    c,_=floor;post(c,'create');post(c,'standby')
    # Browser sockets use the same HttpOnly Reach session cookie, no token URLs.
    with c.websocket_connect('/studio/slate/live',headers={'cookie':WS_SESSION_COOKIE+'='+create_access_token({'sub':'listener','role':'viewer'})}) as listener:
        with c.websocket_connect('/studio/slate/live',headers={'cookie':WS_SESSION_COOKIE+'='+create_access_token({'sub':'director','role':'mod'})}) as director:
            director.send_json({'samples':[0,.1,-.1]})
            packet=listener.receive_json()
            assert packet['type']=='director_voice' and packet['samples']==[0,.1,-.1]
            assert packet['sample_rate']==16000
        listener.send_json({'samples':[.2]})
        assert listener.receive()['code']==1008


def test_voice_rejects_malformed_and_cross_origin(floor):
    c,_=floor;post(c,'create');post(c,'standby')
    cookie={'cookie':WS_SESSION_COOKIE+'='+create_access_token({'sub':'director','role':'mod'})}
    with c.websocket_connect('/studio/slate/live',headers=cookie) as ws:
        ws.send_json({'samples':[2]})
        assert ws.receive()['code']==1008
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with c.websocket_connect('/studio/slate/live',headers={**cookie,'origin':'https://hostile.invalid'}):
            pass
