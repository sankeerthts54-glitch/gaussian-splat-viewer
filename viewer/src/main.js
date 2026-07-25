import * as GaussianSplats3D from 'https://unpkg.com/@mkkellogg/gaussian-splats-3d@0.4.7/build/gaussian-splats-3d.module.js';

document.addEventListener('DOMContentLoaded', () => {
    // 7. Cursor Glow
    const cursorGlow = document.getElementById('cursor-glow');
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (cursorGlow && !isTouchDevice) {
        document.addEventListener('mousemove', (e) => {
            cursorGlow.style.left = `${e.clientX}px`;
            cursorGlow.style.top = `${e.clientY}px`;
        });
    } else if (cursorGlow) {
        cursorGlow.style.display = 'none';
    }

    // Mobile hamburger menu
    const hamburger = document.getElementById('hamburger');
    const mobileDrawer = document.getElementById('mobile-drawer');
    if (hamburger && mobileDrawer) {
        hamburger.addEventListener('click', () => {
            const isOpen = hamburger.classList.toggle('open');
            mobileDrawer.classList.toggle('open', isOpen);
            hamburger.setAttribute('aria-expanded', isOpen);
        });
        // Close drawer when a link is clicked
        mobileDrawer.querySelectorAll('.mobile-nav-link').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('open');
                mobileDrawer.classList.remove('open');
                hamburger.setAttribute('aria-expanded', 'false');
            });
        });
    }

    // 1. Particle Canvas
    const canvas = document.getElementById('particle-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        const colors = ['#818cf8', '#06b6d4', '#a78bfa'];
        let mouseX = window.innerWidth / 2;
        let mouseY = window.innerHeight / 2;

        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        if (!isTouchDevice) {
            document.addEventListener('mousemove', (e) => {
                mouseX = e.clientX;
                mouseY = e.clientY;
            });
        }

        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.vx = (Math.random() - 0.5) * 0.5;
                this.vy = (Math.random() - 0.5) * 0.5;
                this.radius = Math.random() * 2 + 1;
                this.color = colors[Math.floor(Math.random() * colors.length)];
                this.opacity = Math.random() * 0.4 + 0.1;
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;

                // Wrap around edges
                if (this.x < 0) this.x = canvas.width;
                if (this.x > canvas.width) this.x = 0;
                if (this.y < 0) this.y = canvas.height;
                if (this.y > canvas.height) this.y = 0;

                // Parallax shift based on mouse
                const dx = (mouseX - canvas.width / 2) * 0.01;
                const dy = (mouseY - canvas.height / 2) * 0.01;
                
                this.draw(dx, dy);
            }

            draw(dx, dy) {
                ctx.beginPath();
                ctx.arc(this.x - dx, this.y - dy, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.globalAlpha = this.opacity;
                ctx.fill();
            }
        }

        for (let i = 0; i < 80; i++) {
            particles.push(new Particle());
        }

        const animateParticles = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            const dx = (mouseX - canvas.width / 2) * 0.01;
            const dy = (mouseY - canvas.height / 2) * 0.01;

            particles.forEach((p, index) => {
                p.update();
                
                // Draw connecting lines to nearby particles
                for (let j = index + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    
                    // Apply parallax shift to line coordinates as well
                    const px1 = p.x - dx;
                    const py1 = p.y - dy;
                    const px2 = p2.x - dx;
                    const py2 = p2.y - dy;
                    
                    const dist = Math.hypot(px1 - px2, py1 - py2);
                    
                    if (dist < 150) {
                        ctx.beginPath();
                        ctx.moveTo(px1, py1);
                        ctx.lineTo(px2, py2);
                        ctx.strokeStyle = p.color;
                        // Opacity fades out as distance increases
                        ctx.globalAlpha = 0.08 * (1 - dist / 150);
                        ctx.stroke();
                    }
                }
            });
            ctx.globalAlpha = 1;
            requestAnimationFrame(animateParticles);
        };
        
        animateParticles();
    }

    // 4. Hero Stats Counter Animation
    const animateValue = (obj, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            
            // easeOutExpo
            const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
            const current = Math.floor(start + ease * (end - start));
            
            if (end > 10000) {
                obj.innerHTML = current.toLocaleString();
            } else {
                obj.innerHTML = current;
            }
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                obj.innerHTML = end.toLocaleString();
            }
        };
        window.requestAnimationFrame(step);
    };

    // 2. Scroll Reveal Animations
    const revealElements = document.querySelectorAll('.anim-reveal');
    const statsElements = document.querySelectorAll('.hero-stat-value');
    
    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const delay = el.getAttribute('data-delay') || 0;
                
                setTimeout(() => {
                    el.classList.add('is-visible');
                }, delay);
                
                // Trigger stat counter if it's a stat element
                if (el.classList.contains('hero-stat-value') && el.hasAttribute('data-count')) {
                    const target = parseInt(el.getAttribute('data-count'), 10);
                    animateValue(el, 0, target, 2000);
                }
                
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.15 });

    revealElements.forEach(el => revealObserver.observe(el));
    statsElements.forEach(el => {
        if (!el.classList.contains('anim-reveal')) {
             revealObserver.observe(el);
        }
    });

    // 3. Navigation & 6. Timeline Progress
    const nav = document.getElementById('main-nav');
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section');
    const timelineSection = document.getElementById('pipeline');
    const timelineFill = document.getElementById('timeline-fill');

    window.addEventListener('scroll', () => {
        // Nav background toggle based on scroll depth
        if (nav) {
            if (window.scrollY > 80) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        }

        // Active link highlighting for navigation
        let currentSectionId = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            // Highlight when scrolling near the section
            if (window.scrollY >= (sectionTop - 200)) {
                currentSectionId = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSectionId}`) {
                link.classList.add('active');
            }
        });

        // Timeline Progress calculation
        if (timelineSection && timelineFill) {
            const rect = timelineSection.getBoundingClientRect();
            const windowHeight = window.innerHeight;
            
            // Check if section is currently in view
            if (rect.top < windowHeight && rect.bottom > 0) {
                const totalScroll = rect.height + windowHeight;
                const currentScroll = windowHeight - rect.top;
                let progress = (currentScroll / totalScroll) * 100;
                progress = Math.max(0, Math.min(100, progress)); // Clamp between 0 and 100
                timelineFill.style.height = `${progress}%`;
            }
        }
    });

    // 8. Smooth Scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetEl = document.querySelector(targetId);
            if (targetEl) {
                const navHeight = nav ? nav.offsetHeight : 64;
                const targetPosition = targetEl.getBoundingClientRect().top + window.scrollY - navHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // 5. 3D Gaussian Splat Viewer (Section 3)
    const demoSection = document.getElementById('demo');
    const splatContainer = document.getElementById('splat-container');
    const splatBar = document.getElementById('splat-bar');
    const splatPct = document.getElementById('splat-pct');
    const splatLoading = document.getElementById('splat-loading');
    const statFps = document.getElementById('stat-fps');
    const statGaussians = document.getElementById('stat-gaussians');
    const controlsHint = document.getElementById('controls-hint');
    
    let viewer = null;
    let isViewerInitialized = false;
    let isAutoRotate = false;
    let autoRotateInterval = null;

    const initViewer = () => {
        if (isViewerInitialized || !splatContainer) return;
        isViewerInitialized = true;

        viewer = new GaussianSplats3D.Viewer({
            rootElement: splatContainer,
            cameraUp: [0, -1, 0],
            initialCameraPosition: [0, -0.5, 3],
            initialCameraLookAt: [0, 0, 0],
            sphericalHarmonicsDegree: 2,
            sharedMemoryForWorkers: false,
            dynamicScene: false,
            antialiased: true,
            integrateControls: true,
        });

        viewer.addSplatScene('splats/blender_lego.ksplat', {
            onProgress: (progress, progressMessage, loaderStatus) => {
                const p = Math.round(progress * 100);
                if (splatBar) splatBar.style.width = `${p}%`;
                if (splatPct) splatPct.innerText = `${p}%`;
            },
            showLoadingUI: false,
            splatAlphaRemovalThreshold: 5,
        }).then(() => {
            if (splatLoading) splatLoading.classList.add('loaded');
            viewer.start();
            
            // Fade out the controls hint after 5 seconds
            if (controlsHint) {
                setTimeout(() => {
                    controlsHint.style.opacity = '0';
                    controlsHint.style.transition = 'opacity 1s';
                }, 5000);
            }

            // Update gaussian count stat if available
            setInterval(() => {
                if (viewer && statGaussians && viewer.splatMesh && typeof viewer.splatMesh.getSplatCount === 'function') {
                    const count = viewer.splatMesh.getSplatCount();
                    statGaussians.innerText = count.toLocaleString();
                }
            }, 1000);
            
            // Custom FPS counter
            let frameCount = 0;
            let lastTime = performance.now();
            
            const updateFPS = () => {
                frameCount++;
                const now = performance.now();
                if (now - lastTime >= 1000) {
                    if (statFps) statFps.innerText = frameCount.toString();
                    frameCount = 0;
                    lastTime = now;
                }
                requestAnimationFrame(updateFPS);
            };
            requestAnimationFrame(updateFPS);

        }).catch((err) => {
            console.error('Error loading splat scene:', err);
            if (splatPct) splatPct.innerText = 'Error loading scene';
        });

        // 9. Keyboard Shortcuts for viewer
        window.addEventListener('keydown', (e) => {
            if (!viewer) return;
            
            // Only capture shortcuts if demo section is somewhat in view
            const demoRect = demoSection.getBoundingClientRect();
            const isInView = demoRect.top < window.innerHeight && demoRect.bottom > 0;
            if (!isInView) return;

            if (e.key.toLowerCase() === 'r') {
                viewer.setCameraPosition([0, -0.5, 3], [0, 0, 0], [0, -1, 0]);
            } else if (e.code === 'Space') {
                e.preventDefault(); // Prevent default page scroll
                isAutoRotate = !isAutoRotate;
                
                if (isAutoRotate) {
                    let angle = 0;
                    const radius = 3;
                    autoRotateInterval = setInterval(() => {
                        angle += 0.01;
                        const x = Math.sin(angle) * radius;
                        const z = Math.cos(angle) * radius;
                        viewer.setCameraPosition([x, -0.5, z], [0, 0, 0], [0, -1, 0]);
                    }, 16);
                } else {
                    clearInterval(autoRotateInterval);
                }
            }
        });
    };

    // Lazy load the viewer when demo section scrolls into view
    if (demoSection) {
        const splatObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                initViewer();
                splatObserver.unobserve(demoSection);
            }
        }, { threshold: 0.1 }); // Trigger a bit before fully in view

        splatObserver.observe(demoSection);
    }
});
