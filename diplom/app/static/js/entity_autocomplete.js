window.EntityAutocomplete = (() => {
  function normalize(value) {
    return String(value || "")
      .toLocaleLowerCase("ru-RU")
      .replace(/\s+/g, " ")
      .trim();
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function collectItemsFromRows(rows) {
    return rows.map((row) => {
      const label = row.dataset.autocompleteLabel || row.dataset.searchText || row.textContent || "";
      const meta = row.dataset.autocompleteMeta || "";
      const searchText = row.dataset.searchText || `${label} ${meta}`;

      return {
        label,
        meta,
        searchText,
      };
    });
  }

  function getItemText(item) {
    return normalize(`${item.label || ""} ${item.meta || ""} ${item.searchText || ""}`);
  }

  function scoreItem(item, query) {
    if (!query) return 1;

    const label = normalize(item.label);
    const meta = normalize(item.meta);
    const searchText = getItemText(item);

    if (label === query) return 1000;
    if (label.startsWith(query)) return 800;
    if (label.includes(query)) return 600;
    if (meta.includes(query)) return 260;
    if (searchText.includes(query)) return 180;

    return 0;
  }

  function filterRows(input, rows, countElement, emptyElement, countLabel) {
    const query = normalize(input.value);
    let visibleCount = 0;

    rows.forEach((row) => {
      const rowText = normalize(row.dataset.searchText || row.textContent || "");
      const isVisible = !query || rowText.includes(query);

      row.classList.toggle("entity-search-hidden", !isVisible);

      if (isVisible) {
        visibleCount += 1;
      }
    });

    if (countElement) {
      countElement.textContent = `${countLabel}: ${visibleCount}`;
    }

    if (emptyElement) {
      emptyElement.classList.toggle("is-visible", visibleCount === 0);
    }
  }

  function init(config) {
    const input = document.getElementById(config.inputId);
    const dropdown = document.getElementById(config.dropdownId);

    if (!input || !dropdown) return;

    const field = input.closest(".entity-search-field");
    const rows = Array.from(document.querySelectorAll(config.rowsSelector || "[data-search-row]"));
    const countElement = config.countId ? document.getElementById(config.countId) : null;
    const emptyElement = config.emptyId ? document.getElementById(config.emptyId) : null;
    const clearButton = config.clearButtonId ? document.getElementById(config.clearButtonId) : null;
    const items = Array.isArray(config.items) ? config.items : collectItemsFromRows(rows);
    const countLabel = config.countLabel || "Найдено";
    const maxOptions = Number(config.maxOptions || 10);

    let filteredItems = [];
    let activeIndex = -1;

    function closeDropdown() {
      if (field) field.classList.remove("is-open");
      activeIndex = -1;
    }

    function openDropdown() {
      if (field) field.classList.add("is-open");
    }

    function getFilteredItems() {
      const query = normalize(input.value);

      return items
        .map((item) => ({
          ...item,
          _score: scoreItem(item, query),
        }))
        .filter((item) => item._score > 0)
        .sort((a, b) => {
          if (b._score !== a._score) return b._score - a._score;
          return String(a.label || "").localeCompare(String(b.label || ""), "ru");
        })
        .slice(0, maxOptions);
    }

    function selectItem(item) {
      input.value = item.label || "";
      filterRows(input, rows, countElement, emptyElement, countLabel);
      closeDropdown();

      if (config.submitOnSelect) {
        const form = input.closest("form");
        if (form) {
          form.submit();
        }
      }
    }

    function renderDropdown() {
      filteredItems = getFilteredItems();
      dropdown.innerHTML = "";

      if (filteredItems.length === 0) {
        dropdown.innerHTML = '<div class="entity-search-empty">Ничего не найдено</div>';
        openDropdown();
        return;
      }

      filteredItems.forEach((item, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "entity-search-option";

        if (index === activeIndex) {
          button.classList.add("is-active");
        }

        button.innerHTML = `
          <span class="entity-search-option-main">${escapeHtml(item.label)}</span>
          ${item.meta ? `<span class="entity-search-option-meta">${escapeHtml(item.meta)}</span>` : ""}
        `;

        button.addEventListener("mousedown", (event) => {
          event.preventDefault();
          selectItem(item);
        });

        dropdown.appendChild(button);
      });

      openDropdown();
    }

    input.addEventListener("focus", () => {
      activeIndex = -1;
      renderDropdown();
    });

    input.addEventListener("input", () => {
      activeIndex = -1;
      filterRows(input, rows, countElement, emptyElement, countLabel);
      renderDropdown();
    });

    input.addEventListener("keydown", (event) => {
      const isOpen = field && field.classList.contains("is-open");

      if (!isOpen && event.key === "ArrowDown") {
        activeIndex = 0;
        renderDropdown();
        event.preventDefault();
        return;
      }

      if (!isOpen) return;

      if (event.key === "ArrowDown") {
        activeIndex = Math.min(activeIndex + 1, filteredItems.length - 1);
        renderDropdown();
        event.preventDefault();
      }

      if (event.key === "ArrowUp") {
        activeIndex = Math.max(activeIndex - 1, 0);
        renderDropdown();
        event.preventDefault();
      }

      if (event.key === "Enter" && activeIndex >= 0 && filteredItems[activeIndex]) {
        event.preventDefault();
        selectItem(filteredItems[activeIndex]);
      }

      if (event.key === "Escape") {
        closeDropdown();
      }
    });

    input.addEventListener("blur", () => {
      setTimeout(closeDropdown, 140);
    });

    if (clearButton) {
      clearButton.addEventListener("click", () => {
        input.value = "";
        filterRows(input, rows, countElement, emptyElement, countLabel);
        closeDropdown();
        input.focus();
      });
    }

    document.addEventListener("click", (event) => {
      if (field && !field.contains(event.target)) {
        closeDropdown();
      }
    });

    filterRows(input, rows, countElement, emptyElement, countLabel);
  }

  return {
    init,
  };
})();