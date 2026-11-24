| 基准 | 指标 | GPT-3 few-shot（175B） | 此前 SOTA | 出处 |
|---|---|---|---|---|
| LAMBADA | 准确率 | **86.4** | 68.0（Turing-NLG [Tur20]） | 表 3.2，§3.1.2 |
| TriviaQA | 准确率（wiki split 测试服务器） | **71.2** | 68.0（RAG，fine-tuned，开放域） | 表 3.3，§3.2 |
| CoQA | F1 | 85.0 | **90.7**（fine-tuned） | 表 3.7，§3.6 |
| SuperGLUE（平均分） | 平均分 | 71.8 | **89.0**（fine-tuned；BERT-Large fine-tuned 为 69.0） | 表 3.8，§3.7 |
| WMT14 Fr→En | BLEU | **39.2** | 35.0（有监督） | 表 3.4，§3.3 |

两点说明：
- LAMBADA 的"此前 SOTA"是 Turing-NLG 的成绩，不是 fine-tuned 模型。论文表 3.2 只写"SOTA"，引用 [Tur20]。
- WMT14 Fr→En 的 BLEU 用 multi-bleu.perl 加 XLM 分词计算。SacreBLEU 的结果在附录 H。

**总结：** GPT-3 明显落后 fine-tuned 模型的，是需要比较两段文本或在长段落上做推理的任务，比如 SuperGLUE 里的 WiC（49.4，接近随机水平）、RTE、CB，还有 DROP、QuAC、RACE 这类阅读理解（例如 DROP 36.5 对 89.1）。它擅长的是语言建模、补全和知识问答；在推理和阅读理解上，平均比 fine-tuned SOTA 低十几到几十分。

（提取方式：用 pdftotext 把 PDF 转成文本，再按 SOTA 行只读出相关表格，没有通读全文。）