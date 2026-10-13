// Main UI & Shared Utilities

document.addEventListener('DOMContentLoaded', () => {
  // ========== Sidebar Management ==========
  const menuToggle = document.getElementById('menuToggle');
  const appSidebar = document.getElementById('appSidebar');
  const appWrapper = document.querySelector('.app-wrapper');
  const SIDEBAR_STORAGE_KEY = 'sidebarState';
  const MOBILE_BREAKPOINT = 900;
  
  // Create overlay and close button
  const createSidebarOverlay = () => {
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.id = 'sidebarOverlay';
    document.body.appendChild(overlay);
    return overlay;
  };
  
  const createCloseButton = () => {
    const btn = document.createElement('button');
    btn.className = 'sidebar-close-btn';
    btn.id = 'sidebarCloseBtn';
    btn.setAttribute('aria-label', 'Close navigation');
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
    return btn;
  };
  
  const sidebarOverlay = createSidebarOverlay();
  const closeBtn = createCloseButton();
  
  if (appSidebar) {
    appSidebar.insertBefore(closeBtn, appSidebar.firstChild);
  }
  
  // Get sidebar state from storage
  const getSidebarState = () => {
    const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY);
    if (stored) return JSON.parse(stored);
    return { isCollapsed: false };
  };
  
  // Save sidebar state to storage
  const saveSidebarState = (state) => {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, JSON.stringify(state));
  };
  
  // Initialize sidebar from saved state
  const initSidebar = () => {
    const state = getSidebarState();
    const isMobile = window.innerWidth <= MOBILE_BREAKPOINT;
    
    if (!isMobile && state.isCollapsed) {
      appSidebar.classList.add('collapsed');
    } else {
      appSidebar.classList.remove('collapsed');
    }
  };
  
  // Open sidebar (mobile)
  const openSidebar = () => {
    appSidebar.classList.add('open');
    sidebarOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  };
  
  // Close sidebar (mobile)
  const closeSidebar = () => {
    appSidebar.classList.remove('open');
    sidebarOverlay.classList.remove('active');
    document.body.style.overflow = '';
  };
  
  // Toggle sidebar collapse (desktop)
  const toggleSidebarCollapse = () => {
    const isMobile = window.innerWidth <= MOBILE_BREAKPOINT;
    if (isMobile) return;
    
    appSidebar.classList.toggle('collapsed');
    const isCollapsed = appSidebar.classList.contains('collapsed');
    saveSidebarState({ isCollapsed });
  };
  
  // Menu toggle button - opens on mobile, toggles collapse on desktop
  if (menuToggle && appSidebar) {
    menuToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const isMobile = window.innerWidth <= MOBILE_BREAKPOINT;
      
      if (isMobile) {
        const isOpen = appSidebar.classList.contains('open');
        if (isOpen) {
          closeSidebar();
        } else {
          openSidebar();
        }
      } else {
        toggleSidebarCollapse();
      }
    });
  }
  
  // Close button (mobile only)
  if (closeBtn && appSidebar) {
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeSidebar();
    });
  }
  
  // Overlay click closes sidebar
  if (sidebarOverlay && appSidebar) {
    sidebarOverlay.addEventListener('click', (e) => {
      e.stopPropagation();
      closeSidebar();
    });
  }
  
  // ESC key closes sidebar
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && appSidebar && appSidebar.classList.contains('open')) {
      closeSidebar();
    }
  });
  
  // Sidebar links close mobile sidebar
  const navLinks = appSidebar.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      const isMobile = window.innerWidth <= MOBILE_BREAKPOINT;
      if (isMobile && appSidebar.classList.contains('open')) {
        closeSidebar();
      }
    });
  });
  
  // Handle window resize
  window.addEventListener('resize', () => {
    const isMobile = window.innerWidth <= MOBILE_BREAKPOINT;
    if (isMobile) {
      closeSidebar();
    } else {
      sidebarOverlay.classList.remove('active');
      appSidebar.classList.remove('open');
    }
  });
  
  // Initialize sidebar on load
  initSidebar();

  // Sample data loading triggers
  const sampleButtons = ['btnLoadSample', 'btnEmptyLoadSample', 'btnLoadSampleInline'];
  sampleButtons.forEach(btnId => {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const originalText = btn.innerHTML;
        btn.innerHTML = 'Loading Sample Data...';
        btn.disabled = true;

        try {
          const res = await fetch('/api/load-sample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });
          const data = await res.json();
          if (data.success) {
            window.location.href = data.redirect_url;
          } else {
            alert('Error loading sample data: ' + (data.error || 'Unknown error'));
            btn.innerHTML = originalText;
            btn.disabled = false;
          }
        } catch (err) {
          alert('Network error while loading sample dataset: ' + err.message);
          btn.innerHTML = originalText;
          btn.disabled = false;
        }
      });
    }
  });
});

// Multi-Currency Engine & Formatter Definitions
window.SUPPORTED_CURRENCIES = {
  'USD': { code: 'USD', symbol: '$', name: 'US Dollar ($)', flag: '🇺🇸', position: 'prefix' },
  'EUR': { code: 'EUR', symbol: '€', name: 'Euro (€)', flag: '🇪🇺', position: 'prefix' },
  'GBP': { code: 'GBP', symbol: '£', name: 'British Pound (£)', flag: '🇬🇧', position: 'prefix' },
  'JPY': { code: 'JPY', symbol: '¥', name: 'Japanese Yen (¥)', flag: '🇯🇵', position: 'prefix' },
  'INR': { code: 'INR', symbol: '₹', name: 'Indian Rupee (₹)', flag: '🇮🇳', position: 'prefix' },
  'CAD': { code: 'CAD', symbol: 'CA$', name: 'Canadian Dollar (CA$)', flag: '🇨🇦', position: 'prefix' },
  'AUD': { code: 'AUD', symbol: 'A$', name: 'Australian Dollar (A$)', flag: '🇦🇺', position: 'prefix' },
  'CHF': { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc (CHF)', flag: '🇨🇭', position: 'prefix' },
  'CNY': { code: 'CNY', symbol: 'CN¥', name: 'Chinese Yuan (CN¥)', flag: '🇨🇳', position: 'prefix' },
  'BRL': { code: 'BRL', symbol: 'R$', name: 'Brazilian Real (R$)', flag: '🇧🇷', position: 'prefix' },
  'MXN': { code: 'MXN', symbol: 'Mex$', name: 'Mexican Peso (Mex$)', flag: '🇲🇽', position: 'prefix' },
  'SGD': { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar (S$)', flag: '🇸🇬', position: 'prefix' },
  'AED': { code: 'AED', symbol: 'AED', name: 'UAE Dirham (AED)', flag: '🇦🇪', position: 'prefix' },
  'KRW': { code: 'KRW', symbol: '₩', name: 'South Korean Won (₩)', flag: '🇰🇷', position: 'prefix' },
  'SEK': { code: 'SEK', symbol: 'kr', name: 'Swedish Krona (kr)', flag: '🇸🇪', position: 'suffix' },
  'NZD': { code: 'NZD', symbol: 'NZ$', name: 'New Zealand Dollar (NZ$)', flag: '🇳🇿', position: 'prefix' },
  'ZAR': { code: 'ZAR', symbol: 'R', name: 'South African Rand (R)', flag: '🇿🇦', position: 'prefix' }
};

function getCurrentCurrencyCode() {
  if (window.APP_CURRENCY && window.APP_CURRENCY.code) {
    return window.APP_CURRENCY.code.toUpperCase();
  }
  const stored = localStorage.getItem('selected_currency');
  if (stored && window.SUPPORTED_CURRENCIES[stored.toUpperCase()]) {
    return stored.toUpperCase();
  }
  return 'USD';
}

function getCurrentCurrency() {
  const code = getCurrentCurrencyCode();
  return window.SUPPORTED_CURRENCIES[code] || window.SUPPORTED_CURRENCIES['USD'];
}

function getCurrencySymbol(currencyCode) {
  const code = (currencyCode || getCurrentCurrencyCode()).toUpperCase();
  const info = window.SUPPORTED_CURRENCIES[code] || window.SUPPORTED_CURRENCIES['USD'];
  return info.symbol;
}

function formatCurrency(val, currencyCode) {
  const code = (currencyCode || getCurrentCurrencyCode()).toUpperCase();
  const info = window.SUPPORTED_CURRENCIES[code] || window.SUPPORTED_CURRENCIES['USD'];
  const num = parseFloat(val);
  if (isNaN(num)) {
    const pos = info.position || 'prefix';
    const sym = info.symbol;
    const sep = (sym.length >= 3 && !sym.endsWith('$')) ? ' ' : '';
    return pos === 'suffix' ? '0.00 ' + sym : sym + sep + '0.00';
  }

  const isNegative = num < 0;
  const absVal = Math.abs(num);
  const formattedNum = absVal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const symbol = info.symbol;
  const pos = info.position || 'prefix';

  let res;
  if (pos === 'suffix') {
    res = `${formattedNum} ${symbol}`;
  } else {
    const sep = (symbol.length >= 3 && !symbol.endsWith('$')) ? ' ' : '';
    res = `${symbol}${sep}${formattedNum}`;
  }
  return isNegative ? `-${res}` : res;
}

function formatCurrencyShort(val, currencyCode) {
  const code = (currencyCode || getCurrentCurrencyCode()).toUpperCase();
  const info = window.SUPPORTED_CURRENCIES[code] || window.SUPPORTED_CURRENCIES['USD'];
  const num = parseFloat(val);
  if (isNaN(num)) return '0';

  const isNegative = num < 0;
  const absVal = Math.abs(num);
  let numStr;
  if (absVal >= 1000000) {
    numStr = (absVal / 1000000).toFixed(1).replace('.0', '') + 'M';
  } else if (absVal >= 1000) {
    numStr = (absVal / 1000).toFixed(0) + 'k';
  } else {
    numStr = absVal.toFixed(0);
  }

  const symbol = info.symbol;
  const pos = info.position || 'prefix';
  let res;
  if (pos === 'suffix') {
    res = `${numStr} ${symbol}`;
  } else {
    const sep = (symbol.length >= 3 && !symbol.endsWith('$')) ? ' ' : '';
    res = `${symbol}${sep}${numStr}`;
  }
  return isNegative ? `-${res}` : res;
}

function formatNumber(val) {
  const num = parseFloat(val);
  if (isNaN(num)) return '0';
  return num.toLocaleString('en-US');
}

async function setCurrentCurrency(code) {
  const upperCode = (code || 'USD').toUpperCase();
  if (!window.SUPPORTED_CURRENCIES[upperCode]) return;

  localStorage.setItem('selected_currency', upperCode);
  document.cookie = `selected_currency=${upperCode}; path=/; max-age=31536000; SameSite=Lax`;
  if (window.APP_CURRENCY) {
    window.APP_CURRENCY = {
      code: upperCode,
      ...window.SUPPORTED_CURRENCIES[upperCode]
    };
  }

  try {
    await fetch('/api/currency', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ currency: upperCode })
    });
  } catch (e) {
    console.warn('Failed to sync currency to backend', e);
  }

  window.dispatchEvent(new CustomEvent('currencyChanged', {
    detail: { currency: upperCode, info: window.SUPPORTED_CURRENCIES[upperCode] }
  }));
}

function showCurrencyToast(message) {
  let toast = document.getElementById('currencyToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'currencyToast';
    toast.className = 'currency-toast';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg><span>${message}</span>`;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2200);
}
