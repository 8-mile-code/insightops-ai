from pathlib import Path

import aiofiles


class FileStorageService:
    """Responsible for only file storage operations."""
    async def save_file(
            self,
            file_path: Path,
            content: bytes
    ) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
