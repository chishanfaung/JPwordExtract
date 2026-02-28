## 如何添加新词

Sudachi 提供了两种添加新词的方式：**创建用户词典 (User Dictionary)** 和 **贡献到系统词典 (System Dictionary)**。

### 1. 创建用户词典 (User Dictionary)

这是最常用、最灵活的方式，适合在自己的项目中添加特定领域的词汇。

**步骤：**

1.  **创建 CSV 文件**
    创建一个 CSV 文件（例如 `user_dict.csv`），每行定义一个词汇。格式如下（共 18 列）：

    ```csv
    # 词面,左ID,右ID,代价,词面,词性1,词性2,词性3,词性4,活用型,活用形,读音,字典形,A分割,B分割,*,*,*
    TraeAI, -1, -1, 1000, TraeAI, 名詞, 固有名詞, 一般, *, *, *, トラエエーアイ, TraeAI, *, *, *, *, *
    ```

    *   **左ID/右ID**: 填 `-1` 让系统自动分配。
    *   **代价 (Cost)**: 推荐值 `1000` 到 `5000`。数值越小优先级越高。
    *   **词性**: 例如 `名詞,固有名詞,一般,*,*,*`。

2.  **编译词典**
    使用 `sudachipy` 提供的工具将 CSV 编译为二进制 `.dic` 文件。

    ```bash
    # 需要先下载 matrix.def (系统词典构建时会用到，或者从 SudachiDict-raw 下载)
    # 简单方式：直接使用 pip 安装 sudachipy 后
    sudachipy ubuild -o user.dic user_dict.csv
    ```

3.  **在 Python 中使用**

    ```python
    import sudachipy

    # 加载时指定 user_dicts
    dictionary = sudachipy.Dictionary(
        dict="core",
        user_dicts=["user.dic"]  # 这里填你编译好的文件路径
    )
    tokenizer = dictionary.create()
    ```

### 2. 贡献到系统词典 (System Dictionary)

如果你希望某个词被永久加入到 Sudachi 的官方词典中，可以通过以下方式贡献：

*   **数据来源**: 目前 SudachiDict 的原始数据托管在 AWS S3 上，构建脚本会自动下载。
*   **提交申请**: 你可以在 [GitHub Issues](https://github.com/WorksApplications/SudachiDict/issues) 中提交 "Lexicon Request"，提供你希望添加的词汇及其属性。
*   **修改源码**:
    *   虽然主要词典数据在 S3，但你可以在本地构建过程中通过修改构建脚本或拦截下载的 CSV 来测试添加。
    *   对于同义词，你可以直接修改 `src/main/text/synonyms.txt` 并提交 Pull Request。

### 3. 构建脚本分析

本项目 (`SudachiDict`) 是用于构建系统词典的工程。
- `build.gradle` 文件定义了从 S3 下载 `small`, `core`, `notcore` 三份原始 CSV 数据，并调用 `DictionaryBuilder` 将它们合并编译成 `system_core.dic` 等文件。
- 如果你想在构建系统词典时混入自己的数据，可以修改 `build.gradle` 中的 `sources` 列表，加入你自己的 CSV 文件路径。
