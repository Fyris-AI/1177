import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ filename: string }> }
) {
  // Await the params object before using it
  const { filename } = await context.params;
  
  if (!filename) {
    return new NextResponse('Filename parameter is required', { status: 400 });
  }

  try {
    // Decode the filename to handle spaces and special characters
    const decodedFilename = decodeURIComponent(filename);
    console.log('Requested PDF filename:', decodedFilename);
    
    // Validate filename to prevent directory traversal
    if (decodedFilename.includes('..') || !decodedFilename.endsWith('.pdf')) {
      console.error('Invalid filename requested:', decodedFilename);
      return new NextResponse('Invalid filename', { status: 400 });
    }

    // Construct the path to the PDF file in the backend directory
    const pdfPath = path.join(process.cwd(), 'backend', 'data', 'pdf', decodedFilename);
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
        'Content-Disposition': `inline; filename="${encodeURIComponent(decodedFilename)}"`,
      },
    });
  } catch (error) {
    console.error('Error serving PDF:', error);
    return new NextResponse('Error serving PDF', { status: 500 });
  }
} 