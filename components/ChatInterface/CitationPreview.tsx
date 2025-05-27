import React, { useState, useRef, useEffect } from "react";
import { Loader2, FileText } from "lucide-react";

interface CitationPreviewProps {
  url?: string;
  className?: string;
}

const CitationPreview: React.FC<CitationPreviewProps> = ({
  url,
  className,
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Ensure we have a properly formatted PDF URL
  const getPdfUrl = (filename: string) => {
    // If the URL already starts with /api/pdf, return as is
    if (filename.startsWith("/api/pdf/")) {
      return `${filename}#view=FitH&pagemode=none&toolbar=0&navpanes=0&scrollbar=0&page-fit=page-width&background=white`;
    }
    // Otherwise, construct the proper URL with viewer parameters
    return `/api/pdf/${encodeURIComponent(
      filename
    )}#view=FitH&pagemode=none&toolbar=0&navpanes=0&scrollbar=0&page-fit=page-width&background=white`;
  };

  useEffect(() => {
    console.log("CitationPreview mounted with URL:", url);
    if (url) {
      console.log("Is PDF:", url.toLowerCase().endsWith(".pdf"));
      console.log("Constructed URL:", getPdfUrl(url));
    }
  }, [url]);

  if (!url) {
    return null;
  }

  const isPdf = url.toLowerCase().endsWith(".pdf");
  let domain = "";

  try {
    if (!isPdf && url) {
      domain = new URL(url).hostname.replace("www.", "");
    }
  } catch (e) {
    console.error("URL parsing error:", e);
    setError("Ogiltig URL");
    return (
      <div
        className={`rounded-md overflow-hidden w-full bg-card relative ${className}`}
      >
        <div className="absolute inset-0 flex items-center justify-center bg-card/80 z-10">
          <p className="text-sm text-muted-foreground">Ogiltig URL</p>
        </div>
      </div>
    );
  }

  const proxyUrl = isPdf
    ? getPdfUrl(url)
    : `/api/proxy?url=${encodeURIComponent(url)}`;

  const handleLoad = () => {
    console.log("Content loaded successfully");
    setIsLoading(false);
  };

  const handleError = (e: any) => {
    console.error("Error loading content:", e);
    setIsLoading(false);
    setError(
      isPdf
        ? "Det gick inte att ladda PDF-filen."
        : "Det gick inte att ladda webbsidan."
    );
  };

  return (
    <div
      className={`rounded-md overflow-hidden w-full bg-card relative ${className}`}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-card/80 z-10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {error ? (
        <div className="absolute inset-0 flex items-center justify-center bg-card/80 z-10">
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      ) : isPdf ? (
        // For PDFs, use iframe with specific styling
        <div className="w-full h-full relative" style={{ minHeight: "500px" }}>
          <iframe
            src={`${proxyUrl}#view=FitH&pagemode=none&toolbar=0&navpanes=0&scrollbar=0`}
            className="w-full h-full border-0"
            style={{
              width: "100%",
              height: "100%",
              backgroundColor: "white",
            }}
            onLoad={handleLoad}
            onError={handleError}
          />
        </div>
      ) : (
        <iframe
          ref={iframeRef}
          src={proxyUrl}
          className="w-full h-full"
          title={`Preview ${domain}`}
          onLoad={handleLoad}
          onError={handleError}
          loading="lazy"
          sandbox="allow-scripts allow-same-origin"
          referrerPolicy="no-referrer"
        />
      )}
    </div>
  );
};

export default CitationPreview;
