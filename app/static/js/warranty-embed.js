// Flex Warranty Embed Script
// This script will be embedded on product pages to show warranty offers

(function() {
    'use strict';
    
    // Configuration
    const API_BASE_URL = 'https://flex-warranty-api.fly.dev';
    const SESSION_TOKEN_KEY = 'flex_warranty_session';
    
    // Product category mapping
    const PRODUCT_CATEGORIES = {
        'laptop': 'Desktops, Laptops',
        'desktop': 'Desktops, Laptops',
        'computer': 'Desktops, Laptops',
        'tablet': 'Tablets',
        'ipad': 'Tablets',
        'tv': 'TVs',
        'television': 'TVs',
        'monitor': 'Consumer Electronics',
        'phone': 'Consumer Electronics',
        'smartphone': 'Consumer Electronics',
        'camera': 'Consumer Electronics',
        'headphones': 'Consumer Electronics',
        'speaker': 'Consumer Electronics',
        'gaming': 'Consumer Electronics'
    };
    
    // Generate or retrieve session token
    function getSessionToken() {
        let sessionToken = localStorage.getItem(SESSION_TOKEN_KEY);
        if (!sessionToken) {
            sessionToken = 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
            localStorage.setItem(SESSION_TOKEN_KEY, sessionToken);
        }
        return sessionToken;
    }
    
    // Detect product category from product info
    function detectProductCategory(productInfo) {
        const title = productInfo.title.toLowerCase();
        const vendor = productInfo.vendor.toLowerCase();
        
        // Check for specific keywords in title and vendor
        for (const [keyword, category] of Object.entries(PRODUCT_CATEGORIES)) {
            if (title.includes(keyword) || vendor.includes(keyword)) {
                return category;
            }
        }
        
        // Default to Consumer Electronics if no match found
        return 'Consumer Electronics';
    }
    
    // Get current product information
    function getProductInfo() {
        // Try to get product info from Shopify's global objects
        if (window.Shopify && window.Shopify.theme) {
            const product = window.Shopify.theme.product;
            if (product) {
                return {
                    id: product.id,
                    title: product.title,
                    price: parseFloat(product.price) / 100, // Convert from cents
                    vendor: product.vendor
                };
            }
        }
        
        // Fallback: try to extract from page elements
        const productIdMatch = window.location.pathname.match(/\/products\/([^\/]+)/);
        const productId = productIdMatch ? productIdMatch[1] : null;
        
        const priceElement = document.querySelector('[data-product-price]') || 
                           document.querySelector('.price') ||
                           document.querySelector('[class*="price"]');
        const price = priceElement ? parseFloat(priceElement.textContent.replace(/[^0-9.]/g, '')) : 0;
        
        const titleElement = document.querySelector('h1') || 
                           document.querySelector('[data-product-title]');
        const title = titleElement ? titleElement.textContent.trim() : 'Product';
        
        return {
            id: productId,
            title: title,
            price: price,
            vendor: 'Unknown'
        };
    }
    
    // Check if product is eligible for warranty
    function isProductEligible(productInfo) {
        // Skip if vendor is Flex Protect (our warranty product)
        if (productInfo.vendor === 'Flex Protect') {
            return false;
        }
        
        // Add more eligibility rules here
        // For example: only electronics, minimum price, etc.
        return productInfo.price >= 10; // Only products over $10
    }
    
    // Get warranty pricing from API
    async function getWarrantyPricing(productInfo, sessionToken, warrantyTerm = 2) {
        try {
            const productCategory = detectProductCategory(productInfo);
            
            const response = await fetch(`${API_BASE_URL}/api/pricing`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Shop-Domain': window.Shopify.shop,
                    'Authorization': `Bearer ${window.Shopify.theme.api_token || ''}`
                },
                body: JSON.stringify({
                    session_token: sessionToken,
                    product_id: productInfo.id,
                    product_price: productInfo.price,
                    product_category: productCategory,
                    warranty_term: warrantyTerm
                })
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to get warranty pricing:', error);
            return null;
        }
    }
    
    // Create warranty offer HTML
    function createWarrantyOffer(productInfo, pricingData) {
        const warrantyPrice = pricingData.warranty_price;
        const sessionToken = pricingData.session_token;
        const warrantyTerm = pricingData.warranty_term;
        const includesAdh = pricingData.includes_adh;
        const productCategory = pricingData.product_category;
        
        const adhText = includesAdh ? ' (includes accidental damage)' : '';
        const termText = warrantyTerm === 3 ? '3-year' : '2-year';
        
        return `
            <div class="flex-warranty-offer" style="
                border: 2px solid #2563eb;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="
                        background: #2563eb;
                        color: white;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin-right: 15px;
                        font-weight: bold;
                    ">🛡️</div>
                    <div>
                        <h3 style="margin: 0; color: #1e293b; font-size: 18px; font-weight: 600;">
                            Protect Your ${productCategory}
                        </h3>
                        <p style="margin: 5px 0 0 0; color: #64748b; font-size: 14px;">
                            ${termText} extended warranty coverage${adhText}
                        </p>
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <ul style="margin: 0; padding-left: 20px; color: #475569; font-size: 14px;">
                        <li>Extended failure protection</li>
                        <li>Hassle-free replacement</li>
                        <li>24/7 support</li>
                        <li>Peace of mind</li>
                        ${includesAdh ? '<li>Accidental damage coverage</li>' : ''}
                    </ul>
                </div>
                
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    background: white;
                    padding: 15px;
                    border-radius: 6px;
                    border: 1px solid #e2e8f0;
                ">
                    <div>
                        <span style="color: #64748b; font-size: 14px;">Warranty Price:</span>
                        <span style="color: #059669; font-size: 20px; font-weight: bold; margin-left: 8px;">
                            $${warrantyPrice.toFixed(2)}
                        </span>
                        <div style="color: #64748b; font-size: 12px; margin-top: 2px;">
                            ${termText} coverage
                        </div>
                    </div>
                    <button onclick="addWarrantyToCart('${sessionToken}', ${warrantyPrice}, ${warrantyTerm})" style="
                        background: #2563eb;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: background-color 0.2s;
                    " onmouseover="this.style.background='#1d4ed8'" onmouseout="this.style.background='#2563eb'">
                        Add Protection
                    </button>
                </div>
                
                <div style="text-align: center; margin-top: 10px;">
                    <button onclick="skipWarranty()" style="
                        background: none;
                        border: none;
                        color: #64748b;
                        text-decoration: underline;
                        cursor: pointer;
                        font-size: 14px;
                    ">I don't want protection</button>
                </div>
            </div>
        `;
    }
    
    // Add warranty to cart
    window.addWarrantyToCart = function(sessionToken, price, warrantyTerm) {
        // This would integrate with Shopify's cart API
        // For now, we'll just show a message
        const termText = warrantyTerm === 3 ? '3-year' : '2-year';
        alert(`${termText} warranty protection added to cart! Price: $${price.toFixed(2)}`);
        
        // In a real implementation, you would:
        // 1. Add the warranty product variant to cart
        // 2. Update the cart via Shopify's AJAX API
        // 3. Show a success message
    };
    
    // Skip warranty
    window.skipWarranty = function() {
        const offerElement = document.querySelector('.flex-warranty-offer');
        if (offerElement) {
            offerElement.style.display = 'none';
        }
    };
    
    // Initialize warranty offer
    async function initWarrantyOffer() {
        const productInfo = getProductInfo();
        
        if (!productInfo || !isProductEligible(productInfo)) {
            return;
        }
        
        const sessionToken = getSessionToken();
        const pricingData = await getWarrantyPricing(productInfo, sessionToken, 2); // Default to 2-year
        
        if (!pricingData) {
            return;
        }
        
        const offerHTML = createWarrantyOffer(productInfo, pricingData);
        
        // Find a good place to insert the offer
        const insertTarget = document.querySelector('.product-form') ||
                           document.querySelector('[data-product-form]') ||
                           document.querySelector('.product__info') ||
                           document.querySelector('.product-single__info');
        
        if (insertTarget) {
            insertTarget.insertAdjacentHTML('beforebegin', offerHTML);
        } else {
            // Fallback: insert after the first h1 or before the first form
            const fallbackTarget = document.querySelector('h1') || 
                                 document.querySelector('form') ||
                                 document.querySelector('.product');
            if (fallbackTarget) {
                fallbackTarget.insertAdjacentHTML('afterend', offerHTML);
            }
        }
    }
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWarrantyOffer);
    } else {
        initWarrantyOffer();
    }
    
})(); 