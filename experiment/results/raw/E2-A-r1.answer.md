问题出在 `get_encoding_from_headers` 里：对没有 charset 的 `text/*` 类型，它返回的默认值被改成了 `"utf-8"`。我只读了代码，没有修改文件，也没有运行代码复现。

- **位置**：`src/requests/utils.py:556-557`，函数 `get_encoding_from_headers()`：
  ```python
  if "text" in content_type:
      return "utf-8"
  ```
  上游 requests 这里返回的是 `"ISO-8859-1"`。

- **为什么会这样**：`Content-Type: text/html` 经 `_parse_content_type_header()`（`utils.py:514`）解析后，`params` 里没有 `charset`。所以第 553 行的判断不成立，接着走到第 556 行，`"text" in "text/html"` 为真，直接返回 `"utf-8"`。

- **怎么变成 `response.encoding` 的**：`src/requests/adapters.py:378` 的 `build_response()` 执行 `response.encoding = get_encoding_from_headers(response.headers)`，把这个错误的默认值写进了 `response.encoding`。

- **为什么会乱码**：`response.text` 只在 `encoding` 为 `None` 时才调用 `apparent_encoding`（chardet / charset_normalizer）去猜编码。现在拿到的是一个非空的 `"utf-8"`，就不会再猜，而是直接用 UTF-8 解码。老网页通常是 Latin-1、GBK 之类的编码，按 UTF-8 解码就会乱码或出现替换字符。

- **为什么能确定上游是 ISO-8859-1**：RFC 2616 §3.7.1 规定，`text/*` 没有指定 charset 时默认是 ISO-8859-1，上游 requests 一直按这个实现。

- **同一函数的 JSON 分支没问题**：第 559-561 行对 `application/json` 返回 `"utf-8"`，这和上游一致（依据 RFC 4627），不是本次的 bug。

- **还有一处也受影响**：`utils.py:615` 的 `get_unicode_from_response()` 也调用了这个函数，会被同一个默认值带偏。

- **怎么修**：把第 557 行改回 `return "ISO-8859-1"` 就行。