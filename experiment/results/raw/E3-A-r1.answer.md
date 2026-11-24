说明：你的全局 CLAUDE.md 让我把写作交给 Gemini，但这个会话里没有 `ask-gemini` 工具，所以全文是我自己写的。下面提到的类名、方法名和行号，我都对照 `src/requests/sessions.py`、`src/requests/adapters.py` 和 `src/requests/api.py` 核对过。

---

# 为什么要用 requests.Session？它和 HTTPAdapter 怎么配合？

## 先说"连接"是什么

浏览器或程序访问一个网站之前，要先和服务器建立一条 TCP 连接。如果是 HTTPS，还要再做一次 TLS 握手来协商加密。这两步都要来回传好几次消息，常常比请求本身还慢。

所以有一个直接的优化：**连接用完先不关，留着给下一个请求接着用。**存放这些空闲连接的地方叫"连接池"。可以把它想成食堂的碗柜，碗洗干净放回去下次再用，不用每顿饭都去买新碗。

## requests.get 每次都会"买新碗"

打开 `api.py`，`requests.get()` 最终调用的 `request()` 函数里是这样写的（第 58 行）：

```python
with sessions.Session() as session:
    return session.request(method=method, url=url, **kwargs)
```

也就是说，每调用一次 `requests.get()`，都会新建一个 `Session`，用完立刻关掉。连接池跟着这个 Session 一起被丢掉，下一次请求只能重新建连接。

## Session 自己并不管连接

看 `Session.__init__`（`sessions.py` 第 447–449 行）：

```python
self.adapters = OrderedDict()
self.mount("https://", HTTPAdapter())
self.mount("http://", HTTPAdapter())
```

Session 一创建，就给 `https://` 和 `http://` 两个前缀各"挂载"了一个 `HTTPAdapter`。真正干活的是这个适配器：它在 `init_poolmanager()` 里创建 urllib3 的 `PoolManager`，连接池就放在那里。默认的池子大小 `DEFAULT_POOLSIZE` 是 10。

一个请求的流程大致是：

1. 调用 `Session.send()` 后，它先执行 `self.get_adapter(url=request.url)`。
2. `get_adapter()` 依次检查 `self.adapters`，找到第一个和 URL 前缀匹配的适配器。`mount()` 会把较长的前缀排在前面，所以前缀匹配得越具体，越先被选中。
3. 适配器的 `HTTPAdapter.send()` 通过 `get_connection_with_tls_context()` 从池子里取出一个连接（没有就新建一个），再调用 `conn.urlopen()` 把请求发出去。

一句话分工：**Session 负责记住状态（cookies、默认 headers 等），并决定交给哪个适配器；HTTPAdapter 负责管理连接和真正收发数据。**只要 Session 还活着，它的适配器就还在，连接池也一直保留。

## 最短示例

```python
import requests

with requests.Session() as s:
    for i in range(5):
        r = s.get("https://httpbin.org/get")
        print(r.status_code)
```

这 5 次请求都访问同一个主机，后面几次可以直接复用第一次建好的连接。`with` 语句结束时会调用 `Session.__exit__()`，进而调用 `close()`，它会遍历所有适配器，把它们一一关闭。

如果想调整连接池或重试次数，可以自己挂一个适配器：

```python
from requests.adapters import HTTPAdapter
s.mount("https://", HTTPAdapter(pool_maxsize=20, max_retries=3))
```

## 常见误区：用了 Session，却每次都新建

```python
def fetch(url):
    with requests.Session() as s:   # 每次调用都新建 Session
        return s.get(url)
```

这种写法看起来用了 Session，实际上和直接调用 `requests.get()` 没有区别：函数一返回，Session 和它的连接池就一起关掉了。正确的做法是**在外面创建一个 Session，反复传进去使用**，等全部请求结束后再关闭。

## 小结

- 要发很多个请求，尤其是发给同一个网站时，就用一个长期存在的 `Session`。
- 连接池在 `HTTPAdapter` 里面，而不在 `Session` 里。Session 通过 `mount()` 和 `get_adapter()` 把请求交给它。
- 用完记得调用 `close()`，或者直接用 `with` 语句。