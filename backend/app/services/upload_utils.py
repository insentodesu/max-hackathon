from dataclasses import dataclass
from typing import Sequence

from fastapi import UploadFile


@dataclass(slots=True)
class IncomingUpload:
    filename: str
    content: bytes
    content_type: str | None

    @property
    def size(self) -> int:
        return len(self.content)


async def gather_incoming_uploads(files: Sequence[UploadFile]) -> list[IncomingUpload]:
    uploads: list[IncomingUpload] = []
    for file in files:
        content = await file.read()
        file.file.close()
        uploads.append(
            IncomingUpload(
                filename=file.filename or "",
                content=content,
                content_type=file.content_type,
            )
        )
    return uploads