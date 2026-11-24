## 1. 对比表

| | Transformer (1706.03762) | BERT (1810.04805) | GPT-3 (2005.14165) |
|---|---|---|---|
| **模型结构** | Encoder-decoder，两部分都由堆叠的自注意力层和逐位置前馈层组成（§3、Fig.1） | 仅 encoder，多层双向 Transformer 编码器（§3） | 仅 decoder 的自回归语言模型。沿用 GPT-2 架构，dense 与 locally banded sparse attention 交替使用（§2.1）。原文没有用 "decoder-only" 这个词 |
| **预训练目标** | 没有预训练。直接在翻译任务上有监督训练，逐 token 预测，用了标签平滑 ε_ls=0.1（§3.4、§5.4） | Masked LM：随机遮住 15% 的 token 再预测；加上 Next Sentence Prediction（§3.1） | 标准的自回归语言建模，即预测下一个 token（§2、§2.1） |
| **训练数据** | WMT 2014 英德约 450 万句对；WMT 2014 英法 3600 万句（§5.1） | BooksCorpus 8 亿词 + 英文 Wikipedia 25 亿词，合计 33 亿词（§3.1、附录 A.2） | 共训练 3000 亿 token（§2.2）。数据混合：Common Crawl（过滤后）4100 亿 token、权重 60%；WebText2 190 亿、22%；Books1 120 亿、8%；Books2 550 亿、8%；Wikipedia 30 亿、3%（Table 2.2）。Common Crawl 过滤前 45TB，过滤后 570GB（§2.2） |
| **最大模型参数量** | Transformer (big)：213M（Table 3） | BERT_LARGE：340M，L=24, H=1024, A=16（§3） | GPT-3 175B：1750 亿，96 层，d_model=12288（Table 2.1） |
| **主要评测方式** | 机器翻译 BLEU，WMT14 英德、英法 newstest2014（§6.1、Table 2）；另测英语成分句法分析 F1，WSJ（§6.3、Table 4） | 在下游任务上微调，共 11 个任务：GLUE、SQuAD v1.1/v2.0、SWAG（§4、Tables 1–4） | 不更新梯度，在 zero-shot、one-shot、few-shot 三种设定下测，任务给在上下文里（§2）。覆盖语言建模、闭卷问答、翻译、常识推理、阅读理解、SuperGLUE 等（§3.1–3.9） |

## 2. 每篇的核心贡献（各一句）

- **Transformer**：提出一个只用注意力机制的序列转导架构，完全不用循环和卷积（Abstract）。
- **BERT**：用 Masked LM 实现深层双向预训练，先预训练再微调，一个模型在多种 NLP 任务上都拿到了 SOTA（§1）。
- **GPT-3**：把语言模型扩大到 1750 亿参数后，只给少量示例、不做微调的 few-shot 能力明显变强（Abstract）。

## 3. 演进关系（150 字以内）

Transformer 提出了纯注意力架构，但仍是为单一任务做有监督训练的 encoder-decoder。BERT 只取其编码器，在大规模无标注文本上做双向预训练，再对每个任务微调，确立了"预训练＋微调"的做法。GPT-3 走解码器这条自回归路线，参数扩大约 500 倍，用上下文学习取代微调，说明规模本身就能带来通用的少样本能力。

---

**核对情况：** 本地抽不出 PDF 文本：没有 pdftotext/poppler，用 Python 的命令也需要授权。所以表里的数字由 Gemini 从原文提取，我只拿自己对这三篇论文的了解逐条对照过，全部一致，但没有亲手翻原文核实。正式引用前，建议抽查这几处：Transformer Table 3、BERT §3.1、GPT-3 Table 2.1/2.2。如果你批准运行 Python，我可以抽出全文逐条核对。