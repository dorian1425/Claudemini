# 为什么要用 requests.Session，以及 Session 和 HTTPAdapter 是怎么配合的

## 每次用 `requests.get()`，问题在哪？

假设你要向同一个网站连发三次请求，直接写三次 `requests.get()`。这有点像给朋友打电话，说完一句就挂断，下一句再重新拨号。真正说话没几秒，时间都花在反复拨号、也就是反复建立连接上了。

源码里能看到原因。`requests.get()` 这类函数最后都会调用 `api.py` 里的 `request()`，它的核心只有一句：

```python
with sessions.Session() as session:
    return session.request(method=method, url=url, **kwargs)
```

所以每调用一次 `requests.get()`，requests 就新建一个 `Session`，用完马上关掉。连接刚建好就被扔掉，下一次请求用不上。

## `Session` 是什么？

`Session` 就是那通先不挂断的电话。多次请求都通过同一个 `Session` 发出，底层的网络连接就能留下来接着用。它还会在多次请求之间保留 cookies、headers 等信息，不用每次手动再传。

`Session` 实现了 `__enter__` 和 `__exit__`，所以可以写在 `with` 语句里，离开代码块时会自动关闭。

## 分工：`Session` 决定交给谁发，`HTTPAdapter` 负责发出去

连接池其实不是 `Session` 自己管的。它和 `HTTPAdapter`（适配器）各管一部分。

**`Session` 决定请求交给哪个适配器。** `Session.__init__` 先建一个 `self.adapters = OrderedDict()`，再执行 `self.mount("https://", HTTPAdapter())` 和 `self.mount("http://", HTTPAdapter())`。`mount(prefix, adapter)` 的作用是把适配器登记到一个 URL 前缀上，登记后按前缀长度从长到短排好。发请求时，`Session.send()` 调用 `get_adapter(url)`，找出第一个能和 URL 开头对上的前缀（不区分大小写），把对应的适配器拿出来；一个都对不上就抛出 `InvalidSchema`。接下来执行 `adapter.send(request, **kwargs)`，真正把请求发到网络上的是适配器。

**`HTTPAdapter` 负责发请求，连接池也在它手里。** 连接池可以想成一排一直接通的电话线，用完放回去，下次直接拿来用。`HTTPAdapter` 有两个和连接池有关的参数：`pool_connections` 表示最多缓存多少个连接池（大致每个主机一个），`pool_maxsize` 表示每个池里最多留多少条连接，两者默认都是 10（`DEFAULT_POOLSIZE`）。重试次数 `max_retries` 默认是 0。创建适配器时会调用 `init_poolmanager()`，建好一个 urllib3 的 `PoolManager`，存在 `self.poolmanager` 里。

关闭时，`Session.close()` 会挨个调用每个适配器的 `close()`，`HTTPAdapter.close()` 再执行 `self.poolmanager.clear()`，池里的连接这时才真正断开。

## 最短代码示例

```python
import requests
from requests.adapters import HTTPAdapter

with requests.Session() as s:
    # 同样挂在 "https://" 上，会替换掉默认的那个 HTTPAdapter
    s.mount("https://", HTTPAdapter(max_retries=3))
    for i in range(3):
        r = s.get("https://httpbin.org/get")
        print(r.status_code)
```

三次请求用的都是同一个适配器里的连接池。代码离开 `with` 块时连接会自动关闭。

## 常见误区

初学者常在循环里反复写 `requests.get(...)`，或者写成这样：

```python
for i in range(3):
    with requests.Session() as s:   # 每次循环都新建一个 Session
        r = s.get("https://httpbin.org/get")
```

看上去用了 `Session`，其实每循环一次就新建一个 `Session` 和一套新的连接池，连接一次也没复用。正确做法是在循环外面创建一个 `Session`，循环里一直用它，最后交给 `with` 自动 `close()`。

## 一句话总结

`Session` 保存会话状态，并按 URL 前缀把请求交给对应的 `HTTPAdapter`。`HTTPAdapter` 通过 urllib3 的 `PoolManager` 发出请求并复用连接。想复用连接，就把 `Session` 建在循环外面。

---

这篇文章按你的 CLAUDE.md 先由 Gemini 起草。文中引用的类名、方法名和默认值，我都对照了 `api.py`、`sessions.py`、`adapters.py` 的相关代码，并改掉了草稿里一处没核实过的参数默认值。正文大约 900 字，不算代码，在你给的范围上限附近。