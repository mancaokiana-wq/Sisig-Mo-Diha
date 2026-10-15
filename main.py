# 🐍 Sisig Mo Diha — PyScript (Python in the browser)
# All interactive functionality runs here: nav pill, scroll-spy, reveal,
# promo countdown, menu filter, cart, checkout, order form, year.
import js
import json
from datetime import datetime
from pyodide.ffi import create_proxy, create_once_callable

document = js.document
window = js.window
CART_KEY = "diha_cart"

# NOTE: Pyodide destroys implicitly-created proxies after the call, so every
# Python callback handed to the browser must be a retained create_proxy.
_py_proxies = []


def on(el, ev, fn):
    p = create_proxy(fn)
    _py_proxies.append(p)
    el.addEventListener(ev, p)
    return p


def later(ms, fn):
    p = create_once_callable(fn)
    _py_proxies.append(p)
    js.setTimeout(p, ms)
    return p


def all_list(sel):
    nodes = document.querySelectorAll(sel)
    return [nodes.item(i) for i in range(nodes.length)]


def q(sel):
    return document.querySelector(sel)


def load_cart():
    try:
        raw = js.localStorage.getItem(CART_KEY)
        if not raw:
            return []
        data = json.loads(str(raw))
        clean = []
        for it in data:
            try:
                clean.append({"name": str(it["name"]), "price": int(it["price"]), "qty": max(1, int(it.get("qty", 1)))})
            except Exception:
                continue
        return clean
    except Exception:
        return []


def save_cart():
    try:
        js.localStorage.setItem(CART_KEY, json.dumps(cart))
    except Exception:
        pass


# ---------- mobile menu + sliding red pill ----------
nav_links = q("#navLinks")
nav_pill = q("#navPill")


def move_pill(target=None):
    try:
        if target is None:
            target = q(".nav-links a.active")
        if not target or not nav_pill:
            return
        nav_links.classList.add("has-pill")
        nav_pill.style.left = f"{target.offsetLeft}px"
        nav_pill.style.top = f"{target.offsetTop}px"
        nav_pill.style.width = f"{target.offsetWidth}px"
        nav_pill.style.height = f"{target.offsetHeight}px"
        nav_pill.style.opacity = "1"
    except Exception:
        pass


def set_active(link):
    for l in all_list(".nav-links a"):
        l.classList.remove("active")
    link.classList.add("active")
    move_pill(link)


def toggle_menu(e=None):
    nav_links.classList.toggle("open")
    later(50, move_pill)


on(q("#menuBtn"), "click", toggle_menu)


def make_nav_handler(link):
    def handler(e=None):
        set_active(link)
        nav_links.classList.remove("open")
    return handler


for a in all_list("#navLinks a"):
    on(a, "click", make_nav_handler(a))


# ---------- scroll: header, reveal, active nav ----------
header = q("#header")


def on_scroll(e=None):
    y = window.scrollY
    if y > 10:
        header.classList.add("scrolled")
    else:
        header.classList.remove("scrolled")
    for el in all_list(".reveal:not(.visible)"):
        if el.getBoundingClientRect().top < window.innerHeight * 0.92:
            el.classList.add("visible")
    cur = "home"
    for s in all_list("section[id]"):
        if y >= (s.offsetTop - 160):
            _id = s.getAttribute("id")
            if _id:
                cur = _id
    for l in all_list(".nav-links a"):
        if l.getAttribute("href") == f"#{cur}":
            l.classList.add("active")
        else:
            l.classList.remove("active")
    move_pill()


on(window, "scroll", on_scroll)
on(window, "resize", lambda e=None: move_pill())


# ---------- promo countdown (Python timer) ----------
try:
    end = int(js.localStorage.getItem("diha_promo_end") or 0)
except Exception:
    end = 0
if not end or end < js.Date.now():
    end = int(js.Date.now() + 1000 * 60 * 60 * 38)
    try:
        js.localStorage.setItem("diha_promo_end", str(end))
    except Exception:
        pass


def tick(*args):
    d = max(0, end - int(js.Date.now()))
    h = str(d // 3600000).zfill(2)
    m = str((d % 3600000) // 60000).zfill(2)
    s = str((d % 60000) // 1000).zfill(2)
    q("#cdH").textContent = h
    q("#cdM").textContent = m
    q("#cdS").textContent = s


js.window.__pyTick = True
_tick_proxy = create_proxy(tick)
_py_proxies.append(_tick_proxy)
js.setInterval(_tick_proxy, 1000)
tick()


# ---------- menu filter (Python) ----------
def on_filter(e):
    btn = e.currentTarget
    for b in all_list(".filter"):
        b.classList.remove("active")
    btn.classList.add("active")
    f = btn.getAttribute("data-f")
    for dish in all_list(".dish"):
        cats = (dish.getAttribute("data-cat") or "").split(" ")
        dish.style.display = "" if (f == "all" or f in cats) else "none"
    for sub in all_list(".menu-sub"):
        sf = sub.getAttribute("data-sub")
        sub.style.display = "" if (f == "all" or f == sf) else "none"


for b in all_list(".filter"):
    on(b, "click", on_filter)


# ---------- cart (Python list, shared with JS via localStorage) ----------
cart = load_cart()
drawer = q("#cartDrawer")
overlay = q("#cartOverlay")
items_el = q("#cartItems")
total_el = q("#cartTotal")
count_el = q("#cartCount")


def open_cart(e=None):
    drawer.classList.add("show")
    overlay.classList.add("show")


def close_cart(e=None):
    drawer.classList.remove("show")
    overlay.classList.remove("show")


on(q("#cartOpen"), "click", open_cart)
on(q("#cartClose"), "click", close_cart)
on(overlay, "click", close_cart)


def cart_total():
    return sum(i["price"] * i["qty"] for i in cart)


def render_cart():
    count_el.textContent = str(sum(i["qty"] for i in cart))
    save_cart()
    if not cart:
        items_el.innerHTML = "<p class='empty'>Wala pa kay order — pili sa sa menu! 🍳</p>"
        total_el.textContent = "₱0"
        return
    html = ""
    for idx, item in enumerate(cart):
        html += (f"<div class='ci'><div><strong>{item['name']} x{item['qty']}</strong><small>₱{item['price'] * item['qty']}</small></div><button data-act='dec' data-idx='{idx}'>−</button><button data-act='inc' data-idx='{idx}'>+</button><button class='rm' data-act='rem' data-idx='{idx}' aria-label='Remove'>✕</button></div>")
    items_el.innerHTML = html
    total_el.textContent = f"₱{cart_total()}"


def on_cart_click(e):
    try:
        t = e.target
        btn = t.closest("button") if t is not None else None
    except Exception:
        btn = None
    if btn is None:
        return
    idx = int(btn.getAttribute("data-idx"))
    if 0 <= idx < len(cart):
        act = btn.getAttribute("data-act")
        if act == "inc":
            cart[idx]["qty"] += 1
        elif act == "rem":
            cart.pop(idx)
        else:
            cart[idx]["qty"] -= 1
            if cart[idx]["qty"] <= 0:
                cart.pop(idx)
        render_cart()


on(items_el, "click", on_cart_click)


def add_to_cart(e):
    btn = e.currentTarget
    name = btn.getAttribute("data-name")
    price = int(btn.getAttribute("data-price"))
    found = next((i for i in cart if i["name"] == name), None)
    if found:
        found["qty"] += 1
    else:
        cart.append({"name": name, "price": price, "qty": 1})
    render_cart()
    open_cart()
    orig = btn.textContent
    btn.textContent = "Added ✓"
    later(900, lambda o=orig: setattr(btn, "textContent", o))


for b in all_list(".add"):
    on(b, "click", add_to_cart)


def checkout(e=None):
    if not cart:
        js.alert("Pili sa ug sisig! 🍳")
        return
    lines = "\n".join(f"{i['qty']}x {i['name']}" for i in cart)
    js.alert(f"Salamat! 🔥 Order received:\n{lines}\nTotal: ₱{cart_total()}\nLuto na dayon!")
    cart.clear()
    render_cart()
    close_cart()


on(q("#checkoutBtn"), "click", checkout)


# ---------- order-ahead form (Python validation) ----------
form = q("#orderForm")


def submit_order(e):
    e.preventDefault()
    name = (q("#oName").value or "").strip()
    phone = (q("#oPhone").value or "").strip()
    otype = q("#oType").value if q("#oType") else "Dine-in"
    odate = (q("#oDate").value or "").strip() if q("#oDate") else ""
    otime = (q("#oTime").value or "").strip() if q("#oTime") else ""
    note = q("#orderNote")
    if len(phone) < 7:
        note.textContent = "⚠️ Palihug butangi ug valid phone number."
        return
    who = name if name else "suki"
    sched = ""
    if odate or otime:
        sched = f" para sa {(odate + ' ' + otime).strip()}"
    note.textContent = f"Salamat {who}! 🔥 Nadawat na imong {otype} order{sched} — tawagan ka namo."
    form.reset()


on(form, "submit", submit_order)


# ---------- init ----------
q("#year").textContent = str(datetime.now().year)
render_cart()
on_scroll()
later(300, move_pill)
later(1000, move_pill)
tick()
js.window.__pyAlive = True
