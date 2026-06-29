/* =========================================================
   COMPASS CAMPUS - ADMIN HELP DESK BABAK 4
   File: static/js/admin.js

   Fungsi:
   1. Menghitung jumlah karakter balasan admin.
   2. Mencegah submit balasan kosong.
   3. Memberi feedback ringan saat admin mengirim form.
   ========================================================= */

(function () {
    "use strict";

    const replyForms = document.querySelectorAll("[data-admin-reply-form]");

    replyForms.forEach((form) => {
        const textarea = form.querySelector("[data-admin-reply-message]");
        const counter = form.querySelector("[data-admin-reply-counter]");
        const submitButton = form.querySelector("button[type='submit']");

        if (!textarea || !counter || !submitButton) {
            return;
        }

        const updateCounter = () => {
            const length = textarea.value.length;
            counter.textContent = `${length}/2000 karakter`;
        };

        textarea.addEventListener("input", updateCounter);
        updateCounter();

        form.addEventListener("submit", (event) => {
            const message = textarea.value.trim();

            if (message.length < 5) {
                event.preventDefault();
                textarea.focus();
                counter.textContent = "Balasan minimal 5 karakter.";
                return;
            }

            submitButton.disabled = true;
            submitButton.classList.add("is-loading");
            submitButton.textContent = "Mengirim...";
        });
    });


    // Menjaga posisi admin tetap berada di filter atau daftar tiket
    // setelah submit filter, update status, atau kirim balasan.
    function scrollToHashTarget() {
        if (!window.location.hash) {
            return;
        }

        const target = document.getElementById(
            window.location.hash.replace("#", "")
        );

        if (!target) {
            return;
        }

        window.setTimeout(function () {
            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }, 80);
    }

    scrollToHashTarget();

})();


/* =========================================================
   PATCH NAVIGASI HALUS DAN BACK-FORWARD CACHE
   =========================================================
   Menjaga halaman admin tidak menjadi putih saat tombol Back
   browser dipakai, dan menambah transisi keluar antarhalaman.
   ========================================================= */
(function () {
    "use strict";

    const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    function shouldAnimateNavigation(link, event) {
        if (!link || !link.href) {
            return false;
        }

        if (
            event.defaultPrevented ||
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey
        ) {
            return false;
        }

        if (link.target && link.target !== "_self") {
            return false;
        }

        const destination = new URL(link.href, window.location.href);
        const current = new URL(window.location.href);

        if (destination.origin !== current.origin) {
            return false;
        }

        if (
            destination.pathname === current.pathname &&
            destination.search === current.search &&
            destination.hash
        ) {
            return false;
        }

        return link.href !== window.location.href;
    }

    document.querySelectorAll("a[href]").forEach(function (link) {
        link.addEventListener("click", function (event) {
            if (!shouldAnimateNavigation(link, event)) {
                return;
            }

            if (prefersReducedMotion || typeof document.body.animate !== "function") {
                return;
            }

            event.preventDefault();
            const destination = link.href;

            const animation = document.body.animate(
                [{ opacity: 1 }, { opacity: 0 }],
                {
                    duration: 210,
                    easing: "ease-in",
                    fill: "forwards"
                }
            );

            let completed = false;

            function go() {
                if (completed) {
                    return;
                }
                completed = true;
                window.location.href = destination;
            }

            animation.addEventListener("finish", go);
            window.setTimeout(go, 380);
        });
    });

    window.addEventListener("pageshow", function (event) {
        document.body.style.opacity = "";

        if (event.persisted) {
            window.location.reload();
        }
    });
})();
