/**
 * Citation Proxy API
 * 
 * This endpoint fetches external web content and serves it through our domain
 * to avoid CORS issues and provide a more secure iframe experience.
 */

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const url = searchParams.get('url');
  
  if (!url) return new Response('URL required', { status: 400 });
  
  try {
    console.log(`Proxying request to: ${url}`);
    
    const response = await fetch(url, {
      headers: {
        // Some sites check User-Agent to prevent scraping
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
      }
    });
    
    if (!response.ok) {
      return new Response(`Failed to fetch URL: ${response.statusText}`, { 
        status: response.status 
      });
    }
    
    // Get the base URL for resolving relative URLs
    const baseUrl = new URL(url);
    const baseHostname = baseUrl.hostname;
    
    let html = await response.text();
    
    // More comprehensive HTML processing
    html = html
      // Remove all <script> tags to prevent JS errors and service worker issues
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      
      // Remove all font preload and font-face references
      .replace(/<link[^>]*preload[^>]*>/gi, (match) => {
        if (match.includes('font') || match.includes('.woff') || match.includes('.ttf')) {
          return '<!-- Font preload removed -->';
        }
        return match;
      })
      .replace(/@font-face\s*{[^}]*}/gi, '/* Font-face removed */')
      
      // Fix relative URLs starting with /
      .replace(/href=["'](\/[^"']*?)["']/gi, (match, p1) => `href="${baseUrl.origin}${p1}"`)
      .replace(/src=["'](\/[^"']*?)["']/gi, (match, p1) => `src="${baseUrl.origin}${p1}"`)
      
      // Fix relative URLs that don't start with http or /
      .replace(/href=["'](?!http|\/|#|mailto:|tel:)([^"']*?)["']/gi, (match, p1) => {
        try {
          const resolvedUrl = new URL(p1, url).href;
          return `href="${resolvedUrl}"`;
        } catch(e) {
          return match; // If URL resolution fails, keep original
        }
      })
      .replace(/src=["'](?!http|\/|#|data:)([^"']*?)["']/gi, (match, p1) => {
        try {
          const resolvedUrl = new URL(p1, url).href;
          return `src="${resolvedUrl}"`;
        } catch(e) {
          return match; // If URL resolution fails, keep original
        }
      })
      
      // Handle url() references in style attributes and inline CSS
      .replace(/url\(\s*['"]?((?!data:)[^"')]+)["']?\s*\)/gi, (match, p1) => {
        try {
          // If it's already an absolute URL, leave it
          if (p1.startsWith('http')) return match;
          // If it's a relative URL, resolve it
          const resolvedUrl = new URL(p1, url).href;
          return `url("${resolvedUrl}")`;
        } catch(e) {
          return match; // If URL resolution fails, keep original
        }
      })
      
      // Fixed: Add target="_blank" to all links - properly escape quotes
      .replace(/<a\s+([^>]*?)href=["']([^"']+)["']([^>]*?)>/gi, (match, before, href, after) => {
        // Skip anchor links
        if (href.startsWith('#')) return match;
        
        // Check if target attribute already exists
        const hasTarget = /target\s*=/.test(before) || /target\s*=/.test(after);
        
        if (hasTarget) {
          return match; // Don't modify if target already exists
        } else {
          // Add target attribute
          return `<a ${before}href="${href}" target="_blank" rel="noopener noreferrer"${after}>`;
        }
      });
    
    // Inject custom CSS to fix display issues and override problematic styles
    html = html.replace('</head>', `
      <style>
        /* Override font definitions to use system fonts */
        @font-face {
          font-family: Inter, Arial, sans-serif !important;
          src: local('Arial') !important;
          font-weight: normal !important;
        }
        @font-face {
          font-family: Inter, Arial, sans-serif !important;
          src: local('Arial Bold') !important;
          font-weight: bold !important;
        }
        
        /* Hide error messages and alerts */
        [role="alert"] { display: none !important; }
        
        /* Use system fonts */
        * {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
        }
        
        /* Block anything that could overwrite our styles */
        @import { display: none !important; }
      </style>
    </head>`);
    
    // Add base tag to help resolve URLs
    html = html.replace('<head>', `<head>
      <base href="${url}">
      <meta name="referrer" content="no-referrer">
      <!-- Service workers disabled -->
    `);

    // Return the processed HTML with security headers
    return new Response(html, {
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        // Security headers
        'X-Frame-Options': 'SAMEORIGIN',
        'Content-Security-Policy': 
          "default-src 'self' * data: blob:; " +
          "script-src 'none'; " + // Block all scripts
          "style-src 'unsafe-inline' *; " +
          "img-src * data: blob:; " +
          "font-src data: 'self'; " + // Only allow inline fonts
          "connect-src 'none'; " + // Block all network requests from iframe
          "frame-ancestors 'self';",
        // Cache for 15 minutes
        'Cache-Control': 'public, max-age=900'
      }
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return new Response('Failed to fetch URL. The resource might be unavailable or the URL is invalid.', { 
      status: 500 
    });
  }
} 