/*
=========================================================
COMPASS CAMPUS - FAQ INTERAKTIF
File: static/js/faq.js

Fungsi:
1. Accordion FAQ.
2. Search FAQ real-time.
3. Active state kategori berdasarkan hash.
4. Animasi reveal saat scroll.
5. Menjaga transisi tetap halus saat navigasi anchor.
=========================================================
*/

document.addEventListener("DOMContentLoaded", () => {
    const accordionItems = Array.from(document.querySelectorAll("[data-faq-item]"));
    const searchInput = document.getElementById("faq-search-input");
    const noResult = document.getElementById("faq-no-result");
    const categoryLinks = Array.from(document.querySelectorAll("[data-faq-category-link]"));
    const faqGroups = Array.from(document.querySelectorAll("[data-faq-group]"));
    const revealItems = Array.from(document.querySelectorAll(".reveal"));

    /*
    ---------------------------------------------------------
    1. Accordion FAQ
    ---------------------------------------------------------
    */
    accordionItems.forEach((item) => {
        const button = item.querySelector(".faq-question");

        if (!button) {
            return;
        }

        button.addEventListener("click", () => {
            const isOpen = item.classList.contains("is-open");

            // Menutup item lain dalam group yang sama agar tampilan tetap rapi.
            const currentGroup = item.closest("[data-faq-group]");
            const groupItems = currentGroup
                ? Array.from(currentGroup.querySelectorAll("[data-faq-item]"))
                : accordionItems;

            groupItems.forEach((groupItem) => {
                if (groupItem !== item) {
                    groupItem.classList.remove("is-open");
                }
            });

            item.classList.toggle("is-open", !isOpen);
        });
    });


    /*
    ---------------------------------------------------------
    2. Search FAQ
    ---------------------------------------------------------
    */
    function normalizeText(value) {
        return String(value || "")
            .toLowerCase()
            .trim()
            .replace(/\s+/g, " ");
    }

    function filterFaqItems() {
        if (!searchInput) {
            return;
        }

        const query = normalizeText(searchInput.value);
        let visibleCount = 0;

        accordionItems.forEach((item) => {
            const question = normalizeText(item.querySelector(".faq-question")?.textContent);
            const answer = normalizeText(item.querySelector(".faq-answer")?.textContent);
            const keywords = normalizeText(item.dataset.keywords);
            const isMatch = !query || question.includes(query) || answer.includes(query) || keywords.includes(query);

            item.hidden = !isMatch;

            if (isMatch) {
                visibleCount += 1;
            } else {
                item.classList.remove("is-open");
            }
        });

        faqGroups.forEach((group) => {
            const visibleItems = group.querySelectorAll("[data-faq-item]:not([hidden])");
            group.hidden = query && visibleItems.length === 0;
        });

        if (noResult) {
            noResult.hidden = visibleCount > 0;
        }
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterFaqItems);
    }


    /*
    ---------------------------------------------------------
    3. Active category link
    ---------------------------------------------------------
    */
    function setActiveCategory(categoryId) {
        categoryLinks.forEach((link) => {
            link.classList.toggle(
                "active",
                link.dataset.faqCategoryLink === categoryId
            );
        });
    }

    function updateActiveCategoryFromHash() {
        const hash = window.location.hash.replace("#", "");

        if (hash) {
            setActiveCategory(hash);
        }
    }

    categoryLinks.forEach((link) => {
        link.addEventListener("click", () => {
            const targetCategory = link.dataset.faqCategoryLink;

            if (targetCategory) {
                setActiveCategory(targetCategory);
            }
        });
    });

    updateActiveCategoryFromHash();
    window.addEventListener("hashchange", updateActiveCategoryFromHash);


    /*
    ---------------------------------------------------------
    4. Scroll spy kategori
    ---------------------------------------------------------
    */
    if ("IntersectionObserver" in window && faqGroups.length > 0) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setActiveCategory(entry.target.id);
                    }
                });
            },
            {
                root: null,
                rootMargin: "-35% 0px -55% 0px",
                threshold: 0,
            }
        );

        faqGroups.forEach((group) => observer.observe(group));
    }


    /*
    ---------------------------------------------------------
    5. Reveal animation
    ---------------------------------------------------------
    */
    if ("IntersectionObserver" in window) {
        const revealObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        revealObserver.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.12,
            }
        );

        revealItems.forEach((item) => revealObserver.observe(item));
    } else {
        revealItems.forEach((item) => item.classList.add("is-visible"));
    }


    /*
    ---------------------------------------------------------
    6. Membuka section tujuan saat halaman dibuka dari footer
    ---------------------------------------------------------
    */
    if (window.location.hash) {
        const target = document.querySelector(window.location.hash);

        if (target) {
            setTimeout(() => {
                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
            }, 120);
        }
    }
});
