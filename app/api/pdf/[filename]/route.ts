import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    // Decode the filename to handle spaces and special characters
    const filename = decodeURIComponent(params.filename);
    console.log('Requested PDF filename:', filename);
    
    // Validate filename to prevent directory traversal
    if (filename.includes('..') || !filename.endsWith('.pdf')) {
      console.error('Invalid filename requested:', filename);
      return new NextResponse('Invalid filename', { status: 400 });
    }

    // Construct the path to the PDF file in the backend directory
    const pdfPath = path.join(process.cwd(), 'backend', 'data', 'pdf', filename);
    console.log('Attempting to serve PDF from:', pdfPath);
    console.log('Current working directory:', process.cwd());

    // Check if file exists
    if (!fs.existsSync(pdfPath)) {
      console.error('PDF file not found at path:', pdfPath);
      return new NextResponse('PDF not found', { status: 404 });
    }

    // Read the file
    const fileBuffer = fs.readFileSync(pdfPath);
    const pdfArray = new Uint8Array(fileBuffer);
    const pdfBlob = new Blob([pdfArray], { type: 'application/pdf' });

    // Return the PDF with appropriate headers
    return new NextResponse(pdfBlob, {
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `inline; filename="${encodeURIComponent(filename)}"`,
      },
    });
  } catch (error) {
    console.error('Error serving PDF:', error);
    return new NextResponse('Error serving PDF', { status: 500 });
  }
} 