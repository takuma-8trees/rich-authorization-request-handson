const $=s=>document.querySelector(s);
let state={authenticated:false},busy=false;
const pretty=x=>JSON.stringify(x,null,2);
function notice(text){$('#notice').textContent=text;$('#notice').hidden=false;}
function render(){
 for(const mode of ['scope','rar']){
  const token=state.tokens?.[mode];
  $('#'+mode+'-status').textContent=token?(token.expired?'期限切れ — もう一度取得してください':'取得済み · '+new Date(token.claims.exp*1000).toLocaleTimeString('ja-JP')+'まで有効'):'未取得';
  $('#'+mode+'-claims').textContent=token?pretty(token.claims):'未取得';
 }
 const rar=state.tokens?.rar;
 $('#rar-request').textContent=rar?pretty(rar.requested):'未取得';
 $('#rar-response').textContent=rar?pretty(rar.response_details):'未取得';
 const active=state.tokens?.[$('#mode').value];
 $('#active-token').textContent=active?(active.expired?'期限切れ — HTTP 401を確認できます':($('#mode').value==='rar'?'対象：'+active.claims.authorization_details[0].identifier:'対象IDの限定なし')):'トークンを取得してください';
 document.querySelectorAll('[data-doc]').forEach(b=>b.disabled=busy||!active);
 $('#locked').disabled=!state.authenticated||busy;
 $('#export').disabled=!active;
}
async function refresh(){state=await(await fetch('/lab/session')).json();render();}
async function post(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':state.csrf||''},body:JSON.stringify(data)});const out=await r.json();if(!r.ok)throw new Error(out.error||'要求に失敗しました');return out;}
function updateLink(){ $('#rar-login').href='/auth/login?'+new URLSearchParams({mode:'rar',document:$('#grant-document').value,actions:$('#grant-actions').value});}
$('#grant-document').onchange=updateLink;$('#grant-actions').onchange=updateLink;
$('#mode').onchange=()=>{$('#curl').textContent='ここにcurlコマンドを表示します。';render();};
document.querySelectorAll('[data-doc]').forEach(button=>button.onclick=async()=>{
 busy=true;render();
 try{
  const doc=button.dataset.doc,method=button.dataset.method;
  const out=await post('/lab/call',{mode:$('#mode').value,document:doc,method,body:$('#'+doc+'-input').value});
  $('#response-json').textContent=pretty(out);
  const result=$('#result');result.replaceChildren();result.className='result '+(out.http_status===200?'ok':'denied');
  const title=document.createElement('h3');title.textContent='HTTP '+out.http_status+' · '+(out.http_status===200?'実行しました':out.http_status===403?'実行を拒否しました':'実行できませんでした');result.append(title);
  const p=document.createElement('p');p.textContent=method+' '+out.request.path;result.append(p);
  const checks=out.response.decision?.checks;
  if(checks){const row=document.createElement('div');row.className='checks';for(const [key,label] of Object.entries({scope:'scope',rar:'RAR条件',provider:'提供側ポリシー'})){const span=document.createElement('span');span.className=checks[key]?'pass':'fail';span.textContent=(checks[key]?'✓ ':'✕ ')+label;row.append(span);}result.append(row);}
  const message=document.createElement('p');
  message.textContent=out.http_status===200?'返された本文とrevisionを文書カードに反映しました。':out.http_status===403?'文書は変更されていません。拒否理由：'+out.response.decision.reasons.join(', '):'トークンの期限やサービスの稼働状態を確認してください。';result.append(message);
  if(out.response.document){const d=out.response.document;$('#'+doc+'-body').textContent=d.body+'（revision '+d.revision+'）';}
 }catch(e){notice(e.message);}finally{busy=false;await refresh();}
});
$('#locked').onchange=async()=>{const requested=$('#locked').checked;try{await post('/lab/policy',{locked:requested});notice(requested?'文書Aを編集禁止にしました。同じトークンでAを更新してみてください。':'文書Aの編集禁止を解除しました。');}catch(e){$('#locked').checked=!requested;notice(e.message);}};
$('#export').onclick=async()=>{try{const data=await post('/lab/token/'+$('#mode').value,{});$('#curl').textContent="TOKEN='"+data.access_token+"'\ncurl -i http://localhost:18770/documents/doc-a \\\n  -H \"Authorization: Bearer $TOKEN\"";}catch(e){notice(e.message);}};
const params=new URLSearchParams(location.search);
if(params.has('issued')){$('#mode').value=params.get('issued')==='scope'?'scope':'rar';notice('トークンを取得しました。セクション02でAPIを呼び出してください。');}
if(params.has('error'))notice('認可要求は完了しませんでした：'+params.get('error'));
refresh().catch(()=>notice('サービスに接続できません。起動状態を確認してください。'));
fetch('/lab/state').then(r=>r.json()).then(x=>$('#locked').checked=x.doc_a_locked).catch(()=>{});
setInterval(refresh,15000);
