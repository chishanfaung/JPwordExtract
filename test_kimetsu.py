import sudachipy

def test_tokenization(dict_type, text):
    print(f"\n--- 正在使用词典: {dict_type} ---")
    try:
        # 初始化分词器
        tokenizer = sudachipy.Dictionary(dict=dict_type).create()
        
        # 使用 Mode C (通常倾向于最长匹配)
        mode = sudachipy.SplitMode.C
        morphemes = tokenizer.tokenize(text, mode)
        
        print(f"原文: {text}")
        print("分词结果:")
        for m in morphemes:
            # 打印：词面, 词性, 词典ID(0=系统词典), 归一化形式
            print(f"  [{m.surface()}]")
            print(f"    - 词性: {m.part_of_speech()}")
            print(f"    - 字典形: {m.dictionary_form()}")
            
            # 如果是未登录词 (OOV)，Sudachi 会标记为 OOV
            if m.is_oov():
                print(f"    - 状态: 未登录词 (OOV)")
            else:
                print(f"    - 状态: 词典在录")
                
    except Exception as e:
        print(f"加载词典 {dict_type} 失败: {e}")

if __name__ == "__main__":
    target_text = "鬼滅の刃"
    
    # 1. 测试 Small (对应 UniDic 基础词汇)
    test_tokenization("small", target_text)
    
    # 2. 测试 Full (包含扩展词汇)
    test_tokenization("full", target_text)
