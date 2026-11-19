from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".txt", ".vtt", ".md"}
# Same limit as the paste field. A byte is at least one character, so this also caps the text length.
MAX_BYTES = 200_000


async def read_transcript_upload(file: UploadFile) -> str:
    # Cheapest checks first: extension, then size, then encoding.
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Upload a .txt, .vtt or .md file")

    # Read one byte past the limit, so an oversized file is detected without loading all of it.
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 200 KB")

    try:
        # utf-8-sig removes the byte-order mark some editors add to the start of a file.
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="File must be UTF-8 text")
