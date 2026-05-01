/**
 * ピンク髪の魔法使い - インデックスページ動的読み込み
 */

document.addEventListener('DOMContentLoaded', () => {
    fetch('stories/index.json')
        .then(r => r.ok ? r.json() : Promise.reject('no index'))
        .then(data => {
            const episodes = data.episodes || [];
            if (!episodes.length) return showEmpty();
            const sortedDesc = [...episodes].sort((a, b) => b.number - a.number);
            const sortedAsc  = [...episodes].sort((a, b) => a.number - b.number);
            renderHeroBg(sortedDesc[0]);
            renderLatest(sortedDesc[0]);
            renderEpisodeList(sortedAsc);
        })
        .catch(err => {
            console.warn(err);
            showEmpty();
        });
});

function thumbPath(ep) {
    return ep.has_image ? `stories/images/${String(ep.number).padStart(3, '0')}.jpg` : null;
}

function renderHeroBg(latest) {
    const heroBg = document.getElementById('hero-bg');
    const heroCta = document.getElementById('hero-cta');
    const t = thumbPath(latest);
    if (heroBg && t) heroBg.style.backgroundImage = `url('${t}')`;
    if (heroCta) heroCta.href = `stories/${latest.file}`;
}

function renderLatest(ep) {
    const el = document.getElementById('latest-story');
    if (!el) return;
    const thumb = thumbPath(ep);
    el.innerHTML = `
        <a href="stories/${ep.file}" class="episode-card fade-in" style="max-width: 640px;">
            ${thumb
                ? `<div class="thumb" style="background-image:url('${thumb}'); aspect-ratio: 21/9;"></div>`
                : `<div class="thumb-fallback" style="aspect-ratio: 21/9;">第${ep.number}話</div>`}
            <div class="body" style="padding: 1.6rem 1.8rem;">
                <div class="num">EP. ${String(ep.number).padStart(3, '0')}</div>
                <div class="title" style="font-size: 1.4rem;">${ep.title}</div>
                <div class="date">${ep.published} 公開</div>
            </div>
        </a>
    `;
}

function renderEpisodeList(eps) {
    const el = document.getElementById('episodes-list');
    if (!el) return;
    el.innerHTML = '';
    eps.forEach((ep, i) => {
        const t = thumbPath(ep);
        const card = document.createElement('a');
        card.href = `stories/${ep.file}`;
        card.className = 'episode-card';
        card.style.animationDelay = `${i * 60}ms`;
        card.classList.add('fade-in');
        card.innerHTML = `
            ${t
                ? `<div class="thumb" style="background-image:url('${t}');"></div>`
                : `<div class="thumb-fallback">第${ep.number}話</div>`}
            <div class="body">
                <div class="num">EP. ${String(ep.number).padStart(3, '0')}</div>
                <div class="title">${ep.title}</div>
                <div class="date">${ep.published}</div>
            </div>
        `;
        el.appendChild(card);
    });
}

function showEmpty() {
    const latest = document.getElementById('latest-story');
    const list   = document.getElementById('episodes-list');
    if (latest) latest.innerHTML = '<div class="loading">準備中...</div>';
    if (list)   list.innerHTML   = '<div class="loading">準備中...</div>';
}
