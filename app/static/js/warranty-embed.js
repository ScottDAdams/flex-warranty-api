// Flex Warranty Embed Script v2.1.5 - 2025-08-25
// This script will be embedded on product pages to show warranty offers
// VERSION: Removed hardcoded CSS overrides for responsive template support

(function() {
    'use strict';
    
    // Configuration
    const SESSION_TOKEN_KEY = 'flex_warranty_session';
    function injectStyles() {
        if (document.getElementById('fp-embed-styles')) return;
        const style = document.createElement('style');
        style.id = 'fp-embed-styles';
        style.textContent = `
          .fp-option { transition: transform .06s ease, box-shadow .12s ease, border-color .12s ease, filter .12s ease; border:2px solid #d1d5db; }
          .fp-option:hover { filter: brightness(1.02); border-color: var(--fp-accent, #2563eb); box-shadow: 0 0 0 4px var(--fp-glow, rgba(37,99,235,.2)); }
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

    // Handle warranty product pages - hide variant selector and show only selected variant
    function handleWarrantyProductPage() {
        try {
            // Check if we're on a Flex Protect warranty product page
            if (!window.ShopifyAnalytics || !window.ShopifyAnalytics.meta || !window.ShopifyAnalytics.meta.product) {
                return;
            }
            
            const product = window.ShopifyAnalytics.meta.product;
            if (product.vendor !== 'Flex Protect') {
                return;
            }
            
            fpLog('Detected Flex Protect warranty product page, hiding variant selector');
            
            // Get current variant ID from URL
            const urlParams = new URLSearchParams(window.location.search);
            const variantId = urlParams.get('variant');
            
            if (!variantId) {
                fpLog('No variant ID in URL, cannot determine which variant to show');
                return;
            }
            
            // Hide variant selector elements with !important CSS to override theme styles
            const variantSelectors = [
                '#variant-selects', // Target the specific element you found
                '.product__variant-selector',
                '.variant-selector',
                '.product-variant-selector',
                '[data-variant-selector]',
                '.product-form__variants',
                'select[name="id"]',
                '.product-single__variants',
                '.product-variants',
                '.product-options',
                '.product-form__options',
                '.product-single__options'
            ];
            
            let selectorHidden = false;
            
            // Create a comprehensive CSS rule to hide all variant selectors
            const hideVariantCSS = `
                variant-selects,
                [id^="variant-selects"],
                .product__variant-selector,
                .variant-selector,
                .product-variant-selector,
                [data-variant-selector],
                .product-form__variants,
                select[name="id"],
                .product-single__variants,
                .product-variants,
                .product-options,
                .product-form__options,
                .product-single__options {
                    display: none !important;
                }
            `;
            
            // Inject the CSS rule
            const style = document.createElement('style');
            style.textContent = hideVariantCSS;
            document.head.appendChild(style);
            fpLog('Injected CSS to hide variant selectors with !important');
            selectorHidden = true;
            
            // More aggressive approach: find and hide any element containing variant options
            if (!selectorHidden) {
                fpLog('Standard selectors failed, using aggressive approach');
                
                            // First try the specific element you found
            const variantSelects = document.querySelector('#variant-selects');
            if (variantSelects) {
                // Use CSS injection to override the component-picker.css display: block
                const style = document.createElement('style');
                style.textContent = `
                    #variant-selects {
                        display: none !important;
                    }
                    variant-selects {
                        display: none !important;
                    }
                `;
                document.head.appendChild(style);
                fpLog('Hidden #variant-selects element with !important CSS');
                selectorHidden = true;
            } else {
                    // Look for elements that contain variant option text
                    const allElements = document.querySelectorAll('*');
                    let hiddenCount = 0;
                    
                    for (const el of allElements) {
                        try {
                            if (el.children.length === 0 && // Only text nodes
                                el.textContent && 
                                el.textContent.trim() &&
                                el.textContent.includes('Protection -') && 
                                el.textContent.includes('yr') &&
                                !el.textContent.includes('Flex Protect - Protection - f64c0e85 - 3yr')) { // Don't hide the title
                                
                                // Find the closest clickable parent (button, option, etc.)
                                let parent = el.parentElement;
                                while (parent && parent !== document.body) {
                                    if (parent.tagName === 'BUTTON' || 
                                        parent.tagName === 'INPUT' || 
                                        parent.tagName === 'OPTION' ||
                                        parent.classList.contains('option') ||
                                        parent.classList.contains('variant') ||
                                        parent.classList.contains('chip') ||
                                        parent.getAttribute('role') === 'option') {
                                        
                                        parent.style.display = 'none';
                                        fpLog('Hidden variant option parent:', parent.tagName, parent.className, el.textContent);
                                        hiddenCount++;
                                        break;
                                    }
                                    parent = parent.parentElement;
                                }
                            }
                        } catch {}
                    }
                    
                    fpLog(`Aggressive approach hidden ${hiddenCount} variant options`);
                }
            }
            
            if (!selectorHidden) {
                // More targeted fallback: look for specific variant option patterns
                const variantOptionSelectors = [
                    'button[data-variant-id]',
                    'input[data-variant-id]',
                    'select option',
                    '.variant-option',
                    '[data-variant-option]',
                    '.product-option',
                    '[data-product-option]'
                ];
                
                variantOptionSelectors.forEach(selector => {
                    try {
                        document.querySelectorAll(selector).forEach(el => {
                            if (el.textContent && el.textContent.includes('Protection -') && el.textContent.includes('yr')) {
                                // Only hide if it's not the currently selected variant
                                const elVariantId = el.getAttribute('data-variant-id') || el.value;
                                if (elVariantId && String(elVariantId) !== String(variantId)) {
                                    el.style.display = 'none';
                                    fpLog('Hidden variant option:', el.textContent);
                                }
                            }
                        });
                    } catch {}
                });
            }
            
            // Show only the selected variant details
            const selectedVariant = product.variants.find(v => String(v.id) === String(variantId));
            if (selectedVariant) {
                fpLog('Showing only selected variant:', selectedVariant.public_title);
                
                // Update page title to show only selected variant
                const titleElements = [
                    'h1.product-single__title',
                    '.product__title',
                    'h1.product-title',
                    '[data-product-title]',
                    'h1'
                ];
                
                titleElements.forEach(selector => {
                    try {
                        const titleEl = document.querySelector(selector);
                        if (titleEl && titleEl.textContent.includes('Flex Protect')) {
                            titleEl.textContent = `Flex Protect - ${selectedVariant.public_title}`;
                            fpLog('Updated product title');
                        }
                    } catch {}
                });
                
                            // Hide other variant details that might be visible
            const variantDetailSelectors = [
                '.variant-detail',
                '[data-variant-detail]',
                '.product-variant-detail',
                '.product-option__value',
                '.product-option__label',
                '.product-form__option'
            ];
            
            variantDetailSelectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(el => {
                        const elVariantId = el.getAttribute('data-variant-id') || el.getAttribute('data-variant');
                        if (elVariantId && String(elVariantId) !== String(variantId)) {
                            el.style.display = 'none';
                        }
                    });
                } catch {}
            });
            
            // Additional: hide any remaining variant option buttons/chips
            const remainingVariantOptions = document.querySelectorAll('button, .btn, .chip, .option');
            remainingVariantOptions.forEach(el => {
                try {
                    if (el.textContent && 
                        el.textContent.includes('Protection -') && 
                        el.textContent.includes('yr') &&
                        !el.closest('.product-form') && // Don't hide form elements
                        !el.closest('.product-single__form')) {
                        
                        // Check if this is the selected variant
                        const isSelected = el.classList.contains('selected') || 
                                         el.classList.contains('active') ||
                                         el.getAttribute('aria-selected') === 'true';
                        
                        if (!isSelected) {
                            el.style.display = 'none';
                            fpLog('Hidden remaining variant option:', el.textContent);
                        }
                    }
                } catch {}
            });
            }
            
                    } catch (e) {
                fpLog('Error handling warranty product page:', e);
            }
            
            // Use MutationObserver to ensure CSS is injected after the element exists
            const observer = new MutationObserver((mutations, obs) => {
                if (document.querySelector('variant-selects')) {
                    fpLog('Found variant-selects element, re-injecting CSS...');
                    
                    // Re-inject CSS to ensure it takes effect
                    const hideVariantCSS = `
                        variant-selects,
                        [id^="variant-selects"] {
                            display: none !important;
                        }
                    `;
                    const style = document.createElement('style');
                    style.textContent = hideVariantCSS;
                    document.head.appendChild(style);
                    
                    fpLog('Re-injected CSS for variant-selects element');
                    obs.disconnect(); // Stop observing once we've found and hidden it
                }
            });
            
            // Start observing for DOM changes
            observer.observe(document, { childList: true, subtree: true });
            
            // Also run after a short delay as backup
            setTimeout(() => {
                try {
                    fpLog('Running delayed variant hiding...');
                    
                    // Re-run the hiding logic without the recursive call
                    const remainingVariantOptions = document.querySelectorAll('button, .btn, .chip, .option, [data-variant-id]');
                    let delayedHiddenCount = 0;
                    
                    remainingVariantOptions.forEach(el => {
                        try {
                            if (el.textContent && 
                                el.textContent.includes('Protection -') && 
                                el.textContent.includes('yr') &&
                                !el.textContent.includes('Flex Protect - Protection - f64c0e85 - 3yr')) {
                                
                                el.style.display = 'none';
                                fpLog('Delayed hidden variant option:', el.textContent);
                                delayedHiddenCount++;
                            }
                        } catch {}
                    });
                    
                    fpLog(`Delayed hiding found and hidden ${delayedHiddenCount} additional variant options`);
                } catch (e) {
                    fpLog('Error in delayed variant hiding:', e);
                }
            }, 1000);
        }

    // Remove any existing FP modal wrappers/containers before inserting a new one
    function removeExistingModals(){
        try {
            // Only remove modal containers, NOT the product page offer
            const selectors = [
                '#flexprotect-modal-container',
                '.flexprotect-modal-container'
            ];
            
            selectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(el => el.remove());
                } catch {}
            });
        } catch {}
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
    
    // Prefetch helpers
    function preloadImage(url){
        try { if (!url) return; const img = new Image(); img.referrerPolicy = 'no-referrer'; img.decoding = 'async'; img.loading = 'eager'; img.src = url; } catch {}
    }
    function prefetchOfferModal(productInfo, theme, templates, pricingData, showLearnMore){
        try {
            window.__FP_PREFETCH = window.__FP_PREFETCH || {};
            // Compute images to warm
            const t = templates && templates['offer_modal'] ? templates['offer_modal'] : {};
            const STATIC = 'https://flex-warranty-api.fly.dev/static/images/offers';
            const heroUrl = (t && (t.heroUrl || (t.images && t.images.hero))) || `${STATIC}/Hero-Image.png`;
            const brand = (t && t.brand) || { logoUrl: `${STATIC}/FlexProtect-Shield.png` };
            const poweredBy = (t && t.poweredBy) || { logoUrl: `${STATIC}/Powered-By-AIG.png` };
            preloadImage(heroUrl);
            preloadImage(brand && brand.logoUrl);
            preloadImage(poweredBy && poweredBy.logoUrl);
            // Cache server-provided HTML only; no fallback assembly
            const html = (t && typeof t.html === 'string' && !isPlaceholderHtml(t.html)) ? t.html : '';
            window.__FP_PREFETCH.offer_modal = html;
        } catch {}
    }

    // If we inject a full server-provided modal (with overlay/X), wire close events
    function wireServerModalClose(mcontainer, cleanup){
        try {
            const root = document.getElementById('flexprotect-modal-container') || mcontainer;
            if (!root) return;
            try {
                // Force overlay visible and highest stacking context
                const ov = root.querySelector('.modal-overlay');
                if (ov) {
                    ov.style.zIndex = '2147483647';
                    ov.style.display = 'flex';
                    ov.style.position = 'fixed';
                    ov.style.inset = '0';
                }
            } catch {}
            // Avoid extra overrides; rely on snippet CSS to control sizes to match design
            const closeBtn = root.querySelector('.modal-close-btn');
            const overlay = root.querySelector('.modal-overlay');
            const doClose = () => { try { cleanup && cleanup(); } catch {} };
            if (closeBtn) closeBtn.addEventListener('click', doClose, true);
            if (overlay) overlay.addEventListener('click', (e)=>{ try { if (e.target === overlay) doClose(); } catch {} }, true);
            try { document.addEventListener('keydown', (e)=>{ if (e.key === 'Escape') doClose(); }, { once: true }); } catch {}
        } catch {}
    }

    // Ensure modal overlay is visible; if not, fall back to direct insertion
    function ensureModalVisibleOrFallback(mcontainer, html){
        try {
            if (!mcontainer) return { mcontainer, usedFallback: false };
            const overlay = mcontainer.querySelector ? mcontainer.querySelector('.modal-overlay') : null;
            if (overlay) {
                try {
                    overlay.style.zIndex = '2147483647';
                    overlay.style.display = 'flex';
                    overlay.style.position = 'fixed';
                    overlay.style.inset = '0';
                    overlay.style.opacity = overlay.style.opacity || '1';
                    overlay.style.pointerEvents = 'auto';
                } catch {}
                // Remove the fallback logic that was creating duplicate content
                // Just ensure the existing modal is visible
            }
        } catch {}
        return { mcontainer, usedFallback: false };
    }

    // Build options HTML for selector from pricing
    function buildSelectorOptions(pricingData){
        try {
            const valid = Array.isArray(pricingData && pricingData.options) ? pricingData.options.filter(o=> typeof o.price !== 'undefined') : [];
            const sorted = valid.slice().sort((a,b)=> Number(b.price) - Number(a.price));
            const html = `${sorted.map(o=>{
                const termNum = Number(o.term);
                const label = `${termNum} Year${termNum === 1 ? '' : 's'} Protection`;
                const priceFmt = formatMoney(Number(o.price), __FP_I18N.currency, __FP_I18N.locale);
                return `<div class="opt" data-option data-term="${termNum}" data-price="${Number(o.price).toFixed(2)}"><div class="label">${label}</div><div class="price">${priceFmt}</div></div>`;
            }).join('')}
            <div class="opt" data-option data-term="none" data-price="0"><div class="label">Do Not Protect My Purchase</div></div>`;
            return { html, min: valid.length ? Math.min.apply(null, valid.map(o=> Number(o.price))) : null };
        } catch { return { html: '', min: null }; }
    }

    // Hydrate server-supplied modal selector with live pricing
    function hydrateModalSelector(root, pricingData){
        try {
            if (!root || !pricingData) return;
            const { html, min } = buildSelectorOptions(pricingData);
            const opts = root.querySelector('[data-opts]'); if (opts) opts.innerHTML = html;
            const sub = root.querySelector('[data-sub]'); if (sub && min != null) sub.textContent = `For as low as ${formatMoney(min, __FP_I18N.currency, __FP_I18N.locale)}`;
        } catch {}
    }

    // Insert server-provided modal HTML directly (no shadow root duplication)
    function insertServerModalShadow(html, scriptJs){
        // Just inject the HTML directly - it already contains the complete modal structure
        document.body.insertAdjacentHTML('beforeend', html);
        const mcontainer = document.getElementById('flexprotect-modal-container');
        const cleanup = () => { try { mcontainer && mcontainer.remove(); } catch {} };
        
        // Execute the script_js content if provided
        if (scriptJs && typeof scriptJs === 'string' && scriptJs.trim()) {
            try {
                // Wait for DOM to be ready, then execute the script
                setTimeout(() => {
                    try {
                        // Create a script element and execute it
                        const script = document.createElement('script');
                        script.textContent = scriptJs;
                        document.body.appendChild(script);
                        // Remove the script element after execution
                        setTimeout(() => { try { script.remove(); } catch {} }, 100);
                        console.log('Modal script executed successfully');
                    } catch (e) {
                        console.warn('Failed to execute modal script:', e);
                    }
                }, 50); // Small delay to ensure DOM is ready
            } catch (e) {
                console.warn('Failed to execute modal script:', e);
            }
        }
        
        return { mcontainer, cleanup, shadow: null };
    }

    // Insert server-provided product_page HTML in a Shadow DOM to prevent style bleed
    function insertServerInlineShadow(html, beforeNode){
        const host = document.createElement('div');
        host.setAttribute('data-fp-shadow-inline','');
        try {
            host.style.display = 'block';
            host.style.width = '100%';
            if (beforeNode && beforeNode.parentNode) beforeNode.parentNode.insertBefore(host, beforeNode);
            else document.body.appendChild(host);
        } catch {}
        const shadow = host.attachShadow ? host.attachShadow({ mode: 'open' }) : null;
        if (!shadow) { host.innerHTML = html; return { root: host, remove: ()=> { try { host.remove(); } catch {} } }; }
        shadow.innerHTML = html;
        // Let the template's CSS handle typography - no hardcoded overrides
        const root = shadow; // use shadow root for event wiring/hydration
        const remove = () => { try { host.remove(); } catch {} };
        return { root, remove };
    }

    // Detect placeholder sentinel content in template.html
    function isPlaceholderHtml(str){
        try {
            const s = String(str || '').toLowerCase();
            return s.includes('[paste your full offer modal html here]') || s.includes('[paste your full learn more html here]') || s.includes('[paste your full');
        } catch { return false; }
    }

    // Wire up the selector behavior inside the modal (drop-up + GO button)
    function wireSelectorBehavior(root){
        try {
            if (!root || root.__fp_wired) return; root.__fp_wired = true;
            const summary = root.querySelector('[data-summary]');
            const opts = root.querySelector('[data-opts]');
            const go = root.querySelector('[data-go]');
            const title = root.querySelector('[data-title]');
            const sub = root.querySelector('[data-sub]');
            const items = Array.from(root.querySelectorAll('[data-option]'));
            let current = null; let submitted = false;

            function openDrop(open){
                try { opts.classList.toggle('open', !!open); summary.setAttribute('aria-expanded', open ? 'true' : 'false'); } catch {}
            }
            function showGo(show){ try { go.classList.toggle('show', !!show); } catch {} }
            function reset(){ submitted = false; try { summary.classList.remove('ok','bad'); } catch {} showGo(false); }

            if (summary) summary.addEventListener('click', (e)=>{
                e.stopPropagation();
                if (submitted) { reset(); return; }
                const now = !(opts && opts.classList.contains('open'));
                openDrop(now);
                if (now) showGo(false); else if (current) showGo(true);
            }, true);

            items.forEach((it)=>{
                it.addEventListener('click', ()=>{
                    if (submitted) reset();
                    items.forEach(x=> x.classList.remove('selected'));
                    it.classList.add('selected');
                    current = it;
                    const term = it.getAttribute('data-term');
                    const price = it.getAttribute('data-price');
                    if (term === 'none') {
                        // Let database script handle text - just set classes
                        try { summary.classList.add('bad'); summary.classList.remove('ok'); } catch {}
                    } else {
                        // Let database script handle text - just set classes
                        try { summary.classList.add('ok'); summary.classList.remove('bad'); } catch {}
                    }
                    openDrop(false);
                    showGo(true);
                });
            });

            if (go) go.addEventListener('click', ()=>{
                if (!current) return;
                submitted = true;
                const term = current.getAttribute('data-term');
                const price = current.getAttribute('data-price');
                if (term === 'none') {
                    // Let database script handle text
                } else {
                    // Let database script handle text
                }
                root.dispatchEvent(new CustomEvent('fp:selection', { detail: { term, price, submitted: true }, bubbles: true, composed: true }));
            });

            window.addEventListener('click', (e)=>{ try { if (!root.contains(e.target)) openDrop(false); } catch {} }, true);
        } catch {}
    }

    // Hydrate server-provided product_page HTML with dynamic pricing/options
    function hydrateTemplateProductPage(container, pricingData){
        try {
            const options = Array.isArray(pricingData && pricingData.options) ? pricingData.options : [];
            const two = options.find(o=> Number(o.term) === 2);
            const three = options.find(o=> Number(o.term) === 3);
            // Support legacy '.plan', newer '.plan-option', and current '.option' blocks
            const planButtons = Array.from(container.querySelectorAll('.plan'));
            const planOptions = Array.from(container.querySelectorAll('.plan-option'));
            const inlineOptions = Array.from(container.querySelectorAll('.option'));
            const plans = planButtons.length ? planButtons : (planOptions.length ? planOptions : inlineOptions);
            // Map first to 2yr, second to 3yr if present
            if (plans[0] && two){
                plans[0].setAttribute('data-fp-term','2');
                plans[0].setAttribute('data-term','2');
                plans[0].setAttribute('data-fp-price', String(Number(two.price).toFixed(2)));
                plans[0].setAttribute('role','button');
                plans[0].style.cursor = 'pointer';
                try {
                  const priceNode = plans[0].querySelector('.price, .option-price');
                  if (priceNode) priceNode.textContent = `${formatMoney(Number(two.price), __FP_I18N.currency, __FP_I18N.locale)}`;
                  const yearsNode = plans[0].querySelector('.years, .option-title');
                  if (yearsNode) yearsNode.textContent = `2 Years Added Protection –`;
                  else plans[0].textContent = `2 Years – ${formatMoney(Number(two.price), __FP_I18N.currency, __FP_I18N.locale)}`;
                } catch {}
            }
            if (plans[1] && three){
                plans[1].setAttribute('data-fp-term','3');
                plans[1].setAttribute('data-term','3');
                plans[1].setAttribute('data-fp-price', String(Number(three.price).toFixed(2)));
                plans[1].setAttribute('role','button');
                plans[1].style.cursor = 'pointer';
                try {
                  const priceNode = plans[1].querySelector('.price, .option-price');
                  if (priceNode) priceNode.textContent = `${formatMoney(Number(three.price), __FP_I18N.currency, __FP_I18N.locale)}`;
                  const yearsNode = plans[1].querySelector('.years, .option-title');
                  if (yearsNode) yearsNode.textContent = `3 Years Added Protection –`;
                  else plans[1].textContent = `3 Years – ${formatMoney(Number(three.price), __FP_I18N.currency, __FP_I18N.locale)}`;
                } catch {}
            }
            // Low price line if present
            const low = Math.min.apply(null, options.map(o=> Number(o.price)).filter(n=> !isNaN(n)));
            if (isFinite(low)){
                const sub = container.querySelector('[data-sub], .sub');
                if (sub) { try { sub.textContent = `For as low as ${formatMoney(low, __FP_I18N.currency, __FP_I18N.locale)}`; } catch {} }
            }
        } catch {}
    }
    
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
    
    // Create warranty offer HTML: removed hardcoded fallbacks; rely on server-provided HTML only
    function createWarrantyOffer() { return ''; }
    
    function createLearnMoreContent(template) {
        try { if (template && typeof template.html === 'string' && template.html.trim().length > 0) { return template.html; } } catch {}
        return '';
    }
    
    function showModal(innerHtml, titleId) {
        const modal = document.createElement('div');
        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:2147483647;';
        modal.innerHTML = `<div role="dialog" aria-modal="true" ${titleId ? `aria-labelledby="${titleId}"` : ''} tabindex="-1" style="max-width:960px;width:95%;background:#fff;border-radius:12px;padding:12px;outline:none;box-shadow:0 10px 30px rgba(0,0,0,.2);">${innerHtml}<div style=\"text-align:right;margin-top:8px;\"><button type=\"button\" data-fp-close class=\"fp-link\" style=\"background:none;border:none;color:#64748b;cursor:pointer;\">Close</button></div></div>`;
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
                                        const html = (window.__FP_PREFETCH && window.__FP_PREFETCH.offer_modal) || createWarrantyOffer('offer_modal', productInfo, pricingData2, theme, templates['offer_modal']);
                                        const modal = document.createElement('div');
                                        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:2147483647;';
                                        modal.innerHTML = `<div style=\"max-width:820px;width:95%;background:#fff;border-radius:12px;padding:12px;box-shadow:0 10px 30px rgba(0,0,0,.2);\">${html}</div>`;
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
        // Single-call fetch: templates + theme + pricing
        try {
            const fullUrl = new URL(`${PROXY_BASE}/pricing/fulloffer`, window.location.origin);
            if (window.Shopify && window.Shopify.shop) fullUrl.searchParams.set('shop', window.Shopify.shop);
            // price/category_tag will be set after product JSON is known (below) via a second call
            fpLog('fulloffer will fetch after product info');
        } catch {}
        const pj = await fetchProductJson();
        if (!pj) return;
        const tags = Array.isArray(pj.tags) ? pj.tags : [];
        const catTag = (tags.find(t=> String(t).startsWith('flexprotect_cat')) || '').trim();
        if (!catTag) { fpLog('FlexProtect: missing flexprotect_cat tag; skipping. Tags:', tags); return; }
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

        // Fetch full offer once with resolved price and category
        let full = null;
        try {
            const u = new URL(`${PROXY_BASE}/pricing/fulloffer`, window.location.origin);
            if (window.Shopify && window.Shopify.shop) u.searchParams.set('shop', window.Shopify.shop);
            u.searchParams.set('price', String(price));
            u.searchParams.set('category_tag', String(catTag));
            fpLog('fulloffer GET', u.toString());
            const r = await fetch(u.toString());
            if (r.ok) { full = await r.json(); }
            if (full && full.i18n) { __FP_I18N = Object.assign(__FP_I18N, full.i18n || {}); }
            if (full && full.theme) { theme = full.theme; }
            if (full && full.templates) { templates = full.templates; }
            if (full && full.enabled) { placements = Object.assign(placements, full.enabled || {}); }
        } catch {}

        if (placements.product_page === true) {
            const pricingData = (full && full.pricing) ? full.pricing : await getWarrantyPricing(productInfo, sessionToken);
            if (!pricingData) return;
            // Prefer server-provided product_page HTML if present
            const tp = templates['product_page'] || {};
            let offerHTML = '';
            if (tp && typeof tp.html === 'string' && tp.html.trim().length > 0 && !isPlaceholderHtml(tp.html)) {
                offerHTML = tp.html;
            } else {
                offerHTML = createWarrantyOffer('product_page', productInfo, pricingData, theme, templates['product_page'], placements.learn_more === true);
            }
            const insertTarget = document.querySelector('.product-form') || document.querySelector('[data-product-form]') || document.querySelector('.product__info') || document.querySelector('.product-single__info');
            let container = null;
            if (insertTarget) {
                // If server provided full HTML, isolate in shadow to avoid theme bleed
                if (tp && typeof tp.html === 'string' && tp.html.trim().length > 0 && !isPlaceholderHtml(tp.html)) {
                    const ins = insertServerInlineShadow(offerHTML, insertTarget);
                    container = ins && (ins.root || null);
                } else {
                    insertTarget.insertAdjacentHTML('beforebegin', offerHTML);
                    container = insertTarget.previousElementSibling;
                }
            }
            if (container) {
                trackEvent('offer_view', { surface: 'product_page', price: productInfo.price, category_tag: productInfo.category_tag });
                // Warm modal content/images in background for fast display later
                try { prefetchOfferModal(productInfo, theme, templates, pricingData, placements.learn_more === true); } catch {}
                let selected = false;
                let selectedPlan = null;
                const sessionHint = (pricingData && pricingData.session_hint) || '';
                // Do NOT pre-select a plan by default; also no decline by default
                try { localStorage.removeItem(`fp_declined:${productInfo.handle || productInfo.id}`); } catch {}
                // If server HTML provided, hydrate dynamic prices into it
                try { if (tp && typeof tp.html === 'string' && tp.html.trim().length > 0 && !isPlaceholderHtml(tp.html)) { hydrateTemplateProductPage(container, pricingData); } } catch {}
                
                // Execute the script_js content within the Shadow DOM
                if (tp && tp.script_js && typeof tp.script_js === 'string' && tp.script_js.trim()) {
                    try {
                        // Build a closure that aliases document/query within the shadow root
                        const bootstrap = new Function('root', `
                            (function(){
                                var document = root;
                                var shadowRoot = root;
                                var $ = function(sel){ return root.querySelector(sel); };
                                var $$ = function(sel){ return root.querySelectorAll(sel); };
                                try {
                                    ${tp.script_js}
                                } catch(e) { try { console.error('[FlexProtect] inline script error', e); } catch(_){} }
                            })();
                        `);
                        bootstrap(container);
                        fpLog('Inline offer script executed successfully in Shadow DOM');
                    } catch (e) {
                        fpLog('Failed to execute inline offer script in Shadow DOM:', e);
                    }
                }

                // Fallback: bind selection on generic ".option" templates if template script didn't wire
                try {
                    if (!container.__fp_click_bound) {
                        container.__fp_click_bound = true;
                        container.addEventListener('click', (ev)=>{
                            const opt = ev.target && ev.target.closest ? ev.target.closest('.option') : null;
                            if (!opt || (container.contains && !container.contains(opt))) return;
                            // visual classes
                            try { container.querySelectorAll('.option').forEach(x=>{ x.classList && x.classList.remove('selected'); x.classList && x.classList.remove('popular'); }); } catch{}
                            try { opt.classList && opt.classList.add('selected'); if (container.querySelectorAll('.option')[0] === opt) opt.classList.add('popular'); } catch{}
                            // extract term and price from either data-fp-* or template markup
                            let termRaw = opt.getAttribute('data-fp-term') || opt.getAttribute('data-term') || opt.getAttribute('data-option') || '';
                            let priceRaw = opt.getAttribute('data-fp-price') || (opt.querySelector('.price, .option-price') && opt.querySelector('.price, .option-price').textContent) || '';
                            // normalize values
                            let term = Number(String(termRaw).replace(/[^0-9]/g,'') || 0);
                            let price = Number(String(priceRaw).replace(/[^0-9.\-]/g,'') || 0);
                            if (!term && /2y|2yr|2 years?/i.test(String(termRaw))) term = 2;
                            if (!term && /3y|3yr|3 years?/i.test(String(termRaw))) term = 3;
                            if (!term) return;
                            if (!isFinite(price) || price <= 0) return;
                            opt.dispatchEvent(new CustomEvent('fp:selection', { bubbles: true, composed: true, detail: { term, price } }));
                        }, true);
                    }
                } catch {}
                
                // Listen for selection events from the inline offer (Shadow DOM)
                document.addEventListener('fp:selection', async (ev) => {
                    try {
                        // Check if the event originated from our inline offer's Shadow DOM
                        const shadowHost = container.host; // container is the ShadowRoot, so container.host is the host element
                        const originatedInOurShadowDom = ev.composedPath().includes(shadowHost);

                        if (!originatedInOurShadowDom) {
                            return;
                        }
                        
                        const det = ev.detail || {};
                        const term = Number(det.term || 0);
                        const priceSel = Number(det.price || 0);
                        
                        if (!term || !priceSel) return;
                        
                        // Update the selected state
                        selected = true;
                        selectedPlan = { term, price: priceSel };
                        
                        // Track the selection
                        trackEvent('offer_select', { surface: 'product_page', term, price: priceSel });
                        
                        // Remove declined state
                        try { localStorage.removeItem(declinedKey); } catch {}
                        ensureDeclineNotice(false);
                        
                        fpLog('Inline offer selection:', { term, price: priceSel });
                        
                    } catch (e) {
                        fpLog('Error handling inline offer selection:', e);
                    }
                }, true);

                // Decline notice helper (shows a subtle red banner when declined)
                const ensureDeclineNotice = (show) => {
                  try {
                    let n = container.querySelector('.fp-decline-notice');
                    if (show) {
                      if (!n) {
                        n = document.createElement('div');
                        n.className = 'fp-decline-notice';
                        n.style.cssText = 'margin-top:8px;color:#b91c1c;background:#fee2e2;border:1px solid #fecaca;border-radius:6px;padding:8px 10px;font-size:12px;';
                        n.textContent = "You chose to not add product protection to your purchase. If you've changed your mind, just select an option.";
                        container.appendChild(n);
                      } else {
                        n.style.display = 'block';
                      }
                    } else {
                      if (n) n.style.display = 'none';
                    }
                  } catch {}
                };
                // Show notice immediately if previously declined for this product
                if (localStorage.getItem(declinedKey)) ensureDeclineNotice(true);
                container.addEventListener('click', (ev) => {
                  const termBtn = ev.target && ev.target.closest ? ev.target.closest('[data-fp-term]') : null;
                  if (termBtn && container.contains(termBtn)) {
                    const term = Number(termBtn.getAttribute('data-fp-term'));
                    const priceSel = Number(termBtn.getAttribute('data-fp-price'));
                    // Toggle behavior: if already selected, de-select
                    if (selected && selectedPlan && selectedPlan.term === term) {
                      selected = false;
                      selectedPlan = null;
                      container.querySelectorAll('[data-fp-term]').forEach(b=>{ try { b.style.outline='none'; b.style.boxShadow='none'; b.style.borderColor=''; b.classList && b.classList.remove('active'); b.setAttribute && b.setAttribute('aria-pressed','false'); } catch {} });
            return;
        }
                    selectedPlan = { term, price: priceSel };
                    selected = true;
                    try { localStorage.removeItem(declinedKey); } catch {}
                    ensureDeclineNotice(false);
                    // Visual selection with glow
                    container.querySelectorAll('[data-fp-term]').forEach(b=>{ try { b.style.outline = 'none'; b.style.boxShadow = 'none'; b.style.borderColor=''; b.classList && b.classList.remove('active'); b.setAttribute && b.setAttribute('aria-pressed','false'); } catch {} });
                    try {
                      const c = theme?.buttonColor || '#2563eb';
                      termBtn.style.borderColor = c; termBtn.style.boxShadow = '0 0 0 4px rgba(37,99,235,.25)';
                      termBtn.classList && termBtn.classList.add('active'); termBtn.setAttribute && termBtn.setAttribute('aria-pressed','true');
                    } catch {}
                    trackEvent('offer_select', { surface: 'product_page', term, price: priceSel });
                    return;
                  }
                  const declineBtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                  if (declineBtn && container.contains(declineBtn)) {
                    trackEvent('offer_decline', { surface: 'product_page' });
                    localStorage.setItem(declinedKey, '1');
                    // Keep the inline offer visible; show notice; no modal will show due to declined flag
                    ensureDeclineNotice(true);
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
                        let html = '';
                        const tm = templates['offer_modal'] || {};
                        if (tm && typeof tm.html === 'string' && tm.html.trim().length > 0 && !isPlaceholderHtml(tm.html)) {
                          html = tm.html;
                          fpLog('Using server HTML for modal, length:', html.length);
                        } else {
                          html = (window.__FP_PREFETCH && window.__FP_PREFETCH.offer_modal) || createWarrantyOffer('offer_modal', productInfo, pricingData2, theme, templates['offer_modal'], placements.learn_more === true);
                          fpLog('Using fallback HTML for modal, length:', html.length);
                        }
                        let modal = null; let mcontainer = null; let cleanup = () => { try { modal && modal.remove(); } catch {} };
                        // Remove any existing modals before inserting new one
                        removeExistingModals();
                        
                        if (typeof html === 'string' && html.indexOf('flexprotect-modal-container') !== -1) {
                          fpLog('Inserting server modal HTML');
                          const ins = insertServerModalShadow(html, tm.script_js);
                          mcontainer = ins.mcontainer; cleanup = ins.cleanup;
                          fpLog('Modal container found:', mcontainer);
                          try { hydrateModalSelector(mcontainer, pricingData2); } catch {}
                          // Ensure modal is visible and properly positioned
                          if (mcontainer) {
                            try {
                              const overlay = mcontainer.querySelector('.modal-overlay');
                              if (overlay) {
                                overlay.style.zIndex = '2147483647';
                                overlay.style.display = 'flex';
                                overlay.style.position = 'fixed';
                                overlay.style.inset = '0';
                                fpLog('Modal overlay positioned');
                              }
                            } catch {}
                          }
                        } else {
                          modal = document.createElement('div');
                          modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:2147483647;';
                          modal.innerHTML = `<div style=\"max-width:820px;width:95%;background:#fff;border-radius:12px;padding:12px;box-shadow:0 10px 30px rgba(0,0,0,.2);\">${html}</div>`;
                          document.body.appendChild(modal);
                          mcontainer = modal.querySelector('.flex-warranty-offer');
                        }
                        trackEvent('offer_view', { surface: 'offer_modal', price: productInfo.price, category_tag: productInfo.category_tag });
                        try { const selRoot = mcontainer.querySelector('[data-fp-selector]'); if (selRoot) wireSelectorBehavior(selRoot); } catch {}
                        try { wireServerModalClose(mcontainer, cleanup); } catch {}
                        try {
                          mcontainer.addEventListener('fp:selection', async (ev) => {
                            const det = (ev && ev.detail) || {}; const term = Number(det.term || det.Term || 0); const priceSel = Number(det.price || det.Price || 0);
                            if (!term || !priceSel) return;
                            trackEvent('offer_select', { surface: 'offer_modal', term, price: priceSel });
                            let currentVar2 = null; try { currentVar2 = form.querySelector('[name="id"]')?.value || null; } catch {}
                            const parentGidForAdd2 = currentVar2 ? `gid://shopify/ProductVariant/${Number(currentVar2)}` : parentVariantGid;
                            await selectAndAddToCart(sessionToken, priceSel, term, pj.id, parentGidForAdd2, sessionHint);
                            cleanup();
                          }, { once: false });
                        } catch {}
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
                            cleanup();
                            return;
                          }
                          const dbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                          if (dbtn && mcontainer.contains(dbtn)) {
                            trackEvent('offer_decline', { surface: 'offer_modal' });
                            localStorage.setItem(declinedKey, '1');
                            cleanup();
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
                              let html = '';
                              const tm = templates['offer_modal'] || {};
                              if (tm && typeof tm.html === 'string' && tm.html.trim().length > 0 && !isPlaceholderHtml(tm.html)) {
                                html = tm.html;
                              } else {
                                html = (window.__FP_PREFETCH && window.__FP_PREFETCH.offer_modal) || createWarrantyOffer('offer_modal', productInfo, pricingData, theme, templates['offer_modal']);
                              }
                              let modal = null; let mcontainer = null; let cleanup = () => { try { modal && modal.remove(); } catch {} };
                              // Remove any existing modals before inserting new one
                              removeExistingModals();
                              
                              if (typeof html === 'string' && html.indexOf('flexprotect-modal-container') !== -1) {
                                const ins = insertServerModalShadow(html, tm.script_js);
                                mcontainer = ins.mcontainer; cleanup = ins.cleanup;
                                try { hydrateModalSelector(mcontainer, pricingData); } catch {}
                                // Ensure modal is visible without fallback logic
                                ensureModalVisibleOrFallback(mcontainer, html);
                              } else {
                                modal = document.createElement('div');
                                modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999;';
                                modal.innerHTML = `<div style=\"max-width:820px;width:95%;background:#fff;border-radius:12px;padding:12px;box-shadow:0 10px 30px rgba(0,0,0,.2);\">${html}</div>`;
                                document.body.appendChild(modal);
                                mcontainer = modal.querySelector('.flex-warranty-offer');
                              }
                              trackEvent('offer_view', { surface: 'offer_modal', price: productInfo.price, category_tag: productInfo.category_tag });
                              try { const selRoot = mcontainer.querySelector('[data-fp-selector]'); if (selRoot) wireSelectorBehavior(selRoot); } catch {}
                              try { wireServerModalClose(mcontainer, cleanup); } catch {}
                              try { mcontainer.addEventListener('fp:selection', async (ev) => {
                                  const det = (ev && ev.detail) || {}; const term = Number(det.term || det.Term || 0); const priceSel = Number(det.price || det.Price || 0);
                                  if (!term || !priceSel) return;
                                  trackEvent('offer_select', { surface: 'offer_modal', term, price: priceSel });
                                  let currentVar2 = null; try { currentVar2 = form.querySelector('[name="id"]')?.value || null; } catch {}
                                  const parentGidForAdd2 = currentVar2 ? `gid://shopify/ProductVariant/${Number(currentVar2)}` : parentVariantGid;
                                  await selectAndAddToCart(sessionToken, priceSel, term, pj.id, parentGidForAdd2, sessionHint);
                                  cleanup();
                                }, { once: false }); } catch {}
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
                                  cleanup();
                                  return;
                                }
                                const dbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                                if (dbtn && mcontainer.contains(dbtn)) {
                                  trackEvent('offer_decline', { surface: 'offer_modal' });
                                  localStorage.setItem(declinedKey, '1');
                                  cleanup();
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
                                let html = '';
                                const tm = templates['offer_modal'] || {};
                                if (tm && typeof tm.html === 'string' && tm.html.trim().length > 0 && !isPlaceholderHtml(tm.html)) {
                                  html = tm.html;
        } else {
                                  html = (window.__FP_PREFETCH && window.__FP_PREFETCH.offer_modal) || createWarrantyOffer('offer_modal', productInfo, pricingData || (await getWarrantyPricing(productInfo, sessionToken)), theme, templates['offer_modal']);
                                }
                                let modal = null; let mcontainer = null; let cleanup = () => { try { modal && modal.remove(); } catch {} };
                                // Remove any existing modals before inserting new one
                                removeExistingModals();
                                
                                if (typeof html === 'string' && html.indexOf('flexprotect-modal-container') !== -1) {
                                  const ins = insertServerModalShadow(html, tm.script_js);
                                  mcontainer = ins.mcontainer; cleanup = ins.cleanup;
                                  try { hydrateModalSelector(mcontainer, pricingData || (await getWarrantyPricing(productInfo, sessionToken))); } catch {}
                                  // Ensure modal is visible without fallback logic
                                  ensureModalVisibleOrFallback(mcontainer, html);
                                } else {
                                  modal = document.createElement('div');
                                  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999;';
                                  modal.innerHTML = `<div style=\"max-width:820px;width:95%;background:#fff;border-radius:12px;padding:12px;box-shadow:0 10px 30px rgba(0,0,0,.2);\">${html}</div>`;
                                  document.body.appendChild(modal);
                                  mcontainer = modal.querySelector('.flex-warranty-offer');
                                }
                                trackEvent('offer_view', { surface: 'offer_modal', price: productInfo.price, category_tag: productInfo.category_tag });
                                try { const selRoot = mcontainer.querySelector('[data-fp-selector]'); if (selRoot) wireSelectorBehavior(selRoot); } catch {}
                                try { wireServerModalClose(mcontainer, cleanup); } catch {}
                                try { mcontainer.addEventListener('fp:selection', async (ev) => {
                                    const det = (ev && ev.detail) || {}; const term = Number(det.term || det.Term || 0); const priceSel = Number(det.price || det.Price || 0);
                                    if (!term || !priceSel) return;
                                    trackEvent('offer_select', { surface: 'offer_modal', term, price: priceSel });
                                    let currentVar4 = null; try { currentVar4 = document.querySelector('[data-product-form] form [name="id"], form[action*="/cart/add"] [name="id"], form[action="/cart/add"] [name="id"]').value || null; } catch {}
                                    const parentGidForAdd4 = currentVar4 ? `gid://shopify/ProductVariant/${Number(currentVar4)}` : parentVariantGid;
                                    await selectAndAddToCart(sessionToken, priceSel, term, pj.id, parentGidForAdd4, sessionHint);
                                    cleanup();
                                  }, { once: false }); } catch {}
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
                                    cleanup();
                                    return;
                                  }
                                  const dbtn = ev.target && ev.target.closest ? ev.target.closest('button[data-fp-decline]') : null;
                                  if (dbtn && mcontainer.contains(dbtn)) {
                                    trackEvent('offer_decline', { surface: 'offer_modal' });
                                    localStorage.setItem(declinedKey, '1');
                                    cleanup();
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
                        const html = createWarrantyOffer('offer_modal', productInfo, pricingData, theme, templates['offer_modal'], placements.learn_more === true);
                        const modal = document.createElement('div');
                        modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:9999;';
                        modal.innerHTML = `<div style="max-width:820px;width:95%;background:#fff;border-radius:12px;padding:12px;box-shadow:0 10px 30px rgba(0,0,0,.2);">${html}</div>`;
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
            document.addEventListener('DOMContentLoaded', () => { 
                try { hookCartWatchers(); } catch {} 
                try { handleWarrantyProductPage(); } catch {}
            });
        } else { 
            try { hookCartWatchers(); } catch {} 
            try { handleWarrantyProductPage(); } catch {}
        }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWarrantyOffer);
    } else {
        initWarrantyOffer();
        }
    }
    
})(); 