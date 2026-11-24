我没做抽查。按要求我不能读 PDF，也不能运行 pdftotext，所以没有其他途径核对数字。下面所有数字都来自 Gemini 从论文原文提取的结果，出处也是它给的，没有经过独立验证。

## 1. 对比表

| | Transformer (1706.03762) | BERT (1810.04805) | GPT-3 (2005.14165) |
|---|---|---|---|
| **模型结构** | Encoder-Decoder，big 版编码器和解码器各 6 层，d_model=1024，16 头（§3；Table 3） | 只用 Encoder，双向。BERT_LARGE：L=24，H=1024，A=16（§3） | 只用 Decoder，自回归，dense 与稀疏注意力交替。175B 版：96 层，d_model=12288，96 头，上下文 2048（§2.1，Table 2.1） |
| **预训练目标** | 不做预训练。用有监督机器翻译训练，自回归预测下一个 token，加 label smoothing ε=0.1（§3.4，§5.4） | Masked LM（遮掉 15% 的 token，按 80/10/10 处理）+ Next Sentence Prediction（§3.1，附录 A.1） | 自回归语言建模，预测下一个 token（§2，§5） |
| **训练数据** | WMT14 英-德约 4.5M 句对；WMT14 英-法 36M 句（§5.1） | BooksCorpus 800M 词 + 英文 Wikipedia 2,500M 词，合计约 3.3B 词（§3.1） | 五个数据集混合共 499B tokens，其中 Common Crawl 过滤后 410B、WebText2 19B、Books1 12B、Books2 55B、Wikipedia 3B；每个模型训练 300B tokens（§2.2，Table 2.2） |
| **最大模型参数量** | 213M，Transformer big（Table 3） | 340M，BERT_LARGE（§3） | 175B（Table 2.1） |
| **主要评测方式** | WMT14 newstest2014 测 BLEU：英-德 28.4，英-法 41.8（Table 2）；另测英语成分句法分析 WSJ 23，F1 92.7（Table 4） | 预训练后在下游任务上微调：GLUE 80.5（Table 1）、SQuAD v1.1 F1 93.2（Table 2）、SQuAD v2.0 F1 83.1（Table 3）、SWAG 86.3（Table 4），11 项任务达到 SOTA | 不做微调，只给提示：分 zero-shot、one-shot、few-shot 三种设定（§2）。例如 LAMBADA few-shot 86.4%（Table 3.2）、TriviaQA few-shot 71.2%（Table 3.3）、SuperGLUE few-shot 71.8（Table 3.8） |

关于英-法 BLEU：Gemini 指出 Transformer 论文里 Table 2 和摘要写 41.8，§6.1 正文写 41.0，两处不一致。表里用的是 41.8。

## 2. 每篇的核心贡献

- **Transformer**：完全去掉循环和卷积，只用自注意力建模序列，训练可以高度并行，并刷新了机器翻译的最好成绩（摘要，§7）。
- **BERT**：用 Masked LM 实现每一层的深度双向预训练，同一个预训练模型只加一个输出层微调，就能在各类 NLP 任务上达到 SOTA（摘要，§1）。
- **GPT-3**：把自回归语言模型扩到 175B 参数后，模型不更新权重、只靠提示和少量示例就能完成任务（上下文学习），在不少任务上接近甚至超过微调模型（摘要，§1）。

## 3. 演进关系

Transformer 提出了基于自注意力的 Encoder-Decoder 结构，但仍然针对单个任务做有监督训练。BERT 只取其中的 Encoder，用 Masked LM 在无标注文本上做双向预训练，再到下游任务微调，确立了"预训练 + 微调"的做法。GPT-3 走的是另一条路：只取 Decoder，参数和数据扩大约 500 倍，让模型靠上下文中的少量示例完成任务，用提示代替了微调。