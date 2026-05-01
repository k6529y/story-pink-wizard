/**
 * 個別話ページ用 JS
 * - 読書進捗バー (上部)
 * - ヘッダー hide-on-scroll
 */
(() => {
    const header = document.querySelector('.site-header');
    const progress = document.querySelector('.reading-progress');
    let lastY = window.scrollY;

    function update() {
        const y = window.scrollY;
        const docH = document.documentElement.scrollHeight - window.innerHeight;
        const ratio = docH > 0 ? Math.min(1, Math.max(0, y / docH)) : 0;
        if (progress) progress.style.width = (ratio * 100).toFixed(2) + '%';

        if (header) {
            // 下スクロールで隠す・上スクロールで出す
            if (y > 120 && y > lastY) header.classList.add('hidden');
            else header.classList.remove('hidden');
        }
        lastY = y;
    }

    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
})();
