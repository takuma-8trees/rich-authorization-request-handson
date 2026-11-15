"""Verify the token before using its claims; never follow an issuer from a token."""
import asyncio
import os
import time
import httpx
import jwt

ISSUER = os.environ['OIDC_ISSUER']
INTERNAL = os.environ['OIDC_INTERNAL']
ORIGIN = os.environ['APP_ORIGIN']
CLIENT = 'rar-browser'
TYPE = 'urn:rar-lab:document-access:v1'
LOCATION = ORIGIN + '/documents'
keys, loaded = {}, 0
lock = asyncio.Lock()

async def verify(token, audience='document-api'):
    global keys, loaded
    header = jwt.get_unverified_header(token)
    if header.get('alg') != 'RS256' or not isinstance(header.get('kid'), str):
        raise ValueError('Unsupported JWT')
    async with lock:
        if time.monotonic() - loaded > 300 or header['kid'] not in keys:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(INTERNAL + '/protocol/openid-connect/certs')
                r.raise_for_status()
            keys = {k['kid']: jwt.PyJWK.from_dict(k).key for k in r.json()['keys'] if k.get('kty') == 'RSA' and k.get('use', 'sig') == 'sig'}
            loaded = time.monotonic()
    claims = jwt.decode(token, keys[header['kid']], algorithms=['RS256'], issuer=ISSUER, audience=audience,
                        options={'require': ['exp', 'iat', 'iss', 'sub', 'aud']})
    if audience == 'document-api' and (claims.get('typ') != 'Bearer' or claims.get('azp') != CLIENT):
        raise ValueError('Wrong token type/client')
    return claims

def details(document, actions):
    return [{'type': TYPE, 'locations': [LOCATION], 'actions': sorted(actions), 'identifier': document}]

def supported(value):
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        return False
    d = value[0]
    return (set(d) == {'type', 'locations', 'actions', 'identifier'} and d['type'] == TYPE
            and d['locations'] == [LOCATION] and d['identifier'] in ('doc-a', 'doc-b')
            and isinstance(d['actions'], list) and bool(d['actions'])
            and all(isinstance(a, str) and a in ('read', 'update') for a in d['actions'])
            and len(d['actions']) == len(set(d['actions'])))
