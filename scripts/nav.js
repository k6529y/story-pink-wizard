/**
 * ピンク髪の魔法使い - ナビゲーション & 動的コンテンツ読み込み
 * stories/index.json からエピソード一覧を取得する方式
 */

document.addEventListener('DOMContentLoaded', function() {
    loadEpisodeData();
});

function loadEpisodeData() {
    // index.json からエピソード一覧を取得
    fetch('stories/index.json')
        .then(response => {
            if (!response.ok) throw new Error('index.json not found');
            return response.json();
        })
        .then(data => {
            const episodes = data.episodes || [];
            if (episodes.length === 0) {
                showNoContent();
                return;
            }
            // 降順にソート（最新話が先頭）
            const sorted = [...episodes].sort((a, b) => b.number - a.number);
            renderLatestStory(sorted[0]);
            renderEpisodesList([...episodes].sort((a, b) => a.number - b.number));
        })
        .catch(err => {
            console.warn('Failed to load index.json:', err);
            showNoContent();
        });
}

function renderLatestStory(episode) {
    const latestStoryDiv = document.getElementById('latest-story');
    if (!latestStoryDiv) return;

    latestStoryDiv.innerHTML = `
        <div style="text-align: center; padding: 1rem 0 1.5rem;">
            <p style="color: #ff1493; font-size: 1.2rem; font-weight: bold; margin-bottom: 0.4rem;">
                最新エピソード: 第${episode.number}話
            </p>
            <p style="color: #888; font-size: 0.9rem; margin-bottom: 1.5rem;">
                ${episode.published} 公開
            </p>
            <a href="stories/${episode.file}" style="
                display: inline-block;
                padding: 0.9rem 2.5rem;
                background: linear-gradient(135deg, #ff69b4, #ff1493);
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 1.05rem;
                transition: all 0.3s;
                box-shadow: 0 2px 8px rgba(255, 20, 147, 0.25);
            "
            onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(255, 20, 147, 0.4)';"
            onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 8px rgba(255, 20, 147, 0.25)';">
                第${episode.number}話を読む
            </a>
        </div>
    `;
}

function renderEpisodesList(episodes) {
    const episodesListDiv = document.getElementById('episodes-list');
    if (!episodesListDiv) return;

    episodesListDiv.innerHTML = '';
    episodes.forEach(episode => {
        const card = document.createElement('a');
        card.href = `stories/${episode.file}`;
        card.className = 'episode-card';
        card.innerHTML = `
            <div class="number">第${episode.number}話</div>
            <p style="font-size: 0.85rem; color: #999; margin-top: 0.3rem;">${episode.published}</p>
        `;
        episodesListDiv.appendChild(card);
    });
}

function showNoContent() {
    const latestStoryDiv = document.getElementById('latest-story');
    const episodesListDiv = document.getElementById('episodes-list');
    if (latestStoryDiv) latestStoryDiv.innerHTML = '<p style="color:#999; text-align:center; padding:1rem;">最新話を準備中...</p>';
    if (episodesListDiv) episodesListDiv.innerHTML = '<p style="color:#999; text-align:center; padding:1rem;">ストーリーを準備中...</p>';
}
