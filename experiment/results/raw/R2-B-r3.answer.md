我用 pdftotext 把论文转成文本，再用 grep 定位五张结果表。表格不大，自己读比交给 Gemini 更省，所以没有调用它。

| 基准 | 指标 | GPT-3 175B few-shot | 此前 SOTA | 出处 |
|---|---|---|---|---|
| LAMBADA | 准确率 (%) | **86.4**（困惑度 1.92） | 68.0（困惑度 8.63） | 表 3.2，§3.1.2 |
| TriviaQA | 准确率 (%) | **71.2** | 68.0（RAG，fine-tuned，开放域）；闭卷 fine-tuned 最佳 60.5（T5-11B+SSM） | 表 3.3，§3.2 |
| CoQA | F1 | 85.0 | **90.7** | 表 3.7，§3.6 |
| SuperGLUE（总分） | 平均分 | 71.8 | **89.0**（fine-tuned BERT-Large 为 69.0） | 表 3.8，§3.7 |
| WMT14 Fr→En | BLEU | **39.2** | 35.0（有监督） | 表 3.4，§3.3 |

几点说明：
- **LAMBADA**：表中的 68.0 不是 fine-tuned 成绩，而是此前大模型 Turing-NLG（17B）的结果。few-shot 用的是填空格式。
- **TriviaQA**：few-shot 成绩是在 wiki split 测试服务器上测的。GPT-3 是闭卷作答，却超过了开放域检索模型 RAG。
- **WMT14 Fr→En**：few-shot 超过了有监督 SOTA。但反方向 En→Fr 只有 32.6，低于有监督的 45.6。翻译成英文强，从英文翻出去弱。

**总结：** GPT-3 在阅读理解和需要比较两段文本的任务上明显不如 fine-tuned 模型。例如 DROP（36.5 对 89.1）、QuAC、RACE，以及 SuperGLUE 里的 WiC（49.4，接近随机）和 CB（F1 52.0），差距都很大。它占优的是语言建模、闭卷知识问答，以及翻译成英文这类主要靠预训练知识的任务。