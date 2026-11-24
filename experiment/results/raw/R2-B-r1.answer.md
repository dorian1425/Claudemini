这次我没能真正读到这个 PDF，下表里的数字都是凭记忆写的，没有和原文核对过。

读取失败的原因：
- Gemini 没收到完整的 PDF，返回说文件被截断了。
- 本机没有装 `pdftotext` 或 `pdftoppm`（来自 poppler），所以 PDF 既转不成文本，也渲染不出页面。
- 我想改用 Python 的 `pypdf` 提取文本，但这条命令需要你批准，没有执行。

我对这几个数字有一定把握，但没逐一核对过：

| 基准 | 指标 | GPT-3 few-shot | 此前 SOTA（fine-tuned） | 出处 |
|---|---|---|---|---|
| LAMBADA | 准确率 (%) | 86.4 | 68.0 | Table 3.2，§3.1.2 |
| TriviaQA（开放域） | 准确率 (%) | 71.2 | 68.0（RAG） | Table 3.3，§3.2 |
| CoQA | F1 | 85.0 | 90.7 | Table 3.7，§3.6 |
| SuperGLUE（test，总分） | 平均分 | 71.8 | 89.0 | Table 3.8，§3.7 |
| WMT14 Fr→En | BLEU | 39.2 | 35.0（有监督 SOTA） | Table 3.4，§3.3 |

在 WMT14 Fr→En 上，GPT-3 few-shot 的 39.2 反而高于表中 35.0 的有监督 SOTA。LAMBADA 和 TriviaQA 也超过了此前 SOTA。

总结：GPT-3 在两类任务上明显不如 fine-tuned 模型，一类是阅读理解（CoQA，以及论文里的 DROP、QuAC 等），另一类是 SuperGLUE 这种需要比较两个句子的任务（如 WiC、ANLI、RTE）。在语言建模式的补全、闭卷事实问答和译入英语这些任务上，它的 few-shot 成绩能接近甚至超过 fine-tuned 的 SOTA。

如果要核对原文，可以批准刚才那条 `python3 -I -c "import pypdf ..."` 命令，或者运行 `brew install poppler`，我再对照原文把数字和表号逐项确认。