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
})();
