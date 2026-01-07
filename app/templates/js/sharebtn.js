function shareMovie(relativeUrl) {
  // ✅ Fix: convert relative path to full URL
  const shareUrl = relativeUrl.startsWith('http')
    ? relativeUrl
    : window.location.origin + relativeUrl;
  
  if (navigator.share) {
    navigator.share({
      title: '🎬 Watch this movie!',
      text: 'I Found This Great Movie, Check It Out!',
      url: shareUrl
    }).catch(console.error);
  } else {
    navigator.clipboard.writeText(shareUrl)
      .then(() => showToast('🔗 Link copied!'))
      .catch(() => alert('Link: ' + shareUrl));
  }
}

function showToast(msg) {
  const t = document.createElement('div');
  t.textContent = msg;
  Object.assign(t.style, {
    position: 'fixed',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    background: '#333',
    color: 'white',
    padding: '8px 16px',
    borderRadius: '6px',
    boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
    zIndex: '9999',
    fontSize: '14px',
    opacity: '0',
    transition: 'opacity .3s'
  });
  document.body.appendChild(t);
  requestAnimationFrame(() => t.style.opacity = '1');
  setTimeout(() => {
    t.style.opacity = '0';
    setTimeout(() => t.remove(), 300);
  }, 1500);
}
