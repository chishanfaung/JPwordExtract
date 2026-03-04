import pandas as pd
import sudachipy
import os
import re

# 复用 LearningWordExtractor 的逻辑
class LearningWordExtractor:
    def __init__(self):
        print("正在初始化词典 (Full 和 Small)...")
        try:
            self.tokenizer_full = sudachipy.Dictionary(dict="full").create()
            self.tokenizer_small = sudachipy.Dictionary(dict="small").create()
            print("初始化完成。")
        except Exception as e:
            print(f"初始化失败: {e}")
            raise e

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
        """检查是否包含实际语义内容（过滤纯符号）"""
        pattern = r'[a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3005\u30FC]'
        return bool(re.search(pattern, surface))

    def get_word_category(self, morpheme) -> str:
        """
        判断词汇的学习价值级别。
        返回: 'HighFreq', 'Recommended', 'ProperNoun', 'Ignore'
        """
        surface = morpheme.surface()
        pos = morpheme.part_of_speech()
        
        # 0. 内容有效性过滤
        if not self.is_valid_content(surface):
            return 'Ignore'

        # 1. 词性过滤 (Part of Speech Filter)
        # 排除助词、助动词、记号、接辞等
        if pos[0] in {'助詞', '助動詞', '記号', '補助記号', '感動詞', '連体詞', '接続詞', '空白'}:
            return 'Ignore'
            
        # 排除非自立语 (如 "ている" 中的 "いる")
        if pos[1] == '非自立可能':
             return 'Ignore'
             
        # 排除数词
        if pos[1] == '数詞':
            return 'Ignore'

        # 2. 基础词汇判断 (Small Dictionary Check)
        if self.is_in_small_dict(surface):
            # 特例：如果是固有名词，即使在 Small 中也不一定算“基础”，但也无需刻意背诵
            if pos[1] == '固有名詞':
                # 这里为了统一逻辑，暂时归为 ProperNoun
                # 或者你可以定义一个新的类别 'BasicProperNoun'
                # 按照之前的 extract_learning_words.py 逻辑，它返回 "基础(专名)"
                # 这里为了统计方便，我们归类为 ProperNoun
                return 'ProperNoun'
            return 'HighFreq'
            
        # 3. 进阶词汇判断 (Core/Full Only)
        
        # 区分固有名词 (人名/地名/作品名)
        if pos[1] == '固有名詞':
            return 'ProperNoun'
            
        # 普通名词、动词等 -> 这是我们要找的“有学习价值”的词
        return 'Recommended'

def process_excel_with_levels(input_file, output_file_1, output_file_2):
    try:
        extractor = LearningWordExtractor()
    except Exception:
        return

    if not os.path.exists(input_file):
        print(f"文件不存在: {input_file}")
        return

    print(f"正在读取文件: {input_file}")
    try:
        xls = pd.read_excel(input_file, sheet_name=None)
    except Exception as e:
        print(f"读取 Excel 失败: {e}")
        return

    # 统计数据: stats[category][word] = {'count': 0, 'sheets': set()}
    categories = ['HighFreq', 'Recommended', 'ProperNoun']
    global_stats = {cat: {} for cat in categories}

    processed_sheets = {}
    target_col = 'ly-mod-infoset3-name'

    for sheet_name, df in xls.items():
        print(f"正在处理 Sheet: {sheet_name}")
        
        if target_col not in df.columns:
            print(f"  警告: Sheet '{sheet_name}' 中未找到列 '{target_col}'，跳过")
            processed_sheets[sheet_name] = df
            continue

        # 准备新增的列数据
        # 修改为三列: 高频词(基础) | 推荐学习词(进阶) | 专有名词
        high_freq_col = []
        recommended_col = []
        proper_noun_col = []

        for idx, row in df.iterrows():
            text = row[target_col]
            
            if not isinstance(text, str):
                high_freq_col.append("")
                recommended_col.append("")
                proper_noun_col.append("")
                continue

            try:
                # 使用 Mode C 分词
                morphemes = extractor.tokenizer_full.tokenize(text, sudachipy.SplitMode.C)
                
                # 当前行的单词列表
                words_high = []
                words_rec = []
                words_proper = []
                
                for m in morphemes:
                    cat = extractor.get_word_category(m)
                    
                    if cat == 'Ignore':
                        continue
                        
                    word = m.dictionary_form()
                    
                    # 记录统计
                    if cat in global_stats:
                        if word not in global_stats[cat]:
                            global_stats[cat][word] = {'count': 0, 'sheets': set()}
                        global_stats[cat][word]['count'] += 1
                        global_stats[cat][word]['sheets'].add(sheet_name)
                    
                    # 分类收集
                    if cat == 'HighFreq':
                        words_high.append(word)
                    elif cat == 'Recommended':
                        words_rec.append(word)
                    elif cat == 'ProperNoun':
                        words_proper.append(word)

                # 使用逗号分隔
                high_freq_col.append(",".join(words_high))
                recommended_col.append(",".join(words_rec))
                proper_noun_col.append(",".join(words_proper))

            except Exception as e:
                print(f"  处理错误 (Row {idx}): {e}")
                high_freq_col.append("Error")
                recommended_col.append("Error")
                proper_noun_col.append("Error")

        # 将新列添加到 DataFrame
        df['高频词(基础)'] = high_freq_col
        df['推荐学习词(进阶)'] = recommended_col
        df['专有名词'] = proper_noun_col
        
        processed_sheets[sheet_name] = df

    # --- 生成表格 1 (详情) ---
    print(f"正在保存表格 1 到: {output_file_1}")
    try:
        with pd.ExcelWriter(output_file_1, engine='openpyxl') as writer:
            for sheet_name, df in processed_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as e:
        print(f"保存表格 1 失败: {e}")

    # --- 生成表格 2 (统计) ---
    print(f"正在保存表格 2 到: {output_file_2}")
    try:
        with pd.ExcelWriter(output_file_2, engine='openpyxl') as writer:
            for cat in categories:
                stats = global_stats[cat]
                data_list = []
                for word, info in stats.items():
                    data_list.append({
                        '单词': word,
                        'sheet名': ",".join(sorted(list(info['sheets']))),
                        '出现频次': info['count']
                    })
                
                stat_df = pd.DataFrame(data_list)
                
                sheet_name_map = {
                    'HighFreq': '高频词(基础)',
                    'Recommended': '推荐学习词(进阶)',
                    'ProperNoun': '专有名词'
                }
                
                if not stat_df.empty:
                    stat_df = stat_df.sort_values(by='出现频次', ascending=False)
                else:
                    # 创建空表头防止报错
                    stat_df = pd.DataFrame(columns=['单词', 'sheet名', '出现频次'])
                
                stat_df.to_excel(writer, sheet_name=sheet_name_map[cat], index=False)
    except Exception as e:
        print(f"保存表格 2 失败: {e}")

    print("全部处理完成！")

if __name__ == "__main__":
    input_path = "/Users/fangzhishan/Downloads/sudachiDict/全家便利店商品信息.xlsx"
    output_path_1 = "/Users/fangzhishan/Downloads/sudachiDict/全家便利店商品信息_分词详情_Level.xlsx"
    output_path_2 = "/Users/fangzhishan/Downloads/sudachiDict/全家便利店商品信息_词频统计_Level.xlsx"
    
    process_excel_with_levels(input_path, output_path_1, output_path_2)
