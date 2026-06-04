from fastapi import UploadFile, HTTPException


async def read_python_file(upload: UploadFile) -> str:
    if not upload.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .py")

    content = await upload.read()
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="El archivo no es UTF-8 válido")
