document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURATION ---
    const API_URL = 'http://127.0.0.1:5000/find_games'; // This is for local testing

    const genres = ['Obby', 'Horror', 'Puzzle', 'Survival', 'Tycoon', 'RPG', 'Fighting', 'Simulator', 'Roleplay'];
    const devices = ['Any', 'PC', 'Mobile', 'Console', 'VR'];
    const mechanics = ['PvP', 'PvE', 'Building', 'Trading', 'Questing', 'Economy'];
    const vibes = ['Fast-Paced', 'Relaxing', 'Story-Driven', 'Competitive', 'Social', 'Exploration'];

    // --- ELEMENT SELECTORS ---
    const form = document.getElementById('game-finder-form');
    const findButton = document.getElementById('find-game-btn');
    const descriptionInput = document.getElementById('description');
    const genresContainer = document.getElementById('genres');
    const devicesContainer = document.getElementById('devices');
    const mechanicsContainer = document.getElementById('mechanics');
    const vibesContainer = document.getElementById('vibes');
    const groupToggleContainer = document.getElementById('group-toggle');
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');
    const resultsContainer = document.getElementById('results-container');

    // --- FUNCTIONS ---

    // Function to create and render option buttons
    function renderOptions(container, options, multiSelect = true) {
        options.forEach(option => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'option-button';
            button.textContent = option;
            button.dataset.value = option;
            container.appendChild(button);

            button.addEventListener('click', () => {
                if (multiSelect) {
                    button.classList.toggle('active');
                } else {
                    // For single-select options like 'device'
                    const parent = button.parentElement;
                    parent.querySelectorAll('.option-button').forEach(btn => btn.classList.remove('active'));
                    button.classList.add('active');
                }
            });
        });
        // For single select, set a default active button
        if (!multiSelect && container.firstChild) {
            container.firstChild.classList.add('active');
        }
    }

    // Function to get selected values from a button group
    function getSelectedOptions(container) {
        const selected = [];
        container.querySelectorAll('.option-button.active').forEach(button => {
            selected.push(button.dataset.value);
        });
        return selected;
    }

    // Function to display game cards
    function displayResults(games) {
        resultsContainer.innerHTML = ''; // Clear previous results
        if (!games || games.length === 0) {
            resultsContainer.innerHTML = '<p>No games found matching your criteria. Try being more general!</p>';
            return;
        }

        games.forEach(game => {
            const card = document.createElement('div');
            card.className = 'game-card';
            card.innerHTML = `
                <div>
                    <div class="card-header">
                        <h3>${game.gameName}</h3>
                        <div class="match-rating">${game.matchRating}/10</div>
                    </div>
                    <p>${game.description}</p>
                </div>
                <a href="https://www.roblox.com/games/${game.gameId}/${game.urlName}" target="_blank" rel="noopener noreferrer" class="play-button">Play Now</a>
            `;
            resultsContainer.appendChild(card);
        });
    }

    // --- INITIALIZATION ---
    renderOptions(genresContainer, genres, true);
    renderOptions(devicesContainer, devices, false);
    renderOptions(mechanicsContainer, mechanics, true);
    renderOptions(vibesContainer, vibes, true);

    // Event listener for the Solo/Group toggle
    groupToggleContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('toggle-button')) {
            groupToggleContainer.querySelectorAll('.toggle-button').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
        }
    });

    // Event listener for the main form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Show loader and hide old results/errors
        loader.style.display = 'block';
        errorMessage.style.display = 'none';
        resultsContainer.innerHTML = '';
        findButton.disabled = true;
        findButton.textContent = 'Thinking...';

        // Collect all data
        const searchFilters = {
            description: descriptionInput.value,
            genres: getSelectedOptions(genresContainer),
            withGroup: groupToggleContainer.querySelector('.toggle-button.active').dataset.value === 'true',
            device: devicesContainer.querySelector('.option-button.active').dataset.value,
            mechanics: getSelectedOptions(mechanicsContainer),
            vibes: getSelectedOptions(vibesContainer),
        };

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(searchFilters),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
            }

            const games = await response.json();
            displayResults(games);

        } catch (error) {
            errorMessage.textContent = `Error: ${error.message}`;
            errorMessage.style.display = 'block';
        } finally {
            // Hide loader and re-enable button
            loader.style.display = 'none';
            findButton.disabled = false;
            findButton.textContent = 'Find My Game';
        }
    });
});