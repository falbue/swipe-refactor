let HOST = "https://swipe.falbue.ru"
let ROUTE = "/cards/"
let URL = HOST + ROUTE

function fetchCards() {
    const repoId = window.location.hash.substring(1);;
    fetch(`${URL}repo/${repoId}/random`)
        .then(response => response.json())
        .then(data => {
            const fileNameEl = document.getElementById("file-name");
            fileNameEl.textContent = `${data.file_path}`;
            const card_code = document.getElementById("card-code");
            const code = data.code;

            const pre = document.createElement("pre");
            const codeEl = document.createElement("code");
            codeEl.className = "language-python hljs";
            codeEl.textContent = code; // ← безопасно и корректно!
            pre.appendChild(codeEl);
            card_code.innerHTML = ""; // очистить старое
            card_code.appendChild(pre);

            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(codeEl);
            }
        })
        .catch(err => console.error("Ошибка загрузки карточки:", err));
}

document.addEventListener("DOMContentLoaded", () => {
    fetchCards();
});