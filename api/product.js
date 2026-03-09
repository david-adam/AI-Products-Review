/*
 * Vercel Serverless Function: Get Product with AI Review
 * Endpoint: /api/product/[asin]
 * Fetches a single product with its AI-generated review
 * 
 * Path Parameter:
 *   - asin: Product ASIN (passed as query param for Vercel serverless)
 * 
 * Query Parameters:
 *   - asin: Product ASIN (required)
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
    
    // Get ASIN from query
    const asin = req.query.asin;

    if (!asin) {
      return res.status(400).json({ 
        error: 'Missing parameter',
        message: 'Product ASIN is required'
      });
    }

    // Query product with its review
    const statement = {
      q: `SELECT 
        tp.asin,
        tp.title,
        tp.price,
        tp.rating,
        tp.reviews as review_count,
        tp.image,
        tp.affiliate_link,
        tp.category,
        tp.amazon_rank,
        tp.google_trend_score,
        tp.reddit_mentions,
        tp.youtube_views,
        tp.tiktok_views,
        tp.total_score,
        tp.product_summary,
        tp.discovered_date,
        tp.last_updated,
        pr.id as review_id,
        pr.summary as review_summary,
        pr.full_review,
        pr.rating as review_rating,
        pr.pros,
        pr.cons,
        pr.google_drive_image_url,
        pr.google_drive_image_id,
        pr.ai_model as review_ai_model,
        pr.created_at as review_created_at,
        pr.is_active as review_active
      FROM trending_products tp
      LEFT JOIN product_reviews pr ON tp.asin = pr.product_asin AND pr.is_active = 1
      WHERE tp.asin = ?`,
      params: [asin]
    };

    const response = await fetch(httpUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ statements: [statement] })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Turso API error:', response.status, errorText);
      throw new Error(`Turso HTTP API error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    
    // Parse the response
    let product = null;
    if (result && result[0] && result[0].results && result[0].results.rows && result[0].results.rows.length > 0) {
      const columns = result[0].results.columns;
      const row = result[0].results.rows[0];
      product = {};
      columns.forEach((col, idx) => {
        product[col] = row[idx];
      });
    }

    if (!product) {
      return res.status(404).json({ 
        error: 'Product not found',
        message: `No product found with ASIN: ${asin}`
      });
    }

    return res.status(200).json({
      success: true,
      product: product,
      has_ai_review: product.review_id !== null
    });

  } catch (error) {
    console.error('Error fetching product:', error);
    return res.status(500).json({ 
      error: 'Failed to fetch product',
      message: error.message 
    });
  }
}
