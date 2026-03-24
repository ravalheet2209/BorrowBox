document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Scrolled Navbar Effect
    const navbar = document.getElementById('navbar');
    
    window.addEventListener('scroll', () => {
        if (navbar) {
            if (window.scrollY > 80) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    });

    // 2. Intersection Observer for trigger Scroll Animations
    // The classes setup in CSS (e.g., .hidden, .slide-up, .show) are coordinated here.
    const observerOptions = {
        root: null, // Viewport
        rootMargin: '0px',
        threshold: 0.2 // Fire when 20% of element is in view
    };

    const scrollObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add the animation trigger class
                entry.target.classList.add('show');
                
                // Do not unobserve if we want infinite looping on scroll
                // But generally, unobserving is better for performance and UI cohesiveness once built.
                // Uncomment the line below to only animate once:
                // observer.unobserve(entry.target);
            } else {
                // Remove the class so the animation repeats if scattered out of the viewport.
                // Allows repeating animations as you scroll up and down.
                entry.target.classList.remove('show');
            }
        });
    }, observerOptions);

    // Grab all elements marked to be hidden until scroll
    const hiddenElements = document.querySelectorAll('.scroll-hidden');
    hiddenElements.forEach((el) => scrollObserver.observe(el));

    // 3. Smooth Scrolling for Anchor Elements (Navigation Links)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - (navbar && navbar.offsetHeight > 80 ? navbar.offsetHeight : 80),
                    behavior: 'smooth'
                });
            }
        });
    });

    // 4. Subtle Mouse Parallax Effect on Hero Background Elements
    const shapes = document.querySelectorAll('.shape');
    
    document.addEventListener('mousemove', (e) => {
        // Calculate the relative mouse position as a percentage from center
        const x = (e.clientX / window.innerWidth - 0.5) * 2;
        const y = (e.clientY / window.innerHeight - 0.5) * 2;

        if (window.innerWidth > 768) { // run only on desktop
             if (shapes[0]) {
                 // The shape moves inverse to the mouse, feeling floating
                 shapes[0].style.transform = `translate(${x * 60}px, ${y * 60}px)`;
             }
             if (shapes[1]) {
                 shapes[1].style.transform = `translate(${-x * 80}px, ${-y * 80}px)`;
             }
        }
    });
});
