import os
import sys
import json
from datetime import datetime
from pathlib import Path
import time

class ArgFactory:
    def __init__(self):
        self.args = sys.argv[1:]
        self.extract_args(self.args)

    def extract_args(self,args):
        arg_dict = {
            '-p': 'path',
            '-o': 'output',
            '-ie': 'ignore_extension',
            '-if': 'ignore_folder',
        }

        present_arg_dict = {
            '-iw': 'ignore_whitespace',
            '-q': 'quiet',
            '-help': 'help'
        }

        for idx, item in enumerate(args):
            if item in arg_dict:
                type = arg_dict[item]
                switch_content = args[idx + 1]
                setattr(self, type, switch_content)
            if item in present_arg_dict:
                type = present_arg_dict[item]
                setattr(self, type, True)

    
class FileAnalyzer:
    def __init__(self, path, ignore_whitespace = False):
        self.path = path
        self.ignore_whitespace = ignore_whitespace


    def get_lines(self):
        num_lines = 0
        with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
            if self.ignore_whitespace:
                num_lines = sum(1 for line in f if not line.isspace())
            else:
                num_lines = sum(1 for _ in f)
        return num_lines
    
    def run_analysis(self):
        return {
            'path': self.path,
            'lines': self.get_lines()
        }
    
class HistoryAnalyzer:
    def __init__(self, current_scan, history):
        self.current_scan = current_scan
        self.full_history = history
        self.history = self.get_latest_scan()


    def get_latest_scan(self):
        for item in reversed(self.full_history):
            if item['search_path'] == self.current_scan['search_path']:
                return item
        return None
            

    def get_lines_dif(self):

        if not self.history:
            return self.current_scan['total']
        return self.current_scan['total'] - self.history['total']
    
    def get_files_dif(self):
        if not self.history:
            return []

        stats = []

        for new_entry in self.current_scan['items']:
            for old_entry in self.history['items']:
                if new_entry['path'] == old_entry['path'] and (new_entry['lines'] - old_entry['lines']) > 0:
                    stats.append({ 'path': new_entry['path'], 'lines_dif': new_entry['lines'] - old_entry['lines'] })
                    break

        return stats
    

    def get_history_analysis(self):
        return {
            'lines_dif': self.get_lines_dif(),
            'files_dif': self.get_files_dif()
        }


def main():
    time_start = time.time()
    arg_factory = ArgFactory()

    if hasattr(arg_factory, 'help'):
        print("""
=================================
LINE TRACKER
a small utility for tracking lines of code in a codebase and their changes

options: 
-p: path to scan
-o: output file
-ie: ignore extension
-if: ignore folder
-iw: ignore whitespace
-q: quiet
-h: help
              
=================================

""")
        return

    home = str(Path.home())

    existing_data = []
    current_entry = {
       "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
       "items": [],
       "total": 0,
       "search_path": arg_factory.path if hasattr(arg_factory, 'path') else None
   }

    if os.path.exists(f'{home}/.linecounter'):
       with open(f'{home}/.linecounter', 'r') as f:
           existing_data = json.load(f)


    if not hasattr(arg_factory, 'path'):
       print('No path specified')
       return
    
    ignore_paths = []
    if hasattr(arg_factory, 'ignore_folder'):
        ignore_paths = arg_factory.ignore_folder.split(',')
        ignore_paths = [x.strip() for x in ignore_paths]

    print(ignore_paths)

   # loop through filesystem starting at path
    for root, dirs, files in os.walk(arg_factory.path):
           # traverse files
           for name in files:
                path = os.path.join(root, name)
                # if path is in ignore list, skip
                found_path_match = False
                for ignore_path in ignore_paths:
                    if ignore_path in path:
                        found_path_match = True
                        break
                if found_path_match:
                    continue
                # if path has extension to ignore, skip
                if hasattr(arg_factory, 'ignore_extension') and arg_factory.ignore_extension in path:
                    continue

                
                should_ignore_whitespace = hasattr(arg_factory, 'ignore_whitespace')
                file_analyzer = FileAnalyzer(path, should_ignore_whitespace)
                analysis = file_analyzer.run_analysis()

                if not hasattr(arg_factory, 'quiet'):
                    print(f'File: {analysis["path"]} | Lines: {analysis["lines"]}')

                current_entry['total'] += analysis['lines']

                current_entry['items'].append({
                    'path': analysis['path'],
                    'lines': analysis['lines']
                })

    history_file_data = ""

 
    history_analyzer = HistoryAnalyzer(current_entry, existing_data)
    history_analysis = history_analyzer.get_history_analysis()
    history_total_changed = 0
    
    for item in history_analysis['files_dif']:
        history_file_data += f'{item["path"]} | {item["lines_dif"]} lines\n'
        history_total_changed += item['lines_dif']

    
    existing_data.append(current_entry)


    time_end = time.time()
    time_diff = time_end - time_start

    with open(f'{home}/.linecounter', 'w') as f:
        json.dump(existing_data, f, indent=4)


        print(f"""
=================================
CURRENT SCAN
---------------------------------
scan finished in {time_diff} seconds
total lines: {current_entry['total']}
log file exported to {home}/.linecounter
=================================
        """)

        
        print(f"""
=================================
HISTORY ANALYSIS
---------------------------------
lines difference: {history_analysis['lines_dif']}
total lines changed: {history_total_changed}
percentage of codebase affected: {round(history_total_changed / current_entry['total'] * 100, 2) if history_total_changed != 0 and current_entry['total'] != 0 else '0' }%
files difference: {history_file_data if history_file_data != "" else "No files changed"}
=================================
                              
""")



if __name__ == '__main__':
    main()