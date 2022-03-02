import os
import shutil


def clean_up_dir(target_dir):
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)