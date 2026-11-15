"""Tiny BFF for the teaching UI. Auth code + PKCE, opaque server-side sessions."""
import base64
import hashlib
import json
import secrets
import time
from urllib.parse import urlencode
import httpx
from starlette.responses import JSONResponse, RedirectResponse
from .security import CLIENT, INTERNAL, ISSUER, ORIGIN, details, verify

sessions, flows = {}, {}
random = lambda: secrets.token_urlsafe(32)

def session(request):
    now = time.time()
    for key in list(sessions):
        if sessions[key]['expires'] <= now:
            del sessions[key]
    return sessions.get(request.cookies.get('rar_sid'))

def csrf(request, s):
    return s and request.headers.get('origin') == ORIGIN and secrets.compare_digest(request.headers.get('x-csrf-token', ''), s['csrf'])

async def login(request):
    if request.url.hostname != 'localhost':
        return RedirectResponse(ORIGIN + str(request.url).split(str(request.base_url).rstrip('/'), 1)[-1])
    mode = request.query_params.get('mode', 'rar')
    document = request.query_params.get('document', 'doc-a')
    actions = request.query_params.get('actions', 'read,update').split(',')
    if mode not in ('scope', 'rar', 'invalid') or document not in ('doc-a', 'doc-b') or not actions or any(a not in ('read','update') for a in actions) or len(actions) != len(set(actions)):
        return JSONResponse({'error': 'invalid_input'}, 400)
    for key in list(flows):
        if flows[key]['expires'] < time.time():
            del flows[key]
    if len(flows) >= 100:
        return JSONResponse({'error': 'too_many_flows'}, 429)
    flow = {'state': random(), 'nonce': random(), 'verifier': random(), 'mode': mode, 'details': None,
            'expires': time.time()+300, 'old_sid': request.cookies.get('rar_sid')}
    params = {'client_id': CLIENT, 'redirect_uri': ORIGIN+'/auth/callback', 'response_type': 'code',
              'scope': 'openid document.read document.update', 'state': flow['state'], 'nonce': flow['nonce'],
              'code_challenge': base64.urlsafe_b64encode(hashlib.sha256(flow['verifier'].encode()).digest()).decode().rstrip('='), 'code_challenge_method': 'S256'}
    if mode != 'scope':
        flow['details'] = details(document, actions)
        if mode == 'invalid':
            flow['details'][0]['unsupported_condition'] = True
        params['authorization_details'] = json.dumps(flow['details'], separators=(',', ':'))
    flow_id = random()
    flows[flow_id] = flow
    response = RedirectResponse(ISSUER+'/protocol/openid-connect/auth?'+urlencode(params), 302)
    response.set_cookie('rar_flow', flow_id, httponly=True, samesite='lax', max_age=300)
    return response

async def callback(request):
    flow = flows.pop(request.cookies.get('rar_flow'), None)
    error = 'login_failed'
    try:
        if not flow or flow['expires'] < time.time() or request.query_params.get('state') != flow['state']:
            raise ValueError('Invalid state')
        if request.query_params.get('error'):
            error = request.query_params['error'] if request.query_params['error'] in ('access_denied','invalid_authorization_details') else error
            raise ValueError('Authorization rejected')
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(INTERNAL+'/protocol/openid-connect/token', data={
                'grant_type':'authorization_code','client_id':CLIENT,'redirect_uri':ORIGIN+'/auth/callback',
                'code':request.query_params.get('code',''),'code_verifier':flow['verifier']})
            r.raise_for_status()
        tokens = r.json()
        claims = await verify(tokens['access_token'])
        identity = await verify(tokens['id_token'], CLIENT)
        if identity.get('nonce') != flow['nonce'] or identity['sub'] != claims['sub']:
            raise ValueError('Identity mismatch')
        granted = claims.get('authorization_details')
        if granted != flow['details'] or (flow['mode'] == 'rar' and tokens.get('authorization_details') != granted):
            raise ValueError('Granted conditions differ from request')
        old = sessions.pop(flow['old_sid'], None)
        saved = old['tokens'] if old and old['sub'] == claims['sub'] else {}
        saved[flow['mode']] = {'token':tokens['access_token'], 'claims':claims, 'requested':flow['details'], 'response_details':tokens.get('authorization_details')}
        sid = random()
        sessions[sid] = {'sub':claims['sub'],'csrf':random(),'expires':time.time()+900,'tokens':saved}
        response = RedirectResponse('/?issued='+flow['mode'],302)
        response.set_cookie('rar_sid',sid,httponly=True,samesite='lax',max_age=900)
    except Exception:
        # Intentionally no exception text: upstream data can contain credentials.
        response = RedirectResponse('/?error='+error,302)
    response.delete_cookie('rar_flow')
    return response

async def status(request):
    s = session(request)
    if not s:
        return JSONResponse({'authenticated':False})
    result = {}
    for mode, saved in s['tokens'].items():
        c = saved['claims']
        result[mode] = {'claims':{k:c[k] for k in ('iss','sub','aud','azp','iat','exp','scope','authorization_details') if k in c},
                        'requested':saved['requested'],'response_details':saved['response_details'], 'expired':c['exp'] <= time.time()}
    return JSONResponse({'authenticated':True,'csrf':s['csrf'],'tokens':result})

async def export_token(request):
    s = session(request)
    if not csrf(request,s):
        return JSONResponse({'error':'csrf_failed'},403)
    mode = request.path_params['mode']
    if mode not in s['tokens']:
        return JSONResponse({'error':'no_token'},404)
    return JSONResponse({'access_token':s['tokens'][mode]['token']})
