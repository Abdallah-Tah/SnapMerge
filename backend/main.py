from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import os
from uuid import uuid4

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "SnapMerge API - Image to PDF Converter"}


@app.post("/convert")
async def convert_to_pdf(files: list[UploadFile] = File(...)):
    if not files:
        return {"error": "No files provided"}
    
    temp_dir = f"temp/{uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    image_list = []

    try:
        for file in files:
            contents = await file.read()
            path = os.path.join(temp_dir, file.filename)
            with open(path, "wb") as f:
                f.write(contents)
            img = Image.open(path).convert("RGB")
            image_list.append(img)

        pdf_path = f"{temp_dir}/output.pdf"
        if len(image_list) == 1:
            image_list[0].save(pdf_path)
        else:
            image_list[0].save(pdf_path, save_all=True, append_images=image_list[1:])
        
        return FileResponse(pdf_path, media_type="application/pdf", filename="merged.pdf")
    
    except Exception as e:
        return {"error": f"Failed to process images: {str(e)}"}
