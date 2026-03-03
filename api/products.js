/*
 * Vercel Serverless Function: Get Products from Turso
 * Endpoint: /api/products
 */

import { createClient } from '@libsql/client';

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
    const authToken = process.env.TURSO_AUTH_TOKEN || 'eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzI0MzMzNTMsImlkIjoiMDE5Y2FkNDEtZmUwMS03NzI4LTgyMGUtOGU1ZDBiZmJmZThjIiwicmlkIjoiYmJmZWUyMjYtZTI1NS00NmYxLThiZjktNzdiNTk3YWQ0NzA4In0.dRhrBVMddMlLt2PxrE766MRbRQE15wmtO6pNub4yxOvsr2MwjmeMTwzjINFqNUtQ4k6DW5hHBjettS3X-IVbDw';

    if (!authToken) {
      return res.status(500).json({ error: 'TURSO_AUTH_TOKEN not configured' });
    }

    // Create Turso client
    const client = createClient({
      url: dbUrl,
      authToken: authToken
    });

    // Query products
    const limit = parseInt(req.query.limit) || 50;
    const result = await client.execute({
      sql: 'SELECT * FROM products ORDER BY created_at DESC LIMIT ?',
      args: [limit]
    });

    // Transform to array of objects
    const products = result.rows.map(row => ({
      id: row.id,
      asin: row.asin,
      title: row.title,
      price: row.price,
      rating: row.rating,
      reviews: row.reviews,
      image: row.image,
      affiliate_link: row.affiliate_link,
      search_query: row.search_query,
      created_at: row.created_at
    }));

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
