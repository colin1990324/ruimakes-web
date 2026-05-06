---
// 多语言切换逻辑客户端脚本
// 检测 URL 参数 ?lang=zh 或 ?lang=en
// 自动切换页面语言
// 提供手动切换按钮

function initI18n() {
  const url = new URL(window.location.href);
  const lang = url.searchParams.get('lang') || 'zh';
  
  // 检测并应用语言
  applyLang(lang);
  
  // 监听语言切换事件
  window.addEventListener('lang-change', (e) => {
    applyLang(e.detail.lang);
  });
}

function applyLang(lang) {
  // 存储当前语言
  localStorage.setItem('ruimakes-lang', lang);
  
  // 更新静态文本（如果有 data-i18n 属性）
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    const text = i18nData[lang]?.[key];
    if (text) {
      el.textContent = text;
    }
  });
}

function switchLang(lang) {
  const url = new URL(window.location.href);
  url.searchParams.set('lang', lang);
  window.location.href = url.toString();
}

// i18n 静态文本映射
const i18nData = {
  zh: {
    'nav.workbench': '工作站',
    'nav.toolstorage': '工具收纳',
    'nav.contact': '联系',
    'hero.cta': '咨询购买',
    'design.title': '设计理念',
    'gallery.title': '产品图赏',
    'specs.title': '规格参数',
    'dimensions': '外尺寸',
  },
  en: {
    'nav.workbench': 'Workstation',
    'nav.toolstorage': 'Tool Storage',
    'nav.contact': 'Contact',
    'hero.cta': 'Contact to Buy',
    'design.title': 'Design Concept',
    'gallery.title': 'Product Gallery',
    'specs.title': 'Specifications',
    'dimensions': 'Dimensions',
  }
};

// 自动检测浏览器语言
function detectBrowserLang() {
  const browserLang = navigator.language.slice(0, 2);
  const storedLang = localStorage.getItem('ruimakes-lang');
  
  if (storedLang) return storedLang;
  if (browserLang === 'en') return 'en';
  return 'zh';
}

// 初始化
if (typeof window !== 'undefined') {
  initI18n();
}