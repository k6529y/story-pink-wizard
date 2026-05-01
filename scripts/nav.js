/**
 * ピンク髪の魔法使い ─ インデックスページ動的読み込み
 * - story_config.json から章定義を取得
 * - stories/index.json からエピソード一覧を取得
 * - 章ごとにグルーピングして表示
 */

const KANJI_CHAPTERS = ['第一章', '第二章', '第三章', '第四章', '第五章', '第六章', '第七章', '第八章', '第九章', '第十章'];

document.addEventListener('DOMContentLoaded', () => {
    Promise.all([
        fetch('stories/index.json').then(r => r.ok ? r.json() : { episodes: [] }),
        fetch('story_config.json').then(r => r.ok ? r.json() : null).catch(() => null)
    ])
    .then(([idx, config]) => {
        const episodes = idx.episodes || [];
        const arcs = (config && config.story_arcs) ? config.story_arcs : [];

        if (!episodes.length) {
            renderEmpty();
            renderChapterStructure(arcs, []);
            return;
        }

        const sortedDesc = [...episodes].sort((a, b) => b.number - a.number);
        const latest = sortedDesc[0];
        renderHeroBg(latest);
        renderLatest(latest);
        renderChapterStructure(arcs, episodes);
    })
    .catch(err => {
        console.warn(err);
        renderEmpty();
    });
});

function thumbPath(ep) {
    return ep.has_image
        ? `stories/images/${String(ep.number).padStart(3, '0')}.jpg`
        : null;
}

function renderHeroBg(latest) {
    const heroBg  = document.getElementById('hero-bg');
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
        <a href="stories/${ep.file}" class="episode-card latest-card fade-in">
            ${thumb
                ? `<div class="thumb" style="background-image:url('${thumb}');"></div>`
                : `<div class="thumb-fallback">第${ep.number}話</div>`}
            <div class="body">
                <div class="num">第 ${ep.number} 話</div>
                <div class="title">${ep.title}</div>
                <div class="date">${ep.published} 公開</div>
            </div>
        </a>
    `;
}

function renderChapterStructure(arcs, episodes) {
    const root = document.getElementById('episodes-list');
    if (!root) return;
    root.innerHTML = '';

    // 章定義がない場合は単一リストで表示
    if (!arcs.length) {
        const grid = document.createElement('div');
        grid.className = 'episodes-grid';
        episodes.sort((a, b) => a.number - b.number).forEach((ep, i) => {
            grid.appendChild(makeEpisodeCard(ep, i));
        });
        root.appendChild(grid);
        return;
    }

    // 章ごとに分類
    arcs.forEach((arc, idx) => {
        const [from, to] = arc.episodes;
        const chapEpisodes = episodes
            .filter(e => e.number >= from && e.number <= to)
            .sort((a, b) => a.number - b.number);

        const section = document.createElement('div');
        section.className = 'chapter-section';

        // 章ヘッダー
        const divider = document.createElement('div');
        divider.className = 'chapter-divider';
        const chapKanji = KANJI_CHAPTERS[idx] || `第${idx + 1}章`;
        // タイトルは「第一章：目覚め」形式から「目覚め」だけ抽出
        const cleanTitle = (arc.title || '').replace(/^第[一二三四五六七八九十0-9]+章[：:]\s*/, '');
        divider.innerHTML = `
            <span class="ornament">✦</span>
            <span class="chapter-num">${chapKanji}</span>
            <span class="chapter-name">${cleanTitle}</span>
            <span class="chapter-range">第${from}話 ─ 第${to}話</span>
            <span class="line"></span>
        `;
        section.appendChild(divider);

        // エピソードグリッド
        const grid = document.createElement('div');
        grid.className = 'episodes-grid';

        if (chapEpisodes.length === 0) {
            const msg = document.createElement('div');
            msg.className = 'empty-chapter-msg';
            msg.textContent = '── 公開予定 ──';
            grid.classList.add('empty-chapter');
            grid.appendChild(msg);
        } else {
            chapEpisodes.forEach((ep, i) => {
                grid.appendChild(makeEpisodeCard(ep, i));
            });
        }

        section.appendChild(grid);
        root.appendChild(section);
    });
}

function makeEpisodeCard(ep, i) {
    const t = thumbPath(ep);
    const card = document.createElement('a');
    card.href = `stories/${ep.file}`;
    card.className = 'episode-card fade-in';
    card.style.animationDelay = `${i * 50}ms`;
    card.innerHTML = `
        ${t
            ? `<div class="thumb" style="background-image:url('${t}');"></div>`
            : `<div class="thumb-fallback">第${ep.number}話</div>`}
        <div class="body">
            <div class="num">第 ${ep.number} 話</div>
            <div class="title">${ep.title}</div>
            <div class="date">${ep.published}</div>
        </div>
    `;
    return card;
}

function renderEmpty() {
    const latest = document.getElementById('latest-story');
    if (latest) latest.innerHTML = '<div class="loading">準備中</div>';
}
