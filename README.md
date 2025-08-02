# 🔥 SnapMerge - Image to PDF Converter

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.4+-black.svg)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)

**SnapMerge** is a modern, professional web application that converts multiple images into a single PDF file. Built with a FastAPI backend and a beautiful Next.js frontend with shadcn/ui components.

![SnapMerge Demo](https://via.placeholder.com/800x400/4F46E5/FFFFFF?text=SnapMerge+Demo)

## ✨ Features

- 🖼️ **Multi-Image Upload**: Select multiple images at once
- 📱 **Drag & Drop**: Intuitive drag-and-drop interface
- 🎨 **Professional UI**: Modern design with gradients and animations
- 📄 **PDF Conversion**: High-quality image-to-PDF conversion
- 🔄 **Real-time Preview**: See selected files before conversion
- 📊 **File Management**: Add/remove files with file size display
- ⚡ **Fast Processing**: Efficient conversion using PIL/Pillow
- 🌐 **CORS Enabled**: Cross-origin requests supported
- 📱 **Responsive Design**: Works on desktop and mobile devices

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **Python 3.8+** - Programming language
- **PIL/Pillow** - Image processing library
- **Uvicorn** - ASGI server for running the application

### Frontend
- **Next.js 15.4+** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful, accessible UI components
- **Lucide React** - Icon library

## 📋 Prerequisites

- **Python 3.8+** installed on your system
- **Node.js 18+** and npm installed
- **Git** for cloning the repository

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/snapmerge.git
cd snapmerge
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Install shadcn/ui components
npx shadcn@latest init
npx shadcn@latest add button input

# Install additional dependencies
npm install lucide-react
```

## 🏃‍♂️ Running the Application

### Start the Backend Server

```bash
cd backend
source venv/bin/activate  # Activate virtual environment
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: `http://localhost:8000`

### Start the Frontend Server

```bash
cd frontend
npm run dev
```

The frontend will be available at: `http://localhost:3000` (or `http://localhost:3001` if 3000 is in use)

## 📚 API Documentation

### Endpoints

#### `GET /`
- **Description**: Health check endpoint
- **Response**: `{"message": "SnapMerge API - Image to PDF Converter"}`

#### `POST /convert`
- **Description**: Convert multiple images to PDF
- **Parameters**: 
  - `files`: List of image files (multipart/form-data)
- **Supported Formats**: PNG, JPG, JPEG, GIF, BMP, TIFF
- **Response**: PDF file download
- **Error Response**: `{"error": "Error message"}`

### Example Usage with cURL

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  --output merged.pdf
```

## 📁 Project Structure

```
snapmerge/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── venv/               # Virtual environment (created after setup)
│   └── temp/               # Temporary files (created during operation)
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx    # Main page component
│   │   │   ├── layout.tsx  # Root layout
│   │   │   └── globals.css # Global styles
│   │   ├── components/
│   │   │   └── ui/         # shadcn/ui components
│   │   └── lib/
│   │       └── utils.ts    # Utility functions
│   ├── package.json        # Node.js dependencies
│   ├── tailwind.config.js  # Tailwind CSS configuration
│   ├── next.config.js      # Next.js configuration
│   └── tsconfig.json       # TypeScript configuration
└── README.md               # This file
```

## 🔧 Configuration

### Backend Configuration

The backend server can be configured by modifying the following in `backend/main.py`:

- **CORS Origins**: Currently set to `["*"]` for development
- **File Upload Limits**: Adjust FastAPI settings for larger files
- **Temp Directory**: Currently uses `temp/{uuid4()}`

### Frontend Configuration

The frontend can be configured in:

- **API URL**: Update the fetch URL in `src/app/page.tsx`
- **Styling**: Modify Tailwind classes or add custom CSS
- **Components**: Customize shadcn/ui components in `src/components/ui/`

## 🧪 Testing

### Backend Testing

```bash
cd backend
source venv/bin/activate

# Test the API endpoint
curl http://localhost:8000/

# Test with a sample image
curl -X POST "http://localhost:8000/convert" \
  -F "files=@sample.jpg" \
  --output test.pdf
```

### Frontend Testing

```bash
cd frontend

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 📱 Usage Guide

1. **Open the Application**: Navigate to `http://localhost:3001` in your browser
2. **Select Images**: Click "Choose Files" or drag images to the upload area
3. **Preview Files**: Review selected images with file names and sizes
4. **Convert**: Click "Convert to PDF" to process the images
5. **Download**: Once conversion is complete, click "Download PDF"

### Supported File Formats

- **PNG** - Portable Network Graphics
- **JPG/JPEG** - Joint Photographic Experts Group
- **GIF** - Graphics Interchange Format
- **BMP** - Bitmap Image File
- **TIFF** - Tagged Image File Format

## 🚨 Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill the process if needed
kill -9 <PID>
```

#### Frontend Build Errors
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### CORS Issues
- Ensure the backend CORS middleware is properly configured
- Check that the frontend is making requests to the correct backend URL

#### File Upload Issues
- Verify file formats are supported
- Check file sizes (consider adding file size limits)
- Ensure the backend temp directory is writable

## 🔒 Security Considerations

- **File Validation**: Add file type and size validation
- **CORS Configuration**: Restrict origins in production
- **Rate Limiting**: Implement rate limiting for the API
- **File Cleanup**: Implement automatic cleanup of temp files
- **Input Sanitization**: Validate file names and content

## 🚀 Deployment

### Backend Deployment

```bash
# Using Docker (create Dockerfile)
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Deployment

```bash
# Build for production
npm run build

# Deploy to Vercel, Netlify, or other platforms
npm run start
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Next.js](https://nextjs.org/) for the React framework
- [shadcn/ui](https://ui.shadcn.com/) for the beautiful UI components
- [Tailwind CSS](https://tailwindcss.com/) for the utility-first CSS framework
- [PIL/Pillow](https://python-pillow.org/) for image processing

---

⭐ **If you found this project helpful, please give it a star!** ⭐
