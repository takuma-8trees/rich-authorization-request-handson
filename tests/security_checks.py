"""Focused verifier tests with an ephemeral local signing key; not an IdP substitute."""
import asyncio
import time
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from src import security

async def main():
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    security.keys={'test':key.public_key()}
    security.loaded=time.monotonic()
    base={'iss':security.ISSUER,'sub':'test','aud':'document-api','azp':'rar-browser',
          'typ':'Bearer','iat':int(time.time())-1,'exp':int(time.time())+60}
    def token(claims):return jwt.encode(claims,key,algorithm='RS256',headers={'kid':'test'})
    assert (await security.verify(token(base)))['sub']=='test'
    for changes in [{'exp':int(time.time())-1},{'iss':'https://other.invalid'},
                    {'aud':'another-api'},{'azp':'another-client'},{'typ':'ID'}]:
        try:await security.verify(token({**base,**changes}))
        except (ValueError,jwt.PyJWTError):pass
        else:raise AssertionError('Verifier accepted '+str(changes))
    valid=security.details('doc-a',['read'])
    assert security.supported(valid)
    for invalid in [None,[],{},[{}],[{**valid[0],'identifier':['doc-a']}],
                    [{**valid[0],'actions':['read','read']}],
                    [{**valid[0],'actions':[{}]}],[{**valid[0],'extra':True}]]:
        assert not security.supported(invalid)
    print('PASS verifier: expiry, issuer, audience, client, type and malformed RAR')

asyncio.run(main())
