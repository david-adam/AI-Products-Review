/*
 * Vercel Serverless Function: Get AI-Generated Reviews
 * Endpoint: /api/reviews
 * Fetches AI-generated reviews from product_reviews table with product details
 * 
 * Query Parameters:
 *   - limit: Number of reviews to return (default: 20)
 *   - asin: Filter by product ASIN (optional)
 *   - active: Filter by active status (default: 1)
 */

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
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);
    const asin = req.query.asin || null;
    const active = req.query.active !== undefined ? parseInt(req.query.active) : 1;

    // Build query - join with trending_products to get product details
    let query = `
      SELECT 
        pr.id,
        pr.product_asin,
        pr.summary,
        pr.full_review,
        pr.rating,
        pr.pros,
        pr.cons,
        pr.google_drive_image_url,
        pr.google_drive_image_id,
        pr.ai_model,
        pr.created_at,
        pr.updated_at,
        pr.is_active,
        tp.title,
        tp.price,
        tp.rating as product_rating,
        tp.reviews as product_reviews_count,
        tp.image,
        tp.affiliate_link,
        tp.category,
        tp.total_score
      FROM product_reviews pr
      LEFT JOIN trending_products tp ON pr.product_asin = tp.asin
      WHERE pr.is_active = ?
    `;
    
    const params = [active];

    if (asin) {
      query += ` AND pr.product_asin = ?`;
      params.push(asin);
    }

    query += ` ORDER BY pr.created_at DESC LIMIT ?`;
    params.push(limit);

    // Execute query using Turso HTTP API
    const requestBody = {
      statements: [
        { q: query, ...params.reduce((acc, val, idx) => ({...acc, [`p${idx + 1}`]: val}), {}) }
      ]
    };
    
    // For Turso HTTP API, we need to use parameterized differently
    // Let's rebuild with proper parameterization
    const paramValues = params.map((val, idx) => ({ name: `p${idx + 1}`, value: String(val) }));
    
    const statements = [];
    if (asin) {
      statements.push({
        q: `SELECT 
        pr.id,
        pr.product_asin,
        pr.summary,
        pr.full_review,
        pr.rating,
        pr.pros,
        pr.cons,
        pr.google_drive_image_url,
        pr.google_drive_image_id,
        pr.ai_model,
        pr.created_at,
        pr.updated_at,
        pr.is_active,
        tp.title,
        tp.price,
        tp.rating as product_rating,
        tp.reviews as product_reviews_count,
        tp.image,
        tp.affiliate_link,
        tp.category,
        tp.total_score
      FROM product_reviews pr
      LEFT JOIN trending_products tp ON pr.product_asin = tp.asin
      WHERE pr.is_active = ? AND pr.product_asin = ?
      ORDER BY pr.created_at DESC LIMIT ?`,
        params: [active, asin, limit]
      });
    } else {
      statements.push({
        q: `SELECT 
        pr.id,
        pr.product_asin,
        pr.summary,
        pr.full_review,
        pr.rating,
        pr.pros,
        pr.cons,
        pr.google_drive_image_url,
        pr.google_drive_image_id,
        pr.ai_model,
        pr.created_at,
        pr.updated_at,
        pr.is_active,
        tp.title,
        tp.price,
        tp.rating as product_rating,
        tp.reviews as product_reviews_count,
        tp.image,
        tp.affiliate_link,
        tp.category,
        tp.total_score
      FROM product_reviews pr
      LEFT JOIN trending_products tp ON pr.product_asin = tp.asin
      WHERE pr.is_active = ?
      ORDER BY pr.created_at DESC LIMIT ?`,
        params: [active, limit]
      });
    }

    const response = await fetch(httpUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ statements })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Turso API error:', response.status, errorText);
      throw new Error(`Turso HTTP API error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    
    // Parse the response
    const reviews = [];
    if (result && result[0] && result[0].results && result[0].results.rows) {
      const columns = result[0].results.columns;
      for (const row of result[0].results.rows) {
        const review = {};
        columns.forEach((col, idx) => {
          review[col] = row[idx];
        });
        reviews.push(review);
      }
    }

    return res.status(200).json({
      success: true,
      count: reviews.length,
      reviews: reviews
    });

  } catch (error) {
    console.error('Error fetching reviews:', error);
    return res.status(500).json({ 
      error: 'Failed to fetch reviews',
      message: error.message 
    });
  }
}
