/**
 * script.js
 * ---------
 * Vanilla JavaScript (no frameworks) that drives the Trading News
 * Dashboard's frontend behaviour:
 *   - Sidebar navigation between sections
 *   - Live search + filters, calling the Flask /api/news endpoint
 *   - Refresh button (bypasses the server-side cache)
 *   - Session-persistent bookmarking via localStorage
 *   - Loading / empty / error states
 */

(() => {
    "use strict";

    // ---------------------------------------------------------------
    // Constants & element references
    // ---------------------------------------------------------------
    const SAVED_KEY = "trading_dashboard_saved_articles";
    const SEARCH_DEBOUNCE_MS = 450;

    const navList = document.getElementById("navList");
    const pageTitle = document.getElementById("pageTitle");
    const pageSubtitle = document.getElementById("pageSubtitle");

    const searchInput = document.getElementById("searchInput");
    const clearSearchBtn = document.getElementById("clearSearchBtn");
    const refreshBtn = document.getElementById("refreshBtn");

    const filtersBar = document.getElementById("filtersBar");
    const categoryFilter = document.getElementById("categoryFilter");
    const dateFilter = document.getElementById("dateFilter");
    const sourceFilter = document.getElementById("sourceFilter");
    const limitFilter = document.getElementById("limitFilter");
    const applyFiltersBtn = document.getElementById("applyFiltersBtn");
    const resetFiltersBtn = document.getElementById("resetFiltersBtn");

    const statusLine = document.getElementById("statusLine");
    const loadingBar = document.getElementById("loadingBar");
    const newsGrid = document.getElementById("newsGrid");
    const savedGrid = document.getElementById("savedGrid");
    const emptyState = document.getElementById("emptyState");
    const errorState = document.getElementById("errorState");
    const errorMessage = document.getElementById("errorMessage");
    const savedEmptyState = document.getElementById("savedEmptyState");
    const savedCountBadge = document.getElementById("savedCount");
    const cardTemplate = document.getElementById("cardTemplate");

    // ---------------------------------------------------------------
    // State
    // ---------------------------------------------------------------
    let currentSection = "Home";
    let searchDebounceTimer = null;
    let activeRequestToken = 0; // guards against out-of-order responses

    // ---------------------------------------------------------------
    // Saved articles (localStorage) helpers
    // ---------------------------------------------------------------
    function getSavedArticles() {
        try {
            const raw = localStorage.getItem(SAVED_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch (err) {
            console.error("Could not read saved articles:", err);
            return {};
        }
    }

    function setSavedArticles(map) {
        try {
            localStorage.setItem(SAVED_KEY, JSON.stringify(map));
        } catch (err) {
            console.error("Could not persist saved articles:", err);
        }
    }

    function isArticleSaved(url) {
        const saved = getSavedArticles();
        return Object.prototype.hasOwnProperty.call(saved, url);
    }

    function toggleSaveArticle(article) {
        const saved = getSavedArticles();
        if (saved[article.url]) {
            delete saved[article.url];
        } else {
            saved[article.url] = article;
        }
        setSavedArticles(saved);
        updateSavedCount();
    }

    function updateSavedCount() {
        const count = Object.keys(getSavedArticles()).length;
        savedCountBadge.textContent = String(count);
    }

    // ---------------------------------------------------------------
    // UI state helpers
    // ---------------------------------------------------------------
    function showLoading(isLoading) {
        loadingBar.hidden = !isLoading;
        refreshBtn.classList.toggle("is-loading", isLoading);
        refreshBtn.disabled = isLoading;
    }

    function clearStates() {
        emptyState.hidden = true;
        errorState.hidden = true;
        savedEmptyState.hidden = true;
    }

    function showGrid(which) {
        newsGrid.hidden = which !== "news";
        savedGrid.hidden = which !== "saved";
    }

    // ---------------------------------------------------------------
    // Card rendering
    // ---------------------------------------------------------------
    function buildCard(article, { savedView }) {
        const node = cardTemplate.content.cloneNode(true);

        const img = node.querySelector(".news-card-image");
        img.src = article.image;
        img.alt = article.title;

        node.querySelector(".category-badge").textContent = article.category;
        node.querySelector(".news-headline").textContent = article.title;
        node.querySelector(".news-description").textContent = article.description;
        node.querySelector(".news-source").textContent = article.source;
        node.querySelector(".news-date").textContent = article.published_display;

        const readBtn = node.querySelector(".btn-read");
        if (article.url) {
            readBtn.href = article.url;
        } else {
            readBtn.style.pointerEvents = "none";
            readBtn.style.opacity = "0.5";
            readBtn.textContent = "No link available";
        }

        const saveBtn = node.querySelector(".btn-save");

        if (savedView) {
            // On the Saved Articles page, the action is always "Remove"
            saveBtn.textContent = "\u2715 Remove";
            saveBtn.classList.add("saved");
            saveBtn.addEventListener("click", () => {
                toggleSaveArticle(article);
                renderSavedArticles(); // re-render the saved page in place
            });
        } else {
            const refreshSaveLabel = () => {
                const saved = isArticleSaved(article.url);
                saveBtn.textContent = saved ? "\u2705 Saved" : "\u{1F516} Save";
                saveBtn.classList.toggle("saved", saved);
            };
            refreshSaveLabel();
            saveBtn.addEventListener("click", () => {
                toggleSaveArticle(article);
                refreshSaveLabel();
            });
        }

        return node;
    }

    function renderArticles(articles, container, options) {
        container.innerHTML = "";
        const fragment = document.createDocumentFragment();
        articles.forEach((article) => {
            fragment.appendChild(buildCard(article, options));
        });
        container.appendChild(fragment);
    }

    // ---------------------------------------------------------------
    // Saved Articles page
    // ---------------------------------------------------------------
    function renderSavedArticles() {
        const saved = Object.values(getSavedArticles());
        clearStates();

        if (saved.length === 0) {
            showGrid("saved");
            savedGrid.innerHTML = "";
            savedEmptyState.hidden = false;
            statusLine.textContent = "";
            return;
        }

        showGrid("saved");
        renderArticles(saved, savedGrid, { savedView: true });
        statusLine.textContent = `${saved.length} article(s) saved on this device.`;
    }

    // ---------------------------------------------------------------
    // Fetching live news
    // ---------------------------------------------------------------
    function buildQueryParams(forceRefresh) {
        const params = new URLSearchParams();
        params.set("section", currentSection);
        params.set("q", searchInput.value.trim());
        params.set("category", categoryFilter.value);
        params.set("date", dateFilter.value);
        params.set("source", sourceFilter.value.trim());
        params.set("limit", limitFilter.value);
        if (forceRefresh) params.set("refresh", "1");
        return params;
    }

    async function loadNews(forceRefresh = false) {
        clearStates();
        showGrid("news");
        showLoading(true);
        statusLine.textContent = "Fetching the latest news...";

        const token = ++activeRequestToken;
        const params = buildQueryParams(forceRefresh);

        try {
            const response = await fetch(`/api/news?${params.toString()}`);
            const data = await response.json();

            // Ignore stale responses if the user navigated again meanwhile
            if (token !== activeRequestToken) return;

            showLoading(false);

            if (!data.success) {
                errorMessage.textContent = data.error || "Something went wrong while fetching news.";
                errorState.hidden = false;
                newsGrid.innerHTML = "";
                statusLine.textContent = "";
                return;
            }

            if (!data.articles || data.articles.length === 0) {
                emptyState.hidden = false;
                newsGrid.innerHTML = "";
                statusLine.textContent = "";
                return;
            }

            renderArticles(data.articles, newsGrid, { savedView: false });
            statusLine.textContent = `Showing ${data.articles.length} article(s).`;
        } catch (err) {
            if (token !== activeRequestToken) return;
            showLoading(false);
            errorMessage.textContent =
                "Could not reach the server. Please check your internet connection and try again.";
            errorState.hidden = false;
            newsGrid.innerHTML = "";
            statusLine.textContent = "";
            console.error(err);
        }
    }

    // ---------------------------------------------------------------
    // Navigation
    // ---------------------------------------------------------------
    function setActiveNavButton(section) {
        document.querySelectorAll(".nav-item").forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.section === section);
        });
    }

    function switchSection(section) {
        currentSection = section;
        setActiveNavButton(section);
        pageTitle.textContent = section;

        if (section === "Saved Articles") {
            filtersBar.hidden = true;
            pageSubtitle.textContent = "Articles you've bookmarked during this browser session";
            renderSavedArticles();
            return;
        }

        filtersBar.hidden = false;
        pageSubtitle.textContent = "Live headlines from MediaStack";
        searchInput.value = "";
        clearSearchBtn.hidden = true;
        loadNews(false);
    }

    navList.addEventListener("click", (event) => {
        const btn = event.target.closest(".nav-item");
        if (!btn) return;
        switchSection(btn.dataset.section);
    });

    // ---------------------------------------------------------------
    // Search
    // ---------------------------------------------------------------
    searchInput.addEventListener("input", () => {
        clearSearchBtn.hidden = searchInput.value.trim() === "";
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => loadNews(false), SEARCH_DEBOUNCE_MS);
    });

    searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            clearTimeout(searchDebounceTimer);
            loadNews(false);
        }
    });

    clearSearchBtn.addEventListener("click", () => {
        searchInput.value = "";
        clearSearchBtn.hidden = true;
        loadNews(false);
    });

    // ---------------------------------------------------------------
    // Filters
    // ---------------------------------------------------------------
    applyFiltersBtn.addEventListener("click", () => loadNews(false));

    resetFiltersBtn.addEventListener("click", () => {
        categoryFilter.value = "";
        dateFilter.value = "";
        sourceFilter.value = "";
        limitFilter.value = "25";
        loadNews(false);
    });

    // ---------------------------------------------------------------
    // Refresh
    // ---------------------------------------------------------------
    refreshBtn.addEventListener("click", () => {
        if (currentSection === "Saved Articles") {
            renderSavedArticles();
            return;
        }
        loadNews(true);
    });

    // ---------------------------------------------------------------
    // Init
    // ---------------------------------------------------------------
    updateSavedCount();
    switchSection(currentSection);
})();
