import os
import json

class CloudStorageService:
    def __init__(self):
        # Create .files directory if it doesn't exist
        os.makedirs('./.files', exist_ok=True)

    async def upload_file(self, path: str, contents: bytes, metadata: dict = None) -> str:
        # Save file to .files directory
        file_path = os.path.join('./.files', path)
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Save metadata in a sidecar file if provided
        if metadata:
            metadata_path = f"{file_path}.meta.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
        return path

    async def get_file(self, path: str) -> bytes:
        file_path = os.path.join('./.files', path)
        with open(file_path, 'rb') as f:
            return f.read()
            
    async def get_file_metadata(self, path: str) -> dict:
        file_path = os.path.join('./.files', path)
        metadata_path = f"{file_path}.meta.json"
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def delete_file(self, path: str) -> bool:
        file_path = os.path.join('./.files', path)
        metadata_path = f"{file_path}.meta.json"
        
        # Delete the metadata file if it exists
        try:
            os.remove(metadata_path)
        except FileNotFoundError:
            pass
            
        # Delete the main file
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return False
