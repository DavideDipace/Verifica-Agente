const userId = "chef_pro_session_" + Math.random().toString(36).substr(2, 9);
let isWaiting = false; // Impedisce invii multipli durante l'attesa

const sendBtn = document.getElementById('send-btn');
const userInput = document.getElementById('user-input');

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => { 
    if (e.key === 'Enter') sendMessage(); 
});

async function sendMessage() {
    if (isWaiting) return;
    
    const msg = userInput.value.trim();
    if (!msg) return;

    // Mostra messaggio utente
    appendMsg('user', msg);
    userInput.value = '';
    isWaiting = true;

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, message: msg })
        });

        const data = await response.json();
        
        // 1. Messaggio dello Chef (Testo naturale, mai codice)
        appendMsg('ai', data.message);

        // 2. Se ci sono ricette, mostrale con foto piccole e passaggi
        if (data.recipes && data.recipes.length > 0) {
            renderRecipes(data.recipes);
        }

        // 3. Aggiorna la TABELLA nella Sidebar e il numero di persone
        updateSidebarTable(data.inventory, data.num_people);

    } catch (error) {
        console.error("Errore di connessione:", error);
        appendMsg('ai', "Scusami, ho avuto un piccolo imprevisto in cucina. Potresti riprovare?");
    } finally {
        isWaiting = false;
    }
}

/**
 * Aggiunge un fumetto di testo alla chat
 */
function appendMsg(role, text) {
    if (!text) return;
    const win = document.getElementById('chat-window');
    const div = document.createElement('div');
    div.className = `msg-bubble ${role}`;
    
    // innerText garantisce che l'AI non possa iniettare codice o HTML
    div.innerText = text; 
    
    win.appendChild(div);
    
    // Scroll automatico verso il basso
    win.scrollTop = win.scrollHeight;
}

/**
 * Visualizza le ricette come card con immagine e passaggi
 */
function renderRecipes(recipes) {
    const win = document.getElementById('chat-window');
    
    recipes.forEach(r => {
        const card = document.createElement('div');
        card.className = 'recipe-card';
        
        card.innerHTML = `
            <img src="${r.image_url}" alt="${r.name}" onerror="this.src='https://via.placeholder.com/90?text=Piatto'">
            <div class="info">
                <h3>${r.name}</h3>
                <p>${r.steps}</p>
            </div>
        `;
        win.appendChild(card);
    });
    
    win.scrollTop = win.scrollHeight;
}

/**
 * Aggiorna la tabella Sidebar e l'intestazione delle persone
 */
function updateSidebarTable(ingredients, people) {
    const tbody = document.getElementById('pantry-body');
    const header = document.getElementById('people-count');

    // Aggiorna il titolo della sidebar con il numero di persone
    if (header) {
        header.innerText = people ? `Dispensa (per ${people} 👥)` : "Dispensa 🧊";
    }

    // Pulisce la tabella attuale
    tbody.innerHTML = '';

    if (!ingredients || ingredients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; color: #999;">La dispensa è vuota</td></tr>';
        return;
    }

    // Ricostruisce le righe della tabella
    ingredients.forEach(item => {
        const row = document.createElement('tr');
        
        // Se il dato è "?", usiamo la classe 'missing' definita nel CSS per evidenziarlo
        const qtyDisplay = item.quantity === "?" ? `<span class="missing">?</span>` : item.quantity;
        const expDisplay = item.expiry === "?" ? `<span class="missing">?</span>` : item.expiry;

        row.innerHTML = `
            <td><strong>${item.name}</strong></td>
            <td>${qtyDisplay}</td>
            <td>${expDisplay}</td>
        `;
        tbody.appendChild(row);
    });
}