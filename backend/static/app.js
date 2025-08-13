// Small helper
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

async function fetchJSON(url, opts){ 
  const res = await fetch(url, opts); 
  if (!res.ok) throw new Error((await res.json().catch(()=>({error:res.statusText}))).error||res.statusText);
  return res.json();
}

// -------- Home (index) --------
async function loadSlots(){
  const params = new URLSearchParams();
  const d = $("#f-date")?.value; if(d) params.set("date", d);
  const t = $("#f-time")?.value; if(t) params.set("time", t);
  const s = $("#f-size")?.value; if(s) params.set("size", s);
  const a = $("#f-area")?.value; if(a) params.set("area", a);
  const pmin = $("#f-min")?.value; if(pmin) params.set("price_min", pmin);
  const pmax = $("#f-max")?.value; if(pmax) params.set("price_max", pmax);
  const f = $("#f-features")?.value; if(f) params.set("features", f);

  const slots = await fetchJSON(`/api/slots?${params.toString()}`);
  const wrap = $("#slots"); if(!wrap) return;
  wrap.innerHTML = "";

  if(slots.length===0){
    wrap.innerHTML = `<div class="muted">No matching slots.</div>`;
    return;
  }

  for(const s of slots){
    const li = document.createElement("div");
    li.className = "slot pop";
    const dt = new Date(s.date_time);
    li.innerHTML = `
      <h4>${dt.toLocaleDateString()} • ${dt.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</h4>
      <div class="muted">${s.area} • up to ${s.capacity} guests</div>
      <div style="margin:8px 0"><span class="badge">₹${s.price_per_person}/person</span></div>
      <div class="muted">${s.features || ""}</div>
      <div style="margin-top:10px"><button class="btn" data-book="${s.id}">Book Now</button></div>
    `;
    wrap.appendChild(li);
  }

  // attach book handlers
  wrap.addEventListener("click", async (e)=>{
    const bid = e.target?.dataset?.book;
    if(!bid) return;
    const party = prompt("Party size?");
    if(!party) return;
    try{
      await fetchJSON("/api/reservations", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ table_slot_id: Number(bid), party_size: Number(party) })
      });
      alert("Booked!"); loadSlots();
    }catch(err){ alert(err.message); }
  }, { once:true }); // reattached each render
}

async function loadReviews(){
  const wrap = $("#reviews"); if(!wrap) return;
  const rows = await fetchJSON("/api/reviews");
  wrap.innerHTML = rows.map(r=>`
    <div class="review pop">
      <div class="stars">${"★".repeat(r.rating)}${"☆".repeat(5-r.rating)}</div>
      <div class="muted">@${r.username} • ${new Date(r.created_at).toLocaleDateString()}</div>
      <div>${r.comment||""}</div>
    </div>
  `).join("");
}

async function postReview(){
  const btn = $("#btn-review"); if(!btn) return;
  btn.addEventListener("click", async ()=>{
    try{
      const rating = Number($("#rev-rating").value);
      const comment = $("#rev-comment").value;
      await fetchJSON("/api/reviews", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({rating, comment}) });
      $("#rev-comment").value=""; loadReviews();
      alert("Thanks for your review!");
    }catch(err){ alert(err.message); }
  });
}

// -------- My reservations page --------
async function loadMyReservations(){
  const wrap = $("#my-res"); if(!wrap) return;
  const rows = await fetchJSON("/api/reservations/me");
  wrap.innerHTML = rows.map(r=>`
    <div class="slot pop">
      <h4>${new Date(r.date_time).toLocaleString()}</h4>
      <div class="muted">${r.area} • up to ${r.capacity}</div>
      <div class="muted">${r.features||""}</div>
      <button class="btn ghost" data-cancel="${r.id}">Cancel</button>
    </div>
  `).join("");

  wrap.addEventListener("click", async (e)=>{
    const id = e.target?.dataset?.cancel;
    if(!id) return;
    if(!confirm("Cancel this reservation?")) return;
    try{
      await fetchJSON(`/api/reservations/${id}`, { method:"DELETE" });
      loadMyReservations();
    }catch(err){ alert(err.message); }
  }, { once:true });
}

// -------- Staff dashboard --------
async function staffAddSlot(){
  const btn = $("#btn-add-slot"); if(!btn) return;
  btn.addEventListener("click", async ()=>{
    try{
      const payload = {
        date_time: $("#s-datetime").value,
        capacity: Number($("#s-cap").value),
        area: $("#s-area").value,
        price_per_person: Number($("#s-price").value || 0),
        features: $("#s-feat").value
      };
      await fetchJSON("/api/slots", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload) });
      alert("Slot added.");
      renderAllReservations();
    }catch(err){ alert(err.message); }
  });
}

async function renderAllReservations(){
  const wrap = $("#all-res"); if(!wrap) return;
  // quick: combine available + booked for display
  const slots = await fetchJSON("/api/slots?only_available=false");
  // mark booked via absence in slots? We have is_booked field already.
  wrap.innerHTML = slots.map(s=>`
    <div class="slot pop">
      <h4>${new Date(s.date_time).toLocaleString()}</h4>
      <div class="muted">${s.area} • cap ${s.capacity}</div>
      <div>${s.is_booked ? '<span class="badge">Booked</span>' : '<span class="badge">Open</span>'}</div>
      <div class="muted">${s.features||""}</div>
    </div>
  `).join("");
}

async function reports(){
  const btnD = $("#btn-daily"); const btnW = $("#btn-weekly"); const out = $("#report");
  if(!out) return;
  btnD?.addEventListener("click", async ()=>{
    const d = $("#r-date").value;
    const data = await fetchJSON(`/api/reports/daily${d?`?date=${d}`:""}`);
    out.textContent = `Date: ${data.date}\nReservations: ${data.reservations}`;
  });
  btnW?.addEventListener("click", async ()=>{
    const data = await fetchJSON(`/api/reports/weekly`);
    out.textContent = `Week starting: ${data.week_start}\nReservations: ${data.reservations}`;
  });
}

// -------- init per-page --------
window.addEventListener("DOMContentLoaded", ()=>{
  $("#btn-search")?.addEventListener("click", loadSlots);
  loadSlots();
  loadReviews();
  postReview();
  loadMyReservations();
  staffAddSlot();
  renderAllReservations();
  reports();
});
