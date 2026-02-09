let HOST = "https://swipe.falbue.ru"
let ROUTE = "/cards/"
let URL = HOST + ROUTE

function fetchCards() {
    const repoId = window.location.hash.substring(1);
    let cardId = "99c5b859-f8b0-4d24-8e9c-4e2f73c86819"
    fetch(URL + cardId)
        .then(response => response.json())
        .then(data => {
            const card_code = document.getElementById("card_code");
            card_code.innerHTML = data.code;
        })
}

document.addEventListener("DOMContentLoaded", () => {
    fetchCards();
});