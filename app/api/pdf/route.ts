import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs";

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const pdfPath = decodeURIComponent(url.pathname.replace("/api/pdf/", ""));
    
    // Ensure the path is within the data/pdf directory
    const baseDir = path.join(process.cwd(), "data", "pdf");
    const fullPath = path.join(baseDir, pdfPath);
    
    if (!fullPath.startsWith(baseDir)) {
      return new NextResponse("Invalid PDF path", { status: 400 });
    }

    // Check if file exists
    if (!fs.existsSync(fullPath)) {
      return new NextResponse("PDF file not found", { status: 404 });
    }

    // Read and serve the PDF file
    const pdfBuffer = fs.readFileSync(fullPath);
    const pdfArray = new Uint8Array(pdfBuffer);
    const pdfBlob = new Blob([pdfArray], { type: "application/pdf" });
    
    return new NextResponse(pdfBlob, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `inline; filename="${path.basename(pdfPath)}"`,
      },
    });
  } catch (error) {
    console.error("Error serving PDF:", error);
    return new NextResponse("Error serving PDF file", { status: 500 });
  }
} 