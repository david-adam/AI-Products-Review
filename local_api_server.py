#!/usr/bin/env python3
"""
Local API Server - Proxies requests to Turso for local development
Mirrors the Vercel /api/products endpoint with Analytics support
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
import uuid
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Add scraper_api directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from turso_http_client import TursoTrendingDB

# Load environment
load_dotenv()

# Turso config
TURSO_DB_URL = os.getenv('TURSO_DATABASE_URL', 'libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN', '').replace('\n', '').strip()
TURSO_HTTP_URL = TURSO_DB_URL.replace('libsql://', 'https://')


def generate_session_id():
    """Generate a unique session ID"""
    return str(uuid.uuid4())


def parse_user_agent(user_agent):
    """Parse user agent string"""
    ua = (user_agent or '').lower()
    
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device_type = "mobile"
    elif "tablet" in ua or "ipad" in ua:
        device_type = "tablet"
    else:
        device_type = "desktop"
    
    if "chrome" in ua:
        browser = "Chrome"
    elif "safari" in ua:
        browser = "Safari"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "edge" in ua:
        browser = "Edge"
    else:
        browser = "Other"
    
    return {"device_type": device_type, "browser": browser}


class APIHandler(SimpleHTTPRequestHandler):
    """Handle both static files and API requests"""

    def do_GET(self):
        parsed_path = urlparse(self.path)

        # API endpoint: /api/products
        if parsed_path == '/api/products':
            self.handle_products_api(parsed_path)
        elif parsed_path.path == '/api/analytics':
            self.handle_analytics_api(parsed_path)
        else:
            # Serve static files
            super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/generate':
            self.handle_generate_api()
        elif parsed_path.path == '/api/track':
            self.handle_track_api()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_track_api(self):
        """Handle /api/track endpoint for analytics tracking"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            action = data.get('action')
            session_id = data.get('session_id') or generate_session_id()
            user_agent = self.headers.get('user-agent', '')
            ua_info = parse_user_agent(user_agent)
            
            result = {"success": True, "session_id": session_id}
            
            if action == 'pageview':
                query = """
                INSERT INTO page_views (product_asin, page_type, session_id, user_agent, referrer, country, city, device_type, browser)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = [
                    data.get('product_asin'),
                    data.get('page_type', 'product'),
                    session_id,
                    user_agent,
                    data.get('referrer'),
                    data.get('country'),
                    data.get('city'),
                    ua_info['device_type'],
                    ua_info['browser']
                ]
                
                response = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': query, 'params': params}]}
                )
                
                if response.status_code == 200:
                    result['view_id'] = response.json()[0].get('last_insert_rowid')
                    
            elif action == 'click':
                if not data.get('product_asin'):
                    self.send_error(400, 'product_asin required')
                    return
                    
                query = """
                INSERT INTO amazon_clicks (product_asin, session_id, user_agent, referrer, country, city, device_type, browser, link_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = [
                    data.get('product_asin'),
                    session_id,
                    user_agent,
                    data.get('referrer'),
                    data.get('country'),
                    data.get('city'),
                    ua_info['device_type'],
                    ua_info['browser'],
                    data.get('link_type', 'affiliate')
                ]
                
                response = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': query, 'params': params}]}
                )
                
                if response.status_code == 200:
                    result['click_id'] = response.json()[0].get('last_insert_rowid')
                    
            elif action == 'search':
                if not data.get('query'):
                    self.send_error(400, 'query required')
                    return
                    
                query = """
                INSERT INTO search_queries (query, search_type, results_count, clicked_result_asin, session_id, country, city, found_results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = [
                    data.get('query'),
                    data.get('search_type', 'products'),
                    data.get('results_count', 0),
                    data.get('clicked_asin'),
                    session_id,
                    data.get('country'),
                    data.get('city'),
                    1 if data.get('found_results', True) else 0
                ]
                
                response = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': query, 'params': params}]}
                )
                
                if response.status_code == 200:
                    result['search_id'] = response.json()[0].get('last_insert_rowid')
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

    def handle_analytics_api(self, parsed_path):
        """Handle /api/analytics endpoint"""
        try:
            query = parse_qs(parsed_path.query)
            analytics_type = query.get('type', ['overview'])[0]
            days = int(query.get('days', [30])[0])
            sort = query.get('sort', ['views'])[0]
            limit = int(query.get('limit', [50])[0])
            
            start_date = (date.today() - timedelta(days=days)).isoformat()
            response_data = {}
            
            if analytics_type == 'overview':
                queries = [
                    f"SELECT COUNT(*) as count, COUNT(DISTINCT session_id) as unique_visitors FROM page_views WHERE viewed_at >= '{start_date}'",
                    f"SELECT COUNT(*) as count FROM amazon_clicks WHERE clicked_at >= '{start_date}'",
                    f"SELECT COALESCE(SUM(estimated_commission), 0) as total FROM revenue_events WHERE status = 'confirmed' AND sale_date >= '{start_date}'",
                    f"SELECT COUNT(*) as count FROM search_queries WHERE searched_at >= '{start_date}'"
                ]
                
                resp = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': q} for q in queries]}
                )
                
                if resp.status_code == 200:
                    results = resp.json()
                    page_views = results[0]['results']['rows'][0][0] if results[0].get('results', {}).get('rows') else 0
                    unique_visitors = results[0]['results']['rows'][0][1] if results[0].get('results', {}).get('rows') else 0
                    clicks = results[1]['results']['rows'][0][0] if results[1].get('results', {}).get('rows') else 0
                    revenue = results[2]['results']['rows'][0][0] if results[2].get('results', {}).get('rows') else 0
                    searches = results[3]['results']['rows'][0][0] if results[3].get('results', {}).get('rows') else 0
                    
                    ctr = (clicks / page_views * 100) if page_views > 0 else 0
                    
                    response_data = {
                        'total_page_views': page_views,
                        'unique_visitors': unique_visitors,
                        'total_amazon_clicks': clicks,
                        'total_revenue': round(revenue, 2),
                        'total_searches': searches,
                        'ctr': round(ctr, 2),
                        'period_days': days
                    }
            
            elif analytics_type == 'products':
                order_clause = {'views': 'page_views DESC', 'clicks': 'clicks DESC', 'revenue': 'estimated_revenue DESC'}.get(sort, 'page_views DESC')
                
                query = f"""
                SELECT 
                    tp.asin, tp.title, tp.price, tp.image, tp.category,
                    COUNT(DISTINCT pv.id) as page_views,
                    COUNT(DISTINCT ac.id) as amazon_clicks,
                    COALESCE(SUM(re.estimated_commission), 0) as estimated_revenue
                FROM trending_products tp
                LEFT JOIN page_views pv ON tp.asin = pv.product_asin AND pv.viewed_at >= '{start_date}'
                LEFT JOIN amazon_clicks ac ON tp.asin = ac.product_asin AND ac.clicked_at >= '{start_date}'
                LEFT JOIN revenue_events re ON tp.asin = re.product_asin AND re.status = 'confirmed' AND re.sale_date >= '{start_date}'
                GROUP BY tp.asin
                ORDER BY {order_clause}
                LIMIT {limit}
                """
                
                resp = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': query}]}
                )
                
                if resp.status_code == 200:
                    results = resp.json()
                    if results[0].get('results', {}).get('rows'):
                        cols = results[0]['results']['columns']
                        rows = results[0]['results']['rows']
                        response_data['products'] = []
                        for row in rows:
                            item = {}
                            for i, col in enumerate(cols):
                                item[col] = row[i]
                            views = item.get('page_views', 0) or 0
                            clicks = item.get('amazon_clicks', 0) or 0
                            item['ctr'] = round((clicks / views * 100), 2) if views > 0 else 0
                            response_data['products'].append(item)
            
            elif analytics_type == 'revenue':
                query = f"""
                SELECT DATE(sale_date) as date, COALESCE(SUM(estimated_commission), 0) as revenue, COUNT(*) as conversions
                FROM revenue_events WHERE status = 'confirmed' AND sale_date >= '{start_date}'
                GROUP BY DATE(sale_date) ORDER BY date ASC
                """
                
                resp = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': query}]}
                )
                
                if resp.status_code == 200:
                    results = resp.json()
                    if results[0].get('results', {}).get('rows'):
                        cols = results[0]['results']['columns']
                        rows = results[0]['results']['rows']
                        response_data['revenue'] = [dict(zip(cols, row)) for row in rows]
            
            elif analytics_type == 'traffic':
                query = f"""
                SELECT 
                    CASE 
                        WHEN referrer IS NULL OR referrer = '' THEN 'Direct'
                        WHEN referrer LIKE '%google%' THEN 'Google'
                        WHEN referrer LIKE '%facebook%' THEN 'Facebook'
                        WHEN referrer LIKE '%twitter%' THEN 'Twitter'
                        ELSE 'Other'
                    END as source, COUNT(*) as views
                FROM page_views WHERE viewed_at >= '{start_date}'
                GROUP BY source ORDER BY views DESC
                """
                
                resp = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': query}]}
                )
                
                if resp.status_code == 200:
                    results = resp.json()
                    if results[0].get('results', {}).get('rows'):
                        rows = results[0]['results']['rows']
                        total = sum(row[1] for row in rows)
                        response_data['sources'] = [
                            {'source': row[0], 'views': row[1], 'percentage': round((row[1]/total*100), 2)}
                            for row in rows
                        ]
            
            elif analytics_type == 'locations':
                query = f"""
                SELECT COALESCE(country, 'Unknown') as country, COUNT(*) as views
                FROM page_views WHERE viewed_at >= '{start_date}'
                GROUP BY country ORDER BY views DESC LIMIT 20
                """
                
                resp = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': query}]}
                )
                
                if resp.status_code == 200:
                    results = resp.json()
                    if results[0].get('results', {}).get('rows'):
                        rows = results[0]['results']['rows']
                        total = sum(row[1] for row in rows)
                        response_data['locations'] = [
                            {'country': row[0], 'views': row[1], 'percentage': round((row[1]/total*100), 2)}
                            for row in rows
                        ]
            
            elif analytics_type == 'searches':
                query = f"""
                SELECT query, COUNT(*) as search_count, SUM(CASE WHEN clicked_result_asin IS NOT NULL THEN 1 ELSE 0 END) as clicks
                FROM search_queries WHERE searched_at >= '{start_date}'
                GROUP BY LOWER(query) ORDER BY search_count DESC LIMIT {limit}
                """
                
                resp = requests.post(
                    f'{TURSO_HTTP_URL}',
                    headers={'Authorization': f'Bearer {TURSO_AUTH_TOKEN}', 'Content-Type': 'application/json'},
                    json={'statements': [{'q': query}]}
                )
                
                if resp.status_code == 200:
                    results = resp.json()
                    if results[0].get('results', {}).get('rows'):
                        cols = results[0]['results']['columns']
                        rows = results[0]['results']['rows']
                        response_data['searches'] = [dict(zip(cols, row)) for row in rows]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'type': analytics_type, 'days': days, 'data': response_data}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def handle_products_api(self, parsed_path):
        """Handle /api/products endpoint (same as Vercel)"""
        try:
            query = parse_qs(parsed_path.query)
            limit = int(query.get('limit', [50])[0])

            db = TursoTrendingDB(
                db_url=os.getenv('TURSO_DATABASE_URL'),
                auth_token=os.getenv('TURSO_AUTH_TOKEN')
            )

            products = db.get_all_products(limit=limit)

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

    def handle_generate_api(self):
        """Handle /api/generate endpoint for AI content generation"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            asin = data.get('asin')
            action = data.get('action')
            
            if not asin:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'ASIN is required'}).encode('utf-8'))
                return
            
            if action == 'generate':
                import time
                time.sleep(2)
                
                generated_content = {
                    'id': int(time.time()),
                    'asin': asin,
                    'summary': 'This premium wireless headphone delivers exceptional sound quality with active noise cancellation, 30-hour battery life, and premium comfort.',
                    'full_review': 'After thoroughly testing this wireless headphone, I am impressed by its exceptional audio performance...',
                    'rating': 4.5,
                    'pros': 'Excellent sound quality, Effective ANC, 30-hour battery life',
                    'cons': 'No aptX support, Bulky carrying case',
                    'image_url': 'https://via.placeholder.com/600x400/667eea/ffffff?text=Product+Image',
                    'ai_model': 'kimi-k2.5',
                    'created_at': str(time.strftime('%Y-%m-%dT%H:%M:%SZ')),
                    'status': 'pending'
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'content': generated_content}).encode('utf-8'))
                
            elif action in ['approve', 'reject']:
                import time
                time.sleep(0.5)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'action': action}).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Invalid action'}).encode('utf-8'))
                
        except Exception as e:
            print(f"❌ Generate API Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=8888):
    """Start local API server"""

    print("=" * 70)
    print("🚀 Local API Server with Analytics")
    print("=" * 70)
    print()
    print(f"📡 Server running on: http://localhost:{port}")
    print(f"📊 Analytics API: http://localhost:{port}/api/analytics")
    print(f"🎯 Tracking API: http://localhost:{port}/api/track")
    print(f"📦 Products API: http://localhost:{port}/api/products")
    print(f"📈 Dashboard: http://localhost:{port}/analytics.html")
    print()
    print("✅ Features:")
    print("   - Serves static files (HTML, CSS, JS)")
    print("   - Analytics tracking (/api/track)")
    print("   - Analytics dashboard (/api/analytics)")
    print("   - Products API (/api/products)")
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
