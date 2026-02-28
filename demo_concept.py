import sudachipy

def demo_relationship():
    print("=== 概念演示：词典类型 vs 分词模式 ===\n")
    
    # 1. 定义要测试的词典和模式
    dicts = ["small", "core", "full"]
    modes = {
        "A (短)": sudachipy.SplitMode.A,
        "B (中)": sudachipy.SplitMode.B,
        "C (长)": sudachipy.SplitMode.C
    }
    
    text = "東京都選挙管理委員会"
    
    print(f"测试文本: 「{text}」\n")
    
    # 2. 遍历组合
    for dict_name in dicts:
        print(f"--- 词典: {dict_name.upper()} ---")
        try:
            tokenizer = sudachipy.Dictionary(dict=dict_name).create()
            for mode_name, mode_val in modes.items():
                morphemes = tokenizer.tokenize(text, mode_val)
                result = " / ".join([m.surface() for m in morphemes])
                print(f"  模式 {mode_name}: {result}")
        except Exception as e:
            print(f"  (加载失败: {e})")
        print()

if __name__ == "__main__":
    demo_relationship()
