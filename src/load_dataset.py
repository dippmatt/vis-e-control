import subprocess
from pathlib import Path
from colorama import Fore
import pandas as pd

"""
def download_dataset(url: str, target_path: Path):
    dataset_pwd = target_path.parent
    if not target_path.exists():
        subprocess.run(["wget", "-P", str(target_path), url], cwd=dataset_pwd)
    else:
        print(Fore.GREEN + f"Skipping download of {target_path}.")
        print(Fore.RESET + f"{target_path} already exists.")

def unzip_dataset_and_convert(zipped_path: Path, target_path: Path):
    dataset_pwd = zipped_path.parent
    if not target_path.exists():
        subprocess.run(["unzip", str(zipped_path)], cwd=dataset_pwd)
    else:
        print(Fore.GREEN + f"Skipping conversion of {zipped_path} to COCO.")
        print(Fore.RESET + f"{target_path} already exists.")
"""

def _main():
    print(Fore.GREEN + "Loading dataset...")


if __name__ == "__main__":
    _main()