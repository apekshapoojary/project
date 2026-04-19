document.addEventListener('DOMContentLoaded', () => {
    // 1. Page Loader
    const loader = document.querySelector('.page-loader');
    if (loader) {
        window.addEventListener('load', () => {
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 500);
        });
    }

    // 2. Particles JS Configuration
    if (document.getElementById('particles-js')) {
        particlesJS('particles-js', {
            "particles": {
                "number": { "value": 80, "density": { "enable": true, "value_area": 800 } },
                "color": { "value": "#8b5cf6" },
                "shape": { "type": "circle" },
                "opacity": { "value": 0.3, "random": true },
                "size": { "value": 3, "random": true },
                "line_linked": { "enable": true, "distance": 150, "color": "#8b5cf6", "opacity": 0.2, "width": 1 },
                "move": { "enable": true, "speed": 2, "direction": "none", "random": true, "straight": false, "out_mode": "out", "bounce": false }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": { "onhover": { "enable": true, "mode": "grab" }, "onclick": { "enable": true, "mode": "push" }, "resize": true }
            },
            "retina_detect": true
        });
    }

    // 3. Navbar Scroll Effect
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // 4. Typewriter Effect
    const typeTarget = document.querySelector('.typewriter');
    if (typeTarget) {
        const text = typeTarget.getAttribute('data-text');
        let i = 0;
        function type() {
            if (i < text.length) {
                typeTarget.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, 100);
            }
        }
        type();
    }

    // 5. Stat Count Up
    const counts = document.querySelectorAll('.count');
    if (counts.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const target = entry.target;
                    const endValue = parseInt(target.getAttribute('data-target'));
                    let startValue = 0;
                    const duration = 2000;
                    const startTime = performance.now();

                    function update(currentTime) {
                        const elapsed = currentTime - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        target.innerText = Math.floor(progress * endValue);
                        if (progress < 1) requestAnimationFrame(update);
                    }
                    requestAnimationFrame(update);
                    observer.unobserve(target);
                }
            });
        }, { threshold: 0.5 });
        counts.forEach(c => observer.observe(c));
    }

    // 6. GSAP Hover & Floating
    gsap.from(".hero h1", { duration: 1, y: 50, opacity: 0, ease: "power4.out" });
    gsap.from(".hero p", { duration: 1, y: 30, opacity: 0, ease: "power4.out", delay: 0.3 });
});
