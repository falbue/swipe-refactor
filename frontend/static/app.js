// Main app logic for index page

async function startSession() {
    const repoInput = document.getElementById('repo-input').value.trim();
    const errorMessage = document.getElementById('error-message');
    const startBtn = document.getElementById('start-btn');

    if (!repoInput) {
        showError('Введите название репозитория');
        return;
    }

    if (!repoInput.includes('/')) {
        showError('Используйте формат: owner/repo');
        return;
    }

    try {
        startBtn.disabled = true;
        errorMessage.classList.remove('show');

        const session = await apiClient.createSession(repoInput);
        window.location.href = `/session/${session.id}`;
    } catch (error) {
        console.error('Error creating session:', error);
        showError(`Ошибка: ${error.message}`);
    } finally {
        startBtn.disabled = false;
    }
}

function showError(message) {
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

// Allow Enter key to start session
document.addEventListener('DOMContentLoaded', () => {
    const repoInput = document.getElementById('repo-input');
    repoInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            startSession();
        }
    });

    // Check health on load
    apiClient
        .healthCheck()
        .then(() => console.log('✓ API is healthy'))
        .catch((err) => console.error('✗ API health check failed:', err));
});
