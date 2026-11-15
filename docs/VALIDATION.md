# 検証記録

検証日：2026-11-15。再現版：`v0.1.0`。

## 実測環境

- ホスト：Windows ARM64、WSL Ubuntu 24.04 / aarch64。
- Docker Engine 28.4.0、Docker Compose v2.39.2。
- Keycloak 26.8.1 + 本リポジトリのJava 21拡張、OPA 1.9.0-static。
- Python 3.13.18、Starlette 1.10.0、Uvicorn 0.54.0、httpx 0.28.1、PyJWT 2.15.1。Pythonの推移依存も `services/api/constraints.txt` に固定。
- 実ブラウザー：Codex内蔵ブラウザー。localhostでログイン、同意、更新、拒否を確認。掲載画像は実画面の取得物。細い表示幅での折り返しも確認。

Linux/amd64は各ベースイメージのmanifestに存在することを確認しましたが、この版の実行テストはARM64のみです。性能・負荷・本番環境・外部RAR製品との相互運用は検証していません。

## 実行済みの確認

`sh run/verify.sh`：

```text
PASS: 7/7
PASS verifier: expiry, issuer, audience, client, type and malformed RAR
PASS actual login, exact consent, same subject/scope, RAR in token response and JWT
PASS RAR A=200, RAR B=403 with unchanged data, scope B=200
PASS same token, provider policy change => 403; read still allowed
PASS read-only RAR, forged JWT, CSRF and unknown write fields rejected
PASS unknown RAR => invalid_authorization_details; consent cancellation => no token
```

`sh run/verify-opa-offline.sh`：

```text
PASS OPA unavailable: 503, no execution
```

OPA停止後はスクリプトのtrapで復旧。既存の別プロジェクトのコンテナ・ネットワークには変更を加えていません。

署名検証の単体テストだけは一時生成したテスト鍵を使用します。統合テストは実Keycloakでログイン・同意し、実際に発行されたトークンでAPI/OPAを呼びます。HTTPテストクライアントはDockerサービス名に接続するため、localhostに対するブラウザーのSecure Cookie例外をテスト用Cookie jarで模倣しています。本体のCookie設定を変更するものではありません。

ブラウザーで確認した結果：

| 操作 | 実測 |
| --- | --- |
| scope版のログイン・同意 | 発行されて画面に戻る |
| 文書A・read/updateのRAR要求 | 同意画面に対象・操作・要求JSONを表示 |
| RAR版でAを更新 | 200、本文とrevisionが変化 |
| 同じRAR版でBを更新 | 403、RAR条件のみ不一致 |
| scope版でBを更新 | 200 |
| Aを編集禁止にし、同じRAR版で更新 | 403、提供側条件のみ不一致 |
| 編集禁止を解除 | 解除メッセージと未チェック状態を確認 |

## 新規cloneからの再現

実装コミット `d36168d` を `git clone --no-hardlinks` で別ディレクトリへcloneし、空の専用volumeで `docker compose up -d --build` → `sh run/verify.sh` → `sh run/verify-opa-offline.sh` を実行。すべて成功しました。元の実験用構成を一時停止し、検証用Compose project名を `rar-handson-clean`、サブネットを `10.253.72.0/24` にして既存データから分離しました。ビルドキャッシュは共有しています。GitHub経由のclone検証とは区別します。

この後のコミットは検証記録の追記のみで、実行資材は同一です。

## イメージの固定とdigest

Dockerfile / Composeで次のmulti-platform manifest digestを固定。2026-11-15に `docker buildx imagetools inspect` で確認しました。

| イメージ | digest |
| --- | --- |
| `quay.io/keycloak/keycloak:26.8.1` | `sha256:3f3c5f8e03c614774b4bd9173b88391fefa4153bfc010d8012d59ad825377332` |
| `openpolicyagent/opa:1.9.0-static` | `sha256:60b6af32b58377718546ac7d4634eecbfe50ec36f7d3ca3f8ebf515f9826c2ac` |
| `python:3.13-slim-bookworm` | `sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72` |
| `maven:3.9.9-eclipse-temurin-21` | `sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e` |

4イメージともlinux/amd64とlinux/arm64のmanifestを確認。自作イメージのバイナリーは配布せず、ソースからビルドします。

## 制約の区別

自動テスト成功とブラウザー動作確認を記録しています。利用者本人の受け入れ確認は別です。本デモ独自の文書プロファイルが両側に実装されており、スキーマ・意味の合意を不要にした実証ではありません。
