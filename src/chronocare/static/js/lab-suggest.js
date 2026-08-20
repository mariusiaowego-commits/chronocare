(() => {
    const KIND_BADGE = {
        metric: "指标",
        panel: "组合",
        overview: "总览",
    };

    function debounce(fn, ms) {
        let t;
        return (...args) => {
            clearTimeout(t);
            t = setTimeout(() => fn(...args), ms);
        };
    }

    function initBox(input) {
        if (input.dataset.labSuggestReady) return;
        input.dataset.labSuggestReady = "1";
        const form = input.closest("[data-lab-suggest-form]") || input.form;
        const list = form?.querySelector("[data-lab-suggest-list]");
        if (!form || !list) return;

        let items = [];
        let active = -1;
        let lastQ = null;

        function hide() {
            list.hidden = true;
            input.setAttribute("aria-expanded", "false");
            active = -1;
        }

        function show() {
            if (!items.length) {
                hide();
                return;
            }
            list.hidden = false;
            input.setAttribute("aria-expanded", "true");
        }

        function paint() {
            list.innerHTML = items
                .map((item, i) => {
                    const on = i === active;
                    const badge = KIND_BADGE[item.kind] || item.hint || "";
                    return `<li role="option" data-i="${i}" aria-selected="${on}"
                        class="px-3 py-2.5 cursor-pointer flex items-center justify-between gap-3
                               ${on ? "bg-sky-50 dark:bg-sky-900/40" : "hover:bg-slate-50 dark:hover:bg-slate-700/60"}">
                        <span class="text-sm text-slate-800 dark:text-slate-100">${esc(item.label)}</span>
                        <span class="text-[11px] text-slate-400 shrink-0">${esc(badge)}</span>
                    </li>`;
                })
                .join("");
            show();
        }

        function choose(i) {
            const item = items[i];
            if (!item) return;
            input.value = item.query;
            hide();
            form.submit();
        }

        async function load(q) {
            const key = q.trim();
            lastQ = key;
            try {
                const res = await fetch(`/api/lab-query/suggest?q=${encodeURIComponent(key)}`);
                if (!res.ok) return;
                const data = await res.json();
                if (lastQ !== key) return;
                items = data.items || [];
                active = items.length ? 0 : -1;
                paint();
            } catch {
                /* ignore network blips while typing */
            }
        }

        const onType = debounce(() => load(input.value), 120);

        input.addEventListener("input", onType);
        input.addEventListener("focus", () => load(input.value));
        input.addEventListener("keydown", (e) => {
            if (list.hidden || !items.length) {
                if (e.key === "ArrowDown") {
                    e.preventDefault();
                    load(input.value);
                }
                return;
            }
            if (e.key === "ArrowDown") {
                e.preventDefault();
                active = (active + 1) % items.length;
                paint();
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                active = (active - 1 + items.length) % items.length;
                paint();
            } else if (e.key === "Enter" && active >= 0) {
                e.preventDefault();
                choose(active);
            } else if (e.key === "Escape") {
                hide();
            }
        });

        list.addEventListener("mousedown", (e) => {
            const li = e.target.closest("[data-i]");
            if (!li) return;
            e.preventDefault();
            choose(Number(li.getAttribute("data-i")));
        });

        document.addEventListener("click", (e) => {
            if (!form.contains(e.target)) hide();
        });
    }

    function esc(s) {
        return String(s)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function boot() {
        document.querySelectorAll("[data-lab-suggest-input]").forEach(initBox);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
    document.body.addEventListener("htmx:afterSwap", boot);
})();
