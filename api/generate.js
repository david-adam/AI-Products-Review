/*
 * Vercel Serverless Function: Generate AI Content
 * Endpoint: /api/generate
 * Generates review content and images for a product
 */

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { asin, action } = req.body;

    if (!asin) {
      return res.status(400).json({ error: 'Product ASIN is required' });
    }

    // Simulate content generation (in production, this would call the AI pipeline)
    // For now, return mock data to demonstrate the dashboard
    
    if (action === 'generate') {
      // Simulate generation delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock generated content
      const generatedContent = {
        id: Date.now(),
        asin: asin,
        summary: "This premium wireless headphone delivers exceptional sound quality with active noise cancellation, 30-hour battery life, and premium comfort. Perfect for audiophiles and daily commuters alike.",
        full_review: "After thoroughly testing this wireless headphone, I'm impressed by its exceptional audio performance. The sound signature is well-balanced with crisp highs, warm mids, and punchy bass that doesn't overwhelm. The active noise cancellation is among the best I've experienced, effectively blocking out ambient noise in various environments.\n\nComfort is another strong suit - the ear cushions are plush and memory foam-based, allowing for extended listening sessions without fatigue. The 30-hour battery life is more than adequate for daily use, and the quick charge feature provides 5 hours of playback with just 10 minutes of charging.\n\nBuild quality feels premium with a sturdy headband and smooth-adjusting ear cups. The touch controls are intuitive and responsive. While the carrying case is a bit bulky, it's a minor tradeoff for the protection it offers.\n\nThe only drawbacks are the lack of aptX support and the premium price point, but considering the overall performance, it's worth the investment for serious music lovers.",
        rating: 4.5,
        pros: ["Excellent sound quality", "Effective ANC", "30-hour battery life", "Premium comfort", "Quick charging"],
        cons: ["No aptX support", "Bulky carrying case", "Premium price"],
        image_url: "https://via.placeholder.com/600x400/667eea/ffffff?text=Product+Image",
        ai_model: "kimi-k2.5",
        created_at: new Date().toISOString(),
        status: 'pending'
      };

      return res.status(200).json({
        success: true,
        content: generatedContent,
        message: 'Content generated successfully'
      });
    }

    if (action === 'approve' || action === 'reject') {
      // Simulate save delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      return res.status(200).json({
        success: true,
        action: action,
        message: action === 'approve' ? 'Content approved and saved to database' : 'Content rejected',
        timestamp: new Date().toISOString()
      });
    }

    return res.status(400).json({ error: 'Invalid action' });

  } catch (error) {
    console.error('Error generating content:', error);
    return res.status(500).json({ 
      error: 'Failed to generate content',
      message: error.message 
    });
  }
}
