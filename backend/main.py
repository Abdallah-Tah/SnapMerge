from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont
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


def add_filename_to_image(img: Image.Image, filename: str, page_number: int) -> Image.Image:
    """Add professional filename label under the image for visa documentation"""

    # Calculate new image size with space for text
    margin = 60  # Space for text at bottom
    new_width = img.width
    new_height = img.height + margin

    # Create new image with white background
    new_img = Image.new('RGB', (new_width, new_height), 'white')

    # Paste the original image at the top
    new_img.paste(img, (0, 0))

    # Draw text
    draw = ImageDraw.Draw(new_img)

    # Try to load a professional font, fallback to default
    try:
        # Try to use a system font for professional appearance
        font_size = min(24, max(16, new_width // 40))  # Responsive font size
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            font = ImageFont.load_default()

    # Prepare text with page number and filename
    clean_filename = os.path.splitext(filename)[0]  # Remove extension
    text_line1 = f"Document {page_number}"
    text_line2 = clean_filename

    # Calculate text position (centered)
    bbox1 = draw.textbbox((0, 0), text_line1, font=font)
    bbox2 = draw.textbbox((0, 0), text_line2, font=font)
    text1_width = bbox1[2] - bbox1[0]
    text2_width = bbox2[2] - bbox2[0]

    x1 = (new_width - text1_width) // 2
    x2 = (new_width - text2_width) // 2
    y1 = img.height + 5
    y2 = y1 + 25

    # Draw text with professional styling
    # Add subtle shadow effect
    shadow_offset = 1
    draw.text((x1 + shadow_offset, y1 + shadow_offset),
              text_line1, font=font, fill='#CCCCCC')
    draw.text((x2 + shadow_offset, y2 + shadow_offset),
              text_line2, font=font, fill='#CCCCCC')

    # Draw main text
    draw.text((x1, y1), text_line1, font=font,
              fill='#2C3E50')  # Dark blue-gray
    draw.text((x2, y2), text_line2, font=font,
              fill='#34495E')  # Slightly lighter

    # Add a subtle line separator
    line_y = img.height + 2
    draw.line([(new_width//4, line_y), (3*new_width//4, line_y)],
              fill='#BDC3C7', width=1)

    return new_img


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

                # Add professional filename label for visa documentation
                img_with_label = add_filename_to_image(
                    img, file.filename, processed_count + 1)
                print(f"   📝 Added professional filename label")

                # Accept any image dimensions - no validation
                image_list.append(img_with_label)
                file_info.append({
                    "original_name": file.filename,
                    "ordered_name": ordered_filename,
                    "index": processed_count,
                    "size": img_with_label.size,
                    "mode": img_with_label.mode
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
            # Create high-quality PDF for visa documentation
            print(
                f"📄 Creating professional PDF with {len(image_list)} documented images...")

            if len(image_list) == 1:
                image_list[0].save(
                    pdf_path,
                    "PDF",
                    quality=98,  # Higher quality for official documents
                    optimize=False,  # Don't compress for better quality
                    resolution=300.0  # High resolution for professional printing
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
                    quality=98,  # Higher quality for official documents
                    optimize=False,  # Don't compress for better quality
                    resolution=300.0  # High resolution for professional printing
                )

            print(f"✅ High-quality PDF created for visa documentation")

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

        # Enhanced response headers with processing info for visa documentation
        response_headers = {
            "Content-Disposition": f"attachment; filename=immigration_visa_documents_{len(image_list)}_pages.pdf",
            "Cache-Control": "no-cache",
            "X-Processed-Images": str(len(image_list)),
            "X-Total-Files": str(len(files)),
            "X-Skipped-Files": str(len(skipped_files))
        }

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"immigration_visa_documents_{len(image_list)}_pages.pdf",
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
