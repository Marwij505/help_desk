/* =========================================================
   COMPASS CAMPUS — INDEX.JS
   File JavaScript untuk halaman index.html

   Fungsi utama:
   1. Mengaktifkan menu navigasi mobile
   2. Membuka dan menutup panel pencarian global
   3. Memvalidasi form pencarian
   4. Mengisi input dari tombol saran pencarian
   5. Menjalankan animasi saat scroll
   6. Menandai menu navigasi yang sedang aktif
   7. Mengatur FAQ agar lebih rapi
   8. Memperbarui tahun footer secara otomatis
   9. Menambahkan transisi perpindahan halaman
   10. Meningkatkan aksesibilitas keyboard

   PENTING:
   - File ini tidak menggunakan data akun dummy.
   - Proses pencarian sebenarnya akan ditangani Flask.
   - Data kampus nantinya berasal dari backend/database/API.
   ========================================================= */


"use strict";


/* =========================================================
   1. MENUNGGU STRUKTUR HTML SELESAI DIMUAT
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /*
       Class ini mengaktifkan aturan animasi di index.css,
       khususnya pada elemen dengan class .reveal.
    */
    document.documentElement.classList.add("js-enabled");


    /* =====================================================
       2. MENGAMBIL ELEMEN PENTING DARI INDEX.HTML
       ===================================================== */

    /* Header dan navigasi */
    const siteHeader =
        document.getElementById("site-header");

    const mobileMenuButton =
        document.getElementById("mobile-menu-button");

    const primaryNavigation =
        document.getElementById("primary-navigation");

    const navigationLinks =
        Array.from(
            document.querySelectorAll(
                ".primary-navigation .nav-link"
            )
        );


    /* Pencarian global */
    const openSearchButton =
        document.getElementById("open-search-button");

    const closeSearchButton =
        document.getElementById("close-search-button");

    const globalSearchOverlay =
        document.getElementById("global-search-overlay");

    const globalSearchDialog =
        globalSearchOverlay
            ? globalSearchOverlay.querySelector(
                ".global-search-dialog"
            )
            : null;

    const globalSearchForm =
        globalSearchOverlay
            ? globalSearchOverlay.querySelector(
                ".global-search-form"
            )
            : null;

    const globalSearchInput =
        document.getElementById("global-search-input");

    const suggestionButtons =
        document.querySelectorAll(
            ".suggestion-list button"
        );


    /* Pencarian utama */
    const mainSearchForm =
        document.querySelector(".main-search-form");

    const mainSearchInput =
        document.getElementById("main-search-input");


    /* Elemen lain */
    const faqItems =
        Array.from(
            document.querySelectorAll(".faq-item")
        );

    const revealElements =
        Array.from(
            document.querySelectorAll(".reveal")
        );

    const currentYearElement =
        document.getElementById("current-year");


    /* =====================================================
       3. PENGATURAN AKSESIBILITAS ANIMASI
       ===================================================== */

    /*
       Jika pengguna mengaktifkan Reduce Motion pada perangkat,
       animasi yang tidak diperlukan akan dikurangi.
    */
    const prefersReducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;


    /* Media query yang sama dengan index.css */
    const mobileMediaQuery = window.matchMedia(
        "(max-width: 820px)"
    );


    /* =====================================================
       4. LIVE REGION UNTUK SCREEN READER
       ===================================================== */

    /*
       Live region digunakan untuk mengumumkan perubahan seperti:
       - Menu dibuka
       - Pencarian dibuka
       - Input pencarian kosong
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
       5. MEMPERBARUI TAHUN FOOTER
       ===================================================== */

    if (currentYearElement) {
        currentYearElement.textContent =
            String(new Date().getFullYear());
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
       7. MENU NAVIGASI MOBILE
       ===================================================== */

    /**
     * Memeriksa apakah menu mobile sedang terbuka.
     *
     * @returns {boolean}
     */
    function mobileMenuIsOpen() {
        return Boolean(
            primaryNavigation &&
            primaryNavigation.classList.contains(
                "is-open"
            )
        );
    }


    /**
     * Membuka menu navigasi mobile.
     */
    function openMobileMenu() {
        if (
            !mobileMenuButton ||
            !primaryNavigation
        ) {
            return;
        }

        primaryNavigation.classList.add("is-open");

        mobileMenuButton.setAttribute(
            "aria-expanded",
            "true"
        );

        mobileMenuButton.setAttribute(
            "aria-label",
            "Tutup menu navigasi"
        );

        document.body.classList.add("menu-open");

        announce("Menu navigasi dibuka.");
    }


    /**
     * Menutup menu navigasi mobile.
     *
     * @param {boolean} restoreFocus
     */
    function closeMobileMenu(
        restoreFocus = false
    ) {
        if (
            !mobileMenuButton ||
            !primaryNavigation
        ) {
            return;
        }

        primaryNavigation.classList.remove("is-open");

        mobileMenuButton.setAttribute(
            "aria-expanded",
            "false"
        );

        mobileMenuButton.setAttribute(
            "aria-label",
            "Buka menu navigasi"
        );

        document.body.classList.remove("menu-open");

        if (restoreFocus) {
            mobileMenuButton.focus();
        }
    }


    /**
     * Membuka atau menutup menu berdasarkan kondisinya.
     */
    function toggleMobileMenu() {
        if (mobileMenuIsOpen()) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    }


    if (mobileMenuButton) {
        mobileMenuButton.addEventListener(
            "click",
            function (event) {
                event.stopPropagation();
                toggleMobileMenu();
            }
        );
    }


    /*
       Menutup menu ketika salah satu link navigasi ditekan.
    */
    navigationLinks.forEach(function (link) {
        link.addEventListener("click", function () {
            closeMobileMenu();
        });
    });


    /*
       Menutup menu ketika pengguna mengeklik area
       di luar navigasi dan tombol menu.
    */
    document.addEventListener("click", function (event) {
        if (
            !mobileMenuIsOpen() ||
            !primaryNavigation ||
            !mobileMenuButton
        ) {
            return;
        }

        const clickedInsideNavigation =
            primaryNavigation.contains(event.target);

        const clickedMenuButton =
            mobileMenuButton.contains(event.target);

        if (
            !clickedInsideNavigation &&
            !clickedMenuButton
        ) {
            closeMobileMenu();
        }
    });


    /**
     * Menyesuaikan menu ketika ukuran layar berubah.
     */
    function handleResponsiveMenuChange(event) {
        if (!event.matches) {
            closeMobileMenu();
        }
    }


    if (
        typeof mobileMediaQuery.addEventListener ===
        "function"
    ) {
        mobileMediaQuery.addEventListener(
            "change",
            handleResponsiveMenuChange
        );
    } else {
        /*
           Dukungan untuk browser lama.
        */
        mobileMediaQuery.addListener(
            handleResponsiveMenuChange
        );
    }


    /* =====================================================
       8. PANEL PENCARIAN GLOBAL
       ===================================================== */

    /*
       Menyimpan elemen yang sebelumnya memiliki fokus,
       agar fokus dapat dikembalikan setelah modal ditutup.
    */
    let lastFocusedElement = null;


    /**
     * Memeriksa apakah pencarian global sedang terbuka.
     *
     * @returns {boolean}
     */
    function globalSearchIsOpen() {
        return Boolean(
            globalSearchOverlay &&
            globalSearchOverlay.classList.contains(
                "is-open"
            )
        );
    }


    /**
     * Membuka panel pencarian global.
     */
    function openGlobalSearch() {
        if (
            !globalSearchOverlay ||
            !globalSearchInput
        ) {
            return;
        }

        /*
           Menu mobile ditutup agar tidak bertumpuk
           dengan panel pencarian.
        */
        closeMobileMenu();

        lastFocusedElement =
            document.activeElement instanceof HTMLElement
                ? document.activeElement
                : null;

        globalSearchOverlay.classList.add(
            "is-open"
        );

        globalSearchOverlay.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "search-open"
        );

        if (openSearchButton) {
            openSearchButton.setAttribute(
                "aria-expanded",
                "true"
            );
        }

        /*
           Memberikan waktu kepada animasi modal
           sebelum fokus diarahkan ke input.
        */
        window.setTimeout(function () {
            globalSearchInput.focus();
        }, prefersReducedMotion ? 0 : 180);

        announce("Pencarian global dibuka.");
    }


    /**
     * Menutup panel pencarian global.
     *
     * @param {boolean} restoreFocus
     */
    function closeGlobalSearch(
        restoreFocus = true
    ) {
        if (!globalSearchOverlay) {
            return;
        }

        globalSearchOverlay.classList.remove(
            "is-open"
        );

        globalSearchOverlay.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "search-open"
        );

        if (openSearchButton) {
            openSearchButton.setAttribute(
                "aria-expanded",
                "false"
            );
        }

        if (
            restoreFocus &&
            lastFocusedElement &&
            typeof lastFocusedElement.focus ===
                "function"
        ) {
            lastFocusedElement.focus();
        }

        announce("Pencarian global ditutup.");
    }


    if (openSearchButton) {

        /*
           Melengkapi atribut aksesibilitas tombol pencarian.
        */
        openSearchButton.setAttribute(
            "aria-controls",
            "global-search-overlay"
        );

        openSearchButton.setAttribute(
            "aria-expanded",
            "false"
        );

        openSearchButton.addEventListener(
            "click",
            openGlobalSearch
        );
    }


    if (closeSearchButton) {
        closeSearchButton.addEventListener(
            "click",
            function () {
                closeGlobalSearch();
            }
        );
    }


    /*
       Panel ditutup apabila pengguna menekan area gelap
       di luar kotak pencarian.
    */
    if (globalSearchOverlay) {
        globalSearchOverlay.addEventListener(
            "mousedown",
            function (event) {
                if (
                    event.target ===
                    globalSearchOverlay
                ) {
                    closeGlobalSearch();
                }
            }
        );
    }


    /* =====================================================
       9. FOCUS TRAP PADA MODAL PENCARIAN
       ===================================================== */

    /**
     * Mengambil seluruh elemen yang dapat menerima fokus
     * di dalam dialog pencarian.
     *
     * @returns {HTMLElement[]}
     */
    function getSearchFocusableElements() {
        if (!globalSearchDialog) {
            return [];
        }

        return Array.from(
            globalSearchDialog.querySelectorAll(
                [
                    "a[href]",
                    "button:not([disabled])",
                    "input:not([disabled])",
                    "select:not([disabled])",
                    "textarea:not([disabled])",
                    '[tabindex]:not([tabindex="-1"])'
                ].join(",")
            )
        ).filter(function (element) {
            return (
                element instanceof HTMLElement &&
                element.offsetParent !== null
            );
        });
    }


    /**
     * Menjaga fokus keyboard tetap berada di modal
     * selama modal pencarian terbuka.
     *
     * @param {KeyboardEvent} event
     */
    function trapSearchFocus(event) {
        if (
            event.key !== "Tab" ||
            !globalSearchIsOpen()
        ) {
            return;
        }

        const focusableElements =
            getSearchFocusableElements();

        if (focusableElements.length === 0) {
            event.preventDefault();
            return;
        }

        const firstElement =
            focusableElements[0];

        const lastElement =
            focusableElements[
                focusableElements.length - 1
            ];

        if (
            event.shiftKey &&
            document.activeElement === firstElement
        ) {
            event.preventDefault();
            lastElement.focus();
        } else if (
            !event.shiftKey &&
            document.activeElement === lastElement
        ) {
            event.preventDefault();
            firstElement.focus();
        }
    }


    /* =====================================================
       10. KONTROL KEYBOARD GLOBAL
       ===================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            /*
               Menutup menu atau modal dengan tombol Escape.
            */
            if (event.key === "Escape") {

                if (globalSearchIsOpen()) {
                    event.preventDefault();
                    closeGlobalSearch();
                    return;
                }

                if (mobileMenuIsOpen()) {
                    event.preventDefault();
                    closeMobileMenu(true);
                }
            }

            trapSearchFocus(event);
        }
    );


    /* =====================================================
       11. SARAN PENCARIAN
       ===================================================== */

    suggestionButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                if (!globalSearchInput) {
                    return;
                }

                const suggestion =
                    button.textContent.trim();

                globalSearchInput.value =
                    suggestion;

                globalSearchInput.setCustomValidity("");

                globalSearchInput.removeAttribute(
                    "aria-invalid"
                );

                globalSearchInput.focus();

                /*
                   Menempatkan kursor di akhir teks.
                */
                const cursorPosition =
                    globalSearchInput.value.length;

                globalSearchInput.setSelectionRange(
                    cursorPosition,
                    cursorPosition
                );

                announce(
                    `Saran pencarian dipilih: ${suggestion}.`
                );
            }
        );
    });


    /* =====================================================
       12. VALIDASI INPUT PENCARIAN
       ===================================================== */

    /**
     * Memvalidasi input pencarian.
     *
     * @param {HTMLInputElement|null} inputElement
     * @returns {boolean}
     */
    function validateSearchInput(inputElement) {
        if (!inputElement) {
            return true;
        }

        inputElement.value =
            inputElement.value.trim();

        inputElement.setCustomValidity("");

        if (inputElement.value === "") {
            inputElement.setCustomValidity(
                "Masukkan kata kunci pencarian terlebih dahulu."
            );

            inputElement.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        if (inputElement.value.length < 2) {
            inputElement.setCustomValidity(
                "Kata kunci pencarian minimal terdiri dari 2 karakter."
            );

            inputElement.setAttribute(
                "aria-invalid",
                "true"
            );

            return false;
        }

        inputElement.setAttribute(
            "aria-invalid",
            "false"
        );

        return true;
    }


    /**
     * Mengatur validasi pada sebuah form pencarian.
     *
     * @param {HTMLFormElement|null} formElement
     * @param {HTMLInputElement|null} inputElement
     */
    function setupSearchForm(
        formElement,
        inputElement
    ) {
        if (!formElement || !inputElement) {
            return;
        }

        inputElement.addEventListener(
            "input",
            function () {
                inputElement.setCustomValidity("");

                inputElement.removeAttribute(
                    "aria-invalid"
                );
            }
        );

        formElement.addEventListener(
            "submit",
            function (event) {

                const searchIsValid =
                    validateSearchInput(
                        inputElement
                    );

                if (!searchIsValid) {
                    event.preventDefault();

                    inputElement.focus();

                    inputElement.reportValidity();

                    announce(
                        inputElement.validationMessage
                    );

                    return;
                }

                /*
                   Form tidak dihentikan jika valid.

                   Data pencarian akan dikirim ke:
                   GET /search?q=kata-kunci

                   Route tersebut diproses oleh Flask melalui endpoint /search.
                */
                announce(
                    `Mencari ${inputElement.value}.`
                );
            }
        );
    }


    setupSearchForm(
        mainSearchForm,
        mainSearchInput
    );

    setupSearchForm(
        globalSearchForm,
        globalSearchInput
    );


    /* =====================================================
       12B. MENJAGA POSISI SETELAH FORM DIPROSES
       ===================================================== */

    /**
     * Scroll otomatis ke section yang diminta oleh URL.
     * Dipakai agar pencarian yang gagal tetap berada di Program Studi,
     * bukan kembali ke bagian paling atas homepage.
     */
    function scrollToRequestedSection() {
        const parameters = new URLSearchParams(window.location.search);

        const focusFromQuery = parameters.get("focus") || "";

        const focusFromHash = window.location.hash
            ? window.location.hash.replace("#", "")
            : "";

        const targetId = focusFromHash || focusFromQuery;

        if (!targetId) {
            return;
        }

        const targetElement = document.getElementById(targetId);

        if (!targetElement) {
            return;
        }

        window.setTimeout(function () {
            targetElement.scrollIntoView({
                behavior: prefersReducedMotion ? "auto" : "smooth",
                block: "start"
            });

            if (targetElement.id) {
                setActiveNavigation(targetElement.id);
            }
        }, 80);
    }

    scrollToRequestedSection();


    /* =====================================================
       13. FAQ INTERAKTIF
       ===================================================== */

    /*
       Ketika satu FAQ dibuka, FAQ lain akan ditutup.
       Elemen <details> tetap dapat bekerja tanpa JavaScript.
    */
    faqItems.forEach(function (faqItem) {

        const faqSummary =
            faqItem.querySelector("summary");

        if (faqSummary) {
            faqSummary.setAttribute(
                "aria-expanded",
                faqItem.open ? "true" : "false"
            );
        }

        faqItem.addEventListener(
            "toggle",
            function () {

                if (faqSummary) {
                    faqSummary.setAttribute(
                        "aria-expanded",
                        faqItem.open
                            ? "true"
                            : "false"
                    );
                }

                if (!faqItem.open) {
                    return;
                }

                faqItems.forEach(function (otherItem) {
                    if (otherItem === faqItem) {
                        return;
                    }

                    otherItem.open = false;

                    const otherSummary =
                        otherItem.querySelector(
                            "summary"
                        );

                    if (otherSummary) {
                        otherSummary.setAttribute(
                            "aria-expanded",
                            "false"
                        );
                    }
                });
            }
        );
    });


    /* =====================================================
       14. ANIMASI ELEMEN SAAT SCROLL
       ===================================================== */

    function showAllRevealElements() {
        revealElements.forEach(function (element) {
            element.classList.add("is-visible");
        });
    }


    if (
        prefersReducedMotion ||
        !("IntersectionObserver" in window)
    ) {
        showAllRevealElements();
    } else {

        const revealObserver =
            new IntersectionObserver(
                function (
                    entries,
                    observer
                ) {
                    entries.forEach(
                        function (entry) {

                            if (!entry.isIntersecting) {
                                return;
                            }

                            entry.target.classList.add(
                                "is-visible"
                            );

                            /*
                               Setelah terlihat, elemen tidak perlu
                               diawasi lagi agar lebih ringan.
                            */
                            observer.unobserve(
                                entry.target
                            );
                        }
                    );
                },
                {
                    root: null,
                    threshold: 0.12,
                    rootMargin:
                        "0px 0px -45px 0px"
                }
            );


        revealElements.forEach(
            function (element, index) {

                /*
                   Memberikan sedikit perbedaan waktu animasi
                   agar elemen tidak muncul bersamaan.
                */
                element.style.transitionDelay =
                    `${Math.min(index * 35, 210)}ms`;

                revealObserver.observe(element);
            }
        );
    }


    /* =====================================================
       15. NAVIGASI AKTIF BERDASARKAN POSISI SCROLL
       ===================================================== */

    const sectionNavigationLinks =
        navigationLinks.filter(function (link) {
            return link.hash !== "";
        });


    const navigationSections =
        sectionNavigationLinks
            .map(function (link) {
                return document.querySelector(
                    link.hash
                );
            })
            .filter(function (section) {
                return section !== null;
            });


    /**
     * Menandai satu menu navigasi sebagai aktif.
     *
     * @param {string} sectionId
     */
    function setActiveNavigation(sectionId) {
        navigationLinks.forEach(function (link) {

            const isCurrentSection =
                link.hash === `#${sectionId}`;

            link.classList.toggle(
                "active",
                isCurrentSection
            );

            if (isCurrentSection) {
                link.setAttribute(
                    "aria-current",
                    "page"
                );
            } else {
                link.removeAttribute(
                    "aria-current"
                );
            }
        });
    }


    /**
     * Menentukan section yang sedang berada
     * di area utama viewport.
     */
    function updateActiveNavigation() {
        if (navigationSections.length === 0) {
            return;
        }

        const headerHeight = siteHeader
            ? siteHeader.offsetHeight
            : 0;

        const currentPosition =
            window.scrollY +
            headerHeight +
            130;

        let activeSection =
            navigationSections[0];

        navigationSections.forEach(
            function (section) {
                if (
                    section.offsetTop <=
                    currentPosition
                ) {
                    activeSection = section;
                }
            }
        );

        if (activeSection) {
            setActiveNavigation(
                activeSection.id
            );
        }
    }


    /*
       requestAnimationFrame digunakan agar event scroll
       tidak menjalankan perhitungan terlalu sering.
    */
    let scrollFrameRequested = false;

    window.addEventListener(
        "scroll",
        function () {

            if (scrollFrameRequested) {
                return;
            }

            scrollFrameRequested = true;

            window.requestAnimationFrame(
                function () {
                    updateActiveNavigation();
                    scrollFrameRequested = false;
                }
            );
        },
        {
            passive: true
        }
    );

    updateActiveNavigation();


    /* =====================================================
       16. SMOOTH SCROLL UNTUK LINK DALAM HALAMAN
       ===================================================== */

    const pageAnchorLinks =
        document.querySelectorAll(
            'a[href^="#"]:not([href="#"])'
        );


    pageAnchorLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                const targetSelector =
                    link.getAttribute("href");

                if (!targetSelector) {
                    return;
                }

                const targetElement =
                    document.querySelector(
                        targetSelector
                    );

                if (!targetElement) {
                    return;
                }

                event.preventDefault();

                closeMobileMenu();

                targetElement.scrollIntoView({
                    behavior: prefersReducedMotion
                        ? "auto"
                        : "smooth",
                    block: "start"
                });

                /*
                   Memperbarui URL tanpa me-refresh halaman.
                */
                if (history.pushState) {
                    history.pushState(
                        null,
                        "",
                        targetSelector
                    );
                }

                if (targetElement.id) {
                    setActiveNavigation(
                        targetElement.id
                    );
                }
            }
        );
    });


    /* =====================================================
       17. TRANSISI MENUJU HALAMAN LAIN
       ===================================================== */

    /**
     * Memeriksa apakah link aman diberi transisi keluar.
     *
     * @param {HTMLAnchorElement} link
     * @param {MouseEvent} event
     * @returns {boolean}
     */
    function canAnimatePageNavigation(
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
            link.target === "_blank" ||
            link.hasAttribute(
                "data-no-transition"
            )
        ) {
            return false;
        }

        const destination = new URL(
            link.href,
            window.location.href
        );

        /*
           Tidak memberi transisi untuk protokol eksternal.
        */
        if (
            destination.protocol !== "http:" &&
            destination.protocol !== "https:"
        ) {
            return false;
        }

        /*
           Tidak memberi transisi untuk website berbeda.
        */
        if (
            destination.origin !==
            window.location.origin
        ) {
            return false;
        }

        /*
           Link anchor di halaman yang sama sudah ditangani
           oleh fungsi smooth scroll.
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

        /*
           Jangan melakukan transisi apabila URL sama persis.
        */
        if (
            destination.href ===
            window.location.href
        ) {
            return false;
        }

        return true;
    }


    const internalPageLinks =
        document.querySelectorAll("a[href]");


    internalPageLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                if (
                    !canAnimatePageNavigation(
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

                closeMobileMenu();
                closeGlobalSearch(false);

                const destination =
                    link.href;

                const exitAnimation =
                    document.body.animate(
                        [
                            {
                                opacity: 1
                            },
                            {
                                opacity: 0
                            }
                        ],
                        {
                            duration: 240,
                            easing: "ease-in",
                            fill: "forwards"
                        }
                    );


                /*
                   Fallback digunakan jika event finish
                   tidak berjalan pada browser tertentu.
                */
                let navigationCompleted = false;

                function navigateToDestination() {
                    if (navigationCompleted) {
                        return;
                    }

                    navigationCompleted = true;

                    window.location.href =
                        destination;
                }


                exitAnimation.addEventListener(
                    "finish",
                    navigateToDestination
                );

                window.setTimeout(
                    navigateToDestination,
                    400
                );
            }
        );
    });


    /* =====================================================
       18. RESET STATUS SAAT KEMBALI DARI BROWSER
       ===================================================== */

    window.addEventListener(
        "pageshow",
        function () {

            /*
               Mengembalikan tampilan apabila halaman
               dipulihkan dari Back-Forward Cache.
            */
            document.body.style.opacity = "";

            closeMobileMenu();

            if (globalSearchIsOpen()) {
                closeGlobalSearch(false);
            }
        }
    );

});