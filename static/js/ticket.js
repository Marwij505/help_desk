/* =========================================================
   COMPASS CAMPUS - TICKET HELP DESK JAVASCRIPT
   File: static/js/ticket.js

   Fungsi:
   1. Menghitung jumlah karakter isi pertanyaan.
   2. Memberi status loading saat form dikirim.
   3. Menghilangkan pesan flash setelah beberapa detik.
   ========================================================= */

(function () {
    "use strict";

    const ticketMessage = document.querySelector("[data-ticket-message]");
    const ticketCounter = document.querySelector("[data-ticket-counter]");
    const ticketForm = document.querySelector("[data-ticket-form]");
    const ticketSubmit = document.querySelector("[data-ticket-submit]");
    const flashItems = document.querySelectorAll(".ticket-flash");

    // Mengupdate penghitung karakter textarea.
    function updateCounter() {
        if (!ticketMessage || !ticketCounter) {
            return;
        }

        ticketCounter.textContent = String(ticketMessage.value.length);
    }

    if (ticketMessage) {
        updateCounter();
        ticketMessage.addEventListener("input", updateCounter);
    }

    // Memberi feedback saat form dikirim agar user tahu sistem memproses tiket.
    if (ticketForm && ticketSubmit) {
        ticketForm.addEventListener("submit", function () {
            ticketSubmit.classList.add("is-loading");
            ticketSubmit.textContent = "Mengirim tiket...";
        });
    }

    // Flash message tetap muncul cukup lama, lalu hilang halus.
    if (flashItems.length > 0) {
        window.setTimeout(function () {
            flashItems.forEach(function (item) {
                item.style.opacity = "0";
                item.style.transform = "translateY(-6px)";
                item.style.transition = "opacity 220ms ease, transform 220ms ease";
            });
        }, 5200);
    }


    // Jika URL memiliki anchor, tetap fokus ke bagian tersebut setelah reload.
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
   Menjaga halaman ticket tidak berubah menjadi putih saat user
   memakai tombol Back browser, serta memberi transisi keluar.
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
