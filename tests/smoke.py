"""Real IdP/browser-form/API checks. No mocked token issuance, no JWT logging."""
import asyncio
import html
import json
import os
import re
from urllib.parse import urljoin, urlsplit, parse_qs
import httpx
import jwt

APP='http://localhost:18770'
IDP='http://localhost:18771'

class Browser:
    def __init__(self):self.client=httpx.AsyncClient(timeout=15,follow_redirects=False)
    async def close(self):await self.client.aclose()
    async def request(self,url,method='GET',**kwargs):
        target=url.replace(APP,'http://api:8000').replace(IDP,'http://keycloak:8080')
        headers={'Host':urlsplit(url).netloc,**kwargs.pop('headers',{})}
        response=await self.client.request(method,target,headers=headers,**kwargs)
        # Browsers allow Secure cookies on localhost. These test-only URLs use
        # Docker service names, so emulate that localhost exception in the jar.
        for cookie in self.client.cookies.jar:
            cookie.secure=False
        return response
    async def follow(self,url):
        for _ in range(15):
            r=await self.request(url)
            if r.is_redirect:url=urljoin(url,r.headers['location']);continue
            return url,r
        raise AssertionError('Redirect loop')
    def form(self,url,r):
        match=re.search(r'<form[^>]*action="([^"]+)"',r.text)
        assert match,'Form missing'
        action=urljoin(url,html.unescape(match[1]));data={}
        for tag in re.findall(r'<input\b[^>]*>',r.text):
            name=re.search(r'name="([^"]+)"',tag);value=re.search(r'value="([^"]*)"',tag)
            if 'type="hidden"' in tag and name:data[name[1]]=html.unescape(value[1]) if value else ''
        return action,data
    async def signin(self,mode='rar',actions='read,update',approve=True):
        url,r=await self.follow(APP+'/auth/login?mode='+mode+'&actions='+actions)
        action,data=self.form(url,r);data.update(username='alice',password='alice-demo-password',credentialId='')
        r=await self.request(action,'POST',data=data)
        if r.is_redirect:url,r=await self.follow(urljoin(action,r.headers['location']))
        else:url=action
        assert 'アクセス許可を確認' in r.text,'Exact consent page missing'
        if mode=='rar':assert 'doc-a' in r.text
        action,data=self.form(url,r);data['approve']='yes' if approve else 'no'
        r=await self.request(action,'POST',data=data)
        assert r.is_redirect,'Consent did not finish'
        url,r=await self.follow(urljoin(action,r.headers['location']))
        if not approve:
            assert 'error=access_denied' in url
            return None
        assert 'issued='+mode in url, 'Token flow failed: '+str(parse_qs(urlsplit(url).query))
        r=await self.request(APP+'/lab/session');s=r.json()
        assert s['authenticated'],s
        return s
    async def post(self,path,data,csrf):return await self.request(APP+path,'POST',json=data,headers={'Origin':APP,'X-CSRF-Token':csrf})

async def api(token,doc,method='GET',body=None):
    async with httpx.AsyncClient(timeout=10) as c:
        return await c.request(method,'http://api:8000/documents/'+doc,headers={'Authorization':'Bearer '+token} if token else {},json=body)

async def main():
    browser=Browser()
    try:
        assert (await api('', 'doc-a')).status_code==401
        s=await browser.signin('scope')
        scope=(await browser.post('/lab/token/scope',{},s['csrf'])).json()['access_token']
        s=await browser.signin('rar')
        rar=(await browser.post('/lab/token/rar',{},s['csrf'])).json()['access_token']
        assert 'authorization_details' not in s['tokens']['scope']['claims']
        claims=s['tokens']['rar']['claims']
        assert claims['authorization_details']==s['tokens']['rar']['requested']==s['tokens']['rar']['response_details']
        assert set(claims['scope'].split())==set(s['tokens']['scope']['claims']['scope'].split())
        assert claims['sub']==s['tokens']['scope']['claims']['sub']
        # Inspect the complete, already API-verified token, not the UI's whitelist.
        assert 'act' not in jwt.decode(rar,options={'verify_signature':False})
        if os.getenv('OPA_OFFLINE')=='1':
            r=await api(rar,'doc-a','PATCH',{'body':'must not run'})
            assert r.status_code==503 and r.json()['executed'] is False
            print('PASS OPA unavailable: 503, no execution');return
        print('PASS actual login, exact consent, same subject/scope, RAR in token response and JWT')
        assert (await browser.post('/lab/policy',{'locked':False},s['csrf'])).status_code==200
        before=(await api(scope,'doc-b')).json()['document']
        a=await api(rar,'doc-a','PATCH',{'body':'smoke: A updated'})
        assert a.status_code==200 and a.json()['document']['body']=='smoke: A updated'
        denied=await api(rar,'doc-b','PATCH',{'body':'must not run'})
        assert denied.status_code==403 and denied.json()['decision']['reasons']==['rar_out_of_bounds']
        assert (await api(scope,'doc-b')).json()['document']==before
        assert (await api(scope,'doc-b','PATCH',{'body':'smoke: B updated with scope'})).status_code==200
        print('PASS RAR A=200, RAR B=403 with unchanged data, scope B=200')
        await browser.post('/lab/policy',{'locked':True},s['csrf'])
        r=await api(rar,'doc-a','PATCH',{'body':'must not run'})
        assert r.status_code==403 and r.json()['decision']['reasons']==['provider_policy_denied']
        assert (await api(rar,'doc-a')).json()['document']['body']=='smoke: A updated'
        await browser.post('/lab/policy',{'locked':False},s['csrf'])
        print('PASS same token, provider policy change => 403; read still allowed')
        assert (await browser.post('/lab/policy',{'locked':True},'wrong')).status_code==403
        assert (await browser.request(APP+'/auth/callback?code=bad&state=bad')).is_redirect
        assert (await api(rar[:-10]+'AAAAAAAAAA','doc-a')).status_code==401
        assert (await api(rar,'doc-a','PATCH',{'body':'x','owner':'other'})).status_code==400
        readonly=await browser.signin('rar',actions='read')
        t=(await browser.post('/lab/token/rar',{},readonly['csrf'])).json()['access_token']
        assert (await api(t,'doc-a')).status_code==200
        assert (await api(t,'doc-a','PATCH',{'body':'must not run'})).status_code==403
        print('PASS read-only RAR, forged JWT, CSRF and unknown write fields rejected')
        invalid=Browser()
        try:
            url,r=await invalid.follow(APP+'/auth/login?mode=invalid')
            assert 'invalid_authorization_details' in url or 'invalid_authorization_details' in r.text,'Unknown RAR field was not rejected'
        finally:await invalid.close()
        cancellation=Browser()
        try:await cancellation.signin(approve=False)
        finally:await cancellation.close()
        print('PASS unknown RAR => invalid_authorization_details; consent cancellation => no token')
    finally:await browser.close()

asyncio.run(main())
