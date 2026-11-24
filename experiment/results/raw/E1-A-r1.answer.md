本会话里没有 CLAUDE.md 提到的 Gemini 工具（`ask-gemini`），所以源码是我自己读的。下面路径都相对于 `src/requests/`。

**调用链（按顺序）**

1. `api.py:62` `get(url, params=None, **kwargs)`：只调用 `request("get", url, params=params, ...)`（`api.py:73`）。
2. `api.py:14` `request()`：用 `with sessions.Session() as session:` 新建一个临时 Session（`api.py:58`），再调用 `session.request(...)`（`api.py:59`）。`with` 块结束时 Session 会被关闭，它的连接池也一起释放。
3. `sessions.py:447-449` `Session.__init__`：创建 `self.adapters = OrderedDict()`，然后 `mount("https://", HTTPAdapter())` 和 `mount("http://", HTTPAdapter())`（`mount` 在 `sessions.py:799`）。
4. `adapters.py:202` `HTTPAdapter.__init__`：在 `adapters.py:222` 调用 `init_poolmanager(pool_connections, pool_maxsize, block=...)`。
5. `adapters.py:240` `init_poolmanager`：在 `adapters.py:259` 执行 `self.poolmanager = PoolManager(...)`。**连接池管理器在这里创建**（urllib3 的 PoolManager，默认 10 个池，每个池最多 10 个连接）。
6. `sessions.py:500` `Session.request`：先构造用户层的 `Request` 对象（`models.py:230`），然后 `prep = self.prepare_request(req)`（`sessions.py:575`），再用 `merge_environment_settings`（`sessions.py:750`）合并环境变量里的代理、`verify`、`cert` 等设置，最后 `self.send(prep, **send_kwargs)`（`sessions.py:589`）。
7. `sessions.py:457` `Session.prepare_request`：把 Session 级的 headers、cookies、auth、params 与本次请求的参数合并，再调用 `PreparedRequest.prepare(...)`（`sessions.py:484`）。
8. `models.py:351` `PreparedRequest.prepare`：依次调用 `prepare_method`（393）、`prepare_url`（409）、`prepare_headers`（483）、`prepare_cookies`（610）、`prepare_body`（494）、`prepare_auth`（588）和 `prepare_hooks`（630）。`prepare_body` 内部还会调用 `prepare_content_length`（572）。
9. `sessions.py:673` `Session.send`：用 `self.get_adapter(url=request.url)`（`sessions.py:697`，定义在 `sessions.py:781`）按 URL 前缀找到对应的 adapter，然后 `r = adapter.send(request, **kwargs)`（`sessions.py:703`）。拿到响应后接着处理：response 钩子（710）、提取 cookies（718）、跟随重定向 `resolve_redirects`（723，内部又回到 `self.send`，见 `sessions.py:265`）。
10. `adapters.py:613` `HTTPAdapter.send`：先 `get_connection_with_tls_context(...)`（633）取连接池，然后依次做 `cert_verify`（304）、`request_url`（546）、`add_headers`（578），并处理 timeout 和 chunked 参数。
11. `adapters.py:446` `get_connection_with_tls_context`：先用 `build_connection_pool_key_attributes`（396）根据 scheme、host、port 和 TLS 参数算出池的 key。不走代理时调用 `self.poolmanager.connection_from_host(...)`（489）；走代理时先 `proxy_manager_for(proxy)`（266/483），再调用它的 `connection_from_host`（484）。**连接池在这里复用**：key 相同就拿到同一个 `HTTPConnectionPool`/`HTTPSConnectionPool`，没有才新建。
12. `adapters.py:667` `conn.urlopen(...)`：从这一步起交给 urllib3。它从池里取一个空闲连接，没有就新建，然后真正发出 HTTP 请求。调用时传了 `redirect=False`（重定向由 requests 自己处理）和 `retries=self.max_retries`。拿到原始响应后，由 `build_response`（359）包装成 `requests.Response`。

**三个核心类的分工**

13. **Session**：保存跨请求共享的状态，包括 headers、cookies、auth、proxies 和已挂载的 adapters。它负责合并参数、选择 adapter、处理重定向、cookie 和钩子，本身不碰网络。
14. **PreparedRequest**：把参数编码成可以直接发送的最终形态，包括规范化的 URL、headers、body、Content-Length，以及应用 auth 和 cookies 后的结果，是一个与传输无关的数据对象。**HTTPAdapter**：传输层，负责持有 PoolManager 和代理管理器，按 TLS 上下文选择连接池，设置超时和重试，调用 urllib3 的 `urlopen`，再把结果包装成 Response。
15. **连接池小结**：在 `HTTPAdapter.__init__` → `init_poolmanager`（`adapters.py:259`）创建；在 `get_connection_with_tls_context` → `connection_from_host`（`adapters.py:489`）按 host 和 TLS key 复用池，池内的连接再由 urllib3 复用。要注意的是，`requests.get()` 每次都新建并关闭一个 Session，所以**连接无法跨调用复用**。想复用连接，需要自己持有一个 `requests.Session()`，用它发多个请求。