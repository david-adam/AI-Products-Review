#!/usr/bin/env python3
"""
Simple HTTP API for social media push functionality
Provides endpoints that the frontend can call
"""

import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from social_push import SocialPushHandler, ProductManager

PRODUCTS_FILE = 'products_with_content.json'

class SocialPushAPI(BaseHTTPRequestHandler):
    """Handle API requests for social media push"""
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/products':
            self.get_products()
        elif path == '/api/pushed':
            self.get_pushed_log()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/push/telegram':
            self.push_to_telegram()
        elif path == '/api/push/all':
            self.push_to_all()
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def get_products(self):
        """Get all products"""
        try:
            with open(PRODUCTS_FILE, 'r') as f:
                products = json.load(f)
            
            self._set_headers(200)
            self.wfile.write(json.dumps(products).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def get_pushed_log(self):
        """Get log of pushed products"""
        push_handler = SocialPushHandler()
        self._set_headers(200)
        self.wfile.write(json.dumps(push_handler.pushed_products).encode())
    
    def push_to_telegram(self):
        """Push product to Telegram"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            asin = data.get('asin')
            chat_id = data.get('chat_id')
            
            if not asin:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'ASIN required'}).encode())
                return
            
            # Load product
            product_manager = ProductManager(PRODUCTS_FILE)
            product = product_manager.get_product(asin)
            
            if not product:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Product not found'}).encode())
                return
            
            # Push to Telegram (async in sync context)
            push_handler = SocialPushHandler()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(push_handler.push_to_telegram(product, chat_id))
            loop.close()
            
            self._set_headers(200)
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def push_to_all(self):
        """Push product to all platforms"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            asin = data.get('asin')
            
            if not asin:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'ASIN required'}).encode())
                return
            
            # Load product
            product_manager = ProductManager(PRODUCTS_FILE)
            product = product_manager.get_product(asin)
            
            if not product:
                self._set_headers(404)
                self.wfile.write(json.dumps({'error': 'Product not found'}).encode())
                return
            
            # Push to all platforms
            push_handler = SocialPushHandler()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(push_handler.push_to_all(product))
            loop.close()
            
            self._set_headers(200)
            self.wfile.write(json.dumps(results).encode())
            
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def log_message(self, format, *args):
        """Log to console instead of file"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_api_server(port=8100):
    """Start the API server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SocialPushAPI)
    
    print(f"✅ Social Push API running on http://localhost:{port}")
    print(f"📡 Endpoints:")
    print(f"   GET  /api/products - Get all products")
    print(f"   GET  /api/pushed - Get pushed products log")
    print(f"   POST /api/push/telegram - Push to Telegram")
    print(f"   POST /api/push/all - Push to all platforms")
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ API server stopped")


if __name__ == '__main__':
    run_api_server()
