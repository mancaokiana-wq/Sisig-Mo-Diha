# 🐍 Sisig Mo Diha — 100% PyScript (Python in the browser)
# Menu filter, cart, promo countdown, copy-code, order form, reveal, nav.
import js
from datetime import datetime

document = js.document
window = js.window

def all_list(sel):
    nodes = document.querySelectorAll(sel)
    return [nodes.item(i) for i in range(nodes.length)]

def q(sel):
    return document.querySelector(sel)

# ---------- mobile menu ----------
nav_links = q("#navLinks")

def toggle_menu(e=None):
    nav_links.classList.toggle("open")

q("#menuBtn").addEventListener("click", toggle_menu)

for a in all_list("#navLinks a"):
    def _close(e=None):
        nav_links.classList.remove("open")
    a.addEventListener("click", _close)

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

window.addEventListener("scroll", on_scroll)

# ---------- copy promo code (Python!) ----------
copyBtn = q("#copyCode")
if copyBtn:
    def copy_code(e):
        btn = e.currentTarget
        code = btn.textContent.strip()
        try:
            js.navigator.clipboard.writeText(code)
        except Exception:
            pass
        btn.textContent = "Copied ✓"
        js.setTimeout(lambda: setattr(btn, "textContent", code), 1200)
    copyBtn.addEventListener("click", copy_code)

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

js.setInterval(tick, 1000)
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

for b in all_list(".filter"):
    b.addEventListener("click", on_filter)

# ---------- cart (Python list) ----------
cart = []
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

q("#cartOpen").addEventListener("click", open_cart)
q("#cartClose").addEventListener("click", close_cart)
overlay.addEventListener("click", close_cart)

def cart_total():
    return sum(i["price"] * i["qty"] for i in cart)

def render_cart():
    count_el.textContent = str(sum(i["qty"] for i in cart))
    if not cart:
        items_el.innerHTML = "<p class='empty'>Wala pa kay order — pili sa sa menu! 🍳</p>"
        total_el.textContent = "₱0"
        return
    html = ""
    for idx, item in enumerate(cart):
        html += (
            f"<div class='ci'><div><strong>{item['name']} x{item['qty']}</strong>"
            f"<small>₱{item['price'] * item['qty']}</small></div>"
            f"<button data-act='dec' data-idx='{idx}'>−</button>"
            f"<button data-act='inc' data-idx='{idx}'>+</button></div>"
        )
    items_el.innerHTML = html
    total_el.textContent = f"₱{cart_total()}"
    for b in all_list(".ci button"):
        b.addEventListener("click", on_qty)

def on_qty(e):
    btn = e.currentTarget
    idx = int(btn.getAttribute("data-idx"))
    if 0 <= idx < len(cart):
        if btn.getAttribute("data-act") == "inc":
            cart[idx]["qty"] += 1
        else:
            cart[idx]["qty"] -= 1
            if cart[idx]["qty"] <= 0:
                cart.pop(idx)
        render_cart()

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
    btn.textContent = "Added ✓"
    js.setTimeout(lambda: setattr(btn, "textContent", "Add +"), 900)

for b in all_list(".add"):
    b.addEventListener("click", add_to_cart)

def checkout(e=None):
    if not cart:
        js.alert("Pili sa ug sisig! 🍳")
        return
    lines = "\n".join(f"{i['qty']}x {i['name']}" for i in cart)
    js.alert(f"Salamat! 🔥 Order received:\n{lines}\nTotal: ₱{cart_total()}\nLuto na dayon!")
    cart.clear()
    render_cart()
    close_cart()

q("#checkoutBtn").addEventListener("click", checkout)

# ---------- order-ahead form (Python validation) ----------
form = q("#orderForm")

def submit_order(e):
    e.preventDefault()
    name = (q("#oName").value or "").strip()
    phone = (q("#oPhone").value or "").strip()
    otype = q("#oType").value if q("#oType") else "Dine-in"
    note = q("#orderNote")
    if len(phone) < 7:
        note.textContent = "⚠️ Palihug butangi ug valid phone number."
        return
    who = name if name else "suki"
    note.textContent = f"Salamat {who}! 🔥 Nadawat na imong {otype} order — tawagan ka namo. (confirmed with Python 🐍)"
    form.reset()

form.addEventListener("submit", submit_order)

# ---------- init ----------
q("#year").textContent = str(datetime.now().year)
render_cart()
on_scroll()
tick()

status = q("#pyStatus")
if status:
    status.textContent = "🐍 Powered by Python (PyScript) ✅ — cart, filter & promos run on Python"
    js.setTimeout(lambda: status.classList.add("hide"), 3000)
