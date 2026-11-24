这次没做出对比，因为三篇 PDF 我一页都没读到。你要求每个数字都出自原文，我不想凭记忆填表。

具体卡在这几处：
- **Gemini**：CLAUDE.md 里说长 PDF 交给 `ask-gemini`，但这个会话里没有这个工具（gemini-cli MCP 没加载）。
- **命令行**：机器上没有 `pdftotext`。我想用 Python 检查 PDF 库，这条命令需要你授权，没有通过。
- **直接读 PDF**：Read 工具渲染页面要靠 `pdftoppm`，也没装，三篇都报错。

下面任选一种，我就能继续：
1. **批准 Python 命令**：允许我运行 `python3 -I -c "import pypdf"`。如果装了 pypdf，我把 PDF 转成文本存到临时目录，再按关键词定位。
2. **安装 poppler**：`brew install poppler`。装好后 `pdftotext` 和按页读 PDF 都能用。
3. **启用 gemini-cli MCP**：按你的 CLAUDE.md，GPT-3 有 75 页，本来就该交给 Gemini 读。

能读之后，我只看相关的几页：Transformer 的 §5.1 和 Table 3，BERT 的 §3 和 §5，GPT-3 的 §2.1 和 Table 2.1、2.2。然后按你要的格式出表，每个数字都注明出处。