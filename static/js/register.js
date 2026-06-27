/* =========================================================
   COMPASS CAMPUS — REGISTER.JS
   File JavaScript untuk halaman register.html

   Fungsi utama:
   1. Validasi nama lengkap
   2. Validasi format email
   3. Validasi panjang kata sandi
   4. Memastikan konfirmasi kata sandi sama
   5. Memastikan persetujuan kebijakan dicentang
   6. Menampilkan dan menyembunyikan password
   7. Menampilkan alert validasi dengan style register.css
   8. Menampilkan status loading saat form dikirim
   9. Memberikan animasi dan transisi halaman

   PENTING:
   - Tidak ada akun atau data dummy.
   - JavaScript tidak menyimpan data pengguna.
   - Pendaftaran sebenarnya diproses oleh Flask/Python.
   - Pemeriksaan email terdaftar dilakukan melalui MySQL.
   ========================================================= */


"use strict";


/* =========================================================
   1. MENUNGGU HALAMAN SELESAI DIMUAT
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* Menandai bahwa JavaScript aktif */
    document.documentElement.classList.add("js-enabled");


    /* =====================================================
       2. MENGAMBIL ELEMEN REGISTER.HTML
       ===================================================== */

    const registerForm =
        document.getElementById("register-form");

    const fullNameInput =
        document.getElementById("full-name");

    const emailInput =
        document.getElementById("email");

    const passwordInput =
        document.getElementById("password");

    const confirmPasswordInput =
        document.getElementById("confirm-password");

    const passwordToggle =
        document.getElementById("password-toggle");

    const confirmPasswordToggle =
        document.getElementById("confirm-password-toggle");

    const agreementInput =
        document.getElementById("agreement");

    const submitButton =
        document.querySelector(".auth-submit-button");

    const registerCard =
        document.querySelector(".register-card");

    const submitButtonText = submitButton
        ? submitButton.querySelector("span")
        : null;

    const submitButtonIcon = submitButton
        ? submitButton.querySelector("svg")
        : null;


    /* =====================================================
       3. PENGATURAN AKSESIBILITAS ANIMASI
       ===================================================== */

    const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;


    /* =====================================================
       4. LIVE REGION UNTUK SCREEN READER
       ===================================================== */

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
     * Mengumumkan pesan kepada pengguna screen reader.
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
       5. ALERT CUSTOM PADA FORM
       ===================================================== */

    /**
     * Menghapus alert validasi yang dibuat oleh JavaScript.
     */
    function removeClientAlert() {
        const oldAlert = document.getElementById(
            "register-client-alert"
        );

        if (oldAlert) {
            oldAlert.remove();
        }
    }


    /**
     * Menampilkan alert custom pada bagian atas form.
     *
     * Style alert menggunakan class yang sudah ada
     * di register.css:
     *
     * .form-alert
     * .form-alert-error
     *
     * @param {string} message
     */
    function showClientAlert(message) {
        if (!registerForm) {
            return;
        }

        removeClientAlert();

        const alertElement =
            document.createElement("div");

        alertElement.id =
            "register-client-alert";

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

        registerForm.prepend(alertElement);

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
       7. FUNGSI TAMPILKAN / SEMBUNYIKAN PASSWORD
       ===================================================== */

    /**
     * Mengatur tombol untuk menampilkan atau
     * menyembunyikan suatu input password.
     *
     * @param {HTMLInputElement} inputElement
     * @param {HTMLButtonElement} toggleButton
     * @param {string} fieldName
     */
    function setupPasswordToggle(
        inputElement,
        toggleButton,
        fieldName
    ) {
        if (!inputElement || !toggleButton) {
            return;
        }

        toggleButton.addEventListener(
            "click",
            function () {

                const passwordIsHidden =
                    inputElement.type === "password";

                inputElement.type = passwordIsHidden
                    ? "text"
                    : "password";

                toggleButton.setAttribute(
                    "aria-label",
                    passwordIsHidden
                        ? `Sembunyikan ${fieldName}`
                        : `Tampilkan ${fieldName}`
                );

                toggleButton.classList.toggle(
                    "is-password-visible",
                    passwordIsHidden
                );

                announce(
                    passwordIsHidden
                        ? `${fieldName} ditampilkan.`
                        : `${fieldName} disembunyikan.`
                );

                inputElement.focus();

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
        passwordInput,
        passwordToggle,
        "kata sandi"
    );

    setupPasswordToggle(
        confirmPasswordInput,
        confirmPasswordToggle,
        "konfirmasi kata sandi"
    );


    /* =====================================================
       8. VALIDASI NAMA LENGKAP
       ===================================================== */

    /**
     * Memeriksa nama lengkap.
     *
     * @returns {boolean}
     */
    function validateFullName() {
        if (!fullNameInput) {
            return true;
        }

        fullNameInput.value =
            fullNameInput.value
                .trim()
                .replace(/\s+/g, " ");

        fullNameInput.setCustomValidity("");

        if (fullNameInput.value === "") {
            fullNameInput.setCustomValidity(
                "Nama lengkap wajib diisi."
            );

            fullNameInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        if (fullNameInput.value.length < 3) {
            fullNameInput.setCustomValidity(
                "Nama lengkap minimal terdiri dari 3 karakter."
            );

            fullNameInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        fullNameInput.setAttribute(
            "aria-invalid",
            "false"
        );

        return true;
    }


    /* =====================================================
       9. VALIDASI EMAIL
       ===================================================== */

    /**
     * Memeriksa email kosong dan format email.
     *
     * @returns {boolean}
     */
    function validateEmail() {
        if (!emailInput) {
            return true;
        }

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
       10. VALIDASI KATA SANDI
       ===================================================== */

    /**
     * Memeriksa kata sandi kosong dan panjang minimum.
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
       11. VALIDASI KONFIRMASI KATA SANDI
       ===================================================== */

    /**
     * Memastikan konfirmasi password sama
     * dengan password utama.
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
            passwordInput &&
            confirmPasswordInput.value !==
                passwordInput.value
        ) {
            confirmPasswordInput.setCustomValidity(
                "Konfirmasi kata sandi tidak sama."
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
       12. VALIDASI PERSETUJUAN
       ===================================================== */

    /**
     * Memastikan pengguna menyetujui syarat dan kebijakan.
     *
     * @returns {boolean}
     */
    function validateAgreement() {
        if (!agreementInput) {
            return true;
        }

        agreementInput.setCustomValidity("");

        if (!agreementInput.checked) {
            agreementInput.setCustomValidity(
                "Kamu harus menyetujui Syarat dan Ketentuan serta Kebijakan Privasi."
            );

            agreementInput.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        agreementInput.setAttribute(
            "aria-invalid",
            "false"
        );

        return true;
    }


    /* =====================================================
       13. MENGHAPUS ERROR SAAT PENGGUNA MENGETIK
       ===================================================== */

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


    if (fullNameInput) {
        fullNameInput.addEventListener(
            "input",
            function () {
                clearInputError(fullNameInput);
            }
        );

        fullNameInput.addEventListener(
            "blur",
            validateFullName
        );
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


    if (passwordInput) {
        passwordInput.addEventListener(
            "input",
            function () {
                clearInputError(passwordInput);

                /*
                   Konfirmasi diperiksa ulang karena password
                   utama mungkin telah berubah.
                */
                if (
                    confirmPasswordInput &&
                    confirmPasswordInput.value !== ""
                ) {
                    validateConfirmPassword();
                }
            }
        );

        passwordInput.addEventListener(
            "blur",
            validatePassword
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


    if (agreementInput) {
        agreementInput.addEventListener(
            "change",
            function () {
                clearInputError(agreementInput);
                validateAgreement();
            }
        );
    }


    /* =====================================================
       14. ANIMASI FORM KETIKA TIDAK VALID
       ===================================================== */

    function shakeRegisterCard() {
        if (
            !registerCard ||
            prefersReducedMotion ||
            typeof registerCard.animate !== "function"
        ) {
            return;
        }

        registerCard.animate(
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
       15. MENENTUKAN PESAN ERROR UTAMA
       ===================================================== */

    /**
     * Menentukan pesan alert berdasarkan input
     * pertama yang belum valid.
     *
     * @returns {string}
     */
    function getValidationAlertMessage() {
        if (
            fullNameInput &&
            fullNameInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return fullNameInput.validationMessage;
        }

        if (
            emailInput &&
            emailInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return emailInput.validationMessage;
        }

        if (
            passwordInput &&
            passwordInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return passwordInput.validationMessage;
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

        if (
            agreementInput &&
            agreementInput.getAttribute(
                "aria-invalid"
            ) === "true"
        ) {
            return agreementInput
                .validationMessage;
        }

        return "Periksa kembali data pendaftaranmu.";
    }


    /* =====================================================
       16. STATUS LOADING TOMBOL
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
                "Mendaftarkan...";
        }

        if (submitButtonIcon) {
            submitButtonIcon.style.opacity =
                "0.45";
        }

        announce(
            "Data pendaftaran sedang dikirim."
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
                "Daftar Sekarang";
        }

        if (submitButtonIcon) {
            submitButtonIcon.style.opacity =
                "";
        }
    }


    /* =====================================================
       17. PROSES SUBMIT FORM
       ===================================================== */

    if (registerForm) {
        registerForm.addEventListener(
            "submit",
            function (event) {

                removeClientAlert();

                const nameIsValid =
                    validateFullName();

                const emailIsValid =
                    validateEmail();

                const passwordIsValid =
                    validatePassword();

                const confirmationIsValid =
                    validateConfirmPassword();

                const agreementIsValid =
                    validateAgreement();

                const formIsValid =
                    nameIsValid &&
                    emailIsValid &&
                    passwordIsValid &&
                    confirmationIsValid &&
                    agreementIsValid;

                /*
                   Menghentikan submit jika terdapat kesalahan.
                */
                if (!formIsValid) {
                    event.preventDefault();

                    shakeRegisterCard();

                    const alertMessage =
                        getValidationAlertMessage();

                    showClientAlert(alertMessage);

                    const firstInvalidInput =
                        registerForm.querySelector(
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
                   Jika valid, form tidak dihentikan.

                   Data akan dikirim menuju:
                   POST /register

                   Flask/Python nantinya akan:
                   1. Membersihkan dan memvalidasi input.
                   2. Memeriksa apakah email sudah terdaftar.
                   3. Melakukan hashing password.
                   4. Menyimpan pengguna ke MySQL.
                   5. Mengarahkan pengguna ke halaman login.
                */
                setSubmittingState();
            }
        );
    }


    /* =====================================================
       18. ALERT DARI BACKEND FLASK
       ===================================================== */

    /*
       Alert dari Flask biasanya digunakan untuk:
       - Email sudah terdaftar
       - Data gagal disimpan
       - Gangguan database
       - Pendaftaran berhasil
    */
    const backendAlert =
        document.querySelector(
            ".form-alert:not(#register-client-alert)"
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
       19. TRANSISI SAAT PINDAH HALAMAN
       ===================================================== */

    /**
     * Memeriksa apakah link dapat diberi animasi.
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

        if (
            destination.origin !==
            window.location.origin
        ) {
            return false;
        }

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
       20. RESET TOMBOL KETIKA KEMBALI DARI BROWSER
       ===================================================== */

    window.addEventListener(
        "pageshow",
        function () {
            resetSubmittingState();
        }
    );

});