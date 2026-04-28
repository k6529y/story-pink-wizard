/**
 * ピンク髪の魔法使い - ナビゲーション & 動的コンテンツ読み込み
 */

document.addEventListener('DOMContentLoaded', function() {
    loadLatestStory();
    loadEpisodesList();
});

function loadLatestStory() {
    const latestStoryDiv = document.getElementById('latest-story');

    // stories/ ディレクトリを読み込む
    fetch('stories/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load stories directory');
            }
            return response.text();
        })
        .then(html => {
            // HTML パースして HTML ファイルリストを取得
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const links = Array.from(doc.querySelectorAll('a'));
            const htmlFiles = links
                .map(a => a.getAttribute('href'))
                .filter(href => href && href.match(/^\d{3}\.html$/))
                .sort()
                .reverse();

            if (htmlFiles.length === 0) {
                latestStoryDiv.innerHTML = '<p>最新話を準備中...</p>';
                return;
            }

            // 最新話を表示
            const latestFile = htmlFiles[0];
            const episodeNum = parseInt(latestFile.replace('.html', ''));

            fetch(`stories/${latestFile}`)
                .then(r => r.text())
                .then(html => {
                    latestStoryDiv.innerHTML = `
                        <div class="story-header">
                            <p style="color: #ff1493; font-size: 1.1rem; font-weight: bold;">
                                最新エピソード: 第${episodeNum}話
                            </p>
                            <p style="color: #666; font-size: 0.9rem; margin-bottom: 1rem;">
                                ${new Date().toLocaleDateString('ja-JP')} 公開
                            </p>
                        </div>
                        <div class="story-preview">
                            ${html.substring(0, 800)}...
                        </div>
                        <a href="stories/${latestFile}" style="
                            display: inline-block;
                            margin-top: 1rem;
                            padding: 0.8rem 1.5rem;
                            background: linear-gradient(135deg, #ff69b4, #ff1493);
                            color: white;
                            text-decoration: none;
                            border-radius: 4px;
                            font-weight: bold;
                            transition: all 0.3s;
                        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(255, 20, 147, 0.4)';"
                           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                            全文を読む
                        </a>
                    `;
                })
                .catch(err => {
                    console.warn('Failed to load latest story content:', err);
                    latestStoryDiv.innerHTML = `
                        <p>第${episodeNum}話が公開されました。</p>
                        <a href="stories/${latestFile}">読む</a>
                    `;
                });
        })
        .catch(err => {
            console.warn('Failed to load stories directory:', err);
            latestStoryDiv.innerHTML = '<p>ストーリーを読み込み中...</p>';
        });
}

function loadEpisodesList() {
    const episodesListDiv = document.getElementById('episodes-list');

    fetch('stories/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load stories directory');
            }
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const links = Array.from(doc.querySelectorAll('a'));
            const htmlFiles = links
                .map(a => a.getAttribute('href'))
                .filter(href => href && href.match(/^\d{3}\.html$/))
                .sort();

            if (htmlFiles.length === 0) {
                episodesListDiv.innerHTML = '<p>ストーリーを準備中...</p>';
                return;
            }

            // エピソードカードを生成
            episodesListDiv.innerHTML = '';
            htmlFiles.forEach(file => {
                const episodeNum = parseInt(file.replace('.html', ''));
                const card = document.createElement('a');
                card.href = `stories/${file}`;
                card.className = 'episode-card';
                card.innerHTML = `
                    <div class="number">第${episodeNum}話</div>
                    <p>読む</p>
                `;
                episodesListDiv.appendChild(card);
            });
        })
        .catch(err => {
            console.warn('Failed to load episodes list:', err);
            episodesListDiv.innerHTML = '<p>目次を読み込み中...</p>';
        });
}
