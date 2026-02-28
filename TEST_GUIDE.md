
## 如何测试分词结果

测试 Sudachi 分词主要有以下几种方法：

### 1. 使用本项目提供的分析工具 (推荐)

这是最全面的方式，可以同时查看分词结果、词典来源（Small/Core/Full）以及同义词信息。

```bash
# 默认测试
python3 analyze_sudachi.py

# 测试特定句子
python3 analyze_sudachi.py "鬼滅の刃を見に行く"

# 查看详细同义词信息
python3 analyze_sudachi.py --verbose "スマホを買った"
```

### 2. 使用 SudachiPy 命令行工具

SudachiPy 自带了一个命令行工具，可以快速查看分词结果。

> 注意：如果 `sudachipy` 命令未找到，请尝试使用完整路径 `/Users/fangzhishan/Library/Python/3.9/bin/sudachipy` (根据你的 Python 安装位置可能不同)。

```bash
# 基本用法 (默认使用 core 词典)
echo "東京都へ行く" | sudachipy

# 指定词典 (-s small/core/full)
echo "東京都へ行く" | sudachipy -s full

# 指定分词模式 (-m A/B/C)
# A: 短语 (默认)
# B: 中间
# C: 长语 (命名实体等)
echo "東京都へ行く" | sudachipy -m C -s full

# 显示详细信息 (-a)
echo "東京都へ行く" | sudachipy -a
```

### 3. 使用 Python 代码调用

如果你想在自己的 Python 代码中使用，可以参考以下示例：

```python
import sudachipy

# 初始化分词器 (指定使用 full 词典)
tokenizer = sudachipy.Dictionary(dict="full").create()

# 待分词文本
text = "東京都へ行く"

# 分词模式 (A, B, C)
mode = sudachipy.SplitMode.C

# 执行分词
morphemes = tokenizer.tokenize(text, mode)

# 输出结果
for m in morphemes:
    print(f"词面: {m.surface()}")
    print(f"词性: {m.part_of_speech()}")
    print(f"原形: {m.dictionary_form()}")
    print("-" * 10)
```
