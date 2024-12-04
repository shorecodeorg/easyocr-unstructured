# File to package standard project folders into a distribution
# ready for clients to use. Remove development assets that are not needed
# by the end-user or for maintenace. Remove any assets created
# by testing.

import threading
import argparse
import zipfile
import fnmatch
import os
import subprocess
from bandit.core.manager import BanditManager
from bandit.core.config import BanditConfig
from bandit import formatters



class Distro:
    def __init__(self, create_dist: bool, entry_point: str, version: str):
        self.create_dist = create_dist
        self.entry_point = os.path.split(entry_point)[-1]
        self.version = version
        if not self.version:
            self.version = ''
        
    def write_to_zip(self, files: list, dirs: list, project_name: str) -> str:
        zip_fp = f'{project_name}_v{self.version}.zip'
        cwd = os.getcwd()
        with zipfile.ZipFile(zip_fp, 'w', zipfile.ZIP_STORED, allowZip64=True) as zipf:

            for dirpath in dirs:
                if os.path.isdir(dirpath):
                    print(dirpath)
                    arcname = os.path.relpath(dirpath, cwd) + '/'
                    arcname = os.path.join(project_name, arcname)
                    zip_info = zipfile.ZipInfo(arcname)
                    zipf.writestr(zip_info, '')
                else:
                    print(f"Warning: {dirpath} is not a valid directory and will be skipped.")            
            
            for filepath in files:
                if os.path.isfile(filepath):
                    arcname = os.path.relpath(filepath, cwd)
                    arcname = os.path.join(project_name, arcname)
                    zipf.write(filepath, arcname)
                else:
                    print(f"Warning: {filepath} is not a valid file and will be skipped.")
                    
        return zip_fp
        
    def get_files_to_add(self, config: dict) -> list:        
        files_to_add = []
        dirs_to_add = []
        excluded_files = config.get('excluded_files', [])
        excluded_dirs = config.get('excluded_dirs', [])
        excluded_wildcard_files = config.get('excluded_wildcard_files', [])
        excluded_wildcard_dirs = config.get('excluded_wildcard_dirs', [])
        excluded_dir_contents = config.get('excluded_dir_contents', [])

        for root, dirs, files in os.walk(os.getcwd()):
            # Exclude directories            
            dirs[:] = [os.path.join(root, d) for d in dirs if d not in excluded_dirs and not any(fnmatch.fnmatch(os.path.join(root, d), pattern) for pattern in excluded_wildcard_dirs)]
            dirs_to_add.extend(dirs)
            
            for file in files:
                file_path = os.path.join(root, file)
                if (file not in excluded_files 
                        and not any(fnmatch.fnmatch(file, pattern) for pattern in excluded_wildcard_files)
                        and not any(pattern in file_path.split('/') for pattern in excluded_dir_contents)):
                    files_to_add.append(file_path)
        dirs_result = set(dirs_to_add)
        return files_to_add, dirs_result
    
    def get_config(self) -> dict:
        return {
            'excluded_files': ['.gitignore', 'regexp.txt', 'setup.sh', 'setup.py', 'release.py'],
            'excluded_dirs': ['.git', '__pycache__', 'logging', '__pycache__'],
            'excluded_dir_contents': ['output'],
            'excluded_wildcard_files': ['*.wpr', '*.wpu', '*.log', '*_v*.zip'],
            'excluded_wildcard_dirs': ['*.egg-info*'],
        }
    
    def clean_requirements_dot_txt(self) -> None:
        file_path = './requirements.txt'
        target_line = "# Editable Git install with no remote"
    
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
    
            # Find the target line and remove it along with the following line
            for i, line in enumerate(lines):
                if target_line in line.strip():
                    del lines[i:i+2]
    
            # Write the modified content back to the file
            with open(file_path, 'w') as file:
                file.writelines(lines)
    
        except FileNotFoundError:
            print(f"File {file_path} not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def get_project_name(self) -> str:
        return os.path.split(os.path.dirname(__file__))[-1]
    
    def add_bandit_scan(self, files: list) -> list:
        python_files = [f for f in files if f.endswith('.py')]
        if not python_files:
            print("No Python files to scan.")
            return files
        # Create a Bandit manager
        b_conf = BanditConfig()
        b_mgr = BanditManager(b_conf, 'file')
        # Run Bandit on each Python file
        for py_file in python_files:
            b_mgr.discover_files([py_file])
        b_mgr.run_tests()
        # Save the Bandit report to a text file
        report_file = 'docs/bandit_report.txt'
        with open(report_file, 'w') as report_fp:
            formatters.text.report(b_mgr, report_fp, sev_level='Low', conf_level='Low')
        
        # Add the report file to the list of files
        files.append(os.path.abspath(report_file))
        return files
    
    def find_logging_file(self) -> str:
        src_dir = './src'
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith('.py') and not file.endswith('.pyc') and ('logging' in file or 'log_template' in file):
                    file_path = os.path.join(root, file)
                    return file_path
        return None
    
    def remove_dev_mode_logging(self, logging_fp: str) -> None:
        if not logging_fp or not os.path.isfile(logging_fp):
            print(f"File {logging_fp} does not exist.")
            return
        with open(logging_fp, 'r') as file:
            lines = file.readlines()
        with open(logging_fp, 'w') as file:
            for line in lines:
                if line.strip() == 'dev = True':
                    file.write('    dev = False\n')
                else:
                    file.write(line)
    
    def display_docs_reminder(self, zip_fp: str) -> None:
        print('*********************:)*****************************')
        print(f'Project zip file created at {zip_fp}.')
        print('Make sure to review the license and readme files!')
        
    def run_pyinstaller(self, entry_point: str) -> None:
        if not os.path.isfile(entry_point):
            print(f"Entry point file {entry_point} does not exist.")
            return

        entry_dir = os.path.dirname(entry_point)
        sub_dirs = [d for d in os.listdir(entry_dir) if os.path.isdir(os.path.join(entry_dir, d))]

        # Construct the PyInstaller command
        pyinstaller_cmd = [
            'pyinstaller',
            entry_point
        ]

        # Add sub-directories to the PyInstaller command
        for sub_dir in sub_dirs:
            pyinstaller_cmd.extend(['--add-data', f"{os.path.join(entry_dir, sub_dir)}{os.pathsep}{sub_dir}"])

        # Run the PyInstaller command
        try:
            subprocess.run(pyinstaller_cmd, check=True)
            print("PyInstaller ran successfully.")
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller failed: {e}")
    
    def edit_template_dot_bat(self, project_name: str) -> None:
        if not os.path.isfile('template.bat'):
            return
        with open('template.bat', 'r') as fn:
            template = fn.readlines()
        for idx, line in enumerate(template):
            if line == 'python "%~dp0src\.py"\n':
                template.remove(line)
                template.insert(idx, f'python "%~dp0src\{self.entry_point}"\n')
        with open(f'{project_name}.bat', 'w') as fn:
            fn.writelines(template)
        os.remove('template.bat')
    
    def run(self) -> None:
        thread = None
        config = self.get_config()
        self.clean_requirements_dot_txt()        
        project_name = self.get_project_name()
        self.edit_template_dot_bat(project_name)
        logging_fp = self.find_logging_file()
        self.remove_dev_mode_logging(logging_fp)
        if self.create_dist == True:
            thread = threading.Thread(target=self.run_pyinstaller, args=(self.entry_point, ))
            thread.start()
        files, dirs = self.get_files_to_add(config)
        files = self.add_bandit_scan(files)
        zip_fp = self.write_to_zip(files, dirs, project_name)
        if thread:
            thread.join()
        self.display_docs_reminder(zip_fp)
        
def get_args():
    parser = argparse.ArgumentParser(description="Create a zip file for distribution from a Shorecode LLC Python development folder.")
    parser.add_argument('version', help="string: Version number for the distribution.")
    parser.add_argument('dist', help="y/n: Create a Pyinstaller distribution, yes or no.")
    parser.add_argument('entry', help="str: Filepath for the main entry point .py file.")
    
    args = parser.parse_args()
    return args
    

if __name__ == '__main__':
    args = get_args()
    if args.dist == "y":
        dist = True
    else:
        dist = False
    distro = Distro(dist, args.entry, args.version)
    distro.run()
