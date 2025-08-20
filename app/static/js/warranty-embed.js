// Flex Warranty Embed Script
// This script will be embedded on product pages to show warranty offers

(function() {
    'use strict';
    
    // Configuration
    const SESSION_TOKEN_KEY = 'flex_warranty_session';
    function injectStyles() {
        if (document.getElementById('fp-embed-styles')) return;
        const style = document.createElement('style');
        style.id = 'fp-embed-styles';
        style.textContent = `
          .fp-option { transition: transform .06s ease, box-shadow .06s ease, filter .12s ease; }
          .fp-option:hover { filter: brightness(1.06); box-shadow: 0 1px 0 rgba(0,0,0,.08); }
          .fp-option:active { transform: translateY(1px); }
          .fp-link { opacity:.9; }
          .fp-link:hover { opacity:1; text-decoration: underline; }
        `;
        try { document.head.appendChild(style); } catch {}
    }
    function getSelfScript() {
        try {
            const scripts = document.getElementsByTagName('script');
            for (let i = scripts.length - 1; i >= 0; i--) {
                const s = scripts[i];
                const src = (s && s.src) ? String(s.src) : '';
                if (src.indexOf('warranty-embed.js') !== -1) return s;
            }
            return scripts[scripts.length - 1] || null;
        } catch { return null; }
    }
    function getProxyBase() {
        try {
            const me = getSelfScript();
            const src = new URL(me ? me.src : window.location.href);
            return src.searchParams.get('proxy_base') || '/apps/flex-protect';
        } catch { return '/apps/flex-protect'; }
    }
    // Allow storefront token to be passed by script tag param for stability
    try {
      const me = getSelfScript();
      const src = new URL(me ? me.src : window.location.href);
      const t = src.searchParams.get('sf_token');
      if (t) { window.__FP_STOREFRONT_TOKEN = t; }
    } catch {}
    const PROXY_BASE = getProxyBase();
    try { const me = getSelfScript(); fpLog('embed loaded', { src: me ? me.src : null, PROXY_BASE, shop: (window.Shopify && window.Shopify.shop) || null }); } catch {}
    const MAX_SNIPPET = 300;
    function fpLog(...args){
        try { console.log('[FlexProtect]', ...args); } catch {}
    }

    // Storefront GraphQL helpers removed for stability; we rely solely on theme AJAX cart endpoints

    // i18n defaults; server can override via /pricing/config
    let __FP_I18N = { currency: 'USD', locale: 'en-US' };
    function formatMoney(amount, currency, locale) {
        const n = Number(amount || 0);
        try {
            return new Intl.NumberFormat(locale || __FP_I18N.locale, { style: 'currency', currency: currency || __FP_I18N.currency }).format(n);
        } catch {
            return `$${n.toFixed(2)}`;
        }
    }
    function safeTheme(theme) {
        const t = Object.assign({
            textColor: '#1e293b',
            backgroundColor: '#f8fafc',
            buttonColor: '#2563eb',
            chipColor: '#222222',
            chipTextColor: '#ffffff',
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        }, theme || {});
        return t;
    }

    function sleep(ms){ return new Promise(r=> setTimeout(r, ms)); }
    function debounce(fn, wait){ let t; return (...args)=>{ clearTimeout(t); t = setTimeout(()=> fn(...args), wait); }; }

    // getParentLineId removed – nested cart lines path deprecated

    // Deprecated nested cart lines path removed for stability; using /cart/add.js multi-item add
    
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
    
    async function fetchProductJson() {
        const m = window.location.pathname.match(/\/products\/([^\/?#]+)/);
        const handle = m ? m[1] : null;
        if (!handle) return null;
        try {
            const res = await fetch(`/products/${handle}.js`);
            if (!res.ok) return null;
            const j = await res.json();
            j.__handle = handle;
            return j;
        } catch { return null; }
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
    async function getWarrantyPricing(productInfo, sessionToken) {
        try {
            const url = new URL(`${PROXY_BASE}/pricing/options`, window.location.origin);
            if (window.Shopify && window.Shopify.shop) url.searchParams.set('shop', window.Shopify.shop);
            url.searchParams.set('price', String(productInfo.price));
            url.searchParams.set('category_tag', productInfo.category_tag);
            fpLog('options GET', url.toString());
            const res = await fetch(url.toString(), { method: 'GET' });
            const ct = res.headers.get('content-type') || '';
            fpLog('options status', res.status, ct);
            if (!res.ok) throw new Error(`options ${res.status}`);
            return await res.json();
        } catch (error) {
            console.error('Failed to get warranty pricing:', error);
            return null;
        }
    }
    
    // Create warranty offer HTML
    function createWarrantyOffer(productInfo, pricingData, theme, template, showLearnMore) {
        const includesAdh = !!pricingData.includes_adh;
        const options = Array.isArray(pricingData.options) ? pricingData.options : [];
        const tStrings = (template && template.strings) || {};
        const productCategory = productInfo.category_name || 'Device';
        const two = options.find(o=> Number(o.term) === 2);
        const three = options.find(o=> Number(o.term) === 3);
        const colors = safeTheme(theme);
        const headline = tStrings.headline || `Protect Your ${productCategory}`;
        const subhead = tStrings.subhead || `Extended warranty coverage${includesAdh ? ' (includes accidental damage)' : ''}`;
        const declineLabel = tStrings.decline || "I don't want protection";
        const learnMoreLabel = tStrings.learn_more || 'Learn more';
        const includeLearn = !!showLearnMore;
        const bullets = Array.isArray(tStrings.bullets) && tStrings.bullets.length ? tStrings.bullets : [
          'Extended failure protection', 'Hassle-free replacement', '24/7 support', ...(includesAdh ? ['Accidental damage coverage'] : [])
        ];
        const heroUrl = (template && (template.heroUrl || (template.images && template.images.hero))) || null;
        
        return `
            <div class="flex-warranty-offer" style="
                border: 2px solid ${colors.buttonColor};
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                background: ${colors.backgroundColor};
                font-family: ${colors.fontFamily};
                color: ${colors.textColor};
                position: relative;
                z-index: 2;
            ">
                <div style="display:flex; gap:16px; align-items:center; margin-bottom:15px;">
                  <div style="flex:1; min-width:0;">
                    <h3 style="margin:0; color:#1e293b; font-size:18px; font-weight:600;">${headline}</h3>
                    <p style="margin:5px 0 0 0; color:#64748b; font-size:14px;">${subhead}</p>
                    </div>
                  ${heroUrl ? `<img src="${heroUrl}" alt="Protection" style="width:120px; height:auto; border-radius:6px; object-fit:cover;">` : ''}
                </div>
                
                <div style="margin-bottom: 15px;">
                    <ul style="margin:0; padding-left:20px; color:#475569; font-size:14px;">
                      ${bullets.map(b => `<li>${b}</li>`).join('')}
                    </ul>
                </div>
                
                <div style="display:flex; gap:8px;">
                  ${two ? `<button type="button" class="fp-option" data-fp-term="2" data-fp-price="${Number(two.price).toFixed(2)}" style="flex:1; background:${colors.chipColor}; color:${colors.chipTextColor}; border:1px solid ${colors.buttonColor}; padding:12px; border-radius:6px; cursor:pointer; pointer-events:auto;">2 Year: ${formatMoney(Number(two.price), __FP_I18N.currency, __FP_I18N.locale)}</button>`: ''}
                  ${three ? `<button type="button" class="fp-option" data-fp-term="3" data-fp-price="${Number(three.price).toFixed(2)}" style="flex:1; background:${colors.chipColor}; color:${colors.chipTextColor}; border:1px solid ${colors.buttonColor}; padding:12px; border-radius:6px; cursor:pointer; pointer-events:auto;">3 Year: ${formatMoney(Number(three.price), __FP_I18N.currency, __FP_I18N.locale)}</button>`: ''}
                </div>
                <div style="margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
                  ${includeLearn ? `<button type="button" data-fp-learn class="fp-link" style="background:none; border:none; color:#64748b; cursor:pointer; pointer-events:auto;">${learnMoreLabel}</button>` : '<span></span>'}
                  <button type="button" data-fp-decline class="fp-link" style="background:none; border:none; color:#64748b; cursor:pointer; pointer-events:auto;">${declineLabel}</button>
                </div>
            </div>
        `;
    }
    
    function createLearnMoreContent(template, theme) {
        const colors = safeTheme(theme);
        const tStrings = (template && template.strings) || {};
        const headline = tStrings.headline || 'Learn more about protection';
        const subhead = tStrings.subhead || '';
        const bullets = Array.isArray(tStrings.bullets) && tStrings.bullets.length ? tStrings.bullets : [
          'What is covered', 'How claims work', 'Exclusions'
        ];
        const heroUrl = (template && (template.heroUrl || (template.images && template.images.hero))) || null;
        return `
          <div class="flex-warranty-learn" style="padding:16px; color:${colors.textColor}; font-family:${colors.fontFamily};">
            <div style="display:flex; gap:16px; align-items:center; margin-bottom:12px;">
              <div style="flex:1; min-width:0;">
                <h3 id="fp-learn-title" style="margin:0; font-size:18px; font-weight:600;">${headline}</h3>
                ${subhead ? `<p style=\"margin:6px 0 0; color:#64748b;\">${subhead}</p>` : ''}
              </div>
              ${heroUrl ? `<img src="${heroUrl}" alt="Learn more" style="width:120px; height:auto; border-radius:6px; object-fit:cover;">` : ''}
            </div>
            <ul style="margin:0; padding-left:20px; color:#475569;">
              ${bullets.map(b => `<li>${b}</li>`).join('')}
            </ul>
          </div>
        `;
    }

    function showModal(innerHtml, titleId) {
        const modal = document.createElement('div');
        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:9999;';
        modal.innerHTML = `<div role="dialog" aria-modal="true" ${titleId ? `aria-labelledby="${titleId}"` : ''} tabindex="-1" style="max-width:640px;width:92%;background:#fff;border-radius:8px;padding:12px;outline:none;">${innerHtml}<div style=\"text-align:right;margin-top:8px;\"><button type=\"button\" data-fp-close class=\"fp-link\" style=\"background:none;border:none;color:#64748b;cursor:pointer;\">Close</button></div></div>`;
        document.body.appendChild(modal);
        const close = () => { try { modal.remove(); } catch {} };
        modal.addEventListener('click', (e)=>{ if (e.target === modal) close(); });
        const btn = modal.querySelector('[data-fp-close]'); if (btn) btn.addEventListener('click', close);
        try { const pane = modal.querySelector('[role="dialog"]'); if (pane) { pane.focus(); pane.addEventListener('keydown', (e)=>{ if (e.key === 'Escape') close(); }); } } catch {}
        return modal;
    }
    // ensureCartId removed – not used with /cart/add.js flow

    async function selectAndAddToCart(sessionToken, price, term, productId, parentVariantGid, sessionHint) {
        try {
            // Prefer GET to avoid proxy POST issues; include all params in query
            const selUrl = new URL(`${PROXY_BASE}/pricing/select`, window.location.origin);
            if (window.Shopify && window.Shopify.shop) selUrl.searchParams.set('shop', window.Shopify.shop);
            selUrl.searchParams.set('session_token', sessionToken);
            if (sessionHint) selUrl.searchParams.set('session_hint', sessionHint);
            selUrl.searchParams.set('product_id', String(productId));
            selUrl.searchParams.set('price', String(price));
            selUrl.searchParams.set('term', String(term));
            selUrl.searchParams.set('category_tag', window.__FP_CATEGORY_TAG || '');
            fpLog('select GET', selUrl.toString());
            let res = await fetch(selUrl.toString(), { method: 'GET' });
            let ct = res.headers.get('content-type') || '';
            if (!res.ok || !ct.includes('application/json')) {
                const txt = await res.clone().text().catch(()=> '');
                fpLog('select GET non-json/status', res.status, ct, txt.slice(0, MAX_SNIPPET));
            } else {
                fpLog('select GET ok', res.status);
            }
            // If still not OK, try POST as a fallback
            if (!res.ok) {
                fpLog('select POST', selUrl.toString());
                res = await fetch(selUrl.toString(), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_token: sessionToken, product_id: productId, price, term, category_tag: window.__FP_CATEGORY_TAG }) });
                ct = res.headers.get('content-type') || '';
                if (!res.ok || !ct.includes('application/json')) {
                    const txt2 = await res.clone().text().catch(()=> '');
                    fpLog('select POST non-json/status', res.status, ct, txt2.slice(0, MAX_SNIPPET));
                } else {
                    fpLog('select POST ok', res.status);
                }
            }
            if (!res.ok) throw new Error('select failed');
            const j = await res.json();
            const warrantyVariantGid = j.variant_id || '';
            if (!/^gid:\/\/shopify\/ProductVariant\//.test(String(warrantyVariantGid))) throw new Error('variant gid missing');

            // Skip Storefront visibility checks; proceed directly to /cart/add.js

            // Try nested cart lines first; fall back to /cart/add.js if anything fails
            // Use the theme's cart (AJAX cart) exclusively for stability with Online Store carts.
            const items = [];
            const pm = parentVariantGid ? String(parentVariantGid).match(/\/(\d+)$/) : null;
            const parentNumericPre = pm ? pm[1] : null;
            if (parentNumericPre && window.__FP_ADD_BOTH) items.push({ id: Number(parentNumericPre), quantity: 1 });
            const wn = String(warrantyVariantGid).match(/\/(\d+)$/);
            const warrantyNumeric = wn ? wn[1] : null;
            items.push({ id: Number(warrantyNumeric), quantity: 1, properties: { '__FlexProtect.IsWarranty': true, '__FlexProtect.Term': `${term} year`, '__FlexProtect.Price': `$${Number(price).toFixed(2)}`, '__FlexProtect.Parent': parentNumericPre ? String(parentNumericPre) : '' } });
            const addRes = await fetch('/cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ items }) });
            if (!addRes.ok) {
              const t = await addRes.text().catch(()=> '');
              throw new Error(`add.js failed ${addRes.status} ${t.slice(0,120)}`);
            }
            // Wait until cart reflects the added line with non-zero price and resolved title
            for (let i=0; i<20; i++) {
              try {
                const c = await fetch('/cart.js', { credentials: 'include' });
                if (c.ok) {
                  const cj = await c.json();
                  const found = (cj.items || []).find(it => String(it.variant_id) === String(warrantyNumeric));
                  if (found && Number(found.price) > 0 && found.title && found.variant_title) break;
                }
              } catch {}
              await sleep(300);
            }
            // Small extra pause to allow Dawn to render updated sections
            await sleep(150);
            try { window.__FP_WARRANTY_ADDED = true; window.__FP_SUPPRESS_NEXT_NATIVE_ADD = true; setTimeout(()=>{ window.__FP_SUPPRESS_NEXT_NATIVE_ADD = false; }, 2500); } catch {}
            try { window.location.href = '/cart'; } catch {}
        } catch (e) { console.error('Failed to add protection to cart', e); }
    }

    async function cleanupOrphanWarranties() {
        try {
            const cartRes = await fetch('/cart.js', { credentials: 'include' });
            if (!cartRes.ok) return;
            const cart = await cartRes.json();
            const items = Array.isArray(cart.items) ? cart.items : [];
            const parentSet = new Set(items.filter(i=> !((i.properties||{})['__FlexProtect.IsWarranty'])).map(i=> String(i.variant_id)));
            const orphans = [];
            items.forEach((i, idx) => {
                const props = i.properties || {};
                const isW = !!(props['__FlexProtect.IsWarranty']);
                const p = props['__FlexProtect.Parent'] || props['__FlexProtect_Parent'];
                if (isW && p && !parentSet.has(String(p))) {
                    orphans.push({ key: i.key, line: idx + 1 });
                }
            });
            let removed = false;
            for (const o of orphans) {
                try {
                    // Prefer line number per Dawn's cart.js
                    let r = await fetch('/cart/change.js', { method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ line: o.line, quantity: 0 }) });
                    if (!r.ok) {
                        // Fallback by unique key
                        await fetch('/cart/change.js', { method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: o.key, quantity: 0 }) });
                    }
                    removed = true;
                } catch {}
            }
            if (removed) {
                // Ensure UI reflects latest cart for all themes
                try { window.location.reload(); } catch {}
            }
        } catch {}
    }

    // Observe cart interactions (page and drawer) and cleanup orphans after changes
    function hookCartWatchers() {
        const isCartPage = () => (location.pathname === '/cart');
        const debouncedCleanup = debounce(()=> { cleanupOrphanWarranties(); }, 200);

        // 1) Immediately on cart page load
        if (isCartPage()) {
            debouncedCleanup();
            try {
                const cartForm = document.querySelector('form[action="/cart"], form#cart');
                if (cartForm) cartForm.addEventListener('submit', ()=> setTimeout(debouncedCleanup, 200), true);
            } catch {}
        }

        // 2) Watch cart drawer or main cart node
        try {
            const targets = [
                document.querySelector('[id*="CartDrawer"], .drawer, .cart-drawer'),
                document.querySelector('#cart, form#cart, cart-items')
            ].filter(Boolean);
            targets.forEach(t => {
                try {
                    const mo = new MutationObserver(()=> setTimeout(debouncedCleanup, 150));
                    mo.observe(t, { childList: true, subtree: true });
                } catch {}
            });
        } catch {}

        // 3) Intercept XHR to catch themes that use XMLHttpRequest for /cart/add, /cart/change or /cart/update
        try {
            if (!window.__FP_XHR_HOOKED) {
                window.__FP_XHR_HOOKED = true;
                const origOpen = XMLHttpRequest.prototype.open;
                const origSend = XMLHttpRequest.prototype.send;
                XMLHttpRequest.prototype.open = function(method, url) {
                    try { this.__fp_url = url; } catch {}
                    return origOpen.apply(this, arguments);
                };
                XMLHttpRequest.prototype.send = function() {
                    try {
                        const url = String(this.__fp_url || '');
                        const done = () => {
                            try {
                                const path = new URL(url, location.origin).pathname;
                                if (/\/cart\/(change|update)(\.|$)/.test(path)) setTimeout(debouncedCleanup, 150);
                                if (/\/cart\/add(\.|$)/.test(path) && this.status >= 200 && this.status < 300) {
                                  // If no plan selected and not declined, show Offer Modal after successful XHR add
                                  if (placements.offer_modal && !localStorage.getItem(declinedKey) && !(selected && selectedPlan)) {
                                    try {
                                      const render = async () => {
                                        const pricingData2 = await getWarrantyPricing(productInfo, sessionToken);
                                        if (!pricingData2) return;
                                        const html = createWarrantyOffer(productInfo, pricingData2, theme, templates['offer_modal']);
                                        const modal = document.createElement('div');
                                        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:9999;';
                                        modal.innerHTML = `<div style=\"max-width:520px;width:90%;background:#fff;border-radius:8px;padding:12px;\">${html}</div>`;
                                        document.body.appendChild(modal);
                                        const mcontainer = modal.querySelector('.flex-warranty-offer');
                                        trackEvent('offer_view', { surface: 'offer_modal', price: productInfo.price, category_tag: productInfo.category_tag });
                                        mcontainer.addEventListener('click', async (ev) => {
                                          const tbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-term]') : null;
                                          if (tbtn && mcontainer.contains(tbtn)) {
                                            const term = Number(tbtn.getAttribute('data-fp-term'));
                                            const priceSel = Number(tbtn.getAttribute('data-fp-price'));
                                            trackEvent('offer_select', { surface: 'offer_modal', term, price: priceSel });
                                            let currentVar = null;
                                            try { currentVar = document.querySelector('[data-product-form] form [name=\"id\"], form[action*=\"/cart/add\"] [name=\"id\"], form[action=\"/cart/add\"] [name=\"id\"]').value || null; } catch {}
                                            const parentGidForAdd = currentVar ? `gid://shopify/ProductVariant/${Number(currentVar)}` : parentVariantGid;
                                            await selectAndAddToCart(sessionToken, priceSel, term, pj.id, parentGidForAdd, (pricingData2 && pricingData2.session_hint) || '');
                                            modal.remove();
                                            return;
                                          }
                                          const dbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                                          if (dbtn && mcontainer.contains(dbtn)) {
                                            trackEvent('offer_decline', { surface: 'offer_modal' });
                                            localStorage.setItem(declinedKey, '1');
                                            modal.remove();
                                            return;
                                          }
                                          const lbtn = ev.target && ev.target.closest ? ev.target.closest('[data-fp-learn]') : null;
                                          if (lbtn && mcontainer.contains(lbtn)) {
                                            const lmHtml = createLearnMoreContent(templates['learn_more'], theme);
                                            showModal(lmHtml, 'fp-learn-title');
                                          }
                                        });
                                      };
                                      setTimeout(render, 50);
                                    } catch {}
                                  }
                                }
                            } catch {}
                        };
                        this.addEventListener('load', done);
                        this.addEventListener('error', done);
                        this.addEventListener('abort', done);
                    } catch {}
                    return origSend.apply(this, arguments);
                };
            }
        } catch {}

        // 3b) Intercept fetch used by most Dawn-like themes
        try {
            if (!window.__FP_CART_FETCH_HOOKED) {
                window.__FP_CART_FETCH_HOOKED = true;
                const origFetch = window.fetch;
                window.fetch = function() {
                    const args = arguments;
                    return origFetch.apply(this, args).then((resp)=>{
                        try {
                            const req = args[0];
                            const url = (typeof req === 'string') ? req : (req && req.url) || '';
                            const path = new URL(url, location.origin).pathname || '';
                            if (/\/cart\/(change|update)(\.|$)/.test(path)) setTimeout(debouncedCleanup, 150);
                        } catch {}
                        return resp;
                    });
                };
            }
        } catch {}

        // 4) Clicks on remove anchors in cart page
        try {
            document.addEventListener('click', (ev) => {
                const a = ev.target && ev.target.closest ? ev.target.closest('a[href*="/cart/change"]') : null;
                if (a) setTimeout(debouncedCleanup, 250);
            }, true);
        } catch {}
    }

    async function trackEvent(type, payload) {
        try {
            const sessionToken = getSessionToken();
            const evUrl = new URL(`${PROXY_BASE}/events`, window.location.origin);
            if (window.Shopify && window.Shopify.shop) evUrl.searchParams.set('shop', window.Shopify.shop);
            fpLog('event POST', type, evUrl.toString(), payload);
            const res = await fetch(evUrl.toString(), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ type, session_token: sessionToken, payload }) });
            fpLog('event status', res.status);
        } catch {}
    }
    
    // Skip warranty
    window.skipWarranty = function() {
        const offerElement = document.querySelector('.flex-warranty-offer');
        if (offerElement) {
            offerElement.style.display = 'none';
        }
    };
    
    // Initialize warranty offer
    async function initWarrantyOffer() {
        // Fetch placement config via proxy; if product_page disabled, we’ll later bind modal/cart handlers
        let placements = { product_page: true, offer_modal: false, cart: false };
        let theme = null;
        let templates = {};
        let layout = 'compact';
        // Per-product decline key will be computed once product handle/id is known
        let declinedKey = null;
        try {
            const cfgUrl = new URL(`${PROXY_BASE}/pricing/config`, window.location.origin);
            if (window.Shopify && window.Shopify.shop) cfgUrl.searchParams.set('shop', window.Shopify.shop);
            fpLog('config GET', cfgUrl.toString());
            const res = await fetch(cfgUrl.toString());
            if (res.ok) {
                const j = await res.json();
                placements = Object.assign(placements, j.enabled || {});
                theme = j.theme || null;
                templates = j.templates || {};
                layout = j.layout || 'compact';
                if (j.i18n) { __FP_I18N = Object.assign(__FP_I18N, j.i18n || {}); }
                fpLog('config ok', placements, layout, __FP_I18N, theme, Object.keys(templates));
            } else {
                const txt = await res.clone().text().catch(()=> '');
                fpLog('config fail', res.status, txt.slice(0, MAX_SNIPPET));
            }
        } catch {}
        const pj = await fetchProductJson();
        if (!pj) return;
        const tags = Array.isArray(pj.tags) ? pj.tags : [];
        const on = tags.includes('flexprotect_on');
        const catTag = (tags.find(t=> String(t).startsWith('flexprotect_cat')) || '').trim();
        if (!on || !catTag) return;
        const price = (typeof pj.price === 'number' ? pj.price : 0) / 100;
        window.__FP_CATEGORY_TAG = catTag;
        const productInfo = { id: pj.id, handle: pj.__handle, title: pj.title, price, vendor: pj.vendor, tags: pj.tags, category_tag: catTag };
        // Resolve selected/main variant gid
        let mainVariantId = (pj.variants && pj.variants[0] && pj.variants[0].id) ? pj.variants[0].id : null;
        try {
            const urlVar = new URLSearchParams(window.location.search).get('variant');
            if (urlVar) mainVariantId = Number(urlVar);
        } catch {}
        const parentVariantGid = mainVariantId ? `gid://shopify/ProductVariant/${mainVariantId}` : null;
        declinedKey = `fp_declined:${productInfo.handle || productInfo.id}`;
        if (!isProductEligible(productInfo)) return;
        const sessionToken = getSessionToken();

        if (placements.product_page === true) {
            const pricingData = await getWarrantyPricing(productInfo, sessionToken);
            if (!pricingData) return;
            const offerHTML = createWarrantyOffer(productInfo, pricingData, theme, templates['product_page'], placements.learn_more === true);
            const insertTarget = document.querySelector('.product-form') || document.querySelector('[data-product-form]') || document.querySelector('.product__info') || document.querySelector('.product-single__info');
            let container = null;
            if (insertTarget) { insertTarget.insertAdjacentHTML('beforebegin', offerHTML); container = insertTarget.previousElementSibling; }
            if (container) {
                trackEvent('offer_view', { surface: 'product_page', price: productInfo.price, category_tag: productInfo.category_tag });
                let selected = false;
                let selectedPlan = null;
                const sessionHint = (pricingData && pricingData.session_hint) || '';
                container.addEventListener('click', (ev) => {
                  const termBtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-term]') : null;
                  if (termBtn && container.contains(termBtn)) {
                    const term = Number(termBtn.getAttribute('data-fp-term'));
                    const priceSel = Number(termBtn.getAttribute('data-fp-price'));
                    selectedPlan = { term, price: priceSel };
                    selected = true;
                    try { localStorage.removeItem(declinedKey); } catch {}
                    // Visual selection
                    container.querySelectorAll('button[data-fp-term]').forEach(b=>{ try { b.style.outline = 'none'; b.style.boxShadow = 'none'; } catch {} });
                    try { termBtn.style.outline = `2px solid ${theme?.buttonColor || '#2563eb'}`; termBtn.style.boxShadow = '0 0 0 2px rgba(37,99,235,.15)'; } catch {}
                    trackEvent('offer_select', { surface: 'product_page', term, price: priceSel });
                    return;
                  }
                  const declineBtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                  if (declineBtn && container.contains(declineBtn)) {
                    trackEvent('offer_decline', { surface: 'product_page' });
                    localStorage.setItem(declinedKey, '1');
                    // Keep the inline offer visible so merchant can change their mind; no modal will show due to declined flag
                    return;
                  }
                  const learnBtnPg = ev.target && ev.target.closest ? ev.target.closest('[data-fp-learn]') : null;
                  if (learnBtnPg && container.contains(learnBtnPg)) {
                    const lmHtml = createLearnMoreContent(templates['learn_more'], theme);
                    showModal(lmHtml, 'fp-learn-title');
                    return;
                  }
                });

                // Intercept add-to-cart: if a plan is selected, add via /cart/add.js; otherwise, optionally show modal
                const form = document.querySelector('form[action*="/cart/add"], form[action="/cart/add"]') || document.querySelector('[data-product-form] form');
                if (form) {
                  const handleAdd = async (e) => {
                    try {
                      if (selected && selectedPlan && !localStorage.getItem(declinedKey)) {
                        e.preventDefault();
                        // Resolve current variant id from form at click time
                        let currentVar = null;
                        try { currentVar = form.querySelector('[name="id"]')?.value || null; } catch {}
                        const parentGidForAdd = currentVar ? `gid://shopify/ProductVariant/${Number(currentVar)}` : parentVariantGid;
                        window.__FP_ADD_BOTH = true;
                        await selectAndAddToCart(sessionToken, selectedPlan.price, selectedPlan.term, pj.id, parentGidForAdd, sessionHint);
                        window.__FP_ADD_BOTH = false;
                        return;
                      }
                      // Only show modal if no plan is selected and not declined
                      if (placements.offer_modal && !localStorage.getItem(declinedKey) && !(selected && selectedPlan)) {
                        e.preventDefault();
                        const pricingData2 = pricingData || await getWarrantyPricing(productInfo, sessionToken);
                        if (!pricingData2) { form.submit(); return; }
                        const html = createWarrantyOffer(productInfo, pricingData2, theme, templates['offer_modal'], placements.learn_more === true);
                        const modal = document.createElement('div');
                        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:9999;';
                        modal.innerHTML = `<div style=\"max-width:520px;width:90%;background:#fff;border-radius:8px;padding:12px;\">${html}</div>`;
                        document.body.appendChild(modal);
                        const mcontainer = modal.querySelector('.flex-warranty-offer');
                        trackEvent('offer_view', { surface: 'offer_modal', price: productInfo.price, category_tag: productInfo.category_tag });
                        mcontainer.addEventListener('click', async (ev) => {
                          const tbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-term]') : null;
                          if (tbtn && mcontainer.contains(tbtn)) {
                            const term = Number(tbtn.getAttribute('data-fp-term'));
                            const priceSel = Number(tbtn.getAttribute('data-fp-price'));
                            trackEvent('offer_select', { surface: 'offer_modal', term, price: priceSel });
                            let currentVar2 = null;
                            try { currentVar2 = form.querySelector('[name="id"]')?.value || null; } catch {}
                            const parentGidForAdd2 = currentVar2 ? `gid://shopify/ProductVariant/${Number(currentVar2)}` : parentVariantGid;
                            await selectAndAddToCart(sessionToken, priceSel, term, pj.id, parentGidForAdd2, sessionHint);
                            modal.remove();
                            return;
                          }
                          const dbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                          if (dbtn && mcontainer.contains(dbtn)) {
                            trackEvent('offer_decline', { surface: 'offer_modal' });
                            localStorage.setItem(declinedKey, '1');
                            modal.remove();
                            form.submit();
            return;
        }
                        });
                      }
                    } catch { form.submit(); }
                  };
                  // Attach to submit and also to submit button click (some themes short-circuit submit)
                  try { form.addEventListener('submit', handleAdd, true); } catch {}
                  try {
                    const submitBtn = form.querySelector('button[type="submit"], [type="submit"]');
                    if (submitBtn) submitBtn.addEventListener('click', (e)=> { handleAdd(e); }, true);
                  } catch {}

                  // Defensive: capture generic clicks that end up submitting the same product form
                  try {
                    document.addEventListener('click', (e) => {
                      try {
                        const btn = e.target && e.target.closest ? e.target.closest('button[name="add"], button[type="submit"], [type="submit"], .product-form__submit, [data-add-to-cart]') : null;
                        if (!btn) return;
                        const within = btn.closest('form[action*="/cart/add"], form[action="/cart/add"], [data-product-form] form');
                        if (within && within === form) {
                          if (placements.offer_modal && !localStorage.getItem(declinedKey) && !(selected && selectedPlan)) {
                            try { e.preventDefault(); e.stopPropagation(); if (e.stopImmediatePropagation) e.stopImmediatePropagation(); } catch {}
                          }
                          handleAdd(e);
                        }
                      } catch {}
                    }, true);
                  } catch {}

                  // Defensive: patch form.submit to intercept programmatic submits
                  try {
                    if (!window.__FP_FORM_SUBMIT_PATCHED) {
                      window.__FP_FORM_SUBMIT_PATCHED = true;
                      const origSubmit = HTMLFormElement.prototype.submit;
                      HTMLFormElement.prototype.submit = function() {
                        try {
                          const isTarget = (this === form) || this.matches('form[action*="/cart/add"], form[action="/cart/add"], [data-product-form] form');
                          if (isTarget && placements.offer_modal && !localStorage.getItem(declinedKey) && !(selected && selectedPlan)) {
                            if (pricingData) {
                              const html = createWarrantyOffer(productInfo, pricingData, theme, templates['offer_modal']);
                              const modal = document.createElement('div');
                              modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:9999;';
                              modal.innerHTML = `<div style=\"max-width:520px;width:90%;background:#fff;border-radius:8px;padding:12px;\">${html}</div>`;
                              document.body.appendChild(modal);
                              const mcontainer = modal.querySelector('.flex-warranty-offer');
                              trackEvent('offer_view', { surface: 'offer_modal', price: productInfo.price, category_tag: productInfo.category_tag });
                              mcontainer.addEventListener('click', async (ev) => {
                                const tbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-term]') : null;
                                if (tbtn && mcontainer.contains(tbtn)) {
                                  const term = Number(tbtn.getAttribute('data-fp-term'));
                                  const priceSel = Number(tbtn.getAttribute('data-fp-price'));
                                  trackEvent('offer_select', { surface: 'offer_modal', term, price: priceSel });
                                  let currentVar2 = null;
                                  try { currentVar2 = form.querySelector('[name="id"]')?.value || null; } catch {}
                                  const parentGidForAdd2 = currentVar2 ? `gid://shopify/ProductVariant/${Number(currentVar2)}` : parentVariantGid;
                                  await selectAndAddToCart(sessionToken, priceSel, term, pj.id, parentGidForAdd2, sessionHint);
                                  modal.remove();
                                  return;
                                }
                                const dbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                                if (dbtn && mcontainer.contains(dbtn)) {
                                  trackEvent('offer_decline', { surface: 'offer_modal' });
                                  localStorage.setItem(declinedKey, '1');
                                  modal.remove();
                                  try { origSubmit.call(form); } catch {}
                                  return;
                                }
                                const lbtn = ev.target && ev.target.closest ? ev.target.closest('[data-fp-learn]') : null;
                                if (lbtn && mcontainer.contains(lbtn)) {
                                  const lmHtml = createLearnMoreContent(templates['learn_more'], theme);
                                  showModal(lmHtml, 'fp-learn-title');
                                }
                              });
                              return; // prevent native submit
                            }
                          }
                        } catch {}
                        return origSubmit.apply(this, arguments);
                      };
                    }
                  } catch {}
                }

                // Fallback: hook fetch to catch AJAX /cart/add and then add warranty if a plan was selected
                try {
                  if (!window.__FP_FETCH_HOOKED) {
                    window.__FP_FETCH_HOOKED = true;
                    const ADD_RE = /\/cart\/add(\.|$)/;
                    const CHANGE_RE = /\/cart\/(change|update)(\.|$)/;
                    const origFetch = window.fetch;
                    window.fetch = function() {
                      const args = arguments;
                      return origFetch.apply(this, args).then(async (resp)=>{
                        try {
                          const req = args[0];
                          const reqUrl = (typeof req === 'string') ? req : (req && req.url) || '';
                          const path = new URL(reqUrl, window.location.origin).pathname || '';
                          if (ADD_RE.test(path) && resp && resp.ok) {
                            if (window.__FP_SUPPRESS_NEXT_NATIVE_ADD) {
                              // We already executed combined add; ignore theme add echo
                              return resp;
                            }
                            // Case A: a plan was selected inline -> add warranty automatically
                            if (selected && selectedPlan && !localStorage.getItem(declinedKey) && !window.__FP_WARRANTY_ADDED) {
                              window.__FP_WARRANTY_ADDED = true;
                              let currentVar3 = null;
                              try { currentVar3 = document.querySelector('[data-product-form] form [name="id"], form[action*="/cart/add"] [name="id"], form[action="/cart/add"] [name="id"]').value || null; } catch {}
                              const parentGidForAdd3 = currentVar3 ? `gid://shopify/ProductVariant/${Number(currentVar3)}` : parentVariantGid;
                              window.__FP_ADD_BOTH = false; // native add already added the product; only add warranty
                              await selectAndAddToCart(sessionToken, selectedPlan.price, selectedPlan.term, pj.id, parentGidForAdd3, sessionHint);
                            } else if (placements.offer_modal && !localStorage.getItem(declinedKey) && !(selected && selectedPlan)) {
                              // Case B: no plan selected and not declined -> prompt with Offer Modal post-add
                              try {
                                const html = createWarrantyOffer(productInfo, pricingData || (await getWarrantyPricing(productInfo, sessionToken)), theme, templates['offer_modal']);
                                const modal = document.createElement('div');
                                modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:9999;';
                                modal.innerHTML = `<div style=\"max-width:520px;width:90%;background:#fff;border-radius:8px;padding:12px;\">${html}</div>`;
                                document.body.appendChild(modal);
                                const mcontainer = modal.querySelector('.flex-warranty-offer');
                                trackEvent('offer_view', { surface: 'offer_modal', price: productInfo.price, category_tag: productInfo.category_tag });
                                mcontainer.addEventListener('click', async (ev) => {
                                  const tbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-term]') : null;
                                  if (tbtn && mcontainer.contains(tbtn)) {
                                    const term = Number(tbtn.getAttribute('data-fp-term'));
                                    const priceSel = Number(tbtn.getAttribute('data-fp-price'));
                                    trackEvent('offer_select', { surface: 'offer_modal', term, price: priceSel });
                                    let currentVar4 = null;
                                    try { currentVar4 = document.querySelector('[data-product-form] form [name="id"], form[action*="/cart/add"] [name="id"], form[action="/cart/add"] [name="id"]').value || null; } catch {}
                                    const parentGidForAdd4 = currentVar4 ? `gid://shopify/ProductVariant/${Number(currentVar4)}` : parentVariantGid;
                                    await selectAndAddToCart(sessionToken, priceSel, term, pj.id, parentGidForAdd4, sessionHint);
                                    modal.remove();
                                    return;
                                  }
                                  const dbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                                  if (dbtn && mcontainer.contains(dbtn)) {
                                    trackEvent('offer_decline', { surface: 'offer_modal' });
                                    localStorage.setItem(declinedKey, '1');
                                    modal.remove();
                                    return;
                                  }
                                  const lbtn = ev.target && ev.target.closest ? ev.target.closest('[data-fp-learn]') : null;
                                  if (lbtn && mcontainer.contains(lbtn)) {
                                    const lmHtml = createLearnMoreContent(templates['learn_more'], theme);
                                    showModal(lmHtml, 'fp-learn-title');
                                  }
                                });
                              } catch {}
                            }
                          }
                          // When cart changes, remove orphan warranties whose parent is gone
                          if (CHANGE_RE.test(path) && resp && resp.ok) {
                            try {
                              const cartRes = await fetch('/cart.js', { credentials: 'include' });
                              if (cartRes.ok) {
                                const cart = await cartRes.json();
                                const items = Array.isArray(cart.items) ? cart.items : [];
                                const parents = new Set(items
                                  .filter(i=> { const props=(i.properties||{}); return !(props['__FlexProtect.IsWarranty'] || props['__FlexProtect_IsWarranty']); })
                                  .map(i=> String(i.variant_id)));
                                const orphanWarrantyKeys = items
                                  .filter(i=> { const props=(i.properties||{}); return (props['__FlexProtect.IsWarranty'] || props['__FlexProtect_IsWarranty']); })
                                  .filter(i=> { const props=(i.properties||{}); const p = props['__FlexProtect.Parent'] || props['__FlexProtect_Parent']; return p && !parents.has(String(p)); })
                                  .map(i=> i.key);
                                for (const key of orphanWarrantyKeys) {
                                  try { await fetch('/cart/change.js', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: key, quantity: 0 }) }); } catch {}
                                }
                              }
                            } catch {}
                          }
                        } catch {}
                        return resp;
                      });
                    };
                  }
                } catch {}
            }
        } else if (placements.offer_modal === true && !localStorage.getItem(declinedKey)) {
            // Intercept add-to-cart to show modal
            const form = document.querySelector('form[action*="/cart/add"], form[action="/cart/add"]') || document.querySelector('[data-product-form] form');
            if (form) {
                form.addEventListener('submit', async (e) => {
                    try {
                        e.preventDefault();
                        const pricingData = await getWarrantyPricing(productInfo, sessionToken);
                        if (!pricingData) return form.submit();
                        const html = createWarrantyOffer(productInfo, pricingData, theme, templates['offer_modal'], placements.learn_more === true);
                        const modal = document.createElement('div');
                        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:9999;';
                        modal.innerHTML = `<div style="max-width:520px;width:90%;background:#fff;border-radius:8px;padding:12px;">${html}</div>`;
                        document.body.appendChild(modal);
                        const container = modal.querySelector('.flex-warranty-offer');
                        trackEvent('offer_view', { surface: 'offer_modal', price: productInfo.price, category_tag: productInfo.category_tag });
                        container.querySelectorAll('button[data-fp-term]').forEach(btn => {
                            btn.addEventListener('click', async () => {
                                const term = Number(btn.getAttribute('data-fp-term'));
                                const priceSel = Number(btn.getAttribute('data-fp-price'));
                                trackEvent('offer_select', { surface: 'offer_modal', term, price: priceSel });
                                await selectAndAddToCart(sessionToken, priceSel, term, pj.id, parentVariantGid);
                                modal.remove();
                                form.submit();
                            });
                        });
                        const decline = container.querySelector('button[data-fp-decline]');
                        if (decline) decline.addEventListener('click', ()=> { trackEvent('offer_decline', { surface: 'offer_modal' }); localStorage.setItem(declinedKey, '1'); modal.remove(); form.submit(); });
                        const learnBtn = container.querySelector('[data-fp-learn]');
                        if (learnBtn && (templates['learn_more'] || {}).sections) {
                          learnBtn.addEventListener('click', (e)=>{
                            e.preventDefault();
                            const lmHtml = createLearnMoreContent(templates['learn_more'], theme);
                            showModal(lmHtml, 'fp-learn-title');
                          });
                        }
                    } catch { form.submit(); }
                });
            }
        } else if (placements.cart === true && !localStorage.getItem(declinedKey)) {
            // Simple slide-out cart treatment: inject row if drawer present
            const drawer = document.querySelector('[id*="CartDrawer"], .drawer, .cart-drawer');
            if (drawer) {
                const renderRow = async () => {
                    const pricingData = await getWarrantyPricing(productInfo, sessionToken);
                    if (!pricingData) return;
                    const node = document.createElement('div');
                    node.innerHTML = createWarrantyOffer(productInfo, pricingData, theme, templates['cart'], placements.learn_more === true);
                    const container = node.firstElementChild;
                    container.style.margin = '12px';
                    drawer.appendChild(container);
                    trackEvent('offer_view', { surface: 'cart', price: productInfo.price, category_tag: productInfo.category_tag });
                        container.addEventListener('click', (ev) => {
                            const tbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-term]') : null;
                            if (tbtn && container.contains(tbtn)) {
                                const term = Number(tbtn.getAttribute('data-fp-term'));
                                const priceSel = Number(tbtn.getAttribute('data-fp-price'));
                                trackEvent('offer_select', { surface: 'cart', term, price: priceSel });
                                selectAndAddToCart(sessionToken, priceSel, term, pj.id);
                                return;
                            }
                            const dbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                            if (dbtn && container.contains(dbtn)) {
                                trackEvent('offer_decline', { surface: 'cart' });
                                container.remove();
                                return;
                            }
                            const lbtn = ev.target && ev.target.closest ? ev.target.closest('[data-fp-learn]') : null;
                            if (lbtn && container.contains(lbtn)) {
                                const lmHtml = createLearnMoreContent(templates['learn_more'], theme);
                                showModal(lmHtml, 'fp-learn-title');
                                return;
                            }
                        });
                };
                // Initial render and observe for open/close
                renderRow();
            }
        }
        // Always hook cart watchers since embed is site-wide
        hookCartWatchers();
    }
    
    // Single-init guard and DOM ready
    if (!window.__FP_INIT) {
        window.__FP_INIT = true;
        injectStyles();
        // Always attach cart watchers, even if not on a product page
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => { try { hookCartWatchers(); } catch {} });
        } else { try { hookCartWatchers(); } catch {} }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWarrantyOffer);
    } else {
        initWarrantyOffer();
        }
    }
    
})(); 