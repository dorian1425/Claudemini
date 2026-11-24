这条链路主要在 4 个文件里：`api.py`、`sessions.py`、`models.py`、`adapters.py`。下面的行号都是在源码里定位过的。

**调用链（按顺序）**

1. **`requests.get(url)`**，`src/requests/api.py:62`：只做转发，到第 73 行调用 `request("get", url, params=params, **kwargs)`。
2. **`api.request()`**，`src/requests/api.py:14`：在第 58–59 行用 `with sessions.Session() as session:` 新建一个临时 Session，再调用 `session.request(...)`。请求结束后 Session 会关闭，它的连接池也随之丢弃。
3. **`Session.__init__()`**，`src/requests/sessions.py:390`：设置默认 headers（第 394 行），新建 `self.adapters = OrderedDict()`（第 447 行），并在第 448–449 行给 `https://` 和 `http://` 各挂一个 `HTTPAdapter()`（`mount`，第 799 行）。
4. **`HTTPAdapter.__init__()`**，`src/requests/adapters.py:202`：第 222 行调用 `self.init_poolmanager(...)`。
5. **`HTTPAdapter.init_poolmanager()`**，`adapters.py:240`：第 259 行 `self.poolmanager = PoolManager(...)`，**连接池管理器在这里创建**。
6. **`Session.request()`**，`sessions.py:500`：用参数构造 `Request`，第 575 行调用 `self.prepare_request(req)`。接着用 `merge_environment_settings`（第 750 行）合并环境变量里的代理、`verify` 等设置，然后在第 589 行调用 `self.send(prep, **send_kwargs)`。
7. **`Session.prepare_request()`**，`sessions.py:457`：把 Session 级的 headers、cookies、auth 和本次请求的参数合并，在第 484 行调用 `p.prepare(...)`。
8. **`PreparedRequest.prepare()`**，`src/requests/models.py:351`：第 366–377 行依次执行 `prepare_method`（393）、`prepare_url`（409，编码 URL 并拼接 params）、`prepare_headers`（483）、`prepare_cookies`、`prepare_body`（494）、`prepare_auth`（588）、`prepare_hooks`（630）。
9. **`Session.send()`**，`sessions.py:673`：用 `get_adapter(url)`（第 781 行，按 URL 前缀找最长匹配）选出 adapter，第 703 行调用 `adapter.send(request, **kwargs)`。返回后在第 710 行触发 response hook，第 718 行提取 cookies，第 723 行调用 `resolve_redirects`（第 159 行）处理重定向。每一跳重定向都会再走一次 `self.send`（第 265 行）。
10. **`HTTPAdapter.send()`**，`adapters.py:613`：第 633 行调用 `get_connection_with_tls_context(...)` 取得连接池；然后执行 `cert_verify`、`request_url`、`add_headers`，并把 timeout 包装成 `TimeoutSauce`。
11. **`HTTPAdapter.get_connection_with_tls_context()`**，`adapters.py:446`：先通过 `build_connection_pool_key_attributes`（第 396 行，内部调用 `_urllib3_request_context`，第 90 行）算出 scheme、host、port 和 TLS 参数。有代理时在第 483–484 行走 `proxy_manager_for(...).connection_from_host`，没有代理时在第 489 行走 `self.poolmanager.connection_from_host(...)`。**连接池在这里复用**：urllib3 按这组 key 查找已有的 `HTTPConnectionPool`/`HTTPSConnectionPool`，找不到才新建。
12. **`conn.urlopen(...)`**，`adapters.py:667`：交给 urllib3，传入 `redirect=False`（重定向由 requests 自己处理）、`preload_content=False`、`retries=self.max_retries`。urllib3 从池里取一个空闲连接或新建一个 TCP/TLS 连接，**HTTP 请求在这里真正发出**。返回后由 `build_response`（第 359 行）包装成 `requests.Response`。

**三个核心对象的分工**

13. **Session**：保存跨请求共享的状态，包括默认 headers、cookies、auth、proxies 和 hooks。它负责把这些设置合并进每个请求，按 URL 前缀选择 adapter，并处理重定向和 cookie 回写。
14. **PreparedRequest**：最终要发送的请求本体。method、URL、headers 和 body 都已编码定型，可以直接交给传输层，不再含任何 Session 逻辑。
15. **HTTPAdapter**：传输层，负责和 urllib3 对接。它持有 `PoolManager` 和代理用的 `proxy_manager`，负责 TLS 校验、超时、重试，并把 urllib3 的异常转换成 requests 的异常。**连接池创建于** `init_poolmanager`（`adapters.py:259`），**按 host 复用于** `connection_from_host`（`adapters.py:489`，代理走 484）。因为 `requests.get()` 每次都新建 Session，连续调用之间不会复用连接；要复用，就自己持有一个 `requests.Session()` 反复调用。

这个任务用 Grep 加几段局部 Read 就能完成，所以没有交给 Gemini。