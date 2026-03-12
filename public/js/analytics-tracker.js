/*
 * ProductLens AI - Analytics Tracking Code
 * Add this to your product pages for tracking
 * 
 * Usage:
 *   <script src="/js/analytics-tracker.js"><\/script>
 *   <script>
 *     AnalyticsTracker.init({
 *       apiUrl: '/api/track',
 *       productAsin: 'B09V3KXJPB',
 *       pageType: 'product'
 *     });
 *   <\/script>
 */

(function() {
    'use strict';

    // Get or generate session ID
    function getSessionId() {
        let sessionId = localStorage.getItem('pl_session_id');
        if (!sessionId) {
            sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
            localStorage.setItem('pl_session_id', sessionId);
        }
        return sessionId;
    }

    // Get user location from IP (simplified - in production use a service)
    async function getLocation() {
        try {
            // This would typically call an IP geolocation service
            // For now, return null and let the server handle it
            return null;
        } catch (e) {
            return null;
        }
    }

    // Parse UTM parameters from URL
    function getUtmParams() {
        const params = new URLSearchParams(window.location.search);
        return {
            utm_source: params.get('utm_source'),
            utm_medium: params.get('utm_medium'),
            utm_campaign: params.get('utm_campaign')
        };
    }

    // Get referrer
    function getReferrer() {
        return document.referrer || '';
    }

    // Track event
    async function trackEvent(action, data = {}) {
        const sessionId = getSessionId();
        const utmParams = getUtmParams();
        const referrer = getReferrer();

        try {
            const response = await fetch('/api/track', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    session_id: sessionId,
                    referrer: referrer,
                    ...utmParams,
                    ...data
                })
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Analytics tracking error:', error);
            return { success: false, error: error.message };
        }
    }

    // Public API
    window.AnalyticsTracker = {
        // Initialize tracking
        init: function(config) {
            this.config = config || {};
            this.apiUrl = this.config.apiUrl || '/api/track';
            
            // Auto-track page view
            this.trackPageView();
            
            // Set up click tracking for Amazon links
            this.setupClickTracking();
        },

        // Track page view
        trackPageView: async function() {
            const productAsin = this.config.productAsin;
            const pageType = this.config.pageType || 'product';
            
            await trackEvent('pageview', {
                product_asin: productAsin,
                page_type: pageType
            });
        },

        // Track Amazon link click
        trackAmazonClick: async function(productAsin, linkType) {
            return await trackEvent('click', {
                product_asin: productAsin,
                link_type: linkType || 'affiliate'
            });
        },

        // Track search query
        trackSearch: async function(query, resultsCount, foundResults) {
            return await trackEvent('search', {
                query: query,
                results_count: resultsCount || 0,
                found_results: foundResults !== false
            });
        },

        // Set up automatic click tracking for Amazon links
        setupClickTracking: function() {
            const self = this;
            
            // Find all Amazon affiliate links
            document.addEventListener('click', function(e) {
                const link = e.target.closest('a');
                if (!link) return;
                
                const href = link.href || '';
                
                // Check if it's an Amazon link
                if (href.includes('amazon.com') || href.includes('amzn.to') || href.includes('amazon.')) {
                    // Get product ASIN from URL if available
                    const asin = self.extractAsin(href) || self.config.productAsin;
                    
                    // Track the click
                    self.trackAmazonClick(asin, 'affiliate');
                }
            });
        },

        // Extract ASIN from Amazon URL
        extractAsin: function(url) {
            // Pattern 1: /dp/ASIN
            const dpMatch = url.match(/\/dp\/([A-Z0-9]{10})/i);
            if (dpMatch) return dpMatch[1];
            
            // Pattern 2: /gp/product/ASIN
            const gpMatch = url.match(/\/gp\/product\/([A-Z0-9]{10})/i);
            if (gpMatch) return gpMatch[1];
            
            // Pattern 3: ?asin=ASIN or &asin=ASIN
            const asinMatch = url.match(/[?&](?:asin|ASIN)=([A-Z0-9]{10})/i);
            if (asinMatch) return asinMatch[1];
            
            return null;
        },

        // Get current session ID
        getSessionId: getSessionId
    };

    // Auto-initialize if config is provided in data attribute
    document.addEventListener('DOMContentLoaded', function() {
        const trackerScript = document.querySelector('script[data-analytics]');
        if (trackerScript) {
            try {
                const config = JSON.parse(trackerScript.dataset.analytics);
                AnalyticsTracker.init(config);
            } catch (e) {
                console.error('Failed to parse analytics config:', e);
            }
        }
    });

})();
