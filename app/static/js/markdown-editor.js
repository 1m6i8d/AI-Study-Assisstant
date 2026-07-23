/**
 * Shared Markdown editor behavior: adds a Write/Preview toggle to any
 * textarea marked with data-markdown-editor, and renders Markdown safely
 * (marked.js -> DOMPurify) anywhere marked with data-markdown-render.
 */

function renderMarkdownSafely(rawText) {
  const html = marked.parse(rawText || "");
  return DOMPurify.sanitize(html);
}

function initMarkdownEditors() {
  document.querySelectorAll("[data-markdown-editor]").forEach((textarea) => {
    if (textarea.dataset.editorInitialized) return;
    textarea.dataset.editorInitialized = "true";

    const wrapper = document.createElement("div");
    wrapper.className = "md-editor-wrapper";
    textarea.parentNode.insertBefore(wrapper, textarea);

    const tabs = document.createElement("div");
    tabs.className = "md-editor-tabs";
    tabs.innerHTML = `
      <button type="button" class="md-tab md-tab--active" data-mode="write">Write</button>
      <button type="button" class="md-tab" data-mode="preview">Preview</button>
      <span class="md-editor-hint text-muted">Markdown supported</span>
    `;

    const preview = document.createElement("div");
    preview.className = "md-preview";
    preview.hidden = true;

    wrapper.appendChild(tabs);
    wrapper.appendChild(textarea);
    wrapper.appendChild(preview);

    tabs.querySelectorAll(".md-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.querySelectorAll(".md-tab").forEach((t) => t.classList.remove("md-tab--active"));
        tab.classList.add("md-tab--active");

        if (tab.dataset.mode === "preview") {
          preview.innerHTML = renderMarkdownSafely(textarea.value);
          preview.hidden = false;
          textarea.hidden = true;
        } else {
          preview.hidden = true;
          textarea.hidden = false;
        }
      });
    });
  });
}

function renderStaticMarkdown() {
  document.querySelectorAll("[data-markdown-render]").forEach((el) => {
    const raw = el.dataset.markdownSource || el.textContent;
    el.innerHTML = renderMarkdownSafely(raw);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initMarkdownEditors();
  renderStaticMarkdown();
});