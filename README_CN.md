# SudachiDict (中文说明与使用指南)

这是日语分词器 [Sudachi](https://github.com/WorksApplications/Sudachi/) 的系统词典项目。本指南将帮助你了解该项目的功能、核心概念及应用场景。

## 1. 项目核心概念辨析

在使用 Sudachi 之前，必须区分两个独立的核心概念：**词典类型 (Dictionary Types)** 和 **分词模式 (Split Modes)**。

### 1.1 词典类型 (决定"有多少词")
词典类型决定了分词器的**词汇量**。

| 词典类型 | 包含内容 | 适用场景 | 词汇量 (约) |
| :--- | :--- | :--- | :--- |
| **Small** | 仅包含 UniDic 的基础词汇 | 仅需最基础分词，对体积极其敏感 | **12万+** |
| **Core** | 基础词汇 + 常见词 (默认推荐) | 大多数通用场景，文本分析 | **60万+** |
| **Full** | Core + NEologd (新词/流行语/专名) | 命名实体识别(NER)，处理社交媒体/新闻 | **250万+** |

### 1.2 分词模式 (决定"怎么切")
分词模式决定了分词的**粒度**。**任何词典 (Small/Core/Full) 都可以使用任意模式 (A/B/C)。**

以 "東京都選挙管理委員会" 为例：

| 模式 | 说明 | 切分示例 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **Mode A** | **短单位** (Short) | `東京` / `都` / `選挙` / `管理` / `委員` / `会` | 搜索索引、词频统计 |
| **Mode B** | **中间单位** (Middle) | `東京都` / `選挙` / `管理` / `委員会` | 机器翻译、语义分析 |
| **Mode C** | **长单位** (Long) | `東京都` / `選挙管理委員会` | 命名实体识别 (NER)、关键词提取 |

> **误区提示**：不要认为 Small 只能用 Mode A，或者 Full 只能用 Mode C。
> *   你可以用 **Small + Mode C** (尽可能合并基础词)。
> *   你也可以用 **Full + Mode A** (将流行语切分为最小单位)。

## 2. 这个项目能用来做什么？

### 2.1 构建高性能日语搜索系统
*   **配置**: 使用 **Small** 或 **Core** 词典 + **Mode A**。
*   **优势**: Mode A 将复合词拆解为最小语素，提高搜索召回率（搜 "選挙" 能搜到 "選挙管理委員会"）。

### 2.2 自然语言处理与文本挖掘
*   **配置**: 使用 **Core** 词典 + **Mode B**。
*   **优势**: 保持了语义的完整性，同时避免了过度的碎片化，适合情感分析、文本分类。

### 2.3 命名实体识别 (NER) 与新词发现
*   **配置**: 使用 **Full** 词典 + **Mode C**。
*   **优势**: Full 词典收录了大量人名、地名、机构名（如 "鬼滅の刃"），Mode C 倾向于保持它们不被切分。

### 2.4 同义词归一化
*   本项目包含同义词库 (`synonyms.txt`)，可以将不同的写法（如 "スマホ" 和 "スマートフォン"）归一化为同一个 ID。

### 2.5 日语学习与注音工具
*   **功能**: 获取词汇的读音、发音和归一化形式。
*   **示例**:
    *   **读音 (Reading)**: 获取片假名读音 (如 `東京都` -> `トウキョウト`)，可用于生成振假名 (Furigana)。
    *   **归一化 (Normalized)**: 将异体写法统一 (如 `打込む` -> `打ち込む`)，方便初学者查词。
    *   **词典形 (Dictionary Form)**: 获取动词/形容词的原形 (如 `行った` -> `行く`)，方便语法学习。

## 3. 字段详解 (Morpheme Fields)

当你调用 `tokenizer.tokenize(text)` 时，返回的每个 `Morpheme` 对象包含以下核心字段：

| 方法 (Method) | 返回值类型 | 说明与示例 |
| :--- | :--- | :--- |
| **`surface()`** | `str` | **词面**。原始文本中的写法。<br>例: `打込む` |
| **`reading_form()`** | `str` | **读音**。全角片假名。<br>例: `ウチコム` (用于注音) |
| **`normalized_form()`** | `str` | **归一化形式**。异体字统一。<br>例: `打ち込む` (用于查词) |
| **`dictionary_form()`** | `str` | **辞书形 (原形)**。动词/形容词的原形。<br>例: `打ち込む` (用于语法分析) |
| **`part_of_speech()`** | `tuple` | **词性**。6层层级结构。<br>例: `('名詞', '固有名詞', '地名', '一般', '*', '*')` |
| **`is_oov()`** | `bool` | **是否未登录词**。`True` 表示词典中不存在，是推测的。<br>例: `False` |
| **`word_id()`** | `int` | **单词ID**。词典内部唯一ID。<br>例: `1295892` |
| **`dictionary_id()`** | `int` | **词典ID**。`0`=系统词典, `1`=用户词典, `-1`=OOV。<br>例: `0` |
| **`synonym_group_ids()`** | `list` | **同义词组ID**。用于关联同义词。<br>例: `[123, 456]` |
| **`begin()` / `end()`** | `int` | **起止位置**。在原文本中的字符索引。<br>例: `0` / `3` |
| **`part_of_speech_id()`** | `int` | **词性ID**。词典内部的 POS ID，比字符串比较更快。<br>例: `12` |
| **`split(mode)`** | `list` | **再分词**。按指定模式 (A/B) 将当前语素拆分为更小的语素。<br>例: `m.split(sudachipy.SplitMode.A)` |

## 4. 快速开始

### 安装
如果你是 Python 用户：
```bash
pip install sudachipy sudachidict_core  # 推荐安装 core
# pip install sudachidict_full          # 需要更多实体时安装 full
```

### 使用示例
```python
import sudachipy

# 1. 选择词典 (Small/Core/Full)
tokenizer = sudachipy.Dictionary(dict="full").create()

# 2. 选择模式 (A/B/C)
mode = sudachipy.SplitMode.C

# 3. 分词
text = "東京都選挙管理委員会"
results = tokenizer.tokenize(text, mode)

for m in results:
    print(m.surface(), m.part_of_speech())
    print(f"读音: {m.reading_form()}")
    print(f"归一化: {m.normalized_form()}")
```

## 5. 进阶应用：筛选有学习价值的单词

如果你在制作日语学习工具，可能希望从文章中自动提取出“难易适中”的单词（即过滤掉太简单的高频词，也区分开太生僻的专有名词）。

我们可以利用 SudachiDict 的分层结构（Small vs Full）来实现这一点。

### 原理
1.  **高频/基础词**: 存在于 `Small` 词典中的词汇（如 `食べる`, `行く`, `私`）。
2.  **中频/进阶词**: 不在 `Small` 但在 `Core/Full` 中的词汇（如 `感染症`, `機能性`）。**这是学习的重点。**
3.  **专有名词**: 词性为 `固有名詞` 的词汇（如 `鬼滅の刃`, `東京都`）。

### 实现代码
本项目提供了 [extract_learning_words.py](extract_learning_words.py) 脚本。关于该脚本的详细文档和使用方法，请查看：
**[EXTRACT_LEARNING_WORDS.md](EXTRACT_LEARNING_WORDS.md)**

```bash
python3 extract_learning_words.py
```

输出示例：
```text
词面           读音               原形           词性                 级别         建议
------------------------------------------------------------------------------------------
私            ワタクシ             私            代名詞-*              基础         高频词 (如吃/做/走)
鬼滅の刃         キメツノヤイバ          鬼滅の刃         名詞-固有名詞            专名         人名/地名/机构名
感染症          カンセンショウ          感染症          名詞-普通名詞            进阶         ⭐️ 推荐学习 (中频/核心词汇)
```

## 6. 高级功能与工具

本项目提供了一些辅助脚本和文档来帮助你深入使用：

*   **[analyze_sudachi.py](analyze_sudachi.py)**: 一个 Python 脚本，用于：
    *   分析一个词是来自 Small、Core 还是 Full 词典。
    *   查看该词的同义词信息（基于 `src/main/text/synonyms.txt`）。
    *   *用法*: `python3 analyze_sudachi.py "鬼滅の刃"`

*   **[ADD_WORDS.md](ADD_WORDS.md)**: 教你如何添加新词。
    *   创建用户词典 (User Dictionary)。
    *   向官方贡献词汇。

*   **[TEST_GUIDE.md](TEST_GUIDE.md)**: 详细的测试指南。
    *   命令行工具使用。
    *   更多代码示例。

## 7. 项目结构与数据来源
- **数据来源**: UniDic 和 NEologd (部分)。
- **构建方式**: 使用 Gradle 自动从 S3 下载原始 CSV 并编译。
    - 运行 `./gradlew build` 可在本地生成 `.dic` 文件。
- **同义词源文件**: `src/main/text/synonyms.txt`。

---
*更多细节请参考官方英文文档: [WorksApplications/SudachiDict](https://github.com/WorksApplications/SudachiDict)*
