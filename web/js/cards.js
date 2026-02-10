let HOST = "https://swipe.falbue.ru"
let ROUTE = "/cards/"
let URL = HOST + ROUTE

function fetchCards() {
    const cardId = "99c5b859-f8b0-4d24-8e9c-4e2f73c86819";
    fetch(URL + cardId)
        .then(response => response.json())
        .then(data => {
            const card_code = document.getElementById("card_code");
            const code = data.code; // Это строка с \n и экранированными кавычками — нормально!

            // ВАЖНО: НЕ используйте innerHTML напрямую с сырым кодом!
            // Лучше создать элемент и вставить текст, чтобы избежать XSS и проблем с экранированием.
            const pre = document.createElement("pre");
            const codeEl = document.createElement("code");
            codeEl.className = "language-python hljs";
            codeEl.textContent = code; // ← безопасно и корректно!
            pre.appendChild(codeEl);
            card_code.innerHTML = ""; // очистить старое
            card_code.appendChild(pre);

            // Теперь запустить подсветку!
            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(codeEl); // или hljs.highlightAll()
            }
        })
        .catch(err => console.error("Ошибка загрузки карточки:", err));
}

document.addEventListener("DOMContentLoaded", () => {
    fetchCards();
});