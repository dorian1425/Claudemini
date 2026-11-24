`requests.get(url)` 的调用链，按调用顺序（路径相对 `src/requests/`，行号是函数定义行或关键调用行）：

1. **`api.get`**（`api.py:62`）：只在 `:73` 调 `request("get", url, params=params, **kwargs)`。
2. **`api.request`**（`api.py:14`）：在 `:58` 用 `with sessions.Session() as session:` 新建一个临时 Session，`:59` 调 `session.request(...)`。`with` 块结束时 Session 关闭，它的连接池也随之销毁。
3. **`Session.__init__`**（`sessions.py:390`）：在 `:448-449` 对 `https://` 和 `http://` 各 `mount` 一个 `HTTPAdapter()`。挂载方法是 `Session.mount`（`:799`），每个前缀对应一个适配器。
4. **`HTTPAdapter.__init__`**（`adapters.py:202`）：在 `:222` 调 `init_poolmanager`（`:240`）。**连接池管理器在这里创建**：`:259` 执行 `self.poolmanager = PoolManager(...)`，默认 `pool_connections=10`、`pool_maxsize=10`。
5. **`Session.request`**（`sessions.py:500`）：`:563` 构造用户级的 `Request` 对象，`:575` 调 `prepare_request`，`:579` 调 `merge_environment_settings`（`:750`，合并环境变量里的代理、`REQUESTS_CA_BUNDLE` 等），`:589` 调 `self.send(prep, **send_kwargs)`。
6. **`Session.prepare_request`**（`sessions.py:457`）：把 Session 级的 headers、cookies、auth、params 和本次请求的参数合并，在 `:484` 调 `p.prepare(...)`，这里的 `p` 是新建的 `PreparedRequest`。
7. **`PreparedRequest.prepare`**（`models.py:351`）：依次执行 `prepare_method`、`prepare_url`、`prepare_headers`、`prepare_cookies`、`prepare_body`、`prepare_auth`、`prepare_hooks`（`:366-377`），产出可以直接发送的请求，包括编码后的 URL、最终的 headers 和 body。
8. **`Session.send`**（`sessions.py:673`）：`:697` 用 `get_adapter`（`:781`）按 URL 前缀找到对应的适配器，`:703` 调 `adapter.send(request, **kwargs)`。拿到响应后，`:710` 触发 response hook；如果遇到重定向，`:723` 的 `resolve_redirects` 会再次走 `send`，`:724` 把中间响应收集进 `history`。
9. **`HTTPAdapter.send`**（`adapters.py:613`）：`:633` 获取连接池，`:639` 执行 `cert_verify`，`:640` 用 `request_url` 算出要发的路径（走代理时用完整 URL），`:641` 执行 `add_headers`。
10. **`HTTPAdapter.get_connection_with_tls_context`**（`adapters.py:446`）：先用 `build_connection_pool_key_attributes`（`:396`）生成池的键（scheme、host、port 加 TLS 参数），然后在 `:489` 调 `self.poolmanager.connection_from_host(...)`；走代理时改用 `:484` 的 `proxy_manager`。**连接池在这里复用**：相同 key 的请求拿到的是同一个 urllib3 `HTTPConnectionPool`。
11. **`conn.urlopen(...)`**（`adapters.py:667`）：进入 urllib3，从池里取出空闲连接或新建 TCP/TLS 连接，然后发出 HTTP 请求。这一步是 requests 和 urllib3 的分界线，真正的网络 I/O 在这之后。`:719` 的 `build_response` 把 urllib3 的响应包装成 `requests.Response`。
12. **Session 的职责**：持有跨请求共享的状态（cookies、headers、auth、代理），合并参数，选择适配器，处理重定向和 hooks。它本身不碰网络。
13. **PreparedRequest 的职责**：一个不再改动的请求快照，负责 URL、headers、body、auth 的最终编码。它是 Session 和 Adapter 之间传递的数据。
14. **HTTPAdapter 的职责**：传输层。它管理 `PoolManager` 和 `ProxyManager`，负责 TLS 证书校验、超时和重试，并把 urllib3 的异常转换成 requests 的异常。
15. **连接池小结**：池在 `HTTPAdapter.__init__` 里通过 `init_poolmanager` 创建（`adapters.py:259`），在 `connection_from_host` 按 key 复用（`adapters.py:489`）。不过 `requests.get()` 每次调用都会新建并关闭一个 Session，所以**连续多次调用 `requests.get` 之间不会复用连接**。要复用连接，需要自己持有一个 `requests.Session()` 反复使用。

这次用 Grep 定位了函数定义和关键调用的行号，没有逐个函数通读源码。上面的职责说明来自定位到的那几行加上我对 requests 的了解。