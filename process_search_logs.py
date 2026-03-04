import pandas as pd
import sudachipy

def process_search_logs(input_file, output_file):
    print("正在初始化 Sudachi 分词器 (Full)...")
    try:
        # 使用 Full 词典，因为它包含更多的新词和专有名词，适合搜索日志分析
        tokenizer = sudachipy.Dictionary(dict="full").create()
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    print(f"正在读取文件: {input_file}")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"读取 CSV 失败: {e}")
        return

    def process_row(text):
        if not isinstance(text, str):
            return "", ""
        
        mode = sudachipy.SplitMode.C
        try:
            morphemes = tokenizer.tokenize(text, mode)
            
            # 1. 收集分词结果 (非 OOV)
            valid_morphemes = [m for m in morphemes if not m.is_oov()]
            forms = [m.dictionary_form() for m in valid_morphemes]
            result_str = ",".join(forms)
            
            # 2. 进行分类备注
            note = ""
            
            # (1) 全都是 OOV -> 纯中文
            if morphemes and all(m.is_oov() for m in morphemes):
                note = "纯中文"
                
            elif len(valid_morphemes) > 0:
                # 统计
                verb_adj_count = 0
                functional_count = 0
                has_other_content = False
                
                particle_aux_count = 0 # 统计助词助动词总数，用于句型判断
                
                for m in valid_morphemes:
                    pos = m.part_of_speech()
                    
                    if pos[0] in ['動詞', '形容詞']:
                        verb_adj_count += 1
                    elif pos[0] in ['助動詞', '接尾辞']:
                        functional_count += 1
                        particle_aux_count += 1
                    elif pos[0] in ['助詞']:
                        functional_count += 1
                        particle_aux_count += 1
                    else:
                        has_other_content = True

                # (2) 动词/形容词变形
                # 规则：有且仅有1个动词/形容词，且没有其他实词
                if verb_adj_count == 1 and not has_other_content:
                    note = "动词/形容词变形"
                    
                # (3) 句型 (互斥，优先判定变形)
                # 规则：分词结果 > 3，且至少 2 个是助词或助动词
                if not note and len(valid_morphemes) > 3:
                     if particle_aux_count >= 2:
                        note = "句型"

            return result_str, note

        except Exception as e:
            print(f"处理错误: {text} -> {e}")
            return "", "Error"

    print("正在进行分词与分类处理...")
    # Apply function
    if 'content' in df.columns:
        # 使用 apply 获取 Series 结果
        result_df = df['content'].apply(lambda x: pd.Series(process_row(x)))
        result_df.columns = ['分词结果', '备注']
        df = pd.concat([df, result_df], axis=1)
    else:
        print("错误: CSV 文件中未找到 'content' 列")
        return

    print(f"正在保存结果到: {output_file}")
    try:
        df.to_csv(output_file, index=False, encoding='utf-8-sig') # 使用 utf-8-sig 以便 Excel 正确打开
        print("处理完成！")
    except Exception as e:
        print(f"保存 CSV 失败: {e}")

if __name__ == "__main__":
    input_csv = "/Users/fangzhishan/Downloads/sudachiDict/search_logs_high_freq_2602281115.csv"
    output_csv = "/Users/fangzhishan/Downloads/sudachiDict/search_logs_high_freq_processed.csv"
    
    process_search_logs(input_csv, output_csv)
