/*
 * Vercel Serverless Function: Analytics API
 * Endpoint: /api/analytics
 * Provides analytics data for the dashboard
 * 
 * Query Parameters:
 *   - type: 'overview', 'products', 'revenue', 'traffic', 'locations', 'searches', 'export'
 *   - days: Number of days to look back (default: 30)
 *   - sort: Sort field for products (default: 'views')
 *   - limit: Number of results (default: 50)
 *   - export: Export type for CSV ('products', 'clicks', 'revenue', 'searches')
 */

// Import analytics functions
import { getOverviewStats, getProductAnalytics, getRevenueOverTime, getTrafficSources, getUserLocations, getTopSearches, exportToCsv } from '../../scripts/analytics.py';

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Get Turso credentials from environment
    const dbUrl = process.env.TURSO_DATABASE_URL || 'libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io';
    let authToken = process.env.TURSO_AUTH_TOKEN;

    if (!authToken) {
      return res.status(500).json({ error: 'TURSO_AUTH_TOKEN not configured' });
    }

    // Clean up auth token
    authToken = authToken.replace(/\s+/g, '').trim();

    if (!authToken) {
      return res.status(500).json({ error: 'TURSO_AUTH_TOKEN is empty after cleaning' });
    }

    // Convert libsql:// to https:// for HTTP API
    const httpUrl = dbUrl.replace('libsql://', 'https://');
    
    // Parse query parameters
    const type = req.query.type || 'overview';
    const days = parseInt(req.query.days) || 30;
    const sort = req.query.sort || 'views';
    const limit = parseInt(req.query.limit) || 50;
    const exportType = req.query.export || 'products';
    
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    const startDateStr = startDate.toISOString().split('T')[0];
    
    let responseData = {};
    
    // Overview stats
    if (type === 'overview') {
      const queries = [
        {
          q: `SELECT COUNT(*) as count, COUNT(DISTINCT session_id) as unique_visitors FROM page_views WHERE viewed_at >= ?`,
          params: [startDateStr]
        },
        {
          q: `SELECT COUNT(*) as count FROM amazon_clicks WHERE clicked_at >= ?`,
          params: [startDateStr]
        },
        {
          q: `SELECT COALESCE(SUM(estimated_commission), 0) as total FROM revenue_events WHERE status = 'confirmed' AND sale_date >= ?`,
          params: [startDateStr]
        },
        {
          q: `SELECT COUNT(*) as count FROM search_queries WHERE searched_at >= ?`,
          params: [startDateStr]
        }
      ];
      
      const response = await fetch(httpUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statements: queries })
      });
      
      if (!response.ok) {
        throw new Error(`Turso API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      const pageViews = result[0]?.results?.rows?.[0]?.[0] || 0;
      const uniqueVisitors = result[0]?.results?.rows?.[0]?.[1] || 0;
      const clicks = result[1]?.results?.rows?.[0]?.[0] || 0;
      const revenue = result[2]?.results?.rows?.[0]?.[0] || 0;
      const searches = result[3]?.results?.rows?.[0]?.[0] || 0;
      
      const ctr = pageViews > 0 ? ((clicks / pageViews) * 100).toFixed(2) : 0;
      
      responseData = {
        total_page_views: pageViews,
        unique_visitors: uniqueVisitors,
        total_amazon_clicks: clicks,
        total_revenue: parseFloat(revenue.toFixed(2)),
        total_searches: searches,
        ctr: parseFloat(ctr),
        period_days: days
      };
    }
    
    // Product analytics
    else if (type === 'products') {
      const orderClause = {
        'views': 'page_views DESC',
        'clicks': 'clicks DESC',
        'revenue': 'estimated_revenue DESC'
      }[sort] || 'page_views DESC';
      
      const query = {
        q: `SELECT 
          tp.asin,
          tp.title,
          tp.price,
          tp.image,
          tp.category,
          COUNT(DISTINCT pv.id) as page_views,
          COUNT(DISTINCT ac.id) as amazon_clicks,
          COALESCE(SUM(re.estimated_commission), 0) as estimated_revenue
        FROM trending_products tp
        LEFT JOIN page_views pv ON tp.asin = pv.product_asin AND pv.viewed_at >= ?
        LEFT JOIN amazon_clicks ac ON tp.asin = ac.product_asin AND ac.clicked_at >= ?
        LEFT JOIN revenue_events re ON tp.asin = re.product_asin AND re.status = 'confirmed' AND re.sale_date >= ?
        GROUP BY tp.asin
        ORDER BY ${orderClause}
        LIMIT ?`,
        params: [startDateStr, startDateStr, startDateStr, limit]
      };
      
      const response = await fetch(httpUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statements: [query] })
      });
      
      if (!response.ok) {
        throw new Error(`Turso API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result[0]?.results?.rows) {
        const columns = result[0].results.columns;
        const rows = result[0].results.rows;
        
        responseData.products = rows.map(row => {
          const item = {};
          columns.forEach((col, idx) => {
            item[col] = row[idx];
          });
          // Calculate CTR
          const views = item.page_views || 0;
          const clicks = item.amazon_clicks || 0;
          item.ctr = views > 0 ? parseFloat(((clicks / views) * 100).toFixed(2)) : 0;
          return item;
        });
      } else {
        responseData.products = [];
      }
    }
    
    // Revenue over time
    else if (type === 'revenue') {
      const query = {
        q: `SELECT 
          DATE(sale_date) as date,
          COALESCE(SUM(estimated_commission), 0) as revenue,
          COUNT(*) as conversions
        FROM revenue_events
        WHERE status = 'confirmed' AND sale_date >= ?
        GROUP BY DATE(sale_date)
        ORDER BY date ASC`,
        params: [startDateStr]
      };
      
      const response = await fetch(httpUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statements: [query] })
      });
      
      if (!response.ok) {
        throw new Error(`Turso API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result[0]?.results?.rows) {
        const columns = result[0].results.columns;
        const rows = result[0].results.rows;
        
        responseData.revenue = rows.map(row => {
          const item = {};
          columns.forEach((col, idx) => {
            item[col] = row[idx];
          });
          return item;
        });
      } else {
        responseData.revenue = [];
      }
    }
    
    // Traffic sources
    else if (type === 'traffic') {
      const query = {
        q: `SELECT 
          CASE 
            WHEN referrer IS NULL OR referrer = '' THEN 'Direct'
            WHEN referrer LIKE '%google%' THEN 'Google'
            WHEN referrer LIKE '%facebook%' THEN 'Facebook'
            WHEN referrer LIKE '%twitter%' THEN 'Twitter'
            WHEN referrer LIKE '%instagram%' THEN 'Instagram'
            WHEN referrer LIKE '%pinterest%' THEN 'Pinterest'
            WHEN referrer LIKE '%reddit%' THEN 'Reddit'
            WHEN referrer LIKE '%tiktok%' THEN 'TikTok'
            ELSE 'Other'
          END as source,
          COUNT(*) as views
        FROM page_views
        WHERE viewed_at >= ?
        GROUP BY source
        ORDER BY views DESC`,
        params: [startDateStr]
      };
      
      const response = await fetch(httpUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statements: [query] })
      });
      
      if (!response.ok) {
        throw new Error(`Turso API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result[0]?.results?.rows) {
        const rows = result[0].results.rows;
        const total = rows.reduce((sum, row) => sum + row[1], 0);
        
        responseData.sources = rows.map(row => ({
          source: row[0],
          views: row[1],
          percentage: parseFloat(((row[1] / total) * 100).toFixed(2))
        }));
      } else {
        responseData.sources = [];
      }
    }
    
    // User locations
    else if (type === 'locations') {
      const query = {
        q: `SELECT 
          COALESCE(country, 'Unknown') as country,
          COUNT(*) as views
        FROM page_views
        WHERE viewed_at >= ?
        GROUP BY country
        ORDER BY views DESC
        LIMIT 20`,
        params: [startDateStr]
      };
      
      const response = await fetch(httpUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statements: [query] })
      });
      
      if (!response.ok) {
        throw new Error(`Turso API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result[0]?.results?.rows) {
        const rows = result[0].results.rows;
        const total = rows.reduce((sum, row) => sum + row[1], 0);
        
        responseData.locations = rows.map(row => ({
          country: row[0],
          views: row[1],
          percentage: parseFloat(((row[1] / total) * 100).toFixed(2))
        }));
      } else {
        responseData.locations = [];
      }
    }
    
    // Top searches
    else if (type === 'searches') {
      const query = {
        q: `SELECT 
          query,
          COUNT(*) as search_count,
          SUM(CASE WHEN clicked_result_asin IS NOT NULL THEN 1 ELSE 0 END) as clicks
        FROM search_queries
        WHERE searched_at >= ?
        GROUP BY LOWER(query)
        ORDER BY search_count DESC
        LIMIT ?`,
        params: [startDateStr, limit]
      };
      
      const response = await fetch(httpUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statements: [query] })
      });
      
      if (!response.ok) {
        throw new Error(`Turso API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result[0]?.results?.rows) {
        const columns = result[0].results.columns;
        const rows = result[0].results.rows;
        
        responseData.searches = rows.map(row => {
          const item = {};
          columns.forEach((col, idx) => {
            item[col] = row[idx];
          });
          return item;
        });
      } else {
        responseData.searches = [];
      }
    }
    
    // Export to CSV
    else if (type === 'export') {
      // This would typically generate CSV server-side
      // For now, return a message
      responseData = {
        message: 'Export functionality - use client-side export from dashboard',
        export_type: exportType
      };
    }
    
    return res.status(200).json({
      success: true,
      type: type,
      days: days,
      data: responseData
    });

  } catch (error) {
    console.error('Analytics API Error:', error);
    return res.status(500).json({ 
      error: 'Failed to fetch analytics',
      message: error.message 
    });
  }
}
