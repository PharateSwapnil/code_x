
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeSwitch = document.getElementById('theme-switch');
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-theme');
        themeSwitch.checked = true;
    }
    
    // Toggle theme when switch is clicked
    themeSwitch.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Handle chat mode cards
    const chatModeCards = document.querySelectorAll('.chat-mode-card');
    
    chatModeCards.forEach(card => {
        card.addEventListener('click', function() {
            const button = this.querySelector('.chat-mode-btn');
            
            if (button.textContent.includes('Get Started')) {
                // Navigate to the corresponding chat interface
                window.location.href = button.closest('a').getAttribute('href') || '/repo_chat';
            } else if (button.textContent.includes('Coming Soon')) {
                alert('This feature is coming soon!');
            }
        });
    });
});
