from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import os
import shutil
from uuid import uuid4
from typing import List
import asyncio

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


@app.post("/preview-order")
async def preview_file_order(files: list[UploadFile] = File(...)):
    """Preview the order of uploaded files without processing them"""
    if not files:
        return {"error": "No files provided"}

    file_preview = []
    for index, file in enumerate(files):
        # Reset file pointer
        await file.seek(0)

        file_preview.append({
            "index": index,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size if hasattr(file, 'size') else "Unknown"
        })

    return {
        "total_files": len(files),
        "processing_order": file_preview,
        "message": f"Files will be processed in the order shown above (0-{len(files)-1})"
    }


def cleanup_temp_directory(temp_dir: str):
    """Clean up temporary directory after processing"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not clean up temp directory {temp_dir}: {e}")


@app.post("/convert")
async def convert_to_pdf(files: list[UploadFile] = File(...)):
    if not files:
        return {"error": "No files provided"}

    print(f"🔄 Starting conversion process...")
    print(f"📊 Received {len(files)} files for processing")

    # Log file details
    for i, file in enumerate(files):
        print(f"   File {i+1}: {file.filename} ({file.content_type})")

    temp_dir = f"temp/{uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    image_list = []
    file_info = []

    try:
        # Process files in the exact order they were uploaded
        processed_count = 0
        skipped_files = []

        for index, file in enumerate(files):
            print(
                f"🔍 Processing file {index + 1}/{len(files)}: {file.filename}")

            # Read file contents directly without validation
            contents = await file.read()
            print(f"   📖 Read {len(contents)} bytes")

            # Create ordered filename to preserve sequence
            file_extension = os.path.splitext(
                file.filename)[1] if file.filename else ".jpg"
            ordered_filename = f"{processed_count:03d}_{file.filename}" if file.filename else f"{processed_count:03d}_image{file_extension}"
            path = os.path.join(temp_dir, ordered_filename)

            # Save file to disk
            with open(path, "wb") as f:
                f.write(contents)

            # Try to process as image - force processing even if validation fails
            try:
                img = Image.open(path)
                print(
                    f"   🖼️  Valid image: {img.size} pixels, mode: {img.mode}")

                # Handle various image formats and modes
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split(
                    )[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                    print(f"   🔄 Converted transparent/palette image to RGB")
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                    print(f"   🔄 Converted {img.mode} to RGB")

                # Accept any image dimensions - no validation
                image_list.append(img)
                file_info.append({
                    "original_name": file.filename,
                    "ordered_name": ordered_filename,
                    "index": processed_count,
                    "size": img.size,
                    "mode": img.mode
                })
                processed_count += 1
                print(
                    f"   ✅ Successfully processed as image #{processed_count}")

            except Exception as img_error:
                # Log the error but still try to continue with other files
                reason = f"Could not process as image: {str(img_error)}"
                print(f"   ❌ {reason}")
                skipped_files.append({
                    "filename": file.filename,
                    "reason": reason
                })
                # Remove the invalid file
                if os.path.exists(path):
                    os.remove(path)
                continue

        if not image_list:
            error_msg = "No valid image files found."
            if skipped_files:
                error_msg += f" Skipped {len(skipped_files)} files: "
                error_msg += ", ".join(
                    [f"{sf['filename']} ({sf['reason']})" for sf in skipped_files[:3]])
                if len(skipped_files) > 3:
                    error_msg += f" and {len(skipped_files) - 3} more..."
            return JSONResponse(
                status_code=400,
                content={"error": error_msg, "skipped_files": skipped_files}
            )

        # Create PDF with images in the exact upload order
        pdf_path = f"{temp_dir}/snapmerge_ordered.pdf"

        try:
            # Save first image as PDF, then append the rest in order
            if len(image_list) == 1:
                image_list[0].save(
                    pdf_path,
                    "PDF",
                    quality=95,
                    optimize=True,
                    resolution=150.0
                )
            else:
                # Ensure all images are in RGB mode for PDF compatibility
                rgb_images = []
                for img in image_list[1:]:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    rgb_images.append(img)

                image_list[0].save(
                    pdf_path,
                    "PDF",
                    save_all=True,
                    append_images=rgb_images,
                    quality=95,
                    optimize=True,
                    resolution=150.0
                )
        except Exception as pdf_error:
            cleanup_temp_directory(temp_dir)
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to create PDF: {str(pdf_error)}"}
            )

        # Log processing summary
        print(f"✅ Successfully processed {len(image_list)} images")
        if skipped_files:
            print(f"⚠️  Skipped {len(skipped_files)} files:")
            for sf in skipped_files:
                print(f"   - {sf['filename']}: {sf['reason']}")

        # Verify the PDF was created successfully
        if not os.path.exists(pdf_path):
            cleanup_temp_directory(temp_dir)
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to create PDF file"}
            )

        # Check PDF file size
        pdf_size = os.path.getsize(pdf_path)
        if pdf_size == 0:
            cleanup_temp_directory(temp_dir)
            return JSONResponse(
                status_code=500,
                content={"error": "Generated PDF file is empty"}
            )

        # Schedule cleanup of temp directory after a longer delay
        asyncio.create_task(delayed_cleanup(
            temp_dir, delay_seconds=600))  # 10 minutes instead of 5

        # Enhanced response headers with processing info
        response_headers = {
            "Content-Disposition": f"attachment; filename=snapmerge_merged_{len(image_list)}_images.pdf",
            "Cache-Control": "no-cache",
            "X-Processed-Images": str(len(image_list)),
            "X-Total-Files": str(len(files)),
            "X-Skipped-Files": str(len(skipped_files))
        }

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"snapmerge_merged_{len(image_list)}_images.pdf",
            headers=response_headers
        )

    except Exception as e:
        # Clean up on error
        cleanup_temp_directory(temp_dir)
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process images: {str(e)}"}
        )


async def delayed_cleanup(temp_dir: str, delay_seconds: int = 300):
    """Clean up temporary directory after a delay"""
    await asyncio.sleep(delay_seconds)
    cleanup_temp_directory(temp_dir)
