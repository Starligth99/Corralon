(function () {
  const TEXT_TYPES = new Set([
    "text",
    "email",
    "password",
    "search",
    "tel",
    "url",
    "number",
    "date",
    "time",
    "datetime-local",
    "month",
    "week"
  ]);

  function disableAutocomplete(root) {
    const forms = root.querySelectorAll("form");
    forms.forEach((form) => {
      form.setAttribute("autocomplete", "off");
    });

    const fields = root.querySelectorAll("input, textarea");
    fields.forEach((field) => {
      const tag = field.tagName.toLowerCase();
      const type = (field.getAttribute("type") || "text").toLowerCase();

      if (tag === "input" && !TEXT_TYPES.has(type)) {
        return;
      }

      field.setAttribute("autocomplete", type === "password" ? "new-password" : "off");
      field.setAttribute("autocorrect", "off");
      field.setAttribute("autocapitalize", "none");
      field.setAttribute("spellcheck", "false");

      if (!field.hasAttribute("readonly")) {
        field.setAttribute("readonly", "readonly");
        field.addEventListener(
          "focus",
          () => {
            field.removeAttribute("readonly");
          },
          { once: true }
        );
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => disableAutocomplete(document));
  } else {
    disableAutocomplete(document);
  }
})();
