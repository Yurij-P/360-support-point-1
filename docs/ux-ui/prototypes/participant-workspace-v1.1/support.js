"use strict";

/*
 * TPS360 Wireframes v1.1 safe local runtime.
 * This docs-only prototype runtime intentionally avoids dynamic code execution,
 * external CDN loading, and cross-window messaging.
 */
(function () {
  const TEMPLATE_SELECTOR = "x-dc";
  const EXPR_RE = /\{\{\s*([^}]+?)\s*\}\}/g;

  class DCLogic {
    constructor() {
      this.state = this.state || {};
      this.__render = () => {};
    }

    setState(patch) {
      const next = typeof patch === "function" ? patch(this.state) : patch;
      this.state = Object.assign({}, this.state, next || {});
      this.__render();
    }
  }

  window.DCLogic = DCLogic;

  function isPlainPath(expr) {
    return /^(true|[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)$/.test(expr);
  }

  function resolve(expr, scopes) {
    const key = String(expr || "").trim();
    if (key === "true") return true;
    if (!isPlainPath(key)) return "";
    const parts = key.split(".");
    for (const scope of scopes) {
      if (!scope || !Object.prototype.hasOwnProperty.call(scope, parts[0])) continue;
      let value = scope[parts[0]];
      for (let i = 1; i < parts.length; i += 1) {
        if (value == null) return "";
        value = value[parts[i]];
      }
      return value == null ? "" : value;
    }
    return "";
  }

  function expressionFromTemplate(value) {
    const match = String(value || "").match(/^\s*\{\{\s*([^}]+?)\s*\}\}\s*$/);
    return match ? match[1].trim() : null;
  }

  function interpolate(value, scopes) {
    return String(value).replace(EXPR_RE, (_match, expr) => {
      const resolved = resolve(expr, scopes);
      if (typeof resolved === "function") return "";
      if (typeof resolved === "boolean") return resolved ? "true" : "false";
      return String(resolved);
    });
  }

  function processChildren(parent, scopes) {
    Array.from(parent.childNodes).forEach((node) => processNode(node, scopes));
  }

  function replaceWithFragment(node, fragment) {
    node.parentNode.insertBefore(fragment, node);
    node.remove();
  }

  function processNode(node, scopes) {
    if (node.nodeType === Node.TEXT_NODE) {
      if (node.nodeValue && node.nodeValue.includes("{{")) {
        node.nodeValue = interpolate(node.nodeValue, scopes);
      }
      return;
    }

    if (node.nodeType !== Node.ELEMENT_NODE) return;

    const tag = node.tagName.toLowerCase();
    if (tag === "sc-if") {
      const expr = expressionFromTemplate(node.getAttribute("value"));
      const shouldRender = expr ? Boolean(resolve(expr, scopes)) : false;
      if (!shouldRender) {
        node.remove();
        return;
      }
      const fragment = document.createDocumentFragment();
      Array.from(node.childNodes).forEach((child) => {
        const clone = child.cloneNode(true);
        processNode(clone, scopes);
        fragment.appendChild(clone);
      });
      replaceWithFragment(node, fragment);
      return;
    }

    if (tag === "sc-for") {
      const expr = expressionFromTemplate(node.getAttribute("list"));
      const asName = node.getAttribute("as") || "item";
      const list = expr ? resolve(expr, scopes) : [];
      const fragment = document.createDocumentFragment();
      (Array.isArray(list) ? list : []).forEach((item, index) => {
        const childScope = Object.assign({}, scopes[0] || {}, { [asName]: item, index, i: index });
        Array.from(node.childNodes).forEach((child) => {
          const clone = child.cloneNode(true);
          processNode(clone, [childScope].concat(scopes));
          fragment.appendChild(clone);
        });
      });
      replaceWithFragment(node, fragment);
      return;
    }

    Array.from(node.attributes).forEach((attr) => {
      const rawName = attr.name;
      const rawValue = attr.value;
      if (!rawValue || !rawValue.includes("{{")) return;

      const expr = expressionFromTemplate(rawValue);
      if (rawName.toLowerCase().startsWith("on") && expr) {
        const handler = resolve(expr, scopes);
        node.removeAttribute(rawName);
        if (typeof handler === "function") {
          const eventName = rawName.slice(2).toLowerCase();
          node.addEventListener(eventName, (event) => handler(event));
        }
        return;
      }

      node.setAttribute(rawName, interpolate(rawValue, scopes));
    });

    processChildren(node, scopes);
  }

  function render(component, mount, template) {
    const values = component.renderVals ? component.renderVals() : {};
    const holder = document.createElement("template");
    holder.innerHTML = template;
    processChildren(holder.content, [values]);
    mount.replaceChildren(holder.content);
  }

  function boot() {
    const source = document.querySelector(TEMPLATE_SELECTOR);
    const Component = window.__TPS360Component;
    if (!source || typeof Component !== "function") return;

    const template = source.innerHTML;
    const mount = document.createElement("div");
    mount.setAttribute("data-tps360-wireframes", "community-first-v1.1");
    source.replaceWith(mount);

    const component = new Component();
    window.__tps360WireframesComponent = component;
    component.__render = () => render(component, mount, template);
    component.__render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
}());
