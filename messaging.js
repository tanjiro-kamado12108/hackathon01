// Messaging Modal Functions
function openMessagingModal() {
    document.getElementById('messagingModal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeMessagingModal() {
    document.getElementById('messagingModal').classList.add('hidden');
    document.body.style.overflow = 'auto';
    // Reset form
    document.getElementById('messageForm').reset();
}

function sendMessage(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const messageData = {
        teacher: formData.get('teacher'),
        subject: formData.get('subject'),
        message: formData.get('message'),
        priority: formData.get('priority')
    };

    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="loading-spinner"></span> Sending...';
    submitBtn.disabled = true;

    // Simulate API call
    setTimeout(() => {
        console.log('Message sent:', messageData);
        showNotification('Message sent successfully!', 'success');
        closeMessagingModal();

        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }, 1500);
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    const modal = document.getElementById('messagingModal');
    if (e.target === modal) {
        closeMessagingModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && !document.getElementById('messagingModal').classList.contains('hidden')) {
        closeMessagingModal();
    }
});
