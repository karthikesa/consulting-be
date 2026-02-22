"""
Product/Vehicle detail page UI - mobile responsive, matches reference design.
Rendered at /v/{vehicle_id}
"""
import html as html_mod
from urllib.parse import quote
from datetime import datetime


def format_updated_date(updated_at) -> str:
    """Format updated_at for display."""
    if not updated_at:
        return ""
    try:
        if hasattr(updated_at, "strftime"):
            return updated_at.strftime("%d %b %Y")
        d = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
        return d.strftime("%d %b %Y")
    except Exception:
        return str(updated_at) if updated_at else ""


def render_product_page(vehicle, base_url: str, img_urls: list) -> str:
    """Render the product detail HTML page - mobile responsive."""
    amount_fmt = f"₹ {float(vehicle.amount):,.0f}"
    desc = html_mod.escape(vehicle.description or "").replace("\n", "<br>")
    name_esc = html_mod.escape(vehicle.name)
    loc_esc = html_mod.escape(str(vehicle.location)) if vehicle.location else ""
    mileage_str = f"{vehicle.mileage:,} km driven" if vehicle.mileage else ""
    updated_str = format_updated_date(vehicle.updated_at)
    share_url = f"{base_url}/v/{vehicle.id}"
    wa_text = quote(f"Check this out: {name_esc} - {amount_fmt} - {share_url}")

    # Carousel slides
    if img_urls:
        slides_html = "\n".join(
            f'<div class="slide" data-idx="{i}"><img src="{u}" alt="{name_esc}"></div>'
            for i, u in enumerate(img_urls)
        )
        img_counter = f'<span class="img-counter">1/{len(img_urls)}</span>'
        dots_html = "".join(
            f'<span class="dot{" active" if i == 0 else ""}" data-idx="{i}"></span>'
            for i in range(len(img_urls))
        )
    else:
        slides_html = '<div class="slide"><div class="img-placeholder">No image</div></div>'
        img_counter = ""
        dots_html = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
  <meta name="theme-color" content="#1a2234">
  <title>{name_esc} - Motors & Cars Consultancy</title>
  <style>
    *{{box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
    html{{-webkit-text-size-adjust:100%}}
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0;padding:0;background:#fff;color:#374151;min-height:100vh}}
    .wrap{{max-width:480px;margin:0 auto;min-height:100vh;display:flex;flex-direction:column}}
    .header{{background:#1a2234;padding:12px 16px;display:flex;align-items:center;gap:12px}}
    .header-back{{color:#fff;font-size:22px;text-decoration:none;padding:6px;line-height:1}}
    .header-spacer{{flex:1}}
    .header-actions{{display:flex;gap:2px;align-items:center}}
    .header-btn{{color:#fff;font-size:18px;padding:8px;text-decoration:none;opacity:0.95}}
    .header-btn:hover{{opacity:1}}
    .content{{flex:1;padding-bottom:100px}}
    .carousel{{position:relative;width:100%;aspect-ratio:1;background:#e5e7eb;overflow:hidden}}
    .carousel-inner{{display:flex;width:100%;height:100%;transition:transform 0.3s ease}}
    .slide{{min-width:100%;height:100%;position:relative}}
    .slide img{{width:100%;height:100%;object-fit:cover}}
    .img-placeholder{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#6b7280;font-size:16px}}
    .carousel-arrow{{position:absolute;top:50%;transform:translateY(-50%);width:36px;height:36px;background:rgba(255,255,255,0.3);color:rgba(255,255,255,0.9);border:none;border-radius:50%;font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:2;backdrop-filter:blur(4px)}}
    .carousel-arrow:hover{{background:rgba(255,255,255,0.5)}}
    .carousel-arrow.left{{left:10px}}
    .carousel-arrow.right{{right:10px}}
    .img-counter{{position:absolute;bottom:40px;right:12px;background:rgba(0,0,0,0.5);color:#fff;padding:4px 10px;border-radius:4px;font-size:12px;z-index:2}}
    .carousel-dots{{position:absolute;bottom:12px;left:0;right:0;display:flex;justify-content:center;gap:6px;z-index:2}}
    .dot{{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,0.4);cursor:pointer;transition:all 0.2s}}
    .dot.active{{background:#fff;width:8px;height:8px;box-shadow:0 0 4px rgba(0,0,0,0.2)}}
    .details{{padding:16px;background:#fff}}
    .product-name{{font-size:20px;font-weight:700;margin:0 0 8px;line-height:1.35;color:#1f2937}}
    .badge{{display:inline-block;background:#2563eb;color:#fff;padding:5px 12px;border-radius:6px;font-size:12px;font-weight:600;margin-bottom:6px}}
    .price{{font-size:24px;font-weight:700;color:#1f2937;margin:0 0 16px}}
    .specs{{background:#f3f4f6;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.04)}}
    .spec-row{{display:flex;align-items:center;gap:12px;padding:10px 0;font-size:14px;color:#374151}}
    .spec-row:not(:last-child){{border-bottom:1px solid #e5e7eb}}
    .spec-icon{{color:#6b7280;font-size:18px;width:22px;text-align:center}}
    .desc-title{{font-size:16px;font-weight:600;margin:0 0 8px;color:#1f2937}}
    .desc-box{{background:#f9fafb;border-radius:12px;padding:16px;font-size:14px;line-height:1.6;color:#374151;border:1px solid #f3f4f6}}
    .action-bar{{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:480px;padding:16px;gap:12px;display:flex;background:#fff;border-top:1px solid #e5e7eb;box-shadow:0 -2px 12px rgba(0,0,0,0.08)}}
    .action-btn{{display:flex;align-items:center;justify-content:center;gap:10px;padding:14px 20px;border-radius:12px;font-size:15px;font-weight:600;text-decoration:none;color:#fff;border:none;cursor:pointer}}
    .action-whatsapp{{background:#2563eb;flex:1.5}}
    .action-call{{background:#ff6b35;flex:1}}
    .footer{{text-align:center;padding:12px;font-size:12px;color:#9ca3af}}
    @media(min-width:481px){{body{{background:#f3f4f6}}.wrap{{box-shadow:0 0 20px rgba(0,0,0,0.1);margin:20px auto}}}}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="header">
      <a href="javascript:history.back()" class="header-back" aria-label="Back">‹</a>
      <span class="header-spacer"></span>
      <div class="header-actions">
        <a href="#" class="header-btn" aria-label="Edit">✎</a>
        <a href="https://wa.me/?text={wa_text}" class="header-btn" aria-label="Share" target="_blank" rel="noopener">↗</a>
        <a href="#" class="header-btn" aria-label="Favorite">♡</a>
      </div>
    </header>
    <main class="content">
      <div class="carousel">
        <div class="carousel-inner" id="carousel">
          {slides_html}
        </div>
        {f'<button class="carousel-arrow left" id="prev" aria-label="Previous">‹</button><button class="carousel-arrow right" id="next" aria-label="Next">›</button>' if len(img_urls) > 1 else ''}
        {img_counter}
        {f'<div class="carousel-dots" id="dots">{dots_html}</div>' if len(img_urls) > 1 else ''}
      </div>
      <div class="details">
        <h1 class="product-name">{name_esc} ({vehicle.model_year})</h1>
        <span class="badge">{vehicle.product.upper()}</span>
        <p class="price">{amount_fmt}</p>
        <div class="specs">
          {f'<div class="spec-row"><span class="spec-icon">⏱</span><span>{mileage_str}</span></div>' if mileage_str else ''}
          {f'<div class="spec-row"><span class="spec-icon">📍</span><span>{loc_esc}</span></div>' if vehicle.location else ''}
          {f'<div class="spec-row"><span class="spec-icon">📅</span><span>Updated {updated_str}</span></div>' if updated_str else ''}
        </div>
        <div class="desc-title">Description</div>
        <div class="desc-box">{desc if desc else "—"}</div>
      </div>
    </main>
    <div class="action-bar">
      <a href="https://wa.me/?text={wa_text}" class="action-btn action-whatsapp" target="_blank" rel="noopener">💬 Share to WhatsApp</a>
      <a href="tel:+919876543210" class="action-btn action-call">☎ Call</a>
    </div>
    <p class="footer">Motors & Cars Consultancy • View in app for full details</p>
  </div>
  <script>
    (function(){{
      var slides=document.querySelectorAll('.slide');
      var dots=document.querySelectorAll('.dot');
      var inner=document.getElementById('carousel');
      var counter=document.querySelector('.img-counter');
      if(slides.length<=1)return;
      var idx=0;
      function go(n){{
        idx=(n+slides.length)%slides.length;
        inner.style.transform='translateX(-'+idx*100+'%)';
        dots.forEach(function(d,i){{d.classList.toggle('active',i===idx);}});
        if(counter)counter.textContent=(idx+1)+'/'+slides.length;
      }}
      document.getElementById('prev')&&document.getElementById('prev').addEventListener('click',function(){{go(idx-1);}});
      document.getElementById('next')&&document.getElementById('next').addEventListener('click',function(){{go(idx+1);}});
      dots.forEach(function(d,i){{d.addEventListener('click',function(){{go(i);}});}});
    }})();
  </script>
</body>
</html>"""
