/* =========================================================
   COMPASS CAMPUS - BABAK 5 CAMPUS DETAIL JS

   Fungsi:
   1. Mengaktifkan animasi masuk halaman.
   2. Menjalankan reveal ketika elemen terlihat di layar.
   3. Menandai menu sidebar sesuai section yang sedang dibaca.
   4. Menjaga tombol Back browser tetap normal.
   ========================================================= */

(function () {
    "use strict";

    const body = document.body;
    const revealElements = document.querySelectorAll(".reveal");
    const sidebarLinks = document.querySelectorAll(".detail-sidebar a[href^='#']");
    const contentSections = Array.from(sidebarLinks)
        .map((link) => document.querySelector(link.getAttribute("href")))
        .filter(Boolean);

    function markPageReady() {
        body.classList.add("page-ready");
        body.classList.remove("page-leaving");
    }

    function setupRevealAnimation() {
        if (!revealElements.length) {
            return;
        }

        if (!("IntersectionObserver" in window)) {
            revealElements.forEach((element) => {
                element.classList.add("is-visible");
            });
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.14,
                rootMargin: "0px 0px -40px 0px",
            }
        );

        revealElements.forEach((element) => {
            observer.observe(element);
        });
    }

    function setupSidebarState() {
        if (!sidebarLinks.length || !contentSections.length || !("IntersectionObserver" in window)) {
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) {
                        return;
                    }

                    const activeId = `#${entry.target.id}`;

                    sidebarLinks.forEach((link) => {
                        link.classList.toggle(
                            "active",
                            link.getAttribute("href") === activeId
                        );
                    });
                });
            },
            {
                threshold: 0.35,
            }
        );

        contentSections.forEach((section) => {
            observer.observe(section);
        });
    }

    function setupPageTransition() {
        const links = document.querySelectorAll("a[href]");

        links.forEach((link) => {
            link.addEventListener("click", (event) => {
                const href = link.getAttribute("href") || "";
                const isHash = href.startsWith("#");
                const isNewTab = link.target === "_blank";
                const skipTransition = link.hasAttribute("data-no-transition");

                if (isHash || isNewTab || skipTransition) {
                    return;
                }

                body.classList.add("page-leaving");
            });
        });
    }

    window.addEventListener("pageshow", () => {
        markPageReady();
    });

    document.addEventListener("DOMContentLoaded", () => {
        markPageReady();
        setupRevealAnimation();
        setupSidebarState();
        setupPageTransition();
    });
})();


// Babak 5B: penanda bahwa direktori kampus realistis sudah aktif.
document.documentElement.dataset.campusSeed = '5B';
