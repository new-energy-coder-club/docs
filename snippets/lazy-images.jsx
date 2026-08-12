import { useEffect } from "react";

/**
 * LazyImages — 给当前页面所有正文 <img> 加浏览器原生懒加载。
 *
 * 用法（在 MDX 顶部 import 后在任意位置挂一次即可，常放在 frontmatter 下方）：
 *   import { LazyImages } from "/snippets/lazy-images.jsx";
 *   <LazyImages />
 *
 * 行为：
 * - 跳过导航栏 / Logo / 已显式声明 loading 的图片。
 * - 为其余 <img> 设置 loading="lazy" + decoding="async"，并提示浏览器在视口外不解析。
 * - 用 MutationObserver 监听 SPA 路由切换与懒加载内容，新增节点也会被处理。
 * - 不渲染任何 DOM，纯副作用。
 */
export const LazyImages = () => {
  useEffect(() => {
    if (typeof document === "undefined") return;

    const applyLazy = (root) => {
      const scope = root || document;
      const images = scope.querySelectorAll
        ? scope.querySelectorAll("img")
        : [];
      images.forEach((img) => {
        // 跳过：导航栏、Logo、头像等关键首屏元素
        if (img.closest("#navbar, header, nav, [data-no-lazy]")) return;
        // 已显式设置过 loading 的尊重原作者意图
        if (img.hasAttribute("loading")) return;
        // 只处理正文内容区
        if (!img.closest("main, article, #content-wrapper")) return;

        img.setAttribute("loading", "lazy");
        img.setAttribute("decoding", "async");
        // 防止 alt 缺失造成可访问性告警
        if (!img.hasAttribute("alt")) img.setAttribute("alt", "");
      });
    };

    // 立即处理一次
    applyLazy(document);

    // SPA 路由切换 / 懒加载内容注入时再次处理
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        for (const node of m.addedNodes) {
          if (!(node instanceof Element)) continue;
          if (node.tagName === "IMG") {
            applyLazy(node.parentElement || document);
          } else if (node.querySelector) {
            applyLazy(node);
          }
        }
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    return () => observer.disconnect();
  }, []);

  return null;
};

export default LazyImages;
