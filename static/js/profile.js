/* =========================================================
   COMPASS CAMPUS - BABAK 7 PROFIL PENGGUNA
   File: static/js/profile.js
   ========================================================= */

(function () {
    "use strict";

    const body = document.body;
    const revealItems = document.querySelectorAll(".reveal");
    const bioInput = document.querySelector("textarea[name='bio']");
    const bioCounter = document.getElementById("bio-counter");
    const profileForms = document.querySelectorAll("form");

    function updateBioCounter() {
        if (!bioInput || !bioCounter) return;
        bioCounter.textContent = String(bioInput.value.length);
    }

    if (bioInput) {
        updateBioCounter();
        bioInput.addEventListener("input", updateBioCounter);
    }

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
            { threshold: 0.14 }
        );

        revealItems.forEach((item) => observer.observe(item));
    } else {
        revealItems.forEach((item) => item.classList.add("is-visible"));
    }

    profileForms.forEach((form) => {
        form.addEventListener("submit", () => {
            const button = form.querySelector("button[type='submit']");
            if (!button) return;

            button.dataset.originalText = button.textContent.trim();
            button.style.opacity = "0.75";
            button.style.pointerEvents = "none";
        });
    });

    document.querySelectorAll("a[href]").forEach((link) => {
        const href = link.getAttribute("href") || "";
        const isExternal = href.startsWith("http") || href.startsWith("mailto:");
        const isAnchor = href.startsWith("#");

        if (isExternal || isAnchor || link.hasAttribute("data-no-transition")) {
            return;
        }

        link.addEventListener("click", () => {
            body.classList.add("is-leaving");
        });
    });

    window.addEventListener("pageshow", () => {
        body.classList.remove("is-leaving");
    });
})();
