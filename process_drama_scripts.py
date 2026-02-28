import sudachipy
import pandas as pd
import os
import glob
import re
import unicodedata
from collections import Counter

class DramaScriptAnalyzer:
    def __init__(self):
        print("正在初始化 Sudachi 分词器 (Full 和 Small)...")
        try:
            self.tokenizer_full = sudachipy.Dictionary(dict="full").create()
            self.tokenizer_small = sudachipy.Dictionary(dict="small").create()
            print("初始化完成。")
        except Exception as e:
            print(f"初始化失败: {e}")
            print("请确保已安装 sudachidict_full 和 sudachidict_small")
            exit(1)

    def to_full_width(self, text: str) -> str:
        """
        将文本中的半角字符转换为全角字符 (NFKC 归一化)
        注意：NFKC 会将半角假名转换为全角假名，也会将全角数字字母转换为半角。
        为了保留“全角假名”的同时处理半角标点等，我们使用自定义的转换或依赖 NFKC。
        这里使用 unicodedata.normalize('NFKC', text) 是最通用的方法，
        它会将半角片假名 (ｱ) 转为全角 (ア)。
        """
        return unicodedata.normalize('NFKC', text)

    def katakana_to_hiragana(self, text: str) -> str:
        """
        将片假名转换为平假名
        片假名范围: 0x30A1-0x30F6
        平假名范围: 0x3041-0x3096
        偏移量: -0x60 (96)
        """
        result = ""
        for char in text:
            code = ord(char)
            if 0x30A1 <= code <= 0x30F6:
                result += chr(code - 0x60)
            else:
                result += char
        return result

    def is_in_small_dict(self, surface: str) -> bool:
        """检查词汇是否在 Small 词典中（基础词）"""
        try:
            morphemes = self.tokenizer_small.tokenize(surface, sudachipy.SplitMode.C)
            if len(morphemes) == 1:
                m = morphemes[0]
                if m.surface() == surface:
                    return True
        except Exception:
            pass
        return False

    def is_valid_content(self, surface: str) -> bool:
        """
        检查是否包含实际语义内容（过滤纯符号）
        只要包含：平假名、片假名、汉字、字母、数字 其中之一，即视为有效
        """
        # \u3040-\u309F: 平假名
        # \u30A0-\u30FF: 片假名
        # \u4E00-\u9FFF: 汉字
        # \u3005: 々 (叠字符)
        # \u30FC: ー (长音)
        # a-zA-Z0-9: 半角字母数字
        pattern = r'[a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3005\u30FC]'
        return bool(re.search(pattern, surface))

    def get_word_category(self, morpheme) -> str:
        """
        获取词汇类别
        返回: 'HighFreq', 'Recommended', 'ProperNoun', 'Ignore'
        """
        surface = morpheme.surface()
        pos = morpheme.part_of_speech()
        
        # 0. 内容有效性过滤 (解决 < > 等符号被识别为名词的问题)
        if not self.is_valid_content(surface):
            return 'Ignore'

        # 1. 忽略特定词性
        # 增加 '空白' 以解决截图中的问题
        ignored_pos = {'助詞', '助動詞', '記号', '補助記号', '感動詞', '連体詞', '接続詞', '接頭辞', '接尾辞', '空白'}
        if pos[0] in ignored_pos:
            return 'Ignore'
            
        # 排除非自立语 (如 "ている" 中的 "いる")
        if pos[1] == '非自立可能':
             return 'Ignore'
             
        # 排除数词
        if pos[1] == '数詞':
            return 'Ignore'

        # 2. 专有名词判断 (人名、地名等)
        if pos[1] == '固有名詞':
            return 'ProperNoun'

        # 3. 基础词汇判断 (Small Dictionary Check)
        if self.is_in_small_dict(surface):
            return 'HighFreq'
            
        # 4. 剩下的即为推荐学习词
        # 主要是 Core/Full 独有的普通名词、动词、形容词等
        return 'Recommended'

    def process_file(self, input_path: str, output_path: str):
        print(f"正在处理文件: {input_path}")
        
        # 准备数据容器
        sheet1_data = [] # 原句子 | 分词结果 | 高频词 | 推荐词 | 专有名词
        
        # 统计频次
        high_freq_counter = Counter()
        recommended_counter = Counter()
        proper_noun_counter = Counter()
        
        # 记录词汇详情 (用于 Sheet 2-4 的列信息: 发音, 词性)
        # Key: surface, Value: {'reading': ..., 'pos': ...}
        word_details = {}

        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 1. 预处理：半角转全角 (NFKC)
            normalized_line = self.to_full_width(line)
            
            # 分词 (Mode C)
            morphemes = self.tokenizer_full.tokenize(normalized_line, sudachipy.SplitMode.C)
            
            # 当前句子的列表收集
            sentence_words = []
            sentence_high_freq = []
            sentence_recommended = []
            sentence_proper = []
            
            for m in morphemes:
                surface = m.surface()
                reading_katakana = m.reading_form()
                
                # 2. 转换读音为平假名
                reading_hiragana = self.katakana_to_hiragana(reading_katakana)
                
                pos = list(m.part_of_speech())
                pos_str = f"{pos[0]}-{pos[1]}"
                
                # 记录分词结果
                sentence_words.append(surface)
                
                category = self.get_word_category(m)
                
                if category == 'Ignore':
                    continue
                
                # 更新详情字典 (如果未记录过)
                if surface not in word_details:
                    word_details[surface] = {
                        'reading': reading_hiragana, # 使用平假名读音
                        'pos': pos_str
                    }
                
                if category == 'HighFreq':
                    sentence_high_freq.append(surface)
                    high_freq_counter[surface] += 1
                elif category == 'Recommended':
                    sentence_recommended.append(surface)
                    recommended_counter[surface] += 1
                elif category == 'ProperNoun':
                    sentence_proper.append(surface)
                    proper_noun_counter[surface] += 1

            # 添加到 Sheet 1 数据
            # 原句子保留原始文本，还是归一化后的？这里选择保留原始文本以便对照，分词结果用归一化后的
            sheet1_data.append({
                '原句子': line,
                '句子分词后的所有单词': " - ".join(sentence_words),
                '高频词': " - ".join(sentence_high_freq),
                '推荐学习词': " - ".join(sentence_recommended),
                '专有名词': " - ".join(sentence_proper)
            })
            
            if (i + 1) % 100 == 0:
                print(f"已处理 {i + 1}/{total_lines} 行...")

        print("数据处理完成，正在生成 Excel...")
        
        # 创建 Sheet 1 DataFrame
        df_sheet1 = pd.DataFrame(sheet1_data)
        
        # 创建 Sheet 2, 3, 4 DataFrames (辅助函数)
        def create_stat_df(counter):
            data = []
            # 按频次降序排列
            for word, count in counter.most_common():
                details = word_details.get(word, {'reading': '', 'pos': ''})
                data.append({
                    '单词': word,
                    '发音': details['reading'],
                    '词性': details['pos'],
                    '频次': count
                })
            return pd.DataFrame(data)

        df_high_freq = create_stat_df(high_freq_counter)
        df_recommended = create_stat_df(recommended_counter)
        df_proper = create_stat_df(proper_noun_counter)

        # 写入 Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_sheet1.to_excel(writer, sheet_name='句子分析', index=False)
            df_high_freq.to_excel(writer, sheet_name='高频词(基础)', index=False)
            df_recommended.to_excel(writer, sheet_name='推荐学习词(进阶)', index=False)
            df_proper.to_excel(writer, sheet_name='专有名词', index=False)
            
        print(f"Excel 文件已保存至: {output_path}")

    def process_file(self, input_path: str, output_path: str):
        print(f"正在处理文件: {input_path}")
        
        # 准备数据容器
        sheet1_data = [] # 原句子 | 分词结果 | 高频词 | 推荐词 | 专有名词
        
        # 统计频次
        high_freq_counter = Counter()
        recommended_counter = Counter()
        proper_noun_counter = Counter()
        
        # 记录词汇详情 (用于 Sheet 2-4 的列信息: 发音, 词性)
        # Key: surface, Value: {'reading': ..., 'pos': ...}
        word_details = {}

        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 1. 预处理：半角转全角 (NFKC)
            normalized_line = self.to_full_width(line)
            
            # 分词 (Mode C)
            morphemes = self.tokenizer_full.tokenize(normalized_line, sudachipy.SplitMode.C)
            
            # 当前句子的列表收集
            sentence_words = []
            sentence_high_freq = []
            sentence_recommended = []
            sentence_proper = []
            
            for m in morphemes:
                surface = m.surface()
                reading_katakana = m.reading_form()
                
                # 2. 转换读音为平假名
                reading_hiragana = self.katakana_to_hiragana(reading_katakana)
                
                pos = list(m.part_of_speech())
                pos_str = f"{pos[0]}-{pos[1]}"
                
                # 记录分词结果
                sentence_words.append(surface)
                
                category = self.get_word_category(m)
                
                if category == 'Ignore':
                    continue
                
                # 更新详情字典 (如果未记录过)
                if surface not in word_details:
                    word_details[surface] = {
                        'reading': reading_hiragana, # 使用平假名读音
                        'pos': pos_str
                    }
                
                if category == 'HighFreq':
                    sentence_high_freq.append(surface)
                    high_freq_counter[surface] += 1
                elif category == 'Recommended':
                    sentence_recommended.append(surface)
                    recommended_counter[surface] += 1
                elif category == 'ProperNoun':
                    sentence_proper.append(surface)
                    proper_noun_counter[surface] += 1

            # 添加到 Sheet 1 数据
            # 原句子保留原始文本，还是归一化后的？这里选择保留原始文本以便对照，分词结果用归一化后的
            sheet1_data.append({
                '原句子': line,
                '句子分词后的所有单词': " - ".join(sentence_words),
                '高频词': " - ".join(sentence_high_freq),
                '推荐学习词': " - ".join(sentence_recommended),
                '专有名词': " - ".join(sentence_proper)
            })
            
            if (i + 1) % 100 == 0:
                print(f"已处理 {i + 1}/{total_lines} 行...")

        print("数据处理完成，正在生成 Excel...")
        
        # 创建 Sheet 1 DataFrame
        df_sheet1 = pd.DataFrame(sheet1_data)
        
        # 创建 Sheet 2, 3, 4 DataFrames (辅助函数)
        def create_stat_df(counter):
            data = []
            # 按频次降序排列
            for word, count in counter.most_common():
                details = word_details.get(word, {'reading': '', 'pos': ''})
                data.append({
                    '单词': word,
                    '发音': details['reading'],
                    '词性': details['pos'],
                    '频次': count
                })
            return pd.DataFrame(data)

        df_high_freq = create_stat_df(high_freq_counter)
        df_recommended = create_stat_df(recommended_counter)
        df_proper = create_stat_df(proper_noun_counter)

        # 写入 Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_sheet1.to_excel(writer, sheet_name='句子分析', index=False)
            df_high_freq.to_excel(writer, sheet_name='高频词(基础)', index=False)
            df_recommended.to_excel(writer, sheet_name='推荐学习词(进阶)', index=False)
            df_proper.to_excel(writer, sheet_name='专有名词', index=False)
            
        print(f"Excel 文件已保存至: {output_path}")

    def process_all(self, directory: str):
        """批量处理目录下所有符合模式的 txt 文件并汇总"""
        # 1. 找到所有目标 txt 文件
        # 假设文件名格式为 "重启人生EP*.txt"
        txt_files = sorted(glob.glob(os.path.join(directory, "重启人生EP*.txt")))
        
        if not txt_files:
            print(f"未在 {directory} 找到 '重启人生EP*.txt' 文件")
            return

        generated_excels = []
        
        # 2. 逐个处理
        for txt_file in txt_files:
            base_name = os.path.splitext(os.path.basename(txt_file))[0]
            output_file = os.path.join(directory, f"{base_name}_analysis.xlsx")
            
            print(f"\n--- 处理文件: {base_name} ---")
            self.process_file(txt_file, output_file)
            generated_excels.append(output_file)
            
        # 3. 合并汇总
        self.merge_excels(directory, generated_excels)

    def merge_excels(self, directory: str, excel_files: list):
        print("\n=== 开始合并所有 Excel ===")
        
        # 容器：Sheet名 -> {单词: {reading, pos, count}}
        # 我们只合并统计类的 Sheet，不合并“句子分析”
        target_sheets = ['高频词(基础)', '推荐学习词(进阶)', '专有名词']
        
        merged_data = {sheet: {} for sheet in target_sheets}
        
        for excel_file in excel_files:
            print(f"读取数据: {os.path.basename(excel_file)}")
            # 读取 Excel，sheet_name=None 表示读取所有 Sheet
            try:
                xls_dict = pd.read_excel(excel_file, sheet_name=None)
            except Exception as e:
                print(f"读取失败 {excel_file}: {e}")
                continue
            
            for sheet_name in target_sheets:
                if sheet_name in xls_dict:
                    df = xls_dict[sheet_name]
                    # 确保列名存在
                    if not {'单词', '发音', '词性', '频次'}.issubset(df.columns):
                        continue
                        
                    for _, row in df.iterrows():
                        word = row['单词']
                        # 跳过空值
                        if pd.isna(word):
                            continue
                            
                        count = row['频次']
                        reading = row['发音']
                        pos = row['词性']
                        
                        if word not in merged_data[sheet_name]:
                            merged_data[sheet_name][word] = {
                                'reading': reading,
                                'pos': pos,
                                'count': 0
                            }
                        # 累加频次
                        merged_data[sheet_name][word]['count'] += count
        
        # 4. 生成汇总 Excel
        output_path = os.path.join(directory, "重启人生_全集汇总.xlsx")
        print(f"正在写入汇总文件: {output_path}")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name in target_sheets:
                word_dict = merged_data[sheet_name]
                
                # 转为 list
                data_list = []
                for word, info in word_dict.items():
                    data_list.append({
                        '单词': word,
                        '发音': info['reading'],
                        '词性': info['pos'],
                        '频次': info['count']
                    })
                
                # 创建 DataFrame 并排序
                if data_list:
                    df = pd.DataFrame(data_list)
                    # 按频次降序，频次相同时按单词排序
                    df = df.sort_values(by=['频次', '单词'], ascending=[False, True])
                else:
                    df = pd.DataFrame(columns=['单词', '发音', '词性', '频次'])
                    
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
        print("✅ 所有任务完成！")

if __name__ == "__main__":
    analyzer = DramaScriptAnalyzer()
    
    # 设定工作目录
    input_dir = "/Users/fangzhishan/Downloads/sudachiDict/重启人生txt/"
    
    # 执行批量处理
    analyzer.process_all(input_dir)
