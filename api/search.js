/*
 * Vercel Serverless Function: Search Products and Reviews
 * Endpoint: /api/search
 * Search functionality for AI content - searches both products and reviews
 * 
 * Query Parameters:
 *   - q: Search query (required)
 *   - type: Filter by type - 'all', 'products', 'reviews' (default: 'all')
 *   - limit: Number of results to return (default: 20)
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
    const query = req.query.q || '';
    const type = req.query.type || 'all';
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);

    if (!query || query.trim().length < 2) {
      return res.status(400).json({ 
        error: 'Invalid query',
        message: 'Search query must be at least 2 characters'
      });
    }

    const searchTerm = `%${query}%`;
    const results = {
      products: [],
      reviews: [],
      total: 0
    };

    // Search products if type is 'all' or 'products'
    if (type === 'all' || type === 'products') {
      const productsStatement = {
        q: `SELECT 
          asin,
          title,
          price,
          rating,
          reviews as review_count,
          image,
          affiliate_link,
          category,
          product_summary,
          total_score
        FROM trending_products 
        WHERE title LIKE ? OR category LIKE ? OR product_summary LIKE ?
        ORDER BY total_score DESC
        LIMIT ?`,
        params: [searchTerm, searchTerm, searchTerm, limit]
      };

      const productsResponse = await fetch(httpUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statements: [productsStatement] })
      });

      if (productsResponse.ok) {
        const productsResult = await productsResponse.json();
        if (productsResult && productsResult[0] && productsResult[0].results && productsResult[0].results.rows) {
          const columns = productsResult[0].results.columns;
          for (const row of productsResult[0].results.rows) {
            const product = {};
            columns.forEach((col, idx) => {
              product[col] = row[idx];
            });
            product.type = 'product';
            results.products.push(product);
          }
        }
      }
    }

    // Search reviews if type is 'all' or 'reviews'
    if (type === 'all' || type === 'reviews') {
      const reviewsStatement = {
        q: `SELECT 
          pr.id,
          pr.product_asin,
          pr.summary,
          pr.full_review,
          pr.rating,
          pr.pros,
          pr.cons,
          pr.ai_model,
          pr.created_at,
          tp.title as product_title,
          tp.price,
          tp.image
        FROM product_reviews pr
        LEFT JOIN trending_products tp ON pr.product_asin = tp.asin
        WHERE pr.is_active = 1 
          AND (pr.summary LIKE ? OR pr.full_review LIKE ? OR pr.pros LIKE ? OR pr.cons LIKE ?)
        ORDER BY pr.created_at DESC
        LIMIT ?`,
        params: [searchTerm, searchTerm, searchTerm, searchTerm, limit]
      };

      const reviewsResponse = await fetch(httpUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ statements: [reviewsStatement] })
      });

      if (reviewsResponse.ok) {
        const reviewsResult = await reviewsResponse.json();
        if (reviewsResult && reviewsResult[0] && reviewsResult[0].results && reviewsResult[0].results.rows) {
          const columns = reviewsResult[0].results.columns;
          for (const row of reviewsResult[0].results.rows) {
            const review = {};
            columns.forEach((col, idx) => {
              review[col] = row[idx];
            });
            review.type = 'review';
            results.reviews.push(review);
          }
        }
      }
    }

    // Calculate total
    results.total = results.products.length + results.reviews.length;

    return res.status(200).json({
      success: true,
      query: query,
      type: type,
      total: results.total,
      products: results.products,
      reviews: results.reviews
    });

  } catch (error) {
    console.error('Error searching:', error);
    return res.status(500).json({ 
      error: 'Failed to search',
      message: error.message 
    });
  }
}
