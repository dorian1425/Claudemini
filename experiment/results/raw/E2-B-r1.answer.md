根本原因在 `get_encoding_from_headers()` 里，`text/*` 类型的默认编码被改成了 `utf-8`。

- **位置**：`src/requests/utils.py:556-557`，函数 `get_encoding_from_headers(headers)`。
- **改动后的代码**：
  ```python
  if "text" in content_type:
      return "utf-8"
  ```
  上游 requests 这里写的是 `return "ISO-8859-1"`。依据是 RFC 2616 §3.7.1：`text/*` 类型没有声明 charset 时，默认是 ISO-8859-1。
- **触发过程**：遇到 `Content-Type: text/html` 时，`_parse_content_type_header()`（`utils.py:514`）解析出 `content_type="text/html"`、`params={}`。第 553 行的 `"charset" in params` 不成立，于是走到第 556 行，`"text" in "text/html"` 成立，函数返回 `utf-8`。
- **怎么变成 `response.encoding` 的**：`src/requests/adapters.py:378` 的 `build_response()` 执行 `response.encoding = get_encoding_from_headers(response.headers)`，把这个错误的默认值直接赋给了 `response.encoding`。
- **为什么会乱码**：`encoding` 已经有值（不是 `None`），所以 `Response.text` 不会再用 `apparent_encoding` 去猜，而是直接按 UTF-8 解码。老网页如果其实是 Latin-1，或 GBK 之类的编码（它们原本靠 ISO-8859-1 的默认值，或调用方自己重新设置编码来处理），解出来就会是乱码或替换字符。
- **其他代码路径**：`utils.py:615` 的 `get_unicode_from_response()` 也调用这个函数，所以它也会受影响。
- **和测试的冲突**：`tests/test_utils.py:619` 期望 `{"content-type": "text/plain"}` 返回 `"ISO-8859-1"`，也就是说这个改动会让现有测试失败。这和上面的判断一致。
- **不要搞混**：第 559-561 行给 `application/json` 默认 `utf-8` 是正常的（依据 RFC 4627），上游本来就是这样，不是问题所在。

我没有修改任何文件，也没有实际运行测试。