# === Project Structure ===

# image-to-pdf-app/

# ├── backend/

# │ ├── main.py # FastAPI backend

# │ └── requirements.txt

# ├── frontend/

# │ ├── pages/

# │ │ └── index.tsx # Upload UI

# │ └── utils/

# │ └── api.ts # Axios for backend calls

# === backend/main.py ===

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

@app.post("/convert")
async def convert_to_pdf(files: list[UploadFile] = File(...)):
temp_dir = f"temp/{uuid4()}"
os.makedirs(temp_dir, exist_ok=True)
image_list = []

    for file in files:
        contents = await file.read()
        path = os.path.join(temp_dir, file.filename)
        with open(path, "wb") as f:
            f.write(contents)
        img = Image.open(path).convert("RGB")
        image_list.append(img)

    pdf_path = f"{temp_dir}/output.pdf"
    image_list[0].save(pdf_path, save_all=True, append_images=image_list[1:])
    return FileResponse(pdf_path, media_type="application/pdf", filename="merged.pdf")

# === backend/requirements.txt ===

fastapi
uvicorn
pillow
python-multipart

# === frontend/utils/api.ts ===

import axios from 'axios'

export const uploadImages = async (files: File[]) => {
const formData = new FormData()
files.forEach(f => formData.append('files', f))
const res = await axios.post('http://localhost:8000/convert', formData, {
responseType: 'blob'
})
return res.data
}

# === frontend/pages/index.tsx ===

import { useState } from 'react'
import { uploadImages } from '../utils/api'

export default function Home() {
const [pdfUrl, setPdfUrl] = useState<string | null>(null)

const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
const files = e.target.files
if (files) {
const pdfBlob = await uploadImages(Array.from(files))
const url = URL.createObjectURL(pdfBlob)
setPdfUrl(url)
}
}

return (
<div style={{ padding: 40 }}>
<h1>Image to PDF Converter</h1>
<input type="file" multiple accept="image/*" onChange={handleUpload} />
{pdfUrl && (
<p><a href={pdfUrl} download="merged.pdf">Download PDF</a></p>
)}
</div>
)
}
