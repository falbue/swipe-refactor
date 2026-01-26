// Session page logic with swipe interface

let currentCard = null;
let sessionId = null;
let sessionData = null;

async function initSession() {
    sessionId = window.location.pathname.split('/').pop();

    try {
        sessionData = await apiClient.getSession(sessionId);
        document.getElementById('repo-name').textContent = sessionData.repo_full_name;
        updateProgress();
        loadCard();
    } catch (error) {
        console.error('Error initializing session:', error);
        showToast(`Ошибка: ${error.message}`, 'error');
        setTimeout(() => (window.location.href = '/'), 2000);
    }
}

async function loadCard() {
    try {
        currentCard = await apiClient.getRandomCard(sessionId);
        renderCard(currentCard);
        initSwipeGestures();
    } catch (error) {
        console.error('Error loading card:', error);
        if (error.message.includes("No more cards")) {
            showToast('🎉 Все карточки обработаны!', 'success');
            document.getElementById('current-card').innerHTML =
                '<div style="text-align: center; padding: 2rem;"><h2>Отлично! Все карточки обработаны</h2><p>Создайте Pull Request или начните новую сессию</p></div>';
        } else {
            showToast(`Ошибка загрузки карточки: ${error.message}`, 'error');
        }
    }
}

function renderCard(card) {
    document.getElementById('file-path').textContent = card.file_path;
    document.getElementById('lines-count').textContent = `${card.start_line}-${card.end_line}`;
    document.getElementById('function-name').textContent = card.ast_signature;
    document.getElementById('code-content').textContent = card.original_content;

    // Highlight code
    if (window.hljs) {
        hljs.highlightElement(document.getElementById('code-content'));
    }
}

function updateProgress() {
    if (!sessionData) return;

    const total = sessionData.total_cards;
    const processed = sessionData.approved_cards + sessionData.edited_cards + sessionData.skipped_cards;
    const percentage = total > 0 ? (processed / total) * 100 : 0;

    document.getElementById('progress-bar').style.width = `${percentage}%`;
    document.getElementById('progress-text').textContent = `${processed}/${total}`;
    document.getElementById('approved-count').textContent = sessionData.approved_cards;
    document.getElementById('edited-count').textContent = sessionData.edited_cards;
    document.getElementById('skipped-count').textContent = sessionData.skipped_cards;
}

async function approveCard() {
    if (!currentCard) return;

    try {
        document.getElementById('approve-btn').disabled = true;
        await apiClient.approveCard(currentCard.id);
        showToast('✓ Карточка одобрена');
        await refreshSession();
        loadCard();
    } catch (error) {
        console.error('Error approving card:', error);
        showToast(`Ошибка: ${error.message}`, 'error');
    } finally {
        document.getElementById('approve-btn').disabled = false;
    }
}

async function skipCard() {
    if (!currentCard) return;

    try {
        document.getElementById('skip-btn').disabled = true;
        await apiClient.skipCard(currentCard.id);
        showToast('⏭️ Карточка пропущена');
        await refreshSession();
        loadCard();
    } catch (error) {
        console.error('Error skipping card:', error);
        showToast(`Ошибка: ${error.message}`, 'error');
    } finally {
        document.getElementById('skip-btn').disabled = false;
    }
}

function openEditor() {
    if (!currentCard) return;
    document.getElementById('code-editor').value = currentCard.original_content;
    document.getElementById('editor-modal').classList.add('show');
}

function closeEditor() {
    document.getElementById('editor-modal').classList.remove('show');
}

async function saveEdit() {
    if (!currentCard) return;

    const editedContent = document.getElementById('code-editor').value;
    if (!editedContent.trim()) {
        showToast('Код не может быть пустым', 'error');
        return;
    }

    try {
        document.querySelector('.modal-footer .btn-primary').disabled = true;
        await apiClient.editCard(currentCard.id, editedContent);
        showToast('✏️ Изменения сохранены и закоммичены');
        closeEditor();
        await refreshSession();
        loadCard();
    } catch (error) {
        console.error('Error editing card:', error);
        showToast(`Ошибка: ${error.message}`, 'error');
    } finally {
        document.querySelector('.modal-footer .btn-primary').disabled = false;
    }
}

async function createPullRequest() {
    if (!sessionId) return;

    const confirmed = confirm(
        'Создать Pull Request с изменениями?\n\n' +
        'Это создаст PR в GitHub с изменениями из текущей сессии.',
    );

    if (!confirmed) return;

    try {
        document.getElementById('create-pr-btn').disabled = true;
        const result = await apiClient.createPullRequest(sessionId);
        showToast('🚀 PR создан и отправлен на GitHub!');
        setTimeout(() => {
            if (result.pr_url) {
                window.open(result.pr_url, '_blank');
            }
        }, 1000);
    } catch (error) {
        console.error('Error creating PR:', error);
        showToast(`Ошибка создания PR: ${error.message}`, 'error');
    } finally {
        document.getElementById('create-pr-btn').disabled = false;
    }
}

async function refreshSession() {
    try {
        sessionData = await apiClient.getSession(sessionId);
        updateProgress();
    } catch (error) {
        console.error('Error refreshing session:', error);
    }
}

function exitSession() {
    if (confirm('Вы уверены? Сессия будет завершена.')) {
        window.location.href = '/';
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Swipe gesture detection
function initSwipeGestures() {
    const cardElement = document.getElementById('current-card');
    if (!cardElement || !window.Hammer) return;

    const mc = new Hammer(cardElement);
    mc.on('swipe', (ev) => {
        if (ev.direction === Hammer.DIRECTION_RIGHT) {
            approveCard();
        } else if (ev.direction === Hammer.DIRECTION_LEFT) {
            openEditor();
        }
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.code === 'ArrowRight') {
        approveCard();
    } else if (e.code === 'ArrowLeft') {
        openEditor();
    } else if (e.code === 'Space') {
        e.preventDefault();
        skipCard();
    } else if (e.key === 'Escape') {
        closeEditor();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initSession();
});
