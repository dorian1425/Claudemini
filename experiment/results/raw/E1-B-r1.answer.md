下面这条调用链从 `requests.get(url)` 一直走到 urllib3 发出连接。我先用 Gemini 读了源码，再用 grep 逐个核对了函数所在行号，下面的行号都对得上。路径都相对于 `src/requests/`。

**调用链（按执行顺序）**

1. `api.py:62` `get()` → 调用 `request("get", url, params=params, **kwargs)`。
2. `api.py:14` `request()` → 在 `api.py:58` 执行 `with sessions.Session() as session:`，然后在 `:59` 调用 `session.request(...)`。
3. `sessions.py:390` `Session.__init__` → 在 `:448-449` 调用 `self.mount("https://" / "http://", HTTPAdapter())`。`sessions.py:799` 的 `mount` 把适配器按前缀登记好，前缀越长越先匹配。
4. `adapters.py:202` `HTTPAdapter.__init__` → `adapters.py:240` `init_poolmanager`，在 `:259` 创建 urllib3 的 `PoolManager`。**连接池管理器就在这里创建**，每个 Session 会有两个。
5. `sessions.py:500` `Session.request` → 用传入参数构造 `Request` 对象，再依次调用 `prepare_request`、`merge_environment_settings` 和 `send`。
6. `sessions.py:457` `Session.prepare_request` → 把 Session 级和本次请求的 cookies、headers、params、auth（包括 `.netrc`）、hooks 合并起来。然后在 `:483` 执行 `p = PreparedRequest()`，再调用 `p.prepare(...)`。
7. `models.py:351` `PreparedRequest.prepare` → 依次处理 method、url、headers、cookies、body、auth、hooks，得到一个可以直接发送的请求。
8. `sessions.py:750` `merge_environment_settings` → 当 `trust_env=True` 时，读取环境变量里的代理设置和 CA 证书路径，再和 `verify`/`cert`/`stream` 合并。
9. `sessions.py:673` `Session.send` → 先在 `sessions.py:781` 用 `get_adapter` 按 URL 前缀选出适配器，再在 `:703` 调用 `adapter.send(...)`。返回后它会跑 response hook、提取 cookies，并通过 `resolve_redirects` 处理重定向（`:723`）。如果不是 stream 模式，在 `:746` 读取 `r.content`。
10. `adapters.py:613` `HTTPAdapter.send` → 这是发送的核心，下面第 11 到 13 条都在它里面依次执行。
11. `adapters.py:446` `get_connection_with_tls_context` → 先经过 `:396` `build_connection_pool_key_attributes`，再到 `:90` `_urllib3_request_context`，算出 scheme/host/port 和 TLS 参数。然后在 `:489` 调用 `self.poolmanager.connection_from_host(...)`，走代理时是 `:484` 的 `proxy_manager.connection_from_host`，代理管理器由 `:266` `proxy_manager_for` 在第一次用到时创建并缓存。**连接池在这里复用**：(scheme, host, port, TLS 参数) 相同的请求拿到的是同一个 `ConnectionPool`，也就复用它里面保持着的 keep-alive 连接。
12. `adapters.py:304` `cert_verify` 在连接池上设置证书校验和客户端证书。`:546` `request_url` 算出要发的 URL：直连时只用路径，经 HTTP 代理时用完整 URL。`:578` `add_headers` 默认什么都不做，留给子类扩展。
13. `adapters.py:667` `conn.urlopen(..., redirect=False, preload_content=False)` → 进入 urllib3 的 `ConnectionPool.urlopen`，**在这里才真正建立或复用 TCP/TLS 连接，并发出 HTTP 报文**。之后 `adapters.py:359` `build_response` 把 urllib3 的响应包装成 `requests.Response` 返回。

**三个核心对象各管什么**

14. **Session** 保存跨请求的状态（默认 headers、cookies、auth、proxies、适配器表），并负责安排流程：准备请求、合并环境设置、选适配器、处理重定向和 hooks。**PreparedRequest** 是经过编码和合并后的最终请求（method、url、headers、body），之后不再改动。**HTTPAdapter** 是传输层，连接 requests 和 urllib3：管理 PoolManager 和 ProxyManager、处理 TLS 和超时、把 urllib3 的异常转换成 requests 的异常、构造 Response。
15. **连接池实际上不跨调用复用**：`requests.get()` 每次都会新建一个 Session，退出 `with` 时依次触发 `Session.__exit__`（`sessions.py:454`）、`Session.close`（`:794`）和 `HTTPAdapter.close`（`adapters.py:536`），最后在 `:542` 执行 `poolmanager.clear()`，所有池化连接都被关掉。所以连续多次调用 `requests.get()` 不会复用 TCP/TLS 连接，只有同一次请求里的重定向能复用。想复用连接，就要自己创建一个 `requests.Session()` 并反复使用它。