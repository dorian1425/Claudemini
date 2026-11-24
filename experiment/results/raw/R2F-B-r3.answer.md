下表数据全部来自 Gemini 的提取结果。我自己没有读 PDF，也没有逐页核对，只拿这几个数和我记忆中的论文数字比过一遍，没发现出入。

| 基准 | 指标 | GPT-3 175B few-shot | 此前 SOTA | 出处 |
|---|---|---|---|---|
| LAMBADA | 准确率 / 困惑度（test，K=15） | 86.4% / 1.92 | 68.0%（Turing-NLG 17B）/ 8.63（GPT-2） | 表 3.2，§3.1.2 |
| TriviaQA | 闭卷准确率（wiki split，test，K=64） | 71.2% | 68.0%（RAG，开放域 fine-tuned）；闭卷 fine-tuned 为 60.5%（T5-11B+SSM） | 表 3.3，§3.2 |
| CoQA | F1（dev，K=5） | 85.0 | 90.7（fine-tuned SOTA） | 表 3.7，§3.6 |
| SuperGLUE（总分） | 平均分（test，K=32） | 71.8（dev 为 73.2） | 89.0（fine-tuned SOTA，T5-11B）；作为参照，BERT-Large 为 69.0 | 表 3.8，§3.7 |
| WMT14 Fr→En | BLEU（multi-bleu，test，K=64） | 39.2（SacreBLEU 为 41.4） | 35.0（有监督 SOTA）；无监督 SOTA 为 34.9（MASS） | 表 3.4，§3.3 |

另有汇总表 H.1（第 63 页）同时列出以上各项。五项中只有 CoQA 和 SuperGLUE 是 GPT-3 落后；LAMBADA、TriviaQA 和 Fr→En 翻译它都超过了此前的 SOTA。

**总结：** GPT-3 明显落后于 fine-tuned 模型的，主要是需要比较两段文本的任务，比如 NLI（ANLI、RTE）和 WiC。WiC 上它只有 49.4，基本是随机水平，fine-tuned 模型是 76.1；论文认为原因是自回归模型看不到双向上下文。另一类是需要深入推理的阅读理解和科学问答，比如 RACE、QuAC、DROP、ARC。翻译方向也有影响：译入英语时它表现很好，但从英语译出（En→Fr、En→Ro 等）时，仍比有监督 SOTA 低 10 BLEU 以上。