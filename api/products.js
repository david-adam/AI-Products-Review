/*
 * Vercel Serverless Function: Get Products from Turso
 * Endpoint: /api/products
 * Uses Turso HTTP API (same approach as Python client)
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

    // Clean up auth token (remove newlines and extra whitespace)
    authToken = authToken.replace(/\s+/g, '').trim();

    if (!authToken) {
      return res.status(500).json({ error: 'TURSO_AUTH_TOKEN is empty after cleaning' });
    }

    // Debug: Log environment variable status (remove in production)
    console.log('TURSO_AUTH_TOKEN present:', !!authToken);
    console.log('TURSO_AUTH_TOKEN length:', authToken.length);
    console.log('TURSO_AUTH_TOKEN prefix:', authToken.substring(0, 50));
    console.log('TURSO_DATABASE_URL:', dbUrl);

    // Convert libsql:// to https:// for HTTP API (same as Python client)
    const httpUrl = dbUrl.replace('libsql://', 'https://');
    
    const limit = parseInt(req.query.limit) || 50;
    
    // Build the request body - query from trending_products table with new columns
    const requestBody = {
      statements: [
        {
          q: `SELECT id, asin, title, price, rating, reviews, image, affiliate_link, product_summary, category, total_score FROM trending_products ORDER BY total_score DESC LIMIT ${limit}`
        }
      ]
    };

    // Execute query using Turso HTTP API
    const response = await fetch(httpUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Turso HTTP API error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();
    
    // Parse the response - Turso HTTP API returns results in different format
    // Each statement result is in result[0].results.rows
    const products = [];
    if (result && result[0] && result[0].results && result[0].results.rows) {
      const columns = result[0].results.columns;
      for (const row of result[0].results.rows) {
        const product = {};
        columns.forEach((col, idx) => {
          product[col] = row[idx];
        });
        products.push(product);
      }
    }

    return res.status(200).json({
      success: true,
      count: products.length,
      products: products
    });

  } catch (error) {
    console.error('Error fetching products:', error);
    return res.status(500).json({ 
      error: 'Failed to fetch products',
      message: error.message 
    });
  }
}
