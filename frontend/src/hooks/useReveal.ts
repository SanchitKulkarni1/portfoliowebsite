import { useEffect, useRef } from "react";

/**
 * Adds `is-visible` to the element the first time it scrolls into view (pairs with the `.reveal` class).
 * Triggers once any part of it is 12% above the bottom of the viewport. A ratio threshold would
 * never fire for elements much taller than the screen, leaving them invisible.
 */
export function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("is-visible");
          observer.disconnect();
        }
      },
      { threshold: 0, rootMargin: "0px 0px -12% 0px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return ref;
}
