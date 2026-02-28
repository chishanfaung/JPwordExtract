import sys
import csv
import argparse
from typing import Dict, List, Any
import sudachipy

def load_synonyms(filepath: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    解析 synonyms.txt 文件，返回以 Group ID 为键的字典。
    """
    synonym_db = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 9:
                    continue
                
                group_id = row[0]
                entry = {
                    "group_id": group_id,
                    "is_noun": row[1] == '1',  # 1: 体言, 2: 用言
                    "expansion_control": row[2],
                    "lexeme_id": row[3],
                    "form_type": row[4], # 0:代表, 1:対訳, 2:别称, 3:旧称, 4:误用
                    "abbr_type": row[5], # 0:代表, 1:略语(英), 2:略语(他)
                    "variant_type": row[6], # 0:代表, 1:英, 2:异, 3:误
                    "field": row[7],
                    "surface": row[8]
                }
                
                if group_id not in synonym_db:
                    synonym_db[group_id] = []
                synonym_db[group_id].append(entry)
    except FileNotFoundError:
        print(f"警告: 找不到同义词文件 {filepath}")
    return synonym_db

class SudachiAnalyzer:
    def __init__(self):
        print("正在初始化 Sudachi 分词器 (Small, Core, Full)...")
        try:
            self.tokenizer_small = sudachipy.Dictionary(dict="small").create()
            self.tokenizer_core = sudachipy.Dictionary(dict="core").create()
            self.tokenizer_full = sudachipy.Dictionary(dict="full").create()
            self.syn_db = load_synonyms("src/main/text/synonyms.txt")
            print("初始化完成。")
        except Exception as e:
            print(f"初始化失败: {e}")
            print("请确保已安装 sudachidict_small, sudachidict_core, sudachidict_full")
            sys.exit(1)

    def check_in_dict(self, tokenizer, surface: str, pos: tuple) -> bool:
        # 使用 C 模式分词，检查该词是否作为一个整体存在
        morphemes = tokenizer.tokenize(surface, sudachipy.SplitMode.C)
        if len(morphemes) == 1:
            m = morphemes[0]
            if m.surface() == surface and m.part_of_speech() == pos:
                return True
        return False

    def analyze(self, text: str, verbose: bool = False):
        print(f"\n分析文本: 「{text}」")
        print("-" * 60)
        
        morphemes = self.tokenizer_full.tokenize(text, sudachipy.SplitMode.C)
        
        for m in morphemes:
            surface = m.surface()
            pos = m.part_of_speech()
            
            # 判断来源
            source = "Full"
            if self.check_in_dict(self.tokenizer_small, surface, pos):
                source = "Small"
            elif self.check_in_dict(self.tokenizer_core, surface, pos):
                source = "Core"
            
            # 获取同义词信息
            synonym_group_ids = m.synonym_group_ids()
            syn_info_str = ""
            
            print(f"【{surface}】")
            print(f"  来源: {source}")
            print(f"  词性: {'-'.join(pos)}")
            
            if synonym_group_ids:
                print(f"  同义词信息:")
                for gid in synonym_group_ids:
                    gid_str = f"{gid:06d}"
                    if gid_str in self.syn_db:
                        group_entries = self.syn_db[gid_str]
                        # 获取代表词信息
                        ref = group_entries[0]
                        field = ref['field'] if ref['field'] else "无"
                        others = [e['surface'] for e in group_entries if e['surface'] != surface]
                        
                        print(f"    - [Group {gid_str}] 分野: {field}")
                        if verbose:
                            print(f"      详细信息:")
                            for entry in group_entries:
                                print(f"        - {entry['surface']} (ID:{entry['lexeme_id']}, Form:{entry['form_type']}, Abbr:{entry['abbr_type']})")
                        else:
                            print(f"      同组词: {', '.join(others[:10])}{'...' if len(others)>10 else ''}")
            else:
                print(f"  同义词信息: 无")
            print("-" * 30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sudachi 分词与词典来源分析工具')
    parser.add_argument('text', nargs='*', help='要分析的文本')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细同义词信息')
    args = parser.parse_args()

    analyzer = SudachiAnalyzer()
    
    if args.text:
        text = " ".join(args.text)
        analyzer.analyze(text, verbose=args.verbose)
    else:
        # 默认测试
        print("未提供文本，运行默认测试...")
        analyzer.analyze("京都に行きたい", verbose=args.verbose)
        analyzer.analyze("鬼滅の刃を見に行く", verbose=args.verbose)
