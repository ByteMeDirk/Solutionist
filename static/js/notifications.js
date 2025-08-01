// Notification AJAX functions
document.addEventListener('DOMContentLoaded', function () {
    // Get the Mark All as Read link
    const markAllAsReadLinks = document.querySelectorAll('.mark-all-as-read');

    markAllAsReadLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const url = this.getAttribute('href');

            // Send AJAX request to mark all notifications as read
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Remove notification badge
                        const badge = document.querySelector('.notification-badge');
                        if (badge) {
                            badge.style.display = 'none';
                        }

                        // Mark all notifications as read in the dropdown
                        const boldItems = document.querySelectorAll('.dropdown-item.fw-bold');
                        boldItems.forEach(item => {
                            item.classList.remove('fw-bold');
                        });
                    }
                })
                .catch(error => console.error('Error:', error));
        });
    });

    // Helper function to get CSRF cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
