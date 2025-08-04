from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont
import os
import shutil
from uuid import uuid4
from typing import List
import asyncio
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import io
import PyPDF2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition",
                    "X-Processed-Images", "X-Total-Files", "X-Skipped-Files"],
)


def optimize_image_for_pdf(img: Image.Image, max_width: int = 800, max_height: int = 1200, quality: int = 65) -> Image.Image:
    """
    Optimize image for PDF to reduce file size while maintaining quality for visa documents
    """
    # Convert to RGB if not already
    if img.mode != 'RGB':
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()
                             [-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        else:
            img = img.convert('RGB')

    # Calculate new dimensions maintaining aspect ratio
    width, height = img.size

    # Only resize if image is larger than max dimensions
    if width > max_width or height > max_height:
        # Calculate scaling factor
        width_ratio = max_width / width
        height_ratio = max_height / height
        scale_factor = min(width_ratio, height_ratio)

        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        # Use LANCZOS for high-quality resizing
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        print(
            f"   📏 Resized from {width}x{height} to {new_width}x{new_height}")

    # Apply additional compression by reducing quality slightly
    # Save to bytes buffer with compression
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)

    # Load back the compressed image
    compressed_img = Image.open(buffer)

    return compressed_img


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


def generate_pdf_filename(file_info: list, image_count: int) -> str:
    """Generate PDF filename using the same logic as the image labels"""

    # If only one image, use the clean filename (same as image label)
    if image_count == 1 and file_info:
        original_name = file_info[0]['original_name']
        # Use the same logic as add_filename_to_image function
        clean_filename = os.path.splitext(original_name)[0]  # Remove extension
        return f"{clean_filename}.pdf"

    # For multiple images, create a descriptive name using the first image's clean filename
    if file_info:
        first_file = file_info[0]['original_name']
        clean_filename = os.path.splitext(first_file)[0]  # Remove extension

        # Add suffix for multiple documents
        if image_count > 1:
            return f"{clean_filename}_and_{image_count-1}_more_documents.pdf"

    # Fallback
    return f"merged_documents_{image_count}_pages.pdf"


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
    margin = 80  # Slightly reduced space for text at bottom
    horizontal_padding = 30  # Equal padding from both sides
    new_width = max(img.width, 800)  # Ensure minimum width for text
    new_height = img.height + margin

    # Create new image with white background
    new_img = Image.new('RGB', (new_width, new_height), 'white')

    # Calculate position to center the original image
    x_offset = (new_width - img.width) // 2
    new_img.paste(img, (x_offset, 0))

    # Draw text
    draw = ImageDraw.Draw(new_img)

    # Try to load a professional font, fallback to default
    try:
        # Adjust font size based on image width while ensuring readability
        # Adjusted font size calculation
        font_size = min(32, max(18, new_width // 50))
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            font = ImageFont.load_default()

    # Prepare text with filename only
    clean_filename = os.path.splitext(filename)[0]  # Remove extension
    text = clean_filename

    # Calculate text size to ensure it fits
    text = clean_filename
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # If text is too wide, try to shrink it
    max_width = new_width - (2 * horizontal_padding)
    if text_width > max_width:
        # Reduce font size until it fits
        while text_width > max_width and font_size > 12:
            font_size -= 2
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

    # Calculate position to center the text
    x = (new_width - text_width) // 2  # Center horizontally
    # Center vertically in margin area
    y = img.height + (margin - text_height) // 2

    # Draw text with professional styling
    # Enhanced shadow effect for better readability
    shadow_offset = 2
    shadow_color = '#BBBBBB'  # Slightly lighter shadow for professional look

    # Draw shadow with multiple layers for depth
    for offset in range(shadow_offset):
        draw.text((x + offset, y + offset),
                  text, font=font, fill=shadow_color)

    # Draw main text with professional styling
    draw.text((x, y), text, font=font,
              fill='#1A365D')  # Rich navy blue for professional look

    return new_img


def create_professional_pdf(image_list: List[Image.Image], pdf_path: str, file_info: List[dict]):
    """Create a professional PDF using ReportLab for consulate documents"""

    # A4 page dimensions in points (1 point = 1/72 inch)
    page_width, page_height = A4
    margin = 0.5 * inch  # 0.5 inch margins
    usable_width = page_width - (2 * margin)
    usable_height = page_height - (2 * margin)

    # Create the PDF canvas
    c = canvas.Canvas(pdf_path, pagesize=A4)

    # Set PDF metadata for official documents
    # c.setTitle("Immigration Visa Documents")
    # c.setAuthor("SnapMerge Document Converter")
    # c.setSubject("Official Immigration Documentation")
    # c.setKeywords("visa, immigration, documents, official")

    for i, img in enumerate(image_list):
        if i > 0:  # Add new page for each image after the first
            c.showPage()

        # Convert PIL image to bytes for ReportLab with compression
        img_buffer = io.BytesIO()
        # Use JPEG with lower quality for smaller file size
        img.save(img_buffer, format='JPEG', quality=70, optimize=True)
        img_buffer.seek(0)

        # Create ImageReader object
        img_reader = ImageReader(img_buffer)

        # Calculate scaling to fit page while maintaining aspect ratio
        img_width_px, img_height_px = img.size

        # Calculate the maximum size that fits on the page
        scale_w = usable_width / img_width_px
        scale_h = usable_height / img_height_px
        # Use the smaller scale to fit both dimensions
        scale = min(scale_w, scale_h)

        # Calculate final dimensions
        final_width = img_width_px * scale
        final_height = img_height_px * scale

        # Center the image on the page
        x_offset = margin + (usable_width - final_width) / 2
        y_offset = margin + (usable_height - final_height) / 2

        # Draw the image at high resolution
        c.drawImage(
            img_reader,
            x_offset,
            y_offset,
            width=final_width,
            height=final_height,
            preserveAspectRatio=True,
            anchor='c'
        )

        # Add professional header
        # c.setFont("Helvetica-Bold", 12)
        # c.drawString(margin, page_height - 30, "OFFICIAL IMMIGRATION DOCUMENT")

        # Add page number and document info
        # c.setFont("Helvetica", 10)
        # page_info = f"Page {i + 1} of {len(image_list)}"
        # if i < len(file_info):
        #     page_info += f" - {file_info[i]['original_name']}"

        # c.drawRightString(page_width - margin, page_height - 30, page_info)

        # Add footer with timestamp and system info
        c.setFont("Helvetica", 8)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        # footer_text = f"Generated by SnapMerge on {timestamp} - High Resolution: 300 DPI"

        # Calculate centered position for footer text
        # text_width = c.stringWidth(footer_text, "Helvetica", 8)
        # footer_x = (page_width - text_width) / 2
        # c.drawString(footer_x, 20, footer_text)

        # Add quality assurance note
        # c.setFont("Helvetica", 7)
        # quality_note = "This document maintains original image quality and resolution for official use"

        # # Calculate centered position for quality note
        # quality_width = c.stringWidth(quality_note, "Helvetica", 7)
        # quality_x = (page_width - quality_width) / 2
        # c.drawString(quality_x, 10, quality_note)

    # Save the PDF with compression
    c.save()

    # Apply additional PDF compression to reduce file size
    compress_pdf(pdf_path)

    print(
        f"✅ Compressed PDF created: {len(image_list)} pages optimized for small file size")


def compress_pdf(pdf_path: str):
    """Compress PDF file to reduce size"""
    try:
        # Read the original PDF
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()

            # Copy pages with compression
            for page in reader.pages:
                # Remove unnecessary data and compress
                page.compress_content_streams()
                writer.add_page(page)

            # Set compression options
            # writer.add_metadata({
            #     '/Title': 'Immigration Visa Documents - Compressed',
            #     '/Subject': 'Official Immigration Documentation',
            #     '/Creator': 'SnapMerge Document Converter'
            # })

            # Write compressed PDF
            temp_path = pdf_path + '.tmp'
            with open(temp_path, 'wb') as output_file:
                writer.write(output_file)

        # Replace original with compressed version
        import shutil
        shutil.move(temp_path, pdf_path)
        print(f"   📦 PDF compressed successfully")

    except Exception as e:
        print(f"   ⚠️  PDF compression failed: {e}")
        # If compression fails, continue with original PDF


@app.post("/convert")
async def convert_to_pdf(
    files: list[UploadFile] = File(...),
    mode: str = Form('merge')  # 'merge' or 'split'
):
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
                original_size = img.size
                print(
                    f"   🖼️  Original image: {img.size} pixels, mode: {img.mode}")

                # Optimize image for PDF (resize + compress)
                img = optimize_image_for_pdf(
                    img, max_width=800, max_height=1200, quality=60)
                print(f"   ✅ Optimized: {original_size} → {img.size} pixels")

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

        # Handle split or merge modes
        if mode == 'split':
            # Generate a PDF per image and zip them
            zip_path = os.path.join(temp_dir, 'split_documents.zip')
            import zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for i, img in enumerate(image_list):
                    info = file_info[i]
                    # single PDF for this image
                    single_name = os.path.splitext(
                        info['original_name'])[0] + '.pdf'
                    single_path = os.path.join(temp_dir, single_name)
                    create_professional_pdf([img], single_path, [info])
                    zf.write(single_path, arcname=single_name)
            # Schedule cleanup
            asyncio.create_task(delayed_cleanup(temp_dir, delay_seconds=600))
            # Return zip file
            return FileResponse(
                zip_path,
                media_type='application/zip',
                headers={
                    'Content-Disposition': f"attachment; filename=split_documents.zip",
                    'Cache-Control': 'no-cache',
                    'X-Processed-Images': str(len(image_list)),
                    'X-Total-Files': str(len(files)),
                    'X-Skipped-Files': str(len(skipped_files))
                }
            )
        # Merge mode: create one PDF with all images
        pdf_path = f"{temp_dir}/snapmerge_ordered.pdf"

        try:
            # Create professional PDF using ReportLab for consulate documents
            print(
                f"📄 Creating professional PDF with {len(image_list)} documented images...")

            # Use ReportLab for better control and professional output
            create_professional_pdf(image_list, pdf_path, file_info)

            print(f"✅ Professional PDF created with ReportLab for consulate submission")

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

        # Generate meaningful PDF filename based on input images
        pdf_filename = generate_pdf_filename(file_info, len(image_list))
        print(f"🏷️  Generated PDF filename: {pdf_filename}")
        print(
            f"📁 File info for filename generation: {[f['original_name'] for f in file_info]}")

        # Enhanced response headers with processing info for visa documentation
        # Properly encode filename for Content-Disposition header
        import urllib.parse
        encoded_filename = urllib.parse.quote(pdf_filename)

        response_headers = {
            "Content-Disposition": f'attachment; filename="{pdf_filename}"; filename*=UTF-8\'\'{encoded_filename}',
            "Cache-Control": "no-cache",
            "X-Processed-Images": str(len(image_list)),
            "X-Total-Files": str(len(files)),
            "X-Skipped-Files": str(len(skipped_files))
        }

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
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
