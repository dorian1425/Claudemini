我没能读到 PDF：本机没装 `pdftotext`/`pdftoppm`，Read 工具也就渲染不了 PDF 页面；改用 Python（pypdf）提取文本时，命令需要你批准，这次没有获批。CLAUDE.md 里配置的 Gemini 工具在本会话中也不可用。

所以下面的数字**是我凭记忆给的，没有对照 PDF 核对过**。这些都是这篇论文常被引用的数字，我比较有把握，但引用之前请再核对一下。最没把握的是 WMT14 Fr→En 那一行的 SOTA。

| 基准 | 指标 | GPT-3 175B few-shot | 此前 SOTA（fine-tuned） | 出处 |
|---|---|---|---|---|
| LAMBADA | 准确率 (acc) | 86.4 | 68.0 | 表 3.2，§3.1.2 |
| TriviaQA | 准确率（开放域） | 71.2 | 68.0（RAG，fine-tuned） | 表 3.3，§3.2 |
| CoQA | F1 | 85.0 | 90.7 | 表 3.7，§3.6 |
| SuperGLUE（总分） | 平均分（测试集） | 71.8 | 89.0 | 表 3.8，§3.7 |
| WMT14 Fr→En | BLEU | 39.2 | 35.0（有监督） | 表 3.4，§3.3 |

说明：
- 表 3.4 的 SOTA 一行里，45.6 是 En→Fr 方向的成绩，Fr→En 方向是 35.0。按这个读法，GPT-3 在 Fr→En 上 few-shot 就超过了此前的有监督 SOTA。这一点我最没把握，请特别核对。
- SuperGLUE 上 GPT-3 few-shot 略高于 fine-tuned BERT-Large（69.0），但比 SOTA 低约 17 分。

总结：GPT-3 明显不如 fine-tuned 模型的，主要是阅读理解（CoQA，以及差距更大的 DROP、QuAC、RACE）和需要比较两段文本的任务，包括自然语言推理（RTE、ANLI）和 WiC。在开放域问答、补全类语言建模和译入英语的翻译上，它接近甚至超过此前的 SOTA。

如果你批准运行 `python3`（用 pypdf 提取文本），或者装一下 poppler（`brew install poppler`），我可以逐项对照原文核对，并把需要改的地方改掉。