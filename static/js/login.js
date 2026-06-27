/* =========================================================
   COMPASS CAMPUS — LOGIN.JS
   File JavaScript untuk halaman login.html

   Fungsi file ini:
   1. Menampilkan dan menyembunyikan kata sandi
   2. Melakukan validasi form pada sisi tampilan
   3. Memberikan animasi saat form tidak valid
   4. Memberikan status loading ketika login dikirim
   5. Memberikan transisi halaman yang halus
   6. Meningkatkan aksesibilitas halaman
   7. Menampilkan alert custom

   PENTING:
   - File ini TIDAK memeriksa akun pengguna.
   - File ini TIDAK menggunakan data dummy.
   - Pemeriksaan email dan password dilakukan oleh Flask.
   - Data akun akan diperiksa melalui database MySQL.
   ========================================================= */


"use strict";


/* =========================================================
   1. MENUNGGU SELURUH STRUKTUR HTML SELESAI DIMUAT
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* Menandai bahwa JavaScript aktif pada halaman */
    document.documentElement.classList.add("js-enabled");


    /* =====================================================
       2. MENGAMBIL ELEMEN PENTING DARI LOGIN.HTML
       ===================================================== */

    const loginForm = document.getElementById("login-form");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const passwordToggle = document.getElementById("password-toggle");
    const submitButton = document.querySelector(".auth-submit-button");

    /*
       Mengambil teks dan ikon di dalam tombol Masuk.
       Digunakan ketika tombol berubah menjadi "Memproses..."
    */
    const submitButtonText = submitButton
        ? submitButton.querySelector("span")
        : null;

    const submitButtonIcon = submitButton
        ? submitButton.querySelector("svg")
        : null;


    /* =====================================================
       3. PENGATURAN REDUCE MOTION
       ===================================================== */

    /*
       Memeriksa apakah pengguna memilih untuk mengurangi animasi
       melalui pengaturan sistem operasi atau browser.
    */
    const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;


    /* =====================================================
       4. AREA PENGUMUMAN UNTUK SCREEN READER
       ===================================================== */

    /*
       Elemen ini digunakan untuk mengumumkan status seperti:
       - Kata sandi ditampilkan
       - Form sedang diproses
       - Form belum lengkap

       Elemen tidak terlihat secara visual.
    */
    const liveRegion = document.createElement("div");

    liveRegion.setAttribute("aria-live", "polite");
    liveRegion.setAttribute("aria-atomic", "true");

    Object.assign(liveRegion.style, {
        position: "absolute",
        width: "1px",
        height: "1px",
        padding: "0",
        margin: "-1px",
        overflow: "hidden",
        clip: "rect(0, 0, 0, 0)",
        whiteSpace: "nowrap",
        border: "0"
    });

    document.body.appendChild(liveRegion);


    /**
     * Mengirim pesan kepada screen reader.
     *
     * @param {string} message Pesan yang akan diumumkan.
     */
    function announce(message) {
        liveRegion.textContent = "";

        window.setTimeout(function () {
            liveRegion.textContent = message;
        }, 50);
    }


    /* =====================================================
       5. ANIMASI MASUK HALAMAN
       ===================================================== */

    /*
       CSS login sudah memiliki animasi pada masing-masing elemen.
       Animasi ini menambahkan fade sederhana untuk seluruh halaman.
    */
    function playPageEnterAnimation() {
        if (prefersReducedMotion) {
            return;
        }

        document.body.animate(
            [
                {
                    opacity: 0
                },
                {
                    opacity: 1
                }
            ],
            {
                duration: 420,
                easing: "ease-out",
                fill: "both"
            }
        );
    }

    playPageEnterAnimation();

    /**
     * Menghapus alert validasi yang dibuat oleh JavaScript.
     *
     * Alert dari Flask tidak akan ikut dihapus karena
     * menggunakan elemen yang berbeda.
     */
    function removeClientAlert() {
        const existingAlert = document.getElementById(
            "login-client-alert"
        );

        if (existingAlert) {
            existingAlert.remove();
        }
    }


    /**
     * Menampilkan alert custom di bagian paling atas form login.
     *
     * Style alert berasal dari login.css:
     * .form-alert
     * .form-alert-error
     *
     * @param {string} message Pesan kesalahan yang ditampilkan.
     */
    function showClientAlert(message) {
        if (!loginForm) {
            return;
        }

        /* Mencegah munculnya lebih dari satu alert */
        removeClientAlert();

        const alertElement = document.createElement("div");

        alertElement.id = "login-client-alert";

        alertElement.className =
            "form-alert form-alert-error";

        alertElement.setAttribute(
            "role",
            "alert"
        );

        alertElement.setAttribute(
            "tabindex",
            "-1"
        );

        alertElement.textContent = message;

        /*
        Menempatkan alert di bagian paling atas
        sebelum input email.
        */
        loginForm.prepend(alertElement);

        /* Animasi alert masuk */
        if (
            !prefersReducedMotion &&
            typeof alertElement.animate === "function"
        ) {
            alertElement.animate(
                [
                    {
                        opacity: 0,
                        transform: "translateY(-10px)"
                    },
                    {
                        opacity: 1,
                        transform: "translateY(0)"
                    }
                ],
                {
                    duration: 320,
                    easing: "ease-out",
                    fill: "both"
                }
            );
        }

        /* Mengumumkan pesan kepada screen reader */
        announce(message);
    }


    /* =====================================================
       6. TAMPILKAN ATAU SEMBUNYIKAN PASSWORD
       ===================================================== */

    if (passwordToggle && passwordInput) {

        passwordToggle.addEventListener("click", function () {

            const passwordIsHidden =
                passwordInput.type === "password";

            /*
               Jika awalnya password, ubah menjadi text.
               Jika awalnya text, ubah kembali menjadi password.
            */
            passwordInput.type = passwordIsHidden
                ? "text"
                : "password";

            /*
               Memperbarui label tombol untuk aksesibilitas.
            */
            passwordToggle.setAttribute(
                "aria-label",
                passwordIsHidden
                    ? "Sembunyikan kata sandi"
                    : "Tampilkan kata sandi"
            );

            /*
               Class ini dapat digunakan nanti jika ingin
               mengganti bentuk ikon mata melalui CSS.
            */
            passwordToggle.classList.toggle(
                "is-password-visible",
                passwordIsHidden
            );

            announce(
                passwordIsHidden
                    ? "Kata sandi ditampilkan."
                    : "Kata sandi disembunyikan."
            );

            /*
               Mengembalikan fokus ke kolom password
               setelah tombol ditekan.
            */
            passwordInput.focus();

            /*
               Menempatkan kursor di bagian akhir password.
            */
            const passwordLength = passwordInput.value.length;

            try {
                passwordInput.setSelectionRange(
                    passwordLength,
                    passwordLength
                );
            } catch (error) {
                /*
                   Beberapa browser lama mungkin tidak mendukungnya.
                   Login tetap dapat digunakan tanpa fungsi ini.
                */
                console.debug(
                    "Posisi kursor password tidak dapat diatur.",
                    error
                );
            }
        });
    }


    /* =====================================================
       7. VALIDASI EMAIL
       ===================================================== */

    /**
     * Memeriksa apakah kolom email telah diisi dengan format benar.
     *
     * @returns {boolean}
     */
    function validateEmail() {
        if (!emailInput) {
            return true;
        }

        /*
           Menghapus spasi di awal dan akhir email.
        */
        emailInput.value = emailInput.value.trim();

        /*
           Menghapus pesan validasi lama sebelum memeriksa ulang.
        */
        emailInput.setCustomValidity("");

        if (emailInput.value === "") {
            emailInput.setCustomValidity(
                "Email wajib diisi."
            );

            emailInput.setAttribute("aria-invalid", "true");

            return false;
        }

        /*
           Browser memeriksa format karena input menggunakan:
           type="email"
        */
        if (emailInput.validity.typeMismatch) {
            emailInput.setCustomValidity(
                "Masukkan format email yang valid."
            );

            emailInput.setAttribute("aria-invalid", "true");

            return false;
        }

        emailInput.setAttribute("aria-invalid", "false");

        return true;
    }


    /* =====================================================
       8. VALIDASI PASSWORD
       ===================================================== */

    /**
     * Memeriksa apakah password telah diisi dan memenuhi
     * panjang minimal.
     *
     * @returns {boolean}
     */
    function validatePassword() {
        if (!passwordInput) {
            return true;
        }

        passwordInput.setCustomValidity("");

        if (passwordInput.value === "") {
            passwordInput.setCustomValidity(
                "Kata sandi wajib diisi."
            );

            passwordInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        if (passwordInput.value.length < 8) {
            passwordInput.setCustomValidity(
                "Kata sandi minimal terdiri dari 8 karakter."
            );

            passwordInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        passwordInput.setAttribute(
            "aria-invalid",
            "false"
        );

        return true;
    }


    /* =====================================================
       9. VALIDASI SAAT PENGGUNA MENGETIK
       ===================================================== */

    if (emailInput) {

        emailInput.addEventListener("input", function () {

            /*
            Menghapus status error ketika pengguna
            mulai memperbaiki email.
            */
            emailInput.setCustomValidity("");
            emailInput.removeAttribute("aria-invalid");

            /* Menghapus alert custom lama */
            removeClientAlert();
        });

        emailInput.addEventListener("blur", function () {
            validateEmail();
        });
    }


    if (passwordInput) {

        passwordInput.addEventListener("input", function () {

            /*
            Menghapus status error ketika pengguna
            mulai memperbaiki kata sandi.
            */
            passwordInput.setCustomValidity("");
            passwordInput.removeAttribute("aria-invalid");

            /* Menghapus alert custom lama */
            removeClientAlert();
        });

        passwordInput.addEventListener("blur", function () {
            validatePassword();
        });
    }

    /**
     * Mengambil pesan error dari input pertama
     * yang belum memenuhi validasi.
     *
     * @returns {string}
     */
    function getValidationAlertMessage() {

        /* Kesalahan pada email */
        if (
            emailInput &&
            emailInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return (
                emailInput.validationMessage ||
                "Periksa kembali alamat email."
            );
        }

        /* Kesalahan pada kata sandi */
        if (
            passwordInput &&
            passwordInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return (
                passwordInput.validationMessage ||
                "Periksa kembali kata sandi."
            );
        }

        return "Periksa kembali data loginmu.";
    }


    /* =====================================================
       10. ANIMASI FORM KETIKA DATA TIDAK VALID
       ===================================================== */

    /**
     * Memberikan animasi goyang ringan pada kartu login.
     */
    function shakeLoginCard() {
        const loginCard = document.querySelector(".auth-card");

        if (!loginCard || prefersReducedMotion) {
            return;
        }

        loginCard.animate(
            [
                {
                    transform: "translateX(0)"
                },
                {
                    transform: "translateX(-7px)"
                },
                {
                    transform: "translateX(7px)"
                },
                {
                    transform: "translateX(-5px)"
                },
                {
                    transform: "translateX(5px)"
                },
                {
                    transform: "translateX(0)"
                }
            ],
            {
                duration: 380,
                easing: "ease-out"
            }
        );
    }


    /* =====================================================
       11. MENGUBAH TOMBOL MENJADI STATUS LOADING
       ===================================================== */

    function setSubmittingState() {
        if (!submitButton) {
            return;
        }

        submitButton.disabled = true;
        submitButton.setAttribute("aria-busy", "true");
        submitButton.classList.add("is-loading");

        if (submitButtonText) {
            submitButtonText.textContent = "Memproses...";
        }

        if (submitButtonIcon) {
            submitButtonIcon.style.opacity = "0.45";
        }

        announce(
            "Data login sedang dikirim untuk diperiksa."
        );
    }


    /**
     * Mengembalikan tombol ke kondisi normal.
     * Berguna ketika pengguna kembali ke halaman melalui tombol Back.
     */
    function resetSubmittingState() {
        if (!submitButton) {
            return;
        }

        submitButton.disabled = false;
        submitButton.removeAttribute("aria-busy");
        submitButton.classList.remove("is-loading");

        if (submitButtonText) {
            submitButtonText.textContent = "Masuk";
        }

        if (submitButtonIcon) {
            submitButtonIcon.style.opacity = "";
        }
    }


    /* =====================================================
       12. PROSES SUBMIT FORM
       ===================================================== */

    if (loginForm) {

        loginForm.addEventListener("submit", function (event) {

            /*
            Menghapus alert client sebelumnya sebelum
            melakukan pemeriksaan ulang.
            */
            removeClientAlert();

            const emailIsValid = validateEmail();
            const passwordIsValid = validatePassword();

            const formIsValid =
                emailIsValid &&
                passwordIsValid;

            /*
            Apabila email atau kata sandi belum benar,
            proses pengiriman dihentikan.
            */
            if (!formIsValid) {
                event.preventDefault();

                /* Memberikan efek goyang pada kartu */
                shakeLoginCard();

                /*
                Menentukan pesan berdasarkan input
                pertama yang mengalami kesalahan.
                */
                const alertMessage =
                    getValidationAlertMessage();

                /*
                Menampilkan pesan pada alert custom,
                bukan hanya popup bawaan browser.
                */
                showClientAlert(alertMessage);

                /*
                Memindahkan fokus ke input pertama
                yang masih salah.
                */
                const firstInvalidInput =
                    loginForm.querySelector(
                        '[aria-invalid="true"]'
                    );

                if (firstInvalidInput) {
                    firstInvalidInput.focus();
                }

                return;
            }

            /*
            Jika seluruh input valid, JavaScript tidak
            menghentikan proses submit.

            Form akan dikirim menuju:
            POST /login

            Flask/Python akan:
            1. Mencari email dalam database MySQL.
            2. Memeriksa hash kata sandi.
            3. Mengirim alert jika akun tidak cocok.
            4. Membuat session jika login berhasil.
            */
            setSubmittingState();
        });
    }


    /* =====================================================
       13. MENAMPILKAN ALERT DARI FLASK
       ===================================================== */

    /*
       Jika backend mengirimkan pesan error atau sukses,
       elemen tersebut akan diberi fokus agar mudah ditemukan.
    */
    const backendAlert = document.querySelector(
        ".form-alert:not(#login-client-alert)"
    );

    if (
        !prefersReducedMotion &&
        typeof backendAlert.animate === "function"
    ) {
        backendAlert.animate(
            [
                {
                    opacity: 0,
                    transform: "translateY(-10px)"
                },
                {
                    opacity: 1,
                    transform: "translateY(0)"
                }
            ],
            {
                duration: 380,
                easing: "ease-out",
                fill: "both"
            }
        );
    }


    /* =====================================================
       14. TRANSISI SAAT PINDAH HALAMAN
       ===================================================== */

    /**
     * Memeriksa apakah sebuah link aman diberi transisi.
     *
     * @param {HTMLAnchorElement} link
     * @param {MouseEvent} event
     * @returns {boolean}
     */
    function canAnimateNavigation(link, event) {

        if (!link || !link.href) {
            return false;
        }

        /*
           Jangan mengganggu fungsi Ctrl + Click,
           Shift + Click, atau klik tombol tengah mouse.
        */
        if (
            event.ctrlKey ||
            event.metaKey ||
            event.shiftKey ||
            event.altKey ||
            event.button !== 0
        ) {
            return false;
        }

        if (
            link.hasAttribute("download") ||
            link.target === "_blank"
        ) {
            return false;
        }

        const destination = new URL(
            link.href,
            window.location.href
        );

        /*
           Hanya memberi transisi pada link dalam website yang sama.
        */
        if (destination.origin !== window.location.origin) {
            return false;
        }

        /*
           Jangan memberi transisi apabila link hanya menuju
           anchor pada halaman yang sama.
        */
        if (
            destination.pathname === window.location.pathname &&
            destination.search === window.location.search &&
            destination.hash
        ) {
            return false;
        }

        return true;
    }


    const internalLinks = document.querySelectorAll("a[href]");

    internalLinks.forEach(function (link) {

        link.addEventListener("click", function (event) {

            if (!canAnimateNavigation(link, event)) {
                return;
            }

            /*
               Apabila pengguna memilih reduce motion,
               halaman langsung berpindah tanpa animasi.
            */
            if (prefersReducedMotion) {
                return;
            }

            event.preventDefault();

            const destination = link.href;

            const pageExitAnimation = document.body.animate(
                [
                    {
                        opacity: 1,
                        transform: "translateY(0)"
                    },
                    {
                        opacity: 0,
                        transform: "translateY(-8px)"
                    }
                ],
                {
                    duration: 260,
                    easing: "ease-in",
                    fill: "forwards"
                }
            );

            pageExitAnimation.addEventListener(
                "finish",
                function () {
                    window.location.href = destination;
                }
            );
        });
    });


    /* =====================================================
       15. RESET TOMBOL KETIKA KEMBALI DARI BROWSER
       ===================================================== */

    /*
       Browser dapat menyimpan keadaan halaman melalui
       Back-Forward Cache. Tombol perlu diaktifkan kembali
       ketika pengguna menekan tombol Back.
    */
    window.addEventListener("pageshow", function () {
        resetSubmittingState();
    });

});