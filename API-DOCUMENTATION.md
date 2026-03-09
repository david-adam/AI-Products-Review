# ProductLens AI API Documentation

## Base URL
```
https://aiproductsreview-fmdnm5mnr-wei-dais-projects-ef69758b.vercel.app
```

**Note:** If you see an authentication prompt, go to Vercel Dashboard > Project Settings > Deployment Protection and disable "Vercel Authentication".

## Endpoints

### 1. Get Products
**GET** `/api/products`

Returns trending products from the database.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | number | 50 | Number of products to return (max 100) |

**Example:**
```bash
curl "https://aiproductsreview-fmdnm5mnr-wei-dais-projects-ef69758b.vercel.app/api/products?limit=10"
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "products": [...]
}
```

---

### 2. Get AI Reviews
**GET** `/api/reviews`

Returns AI-generated product reviews from the product_reviews table.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | number | 20 | Number of reviews to return (max 100) |
| asin | string | - | Filter by product ASIN |
| active | number | 1 | Filter by active status |

**Example:**
```bash
curl "https://aiproductsreview-fmdnm5mnr-wei-dais-projects-ef69758b.vercel.app/api/reviews?limit=5"
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "reviews": [
    {
      "id": 1,
      "product_asin": "B0DGJ7HYG1",
      "summary": "...",
      "full_review": "...",
      "rating": 4.5,
      "pros": "...",
      "cons": "...",
      "title": "Product Title",
      "price": 99.99,
      ...
    }
  ]
}
```

---

### 3. Search Products & Reviews
**GET** `/api/search`

Searches products and AI reviews.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| q | string | - | Search query (required, min 2 chars) |
| type | string | "all" | Filter: "all", "products", or "reviews" |
| limit | number | 20 | Number of results (max 100) |

**Example:**
```bash
curl "https://aiproductsreview-fmdnm5mnr-wei-dais-projects-ef69758b.vercel.app/api/search?q=phone&type=products"
```

**Response:**
```json
{
  "success": true,
  "query": "phone",
  "type": "products",
  "total": 5,
  "products": [...],
  "reviews": []
}
```

---

### 4. Get Product with AI Review
**GET** `/api/product`

Returns a single product with its AI-generated review (if available).

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| asin | string | Yes | Product ASIN |

**Example:**
```bash
curl "https://aiproductsreview-fmdnm5mnr-wei-dais-projects-ef69758b.vercel.app/api/product?asin=B0DGJ7HYG1"
```

**Response:**
```json
{
  "success": true,
  "product": {
    "asin": "B0DGJ7HYG1",
    "title": "...",
    "price": 99.99,
    "review_summary": "...",
    "full_review": "...",
    "has_ai_review": true
  }
}
```

---

## Database Schema

### Tables Used:
- **trending_products** - Main product table
- **product_reviews** - AI-generated reviews (joined with trending_products)

### product_reviews Table:
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| product_asin | TEXT | FK to trending_products |
| summary | TEXT | 100-200 char AI summary |
| full_review | TEXT | 600-900 char AI review |
| rating | REAL | AI-assigned rating (1-5) |
| pros | TEXT | Comma-separated pros |
| cons | TEXT | Comma-separated cons |
| google_drive_image_url | TEXT | AI-generated image URL |
| ai_model | TEXT | Model used (e.g., "kimi-k2.5") |
| created_at | TIMESTAMP | Creation timestamp |
| is_active | INTEGER | Active flag |

---

## Error Handling

All endpoints return standard HTTP status codes:
- `200` - Success
- `400` - Bad Request (missing parameters)
- `405` - Method Not Allowed
- `500` - Internal Server Error

Error response format:
```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

---

## CORS

All endpoints support CORS with the following headers:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type`
