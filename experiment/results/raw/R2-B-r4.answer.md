这些数据由 Gemini 读论文提取，我没有自己打开 PDF 核对。五个核心数字都和我所知的 GPT-3 论文一致。

| 基准 | 指标 | GPT-3 175B few-shot | 此前 SOTA | 出处 |
|---|---|---|---|---|
| LAMBADA | 准确率（test，K=15） | **86.4%**（困惑度 1.92） | 68.0%（Turing-NLG 17B，不是 fine-tuned 成绩，是此前的 zero-shot SOTA）；困惑度 8.63（GPT-2） | Table 3.2（p.12）、Fig. 3.2 |
| TriviaQA | 准确率（闭卷，K=64，wiki split） | **71.2%** | 68.0%（RAG，fine-tuned，开放域设置）；闭卷 fine-tuned 为 60.5%（T5-11B+SSM） | Table 3.3（p.13） |
| CoQA | F1（dev，K=5） | 85.0 | **90.7**（fine-tuned SOTA） | Table 3.7（p.18） |
| SuperGLUE | 总分（test，K=32） | 71.8 | **89.0**（fine-tuned SOTA）；fine-tuned BERT-Large 为 69.0 | Table 3.8（p.19）、§3.7 |
| WMT14 Fr→En | BLEU（multi-bleu，K=64） | **39.2** | 35.0（有监督 SOTA；论文自己说明这个数字未必是真正的最佳成绩） | Table 3.4（p.15）、§3.3 |

加粗的是两者中较高的一方。

**总结：** GPT-3 few-shot 明显不如 fine-tuned 模型的，主要是需要比较两个句子或做推理的任务，例如 WiC、RTE、ANLI 这类 NLI 任务。另外是需要反复回读长文本的阅读理解任务，例如 RACE、DROP、QuAC。论文把原因归于自回归模型缺少双向注意力（§3.7–3.8、§5）。从英语译成其他语言（如 En→Fr、En→De）也明显落后于有监督 SOTA，这和上表里 Fr→En 反而超过 SOTA 的结果正好相反（§3.3）。