# Third-party software

This repository distributes tutorial source and build definitions, not prebuilt container images. The build fetches upstream components. Their licenses and notices remain applicable and are retained in installed packages/images.

| Component | Purpose | Upstream license at the selected version |
| --- | --- | --- |
| Keycloak 26.8.1 | Authentication / OAuth / RAR extension SPI | [Apache-2.0](https://github.com/keycloak/keycloak/blob/26.8.1/LICENSE.txt) |
| OPA 1.9.0 | Policy evaluation | [Apache-2.0](https://github.com/open-policy-agent/opa/blob/v1.9.0/LICENSE) |
| Starlette 1.10.0 | HTTP application | [BSD-3-Clause](https://github.com/Kludex/starlette/blob/1.10.0/LICENSE.md) |
| Uvicorn 0.54.0 | ASGI server | [BSD-3-Clause](https://github.com/Kludex/uvicorn/blob/0.54.0/LICENSE.md) |
| httpx 0.28.1 | HTTP client | [BSD-3-Clause](https://github.com/encode/httpx/blob/0.28.1/LICENSE.md) |
| PyJWT 2.15.1 | JWT validation | [MIT](https://github.com/jpadilla/pyjwt/blob/2.15.1/LICENSE) |

Base images also include Python, Maven, Eclipse Temurin/OpenJDK, Linux distribution packages, and transitive dependencies under their respective licenses. Consult the image and package notices before redistributing a built image. Version/digest information is in [docs/VALIDATION.md](docs/VALIDATION.md).

The local Keycloak providers and consent theme are tutorial additions. Upstream Keycloak source is not vendored or modified. The theme inherits the installed Keycloak theme. The owner's earlier cross-ecosystem-trust prototype ZIP was used as a design reference for Keycloak extension points; its application, datasets, and credential files are not included.

Protocol reference: [RFC 9396](https://www.rfc-editor.org/rfc/rfc9396.html). The document-access type and examples in this repository are tutorial-specific, not an IETF-registered business vocabulary.
