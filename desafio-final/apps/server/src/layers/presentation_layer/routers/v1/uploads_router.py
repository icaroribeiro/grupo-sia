from fastapi import APIRouter
from fastapi import File, UploadFile, HTTPException
from fastapi import status

router = APIRouter()


@router.post("/upload-zip", status_code=201)
async def upload_zip(file: UploadFile = File(...)):
    if file.content_type != "application/zip":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only ZIP files are allowed",
        )

    content = await file.read()

    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(content)

    return {"filename": file.filename, "message": "ZIP file uploaded successfully"}
