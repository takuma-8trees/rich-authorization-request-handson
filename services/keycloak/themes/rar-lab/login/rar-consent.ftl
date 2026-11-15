<#import "template.ftl" as layout>
<@layout.registrationLayout; section>
 <#if section = "header">アクセス許可を確認</#if>
 <#if section = "form">
  <p>RAR Lab が次のアクセスを要求しています。有効期間は5分です。</p>
  <#if rarMode>
   <h2>対象：${documentId}</h2><p>操作：${operations}</p>
   <p>選んだ文書だけが対象です。提供側のポリシーによっては拒否されます。</p>
  <#else>
   <h2>本人が扱える文書の参照・更新</h2><p>scopeだけの比較用要求です。文書IDによる限定はありません。</p>
  </#if>
  <details><summary>実際の認可要求</summary><pre style="white-space:pre-wrap;word-break:break-all">${requestJson}</pre></details>
  <form action="${url.loginAction}" method="post">
   <button type="submit" name="approve" value="yes">この内容を許可する</button>
   <button type="submit" name="approve" value="no">許可しない</button>
  </form>
 </#if>
</@layout.registrationLayout>
