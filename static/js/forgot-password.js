/* =========================================================
   COMPASS CAMPUS — FORGOT-PASSWORD.JS
   File JavaScript untuk halaman forgot-password.html

   Fungsi utama:
   1. Validasi email
   2. Validasi kata sandi baru
   3. Memeriksa kesamaan konfirmasi kata sandi
   4. Menampilkan atau menyembunyikan kata sandi
   5. Menampilkan alert custom
   6. Menampilkan status loading
   7. Memberikan animasi dan transisi halaman

   PENTING:
   - Tidak ada data pengguna dummy.
   - JavaScript tidak memeriksa database.
   - Email terdaftar diperiksa oleh Flask/Python.
   - Password diperbarui melalui database MySQL.
   - Password harus di-hash oleh backend sebelum disimpan.
   ========================================================= */


"use strict";


/* =========================================================
   1. MENUNGGU STRUKTUR HTML SELESAI DIMUAT
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* Menandai bahwa JavaScript aktif */
    document.documentElement.classList.add("js-enabled");


    /* =====================================================
       2. MENGAMBIL ELEMEN DARI FORGOT-PASSWORD.HTML
       ===================================================== */

    const forgotPasswordForm =
        document.getElementById("forgot-password-form");

    const emailInput =
        document.getElementById("email");

    const newPasswordInput =
        document.getElementById("new-password");

    const confirmPasswordInput =
        document.getElementById("confirm-password");

    const newPasswordToggle =
        document.getElementById("new-password-toggle");

    const confirmPasswordToggle =
        document.getElementById("confirm-password-toggle");

    const submitButton =
        document.querySelector(".forgot-submit-button");

    const forgotCard =
        document.querySelector(".forgot-card");

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
       Menghormati pengaturan pengguna yang memilih
       untuk mengurangi animasi.
    */
    const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;


    /* =====================================================
       4. LIVE REGION UNTUK SCREEN READER
       ===================================================== */

    /*
       Elemen ini digunakan untuk mengumumkan pesan
       kepada pengguna pembaca layar.
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
     * @param {string} message
     */
    function announce(message) {
        liveRegion.textContent = "";

        window.setTimeout(function () {
            liveRegion.textContent = message;
        }, 50);
    }


    /* =====================================================
       5. ALERT CUSTOM
       ===================================================== */

    /**
     * Menghapus alert yang dibuat oleh JavaScript.
     */
    function removeClientAlert() {
        const existingAlert = document.getElementById(
            "forgot-client-alert"
        );

        if (existingAlert) {
            existingAlert.remove();
        }
    }


    /**
     * Menampilkan alert custom di bagian atas form.
     *
     * Style menggunakan class dari forgot-password.css:
     * .form-alert
     * .form-alert-error
     *
     * @param {string} message
     */
    function showClientAlert(message) {
        if (!forgotPasswordForm) {
            return;
        }

        removeClientAlert();

        const alertElement =
            document.createElement("div");

        alertElement.id =
            "forgot-client-alert";

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

        forgotPasswordForm.prepend(alertElement);

        /*
           Animasi alert hanya dijalankan jika pengguna
           tidak memilih Reduce Motion.
        */
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

        alertElement.focus();
        announce(message);
    }


    /* =====================================================
       6. ANIMASI MASUK HALAMAN
       ===================================================== */

    function playPageEnterAnimation() {
        if (
            prefersReducedMotion ||
            typeof document.body.animate !== "function"
        ) {
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


    /* =====================================================
       7. TAMPILKAN / SEMBUNYIKAN PASSWORD
       ===================================================== */

    /**
     * Mengatur tombol untuk melihat atau menyembunyikan
     * kolom kata sandi.
     *
     * @param {HTMLInputElement} inputElement
     * @param {HTMLButtonElement} toggleButton
     * @param {string} fieldLabel
     */
    function setupPasswordToggle(
        inputElement,
        toggleButton,
        fieldLabel
    ) {
        if (!inputElement || !toggleButton) {
            return;
        }

        toggleButton.addEventListener(
            "click",
            function () {

                const passwordIsHidden =
                    inputElement.type === "password";

                /*
                   Mengubah tipe input antara password dan text.
                */
                inputElement.type = passwordIsHidden
                    ? "text"
                    : "password";

                /*
                   Memperbarui label aksesibilitas tombol.
                */
                toggleButton.setAttribute(
                    "aria-label",
                    passwordIsHidden
                        ? `Sembunyikan ${fieldLabel}`
                        : `Tampilkan ${fieldLabel}`
                );

                toggleButton.classList.toggle(
                    "is-password-visible",
                    passwordIsHidden
                );

                announce(
                    passwordIsHidden
                        ? `${fieldLabel} ditampilkan.`
                        : `${fieldLabel} disembunyikan.`
                );

                inputElement.focus();

                /*
                   Mengembalikan posisi kursor ke bagian akhir.
                */
                const cursorPosition =
                    inputElement.value.length;

                try {
                    inputElement.setSelectionRange(
                        cursorPosition,
                        cursorPosition
                    );
                } catch (error) {
                    console.debug(
                        "Posisi kursor tidak dapat diatur.",
                        error
                    );
                }
            }
        );
    }


    setupPasswordToggle(
        newPasswordInput,
        newPasswordToggle,
        "kata sandi baru"
    );

    setupPasswordToggle(
        confirmPasswordInput,
        confirmPasswordToggle,
        "konfirmasi kata sandi"
    );


    /* =====================================================
       8. VALIDASI EMAIL
       ===================================================== */

    /**
     * Memeriksa apakah email sudah diisi
     * dan memiliki format yang benar.
     *
     * @returns {boolean}
     */
    function validateEmail() {
        if (!emailInput) {
            return true;
        }

        /*
           Menghapus spasi yang tidak diperlukan.
        */
        emailInput.value =
            emailInput.value.trim();

        emailInput.setCustomValidity("");

        if (emailInput.value === "") {
            emailInput.setCustomValidity(
                "Email wajib diisi."
            );

            emailInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        /*
           Pemeriksaan format menggunakan type="email"
           dari HTML.
        */
        if (emailInput.validity.typeMismatch) {
            emailInput.setCustomValidity(
                "Masukkan format email yang valid."
            );

            emailInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        emailInput.setAttribute(
            "aria-invalid",
            "false"
        );

        return true;
    }


    /* =====================================================
       9. VALIDASI KATA SANDI BARU
       ===================================================== */

    /**
     * Memeriksa kata sandi baru.
     *
     * @returns {boolean}
     */
    function validateNewPassword() {
        if (!newPasswordInput) {
            return true;
        }

        newPasswordInput.setCustomValidity("");

        if (newPasswordInput.value === "") {
            newPasswordInput.setCustomValidity(
                "Kata sandi baru wajib diisi."
            );

            newPasswordInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        if (newPasswordInput.value.length < 8) {
            newPasswordInput.setCustomValidity(
                "Kata sandi baru minimal terdiri dari 8 karakter."
            );

            newPasswordInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        /*
           Menghindari kata sandi yang hanya berisi spasi.
        */
        if (newPasswordInput.value.trim() === "") {
            newPasswordInput.setCustomValidity(
                "Kata sandi tidak boleh hanya berisi spasi."
            );

            newPasswordInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        newPasswordInput.setAttribute(
            "aria-invalid",
            "false"
        );

        return true;
    }


    /* =====================================================
       10. VALIDASI KONFIRMASI KATA SANDI
       ===================================================== */

    /**
     * Memeriksa apakah konfirmasi kata sandi
     * sama dengan kata sandi baru.
     *
     * @returns {boolean}
     */
    function validateConfirmPassword() {
        if (!confirmPasswordInput) {
            return true;
        }

        confirmPasswordInput.setCustomValidity("");

        if (confirmPasswordInput.value === "") {
            confirmPasswordInput.setCustomValidity(
                "Konfirmasi kata sandi wajib diisi."
            );

            confirmPasswordInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        if (
            newPasswordInput &&
            confirmPasswordInput.value !==
                newPasswordInput.value
        ) {
            confirmPasswordInput.setCustomValidity(
                "Konfirmasi kata sandi tidak sama dengan kata sandi baru."
            );

            confirmPasswordInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        confirmPasswordInput.setAttribute(
            "aria-invalid",
            "false"
        );

        return true;
    }


    /* =====================================================
       11. MENGHAPUS ERROR SAAT PENGGUNA MENGETIK
       ===================================================== */

    /**
     * Menghapus status error dari input.
     *
     * @param {HTMLInputElement} inputElement
     */
    function clearInputError(inputElement) {
        if (!inputElement) {
            return;
        }

        inputElement.setCustomValidity("");

        inputElement.removeAttribute(
            "aria-invalid"
        );

        removeClientAlert();
    }


    if (emailInput) {

        emailInput.addEventListener(
            "input",
            function () {
                clearInputError(emailInput);
            }
        );

        emailInput.addEventListener(
            "blur",
            validateEmail
        );
    }


    if (newPasswordInput) {

        newPasswordInput.addEventListener(
            "input",
            function () {

                clearInputError(
                    newPasswordInput
                );

                /*
                   Konfirmasi diperiksa ulang apabila pengguna
                   mengubah kata sandi utama.
                */
                if (
                    confirmPasswordInput &&
                    confirmPasswordInput.value !== ""
                ) {
                    validateConfirmPassword();
                }
            }
        );

        newPasswordInput.addEventListener(
            "blur",
            validateNewPassword
        );
    }


    if (confirmPasswordInput) {

        confirmPasswordInput.addEventListener(
            "input",
            function () {
                clearInputError(
                    confirmPasswordInput
                );
            }
        );

        confirmPasswordInput.addEventListener(
            "blur",
            validateConfirmPassword
        );
    }


    /* =====================================================
       12. ANIMASI FORM KETIKA TIDAK VALID
       ===================================================== */

    function shakeForgotCard() {
        if (
            !forgotCard ||
            prefersReducedMotion ||
            typeof forgotCard.animate !== "function"
        ) {
            return;
        }

        forgotCard.animate(
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
       13. MENENTUKAN PESAN ERROR UTAMA
       ===================================================== */

    /**
     * Mengambil pesan dari input pertama yang bermasalah.
     *
     * @returns {string}
     */
    function getValidationAlertMessage() {
        if (
            emailInput &&
            emailInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return emailInput.validationMessage;
        }

        if (
            newPasswordInput &&
            newPasswordInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return newPasswordInput
                .validationMessage;
        }

        if (
            confirmPasswordInput &&
            confirmPasswordInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return confirmPasswordInput
                .validationMessage;
        }

        return "Periksa kembali data pemulihan akunmu.";
    }


    /* =====================================================
       14. STATUS LOADING TOMBOL
       ===================================================== */

    function setSubmittingState() {
        if (!submitButton) {
            return;
        }

        submitButton.disabled = true;

        submitButton.setAttribute(
            "aria-busy",
            "true"
        );

        submitButton.classList.add(
            "is-loading"
        );

        if (submitButtonText) {
            submitButtonText.textContent =
                "Memperbarui...";
        }

        if (submitButtonIcon) {
            submitButtonIcon.style.opacity =
                "0.45";
        }

        announce(
            "Permintaan perubahan kata sandi sedang diproses."
        );
    }


    function resetSubmittingState() {
        if (!submitButton) {
            return;
        }

        submitButton.disabled = false;

        submitButton.removeAttribute(
            "aria-busy"
        );

        submitButton.classList.remove(
            "is-loading"
        );

        if (submitButtonText) {
            submitButtonText.textContent =
                "Ubah Kata Sandi";
        }

        if (submitButtonIcon) {
            submitButtonIcon.style.opacity =
                "";
        }
    }


    /* =====================================================
       15. PROSES SUBMIT FORM
       ===================================================== */

    if (forgotPasswordForm) {

        forgotPasswordForm.addEventListener(
            "submit",
            function (event) {

                removeClientAlert();

                const emailIsValid =
                    validateEmail();

                const passwordIsValid =
                    validateNewPassword();

                const confirmationIsValid =
                    validateConfirmPassword();

                const formIsValid =
                    emailIsValid &&
                    passwordIsValid &&
                    confirmationIsValid;

                /*
                   Apabila terdapat kesalahan,
                   pengiriman form dihentikan.
                */
                if (!formIsValid) {
                    event.preventDefault();

                    shakeForgotCard();

                    const alertMessage =
                        getValidationAlertMessage();

                    showClientAlert(alertMessage);

                    /*
                       Mengarahkan fokus ke input pertama
                       yang belum valid.
                    */
                    const firstInvalidInput =
                        forgotPasswordForm.querySelector(
                            '[aria-invalid="true"]'
                        );

                    if (firstInvalidInput) {
                        firstInvalidInput.focus();

                        if (
                            typeof firstInvalidInput
                                .reportValidity ===
                            "function"
                        ) {
                            firstInvalidInput
                                .reportValidity();
                        }
                    }

                    return;
                }

                /*
                   Jika valid, JavaScript tidak menghentikan submit.

                   Form dikirim menuju:
                   POST /forgot-password

                   Flask/Python nantinya akan:
                   1. Mencari email dalam database MySQL.
                   2. Menolak jika email tidak terdaftar.
                   3. Memastikan kedua password sama.
                   4. Melakukan hashing password baru.
                   5. Memperbarui password pada database.
                   6. Mengarahkan pengguna kembali ke login.
                */
                setSubmittingState();
            }
        );
    }


    /* =====================================================
       16. ALERT DARI BACKEND FLASK
       ===================================================== */

    /*
       Alert backend dapat digunakan untuk:
       - Email tidak terdaftar
       - Password gagal diperbarui
       - Gangguan database
       - Password berhasil diperbarui
    */
    const backendAlert =
        document.querySelector(
            ".form-alert:not(#forgot-client-alert)"
        );

    if (backendAlert) {

        backendAlert.setAttribute(
            "tabindex",
            "-1"
        );

        window.setTimeout(function () {
            backendAlert.focus();
        }, 420);

        if (
            !prefersReducedMotion &&
            typeof backendAlert.animate ===
                "function"
        ) {
            backendAlert.animate(
                [
                    {
                        opacity: 0,
                        transform:
                            "translateY(-10px)"
                    },
                    {
                        opacity: 1,
                        transform:
                            "translateY(0)"
                    }
                ],
                {
                    duration: 350,
                    easing: "ease-out",
                    fill: "both"
                }
            );
        }
    }


    /* =====================================================
       17. TRANSISI SAAT PINDAH HALAMAN
       ===================================================== */

    /**
     * Memeriksa apakah link dapat diberi transisi.
     *
     * @param {HTMLAnchorElement} link
     * @param {MouseEvent} event
     * @returns {boolean}
     */
    function canAnimateNavigation(
        link,
        event
    ) {
        if (!link || !link.href) {
            return false;
        }

        /*
           Jangan mengganggu Ctrl + Click,
           Shift + Click, dan klik tengah.
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
           Hanya link dalam website yang sama.
        */
        if (
            destination.origin !==
            window.location.origin
        ) {
            return false;
        }

        /*
           Jangan memberi transisi pada anchor
           di halaman yang sama.
        */
        if (
            destination.pathname ===
                window.location.pathname &&
            destination.search ===
                window.location.search &&
            destination.hash
        ) {
            return false;
        }

        return true;
    }


    const internalLinks =
        document.querySelectorAll("a[href]");

    internalLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                if (
                    !canAnimateNavigation(
                        link,
                        event
                    )
                ) {
                    return;
                }

                if (
                    prefersReducedMotion ||
                    typeof document.body.animate !==
                        "function"
                ) {
                    return;
                }

                event.preventDefault();

                const destination =
                    link.href;

                const exitAnimation =
                    document.body.animate(
                        [
                            {
                                opacity: 1,
                                transform:
                                    "translateY(0)"
                            },
                            {
                                opacity: 0,
                                transform:
                                    "translateY(-8px)"
                            }
                        ],
                        {
                            duration: 260,
                            easing: "ease-in",
                            fill: "forwards"
                        }
                    );

                exitAnimation.addEventListener(
                    "finish",
                    function () {
                        window.location.href =
                            destination;
                    }
                );
            }
        );
    });


    /* =====================================================
       18. RESET TOMBOL SAAT KEMBALI DARI BROWSER
       ===================================================== */

    /*
       Mengaktifkan kembali tombol apabila halaman
       dipulihkan dari Back-Forward Cache browser.
    */
    window.addEventListener(
        "pageshow",
        function () {
            resetSubmittingState();
        }
    );

});