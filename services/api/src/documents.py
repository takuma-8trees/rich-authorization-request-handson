"""Real HTTP resource server; all reads and writes go through OPA."""
import asyncio
import os
import uuid
import httpx
from starlette.responses import JSONResponse
from .security import supported, verify

lock = asyncio.Lock()
records = {i:{'id':i,'title':title,'body':'まだ更新されていません','owner':'alice','locked':False,'revision':0} for i,title in [('doc-a','文書A：会議メモ'),('doc-b','文書B：出張メモ')]}

async def document(request):
    authorization = request.headers.get('authorization','')
    try:
        if not authorization.startswith('Bearer '):
            raise ValueError()
        claims = await verify(authorization[7:])
    except Exception:
        return JSONResponse({'error':'invalid_token'},401,headers={'WWW-Authenticate':'Bearer error="invalid_token"'})
    doc_id = request.path_params['document_id']
    if doc_id not in records:
        return JSONResponse({'error':'not_found'},404)
    action = 'read' if request.method == 'GET' else 'update'
    payload = None
    if action == 'update':
        try:
            raw = await request.body()
            if len(raw)>12000:raise ValueError()
            import json
            payload = json.loads(raw)
            if not isinstance(payload,dict) or set(payload) != {'body'} or not isinstance(payload['body'],str) or len(payload['body'])>2000:raise ValueError()
        except (ValueError,TypeError):return JSONResponse({'error':'invalid_body'},400)
    async with lock:
        resource = records[doc_id]
        present = 'authorization_details' in claims
        inp = {'subject':claims.get('preferred_username'),'scope':claims.get('scope',''),
               'rar_present':present,'rar_valid':not present or supported(claims['authorization_details']),
               'authorization_details':claims.get('authorization_details',[]),
               'action':action,'resource':dict(resource)}
        # Never send JWT or document contents to the PDP.
        inp['resource'].pop('body')
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.post(os.environ['OPA_URL'],json={'input':inp})
                r.raise_for_status()
            decision = r.json()['result']
            if not isinstance(decision,dict) or type(decision.get('allow')) is not bool:raise ValueError()
        except (httpx.HTTPError,ValueError,KeyError):
            return JSONResponse({'error':'authorization_unavailable','executed':False},503)
        result = {'decision_id':str(uuid.uuid4()),'action':action,'document_id':doc_id,'decision':decision,'executed':False}
        if not decision['allow']:
            return JSONResponse(result,403)
        before = dict(resource)
        if action=='update':
            resource['body']=payload['body'];resource['revision']+=1
        result.update(executed=True,before=before,document=dict(resource))
        return JSONResponse(result)
