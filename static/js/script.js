document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS Animation Library
    AOS.init({
        once: true,
        offset: 50,
        duration: 800,
        easing: 'ease-in-out'
    });

    // Character Counter
    const newsTextarea = document.getElementById('newsTextarea');
    const charCount = document.getElementById('charCount');
    const clearBtn = document.getElementById('clearBtn');
    const predictForm = document.getElementById('predictionForm');
    const predictBtn = document.getElementById('predictBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const btnText = predictBtn ? predictBtn.querySelector('.btn-text') : null;

    // Update character count on input
    if (newsTextarea && charCount) {
        newsTextarea.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = count + (count === 1 ? ' character' : ' characters');
        });
        
        // Initial count if there's pre-filled text
        if (newsTextarea.value.length > 0) {
            charCount.textContent = newsTextarea.value.length + ' characters';
        }
    }

    // Clear textarea
    if (clearBtn && newsTextarea && charCount) {
        clearBtn.addEventListener('click', function() {
            newsTextarea.value = '';
            charCount.textContent = '0 characters';
            newsTextarea.focus();
        });
    }

    // Form submission animation
    if (predictForm && predictBtn && loadingSpinner && btnText && newsTextarea) {
        predictForm.addEventListener('submit', function(e) {
            if (newsTextarea.value.trim() !== '') {
                btnText.textContent = 'Analyzing...';
                loadingSpinner.classList.remove('d-none');
                predictBtn.classList.add('disabled');
            } else {
                e.preventDefault();
                newsTextarea.focus();
            }
        });
    }

    // Counter Animation for Statistics
    const counters = document.querySelectorAll('.counter');
    const speed = 200; // Lower is faster

    const animateCounters = () => {
        counters.forEach(counter => {
            const updateCount = () => {
                const target = +counter.getAttribute('data-target');
                const count = +counter.innerText;
                const inc = target / speed;

                if (count < target) {
                    // Check if it's a decimal (accuracy)
                    if (target % 1 !== 0) {
                        counter.innerText = (count + inc).toFixed(2);
                    } else {
                        counter.innerText = Math.ceil(count + inc);
                    }
                    setTimeout(updateCount, 15);
                } else {
                    counter.innerText = target;
                }
            };
            updateCount();
        });
    }

    // Trigger counter animation when stats section is in view
    let statsAnimated = false;
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !statsAnimated) {
            animateCounters();
            statsAnimated = true;
        }
    }, { threshold: 0.5 });
    
    const statsSection = document.querySelector('.stat-card');
    if (statsSection && statsSection.parentElement && statsSection.parentElement.parentElement) {
        observer.observe(statsSection.parentElement.parentElement);
    }

    // Smooth scrolling for navigation links
    document.querySelectorAll('a.nav-link, a.btn[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href.startsWith('#') && href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Navbar background on scroll
    const navbar = document.querySelector('.glass-navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(15, 23, 42, 0.95)';
                navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.3)';
            } else {
                navbar.style.background = 'rgba(15, 23, 42, 0.85)';
                navbar.style.boxShadow = '0 4px 30px rgba(0, 0, 0, 0.1)';
            }
        });
    }
});
