/*
 * Vercel Serverless Function: Track Analytics
 * Endpoint: /api/track
 * Tracks page views, clicks, and search queries
 * 
 * POST Body:
 *   {
 *     "action": "pageview" | "click" | "search" | "revenue",
 *     "session_id": "optional-session-id",
 *     "product_asin": "optional-asin",
 *     "page_type": "product|home|search|review",
 *     "referrer": "optional-referrer-url",
 *     "country": "optional-country",
 *     "city": "optional-city",
 *     "utm_source": "optional-utm-source",
 *     "utm_medium": "optional-utm-medium",
 *     "utm_campaign": "optional-utm-campaign",
 *     // For search:
 *     "query": "search-query",
 *     "results_count": 10,
 *     "found_results": true,
 *     // For revenue:
 *     "sale_amount": 99.99,
 *     "amazon_order_id": "optional-order-id",
 *     "commission_rate": 0.03
 *   }
 */

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
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
    
    // Parse request body
    const body = req.body || {};
    const action = body.action;
    
    // Generate session ID if not provided
    const sessionId = body.session_id || generateUUID();
    
    // Get user agent from headers
    const userAgent = req.headers['user-agent'] || '';
    const uaInfo = parseUserAgent(userAgent);
    
    let result = { success: true, session_id: sessionId };
    
    // Track page view
    if (action === 'pageview') {
      const query = {
        q: `INSERT INTO page_views (
          product_asin, page_type, session_id, user_agent, referrer,
          country, city, utm_source, utm_medium, utm_campaign,
          device_type, browser
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        params: [
          body.product_asin || null,
          body.page_type || 'product',
          sessionId,
          userAgent,
          body.referrer || null,
          body.country || null,
          body.city || null,
          body.utm_source || null,
          body.utm_medium || null,
          body.utm_campaign || null,
          uaInfo.device_type,
          uaInfo.browser
        ]
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
        throw new Error(`Failed to track page view: ${response.status}`);
      }
      
      const responseData = await response.json();
      result.view_id = responseData[0]?.last_insert_rowid || null;
      result.action = 'pageview_tracked';
    }
    
    // Track Amazon click
    else if (action === 'click') {
      if (!body.product_asin) {
        return res.status(400).json({ error: 'product_asin is required for click tracking' });
      }
      
      const query = {
        q: `INSERT INTO amazon_clicks (
          product_asin, session_id, user_agent, referrer,
          country, city, device_type, browser, link_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        params: [
          body.product_asin,
          sessionId,
          userAgent,
          body.referrer || null,
          body.country || null,
          body.city || null,
          uaInfo.device_type,
          uaInfo.browser,
          body.link_type || 'affiliate'
        ]
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
        throw new Error(`Failed to track click: ${response.status}`);
      }
      
      const responseData = await response.json();
      result.click_id = responseData[0]?.last_insert_rowid || null;
      result.action = 'click_tracked';
    }
    
    // Track search query
    else if (action === 'search') {
      if (!body.query) {
        return res.status(400).json({ error: 'query is required for search tracking' });
      }
      
      const query = {
        q: `INSERT INTO search_queries (
          query, search_type, results_count, clicked_result_asin,
          session_id, country, city, found_results
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        params: [
          body.query,
          body.search_type || 'products',
          body.results_count || 0,
          body.clicked_asin || null,
          sessionId,
          body.country || null,
          body.city || null,
          body.found_results !== false ? 1 : 0
        ]
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
        throw new Error(`Failed to track search: ${response.status}`);
      }
      
      const responseData = await response.json();
      result.search_id = responseData[0]?.last_insert_rowid || null;
      result.action = 'search_tracked';
    }
    
    // Track revenue event
    else if (action === 'revenue') {
      if (!body.product_asin || !body.sale_amount) {
        return res.status(400).json({ 
          error: 'product_asin and sale_amount are required for revenue tracking' 
        });
      }
      
      const commissionRate = body.commission_rate || 0.03;
      const estimatedCommission = body.sale_amount * commissionRate;
      const today = new Date().toISOString().split('T')[0];
      
      const query = {
        q: `INSERT INTO revenue_events (
          product_asin, amazon_order_id, sale_amount, commission_rate,
          estimated_commission, currency, session_id, status, sale_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        params: [
          body.product_asin,
          body.amazon_order_id || null,
          body.sale_amount,
          commissionRate,
          estimatedCommission,
          body.currency || 'USD',
          sessionId,
          body.status || 'pending',
          body.sale_date || today
        ]
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
        throw new Error(`Failed to track revenue: ${response.status}`);
      }
      
      const responseData = await response.json();
      result.event_id = responseData[0]?.last_insert_rowid || null;
      result.action = 'revenue_tracked';
      result.estimated_commission = estimatedCommission;
    }
    
    else {
      return res.status(400).json({ 
        error: 'Invalid action',
        message: 'Action must be: pageview, click, search, or revenue'
      });
    }
    
    return res.status(200).json(result);

  } catch (error) {
    console.error('Track API Error:', error);
    return res.status(500).json({ 
      error: 'Failed to track event',
      message: error.message 
    });
  }
}

// Helper function to generate UUID
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Helper function to parse user agent
function parseUserAgent(userAgent) {
  const ua = (userAgent || '').toLowerCase();
  
  // Device type
  let deviceType = 'desktop';
  if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
    deviceType = 'mobile';
  } else if (ua.includes('tablet') || ua.includes('ipad')) {
    deviceType = 'tablet';
  }
  
  // Browser
  let browser = 'Other';
  if (ua.includes('chrome')) {
    browser = 'Chrome';
  } else if (ua.includes('safari')) {
    browser = 'Safari';
  } else if (ua.includes('firefox')) {
    browser = 'Firefox';
  } else if (ua.includes('edge')) {
    browser = 'Edge';
  }
  
  return { device_type: deviceType, browser: browser };
}
