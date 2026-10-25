(function () {
  var root = document.documentElement;
  root.classList.add("js");

  var header = document.querySelector(".site-header");
  var onScroll = function () {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 8);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  var revealNodes = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -6% 0px" }
    );
    revealNodes.forEach(function (node) {
      observer.observe(node);
    });
  } else {
    revealNodes.forEach(function (node) {
      node.classList.add("is-in");
    });
  }

  var navLinks = Array.prototype.slice.call(document.querySelectorAll("[data-nav]"));
  var sections = navLinks
    .map(function (link) {
      return document.querySelector(link.getAttribute("href"));
    })
    .filter(Boolean);

  if ("IntersectionObserver" in window && sections.length) {
    var spy = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var id = entry.target.id;
          navLinks.forEach(function (link) {
            var on = link.getAttribute("href") === "#" + id;
            link.classList.toggle("is-active", on);
            if (on) link.setAttribute("aria-current", "true");
            else link.removeAttribute("aria-current");
          });
        });
      },
      { rootMargin: "-42% 0px -48% 0px", threshold: 0 }
    );
    sections.forEach(function (section) {
      spy.observe(section);
    });
  }

  function copyWithFallback(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (err) {
      ok = false;
    }
    area.remove();
    return ok;
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).then(
        function () {
          return true;
        },
        function () {
          return copyWithFallback(text);
        }
      );
    }
    return Promise.resolve(copyWithFallback(text));
  }

  document.querySelectorAll("[data-copy]").forEach(function (button) {
    var label = button.textContent;
    button.addEventListener("click", function () {
      copyText(button.getAttribute("data-copy")).then(function (ok) {
        button.textContent = ok ? "Copied" : "Copy failed";
        window.setTimeout(function () {
          button.textContent = label;
        }, 1600);
      });
    });
  });

  var toggle = document.querySelector(".nav-toggle");
  var panel = document.querySelector("#mobile-nav");
  if (toggle && panel) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", open ? "false" : "true");
      panel.hidden = open;
      toggle.textContent = open ? "Menu" : "Close";
    });
    panel.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        toggle.setAttribute("aria-expanded", "false");
        panel.hidden = true;
        toggle.textContent = "Menu";
      });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        toggle.setAttribute("aria-expanded", "false");
        panel.hidden = true;
        toggle.textContent = "Menu";
        toggle.focus();
      }
    });
  }
})();
