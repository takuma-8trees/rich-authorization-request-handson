"""Compose the tutorial UI, OAuth client, and protected HTTP API."""
import logging
import httpx
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from . import auth, documents

logging.getLogger('httpx').setLevel(logging.WARNING)

async def index(request):return FileResponse('public/index.html')
async def health(request):return JSONResponse({'status':'ok'})

async def lab_call(request):
    s=auth.session(request)
    if not auth.csrf(request,s):return JSONResponse({'error':'csrf_failed'},403)
    try:
        data=await request.json();mode=data['mode'];doc=data['document'];method=data['method']
        if mode not in ('scope','rar') or doc not in documents.records or method not in ('GET','PATCH'):raise ValueError()
        saved=s['tokens'].get(mode)
        if not saved:return JSONResponse({'error':'先にトークンを取得してください'},400)
        body={'body':data.get('body','')} if method=='PATCH' else None
        async with httpx.AsyncClient(timeout=10) as client:
            r=await client.request(method,'http://127.0.0.1:8000/documents/'+doc,headers={'Authorization':'Bearer '+saved['token']},json=body)
        return JSONResponse({'http_status':r.status_code,'request':{'method':method,'path':'/documents/'+doc,'body':body},'response':r.json()})
    except (ValueError,KeyError):return JSONResponse({'error':'invalid_input'},400)
    except httpx.HTTPError:return JSONResponse({'error':'api_unavailable'},503)

async def policy(request):
    s=auth.session(request)
    if not auth.csrf(request,s):return JSONResponse({'error':'csrf_failed'},403)
    data=await request.json()
    if set(data)!={'locked'} or type(data['locked']) is not bool:return JSONResponse({'error':'invalid_input'},400)
    # Teaching control, not a production admin endpoint. Changes provider-side resource state.
    async with documents.lock:documents.records['doc-a']['locked']=data['locked']
    return JSONResponse({'doc_a_locked':data['locked']})

async def lab_state(request):
    return JSONResponse({'doc_a_locked':documents.records['doc-a']['locked']})

async def headers(request,call_next):
    response=await call_next(request)
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Content-Security-Policy']="default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response

app=Starlette(routes=[Route('/',index),Route('/health',health),Route('/auth/login',auth.login),Route('/auth/callback',auth.callback),
 Route('/lab/session',auth.status),Route('/lab/token/{mode}',auth.export_token,methods=['POST']),
 Route('/lab/call',lab_call,methods=['POST']),Route('/lab/policy',policy,methods=['POST']),Route('/lab/state',lab_state),
 Route('/documents/{document_id}',documents.document,methods=['GET','PATCH']),Mount('/static',StaticFiles(directory='public'))],
 middleware=[Middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','api']),Middleware(BaseHTTPMiddleware,dispatch=headers)])
