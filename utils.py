# utils.py
from pathlib import Path
import zipfile
from werkzeug.utils import secure_filename

def create_zip(folder: Path, zip_path: Path):
    with zipfile.ZipFile(zip_path, 'w') as z:
        for f in folder.iterdir():
            z.write(f, arcname=f.name)
    return zip_path

def safe_filename(name: str) -> str:
    return secure_filename(name)
