document.addEventListener("DOMContentLoaded", () => {
    const input = document.querySelector("[data-global-search]");
    const box = document.querySelector("[data-search-suggestions]");
    if (!input || !box) return;

    let timer = null;

    input.addEventListener("input", () => {
        const q = input.value.trim();
        if (timer) {
            clearTimeout(timer);
        }
        if (q.length < 2) {
            box.innerHTML = "";
            box.classList.remove("visible");
            return;
        }
        timer = setTimeout(() => fetchSuggestions(q), 200);
    });

    input.addEventListener("blur", () => {
        setTimeout(() => {
            box.innerHTML = "";
            box.classList.remove("visible");
        }, 150);
    });

    function fetchSuggestions(query) {
        fetch(`/api/catalog/products/?search=${encodeURIComponent(query)}`)
            .then((r) => r.json())
            .then((data) => {
                if (!Array.isArray(data) || data.length === 0) {
                    box.innerHTML = "";
                    box.classList.remove("visible");
                    return;
                }
                const top = data.slice(0, 5);
                box.innerHTML = top
                    .map(
                        (p) =>
                            `<a href="/catalog/${p.slug}/" class="suggestion-item">
                                <span class="suggestion-name">${escapeHtml(p.name)}</span>
                                <span class="suggestion-meta">${escapeHtml(
                                    p.product_type
                                )} · ${p.price} ₽</span>
                             </a>`
                    )
                    .join("");
                box.classList.add("visible");
            })
            .catch(() => {
                box.innerHTML = "";
                box.classList.remove("visible");
            });
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});

