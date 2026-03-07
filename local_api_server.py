#!/usr/bin/env python3
"""
Local API Server - Proxies requests to Turso for local development
Mirrors the Vercel /api/products endpoint
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Add scraper_api directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from turso_http_client import TursoTrendingDB

# Load environment
load_dotenv()

class APIHandler(SimpleHTTPRequestHandler):
    """Handle both static files and API requests"""

    def do_GET(self):
        parsed_path = urlparse(self.path)

        # API endpoint: /api/products
        if parsed_path.path == '/api/products':
            self.handle_products_api(parsed_path)
        else:
            # Serve static files
            super().do_GET()

    def handle_products_api(self, parsed_path):
        """Handle /api/products endpoint (same as Vercel)"""
        try:
            # Parse query parameters
            query = parse_qs(parsed_path.query)
            limit = int(query.get('limit', [50])[0])

            # Fetch from Turso
            db = TursoTrendingDB(
                db_url=os.getenv('TURSO_DATABASE_URL'),
                auth_token=os.getenv('TURSO_AUTH_TOKEN')
            )

            # Get all products (no min_score filter) to match Vercel behavior
            products = db.get_all_products(limit=limit)

            # Send JSON response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {
                'success': True,
                'count': len(products),
                'products': products
            }

            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"❌ API Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = {
                'success': False,
                'error': 'Failed to fetch products',
                'message': str(e)
            }

            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server(port=8080):
    """Start local API server"""

    print("=" * 70)
    print("🚀 Local API Server")
    print("=" * 70)
    print()
    print(f"📡 Server running on: http://localhost:{port}")
    print(f"📊 Products API: http://localhost:{port}/api/products")
    print(f"🌐 Products Page: http://localhost:{port}/products.html")
    print(f"🔧 Social Push: http://localhost:{port}/social_push.html")
    print()
    print("✅ Features:")
    print("   - Serves static files (HTML, CSS, JS)")
    print("   - Proxies /api/products to Turso cloud DB")
    print("   - Same behavior as Vercel deployment")
    print("   - Local fallback to products_with_content.json")
    print()
    print("⚠️  Press Ctrl+C to stop")
    print("=" * 70)
    print()

    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
