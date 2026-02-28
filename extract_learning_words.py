import sudachipy
import argparse
from typing import List, Tuple, Dict

class LearningWordExtractor:
    def __init__(self):
        print("正在初始化词典 (Full 和 Small)...")
        try:
            # 主分词器：使用 Full 词典，保证切分最准确（包含专有名词）
            self.tokenizer_full = sudachipy.Dictionary(dict="full").create()
            
            # 辅助分词器：使用 Small 词典，用于判断词汇是否“基础”
            self.tokenizer_small = sudachipy.Dictionary(dict="small").create()
            print("初始化完成。")
        except Exception as e:
            print(f"初始化失败: {e}")
            print("请确保已安装 sudachidict_full 和 sudachidict_small")
            exit(1)

    def is_in_small_dict(self, surface: str) -> bool:
        """
        检查一个词是否存在于 Small 词典中（即是否为基础词汇）。
        使用 Mode C 检查是否能作为整体分出。
        """
        try:
            morphemes = self.tokenizer_small.tokenize(surface, sudachipy.SplitMode.C)
            if len(morphemes) == 1:
                m = morphemes[0]
                if m.surface() == surface:
                    return True
        except Exception:
            pass
        return False

    def get_word_level(self, morpheme) -> tuple:
        """
        判断词汇的学习价值级别。
        返回: (级别标签, 建议)
        """
        surface = morpheme.surface()
        pos = morpheme.part_of_speech()
        
        # 1. 词性过滤 (Part of Speech Filter)
        # 排除助词、助动词、记号、接辞等
        if pos[0] in {'助詞', '助動詞', '記号', '補助記号', '感動詞', '連体詞', '接続詞'}:
            return "忽略", ""
            
        # 排除非自立语 (如 "ている" 中的 "いる")
        if pos[1] == '非自立可能':
             return "忽略", ""
             
        # 排除数词
        if pos[1] == '数詞':
            return "忽略", ""

        # 2. 基础词汇判断 (Small Dictionary Check)
        # 如果在 Small 中存在，通常是极高频的基础词 (如 "食べる", "行く", "私")
        if self.is_in_small_dict(surface):
            # 特例：如果是固有名词，即使在 Small 中也不一定算“基础”，但也无需刻意背诵
            if pos[1] == '固有名詞':
                return "基础(专名)", "常见地名/人名"
            return "基础", "高频词 (如吃/做/走)"
            
        # 3. 进阶词汇判断 (Core/Full Only)
        # 如果不在 Small 中，但在 Full 中，说明是中低频词或复合词
        
        # 区分固有名词 (人名/地名/作品名)
        if pos[1] == '固有名詞':
            return "专名", "人名/地名/机构名"
            
        # 普通名词、动词等 -> 这是我们要找的“有学习价值”的词
        return "进阶", "⭐️ 推荐学习 (中频/核心词汇)"

    def extract(self, text: str):
        print(f"\n正在分析文本: 「{text[:30]}...」")
        print("-" * 90)
        print(f"{'词面':<12} {'读音':<16} {'原形':<12} {'词性':<18} {'级别':<10} {'建议'}")
        print("-" * 90)
        
        morphemes = self.tokenizer_full.tokenize(text, sudachipy.SplitMode.C)
        
        for m in morphemes:
            surface = m.surface()
            reading = m.reading_form()
            base = m.dictionary_form()
            pos_str = f"{m.part_of_speech()[0]}-{m.part_of_speech()[1]}"
            
            level, suggestion = self.get_word_level(m)
            
            if level == "忽略":
                continue
                
            # 格式化输出 (简单对齐)
            print(f"{surface:<12} {reading:<16} {base:<12} {pos_str:<18} {level:<10} {suggestion}")

if __name__ == "__main__":
    extractor = LearningWordExtractor()
    
    # 测试文本：包含基础词(食べる)、进阶词(感染症)、专有名词(鬼滅の刃)
    sample_text = "私は昨日、東京で鬼滅の刃の映画を見ました。感染症対策が徹底されていました。ご飯も食べた。"
    
    extractor.extract(sample_text)
