let HOST = "https://swipe.falbue.ru"
let ROUTE = "/repositories/"
let URL = HOST + ROUTE

function fetchRepos() {
    fetch(URL)
        .then(response => response.json())
        .then(data => {
            const listRepos = document.getElementById("listRepos");
            listRepos.innerHTML = "";
            data.forEach(repo => {
                const card = document.createElement("div");
                owner = repo.repo_full_name.split("/")[0]
                repo_name = repo.repo_full_name.split("/")[1]
                card.className = "card w100";
                card.innerHTML = `
                    <main class="between">
                        <div>
                            <h4>${repo_name}</h4>
                            <h5>${owner}</h5>
                        </div>
                        <a href="html/cards.html#${repo.id}" class="button"><i class="iconoir-open-new-window"></i></a>
                    </main>
                `;
                listRepos.appendChild(card);
            });
        })
}

document.addEventListener("DOMContentLoaded", () => {
    fetchRepos();
});
