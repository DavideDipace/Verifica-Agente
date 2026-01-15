const userId = "user_" + Math.random().toString(36).substr(2, 9);

document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
    const input = document.getElementById('user-input');
    const msg = input.value.trim();
    if (!msg) return;

    appendMessage('user', msg);
    input.value = '';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, message: msg })
        });

        const data = await response.json();
        
        appendMessage('ai', data.response);

        if (data.recipes && data.recipes.length > 0) {
            appendRecipes(data.recipes);
        }

        updatePantry(data.inventory);
    } catch (error) {
        appendMessage('ai', "Errore di connessione al server Chef. Riprova!");
        console.error(error);
    }
}

function appendMessage(role, text) {
    const win = document.getElementById('chat-window');
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg-wrapper ${role}`;
    msgDiv.innerHTML = `
        <div class="msg-bubble">
            ${text}
        </div>
    `;
    win.appendChild(msgDiv);
    win.scrollTop = win.scrollHeight;
}

function appendRecipes(recipes) {
    const win = document.getElementById('chat-window');
    const grid = document.createElement('div');
    grid.className = 'recipe-grid';
    
    recipes.forEach(r => {
        grid.innerHTML += `
            <div class="recipe-card">
                <img src="${r.image}" alt="${r.name}">
                <div class="card-info">
                    <strong>${r.name}</strong>
                </div>
            </div>
        `;
    });
    
    win.appendChild(grid);
    win.scrollTop = win.scrollHeight;
}

function updatePantry(items) {
    const list = document.getElementById('pantry-list');
    list.innerHTML = items.map(i => `
        <li class="pantry-item">
            <span class="ing-name">${i.name}</span>
            <span class="ing-qty">${i.quantity}</span>
            <div class="ing-expiry">Scadenza: ${i.expiry}</div>
        </li>
    `).join('');
}