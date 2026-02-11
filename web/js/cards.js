let HOST = "https://swipe.falbue.ru"
let ROUTE = "/cards/"
let URL = HOST + ROUTE

function fetchCards() {
    const repoId = window.location.hash.substring(1);;
    fetch(`${URL}repo/${repoId}/random`)
        .then(response => response.json())
        .then(data => {
            const card_code = document.getElementById("card_code");
            const code = data.code;

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