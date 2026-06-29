/* =========================================================
   COMPASS CAMPUS - BABAK 6
   File: static/js/recommendation.js
   Modul: Pemetaan Minat dan Rekomendasi
   ========================================================= */

(function () {
    "use strict";

    const revealElements = document.querySelectorAll(".reveal");

    if ("IntersectionObserver" in window) {
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
                threshold: 0.12,
            }
        );

        revealElements.forEach((element) => observer.observe(element));
    } else {
        revealElements.forEach((element) => element.classList.add("is-visible"));
    }

    // Transisi halus saat pindah halaman internal.
    document.querySelectorAll("a[href]").forEach((link) => {
        const href = link.getAttribute("href");

        if (!href || href.startsWith("#") || link.target === "_blank") {
            return;
        }

        link.addEventListener("click", (event) => {
            const url = new URL(link.href, window.location.origin);

            if (url.origin !== window.location.origin) {
                return;
            }

            event.preventDefault();
            document.body.classList.add("is-leaving");

            window.setTimeout(() => {
                window.location.href = link.href;
            }, 160);
        });
    });

    // Saat user kembali memakai tombol Back browser, pastikan halaman muncul normal.
    window.addEventListener("pageshow", () => {
        document.body.classList.remove("is-leaving");
        revealElements.forEach((element) => element.classList.add("is-visible"));
    });
})();
