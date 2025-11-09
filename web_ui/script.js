// Podelli POC - Frontend JavaScript

// Load all data when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadCharacters();
    loadEpisodes();
});

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/metadata');
        const data = await response.json();

        const assets = data.assets || [];

        // Count asset types
        const imageCount = assets.filter(a => a.asset_type === 'image').length;
        const audioCount = assets.filter(a => a.asset_type === 'audio').length;
        const videoCount = assets.filter(a => a.asset_type === 'video').length;

        // Count unique episodes
        const episodeIds = new Set(assets.filter(a => a.episode_id).map(a => a.episode_id));

        // Update DOM
        document.getElementById('stat-episodes').textContent = episodeIds.size;
        document.getElementById('stat-images').textContent = imageCount;
        document.getElementById('stat-audio').textContent = audioCount;
        document.getElementById('stat-videos').textContent = videoCount;

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load character references
async function loadCharacters() {
    try {
        const metaResponse = await fetch('/api/metadata');
        const metadata = await metaResponse.json();

        const universeResponse = await fetch('/api/universe');
        const universe = await universeResponse.json();

        const charactersGrid = document.getElementById('characters-grid');

        // Get character reference assets
        const charAssets = metadata.assets.filter(a => a.category === 'character_reference');

        if (charAssets.length === 0) {
            charactersGrid.innerHTML = '<p class="loading">No characters generated yet.</p>';
            return;
        }

        // Create character cards
        charactersGrid.innerHTML = '';

        charAssets.forEach(asset => {
            // Find character info from universe data
            const charInfo = universe.main_characters.characters.find(
                c => c.id === asset.character_id
            );

            const card = document.createElement('div');
            card.className = 'character-card';

            card.innerHTML = `
                <img src="/assets/${asset.file_path.replace('output/', '')}"
                     alt="${charInfo?.name || asset.character_id}"
                     class="character-image"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22300%22><rect fill=%22%23ddd%22 width=%22200%22 height=%22300%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 fill=%22%23999%22>No Image</text></svg>'">
                <div class="character-name">${charInfo?.name || asset.character_id}</div>
                <div class="character-role">${charInfo?.role || 'Character'}</div>
            `;

            charactersGrid.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading characters:', error);
        document.getElementById('characters-grid').innerHTML =
            '<p class="loading">Error loading characters.</p>';
    }
}

// Load episodes
async function loadEpisodes() {
    try {
        const episodesResponse = await fetch('/api/episodes');
        const episodes = await episodesResponse.json();

        const metaResponse = await fetch('/api/metadata');
        const metadata = await metaResponse.json();

        const container = document.getElementById('episodes-container');

        if (episodes.length === 0) {
            container.innerHTML = '<p class="loading">No episodes generated yet. Run main.py first!</p>';
            return;
        }

        container.innerHTML = '';

        episodes.forEach((episode, index) => {
            const card = document.createElement('div');
            card.className = 'episode-card';

            let dialogueHTML = '';

            episode.dialogue_lines.forEach((line, idx) => {
                // Find corresponding audio asset
                const audioAsset = metadata.assets.find(
                    a => a.asset_type === 'audio' &&
                         a.episode_id === episode.episode_id &&
                         a.sequence_id === `SEQ_${idx+1}`
                );

                const audioPath = audioAsset ?
                    `/assets/${audioAsset.file_path.replace('output/', '')}` :
                    null;

                dialogueHTML += `
                    <div class="dialogue-line">
                        <div class="dialogue-speaker"><­ ${line.speaker}</div>
                        <div class="dialogue-text">${line.text_fr}</div>
                        <div class="dialogue-translation">${line.text_en}</div>
                        ${audioPath ? `<audio controls src="${audioPath}"></audio>` : ''}
                    </div>
                `;
            });

            card.innerHTML = `
                <div class="episode-header">
                    <h3 class="episode-title">Episode ${index + 1}: ${episode.title_fr}</h3>
                    <p class="episode-objective">${episode.objective_fr}</p>
                </div>
                <div class="dialogues">
                    ${dialogueHTML}
                </div>
            `;

            container.appendChild(card);
        });

    } catch (error) {
        console.error('Error loading episodes:', error);
        document.getElementById('episodes-container').innerHTML =
            '<p class="loading">Error loading episodes.</p>';
    }
}
