const { useState, useEffect } = React;

const API = "http://localhost:5000/api";

const App = () => {
  const [kiosks, setKiosks] = useState([]);
  const [activeKiosk, setActiveKiosk] = useState(null);
  const [state, setState] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState([]);
  const [purchaseForm, setPurchaseForm] = useState({ pid: "", qty: 1, uid: "USER001" });
  const [priceCalc, setPriceCalc] = useState({ base: 100, qty: 1 });
  const [calcResult, setCalcResult] = useState(null);

  const toast = (msg, type = "success") => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3000);
  };

  const fetchData = async () => {
    try {
      const [kR, sR, iR] = await Promise.all([
        fetch(`${API}/kiosks`), fetch(`${API}/state`), fetch(`${API}/inventory`)
      ]);
      setKiosks(await kR.json());
      const s = await sR.json();
      setState(s);
      setInventory(await iR.json());
      setEvents(s.events || []);
      setActiveKiosk(s.id);
      setLoading(false);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 3000); return () => clearInterval(iv); }, []);

  const post = async (endpoint, body = {}) => {
    try {
      const r = await fetch(`${API}/${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const d = await r.json();
      if (d.error) { toast(d.error, "error"); return d; }
      toast(d.message || "Action completed", "success");
      fetchData();
      return d;
    } catch (e) { toast("Failed: " + e.message, "error"); }
  };

  const handlePurchase = (e) => {
    e.preventDefault();
    if (!purchaseForm.pid) { toast("Select a product", "error"); return; }
    post("purchase", purchaseForm);
  };

  const handleCalcPrice = async () => {
    const r = await fetch(`${API}/price/calculate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(priceCalc) });
    setCalcResult(await r.json());
  };

  if (loading) return (
    <div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100vh',flexDirection:'column',gap:'15px'}}>
      <div style={{fontFamily:'var(--font-brand)',fontSize:'2rem',color:'var(--neon)',letterSpacing:'4px'}}>AURA OS</div>
      <div style={{color:'var(--t3)',fontFamily:'var(--font-mono)',fontSize:'0.8rem'}}>Initializing systems...</div>
    </div>
  );

  const modeColors = { active: 'var(--success)', maintenance: 'var(--warn)', emergency: 'var(--danger)', power_saving: 'var(--neon)' };
  const modeIcons = { active: '⚡', maintenance: '🔧', emergency: '🚨', power_saving: '💤' };
  const isMaintenanceOrEmergency = state?.mode === 'maintenance' || state?.mode === 'emergency';

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <h1>AURA OS</h1>
          <span>Retail Intelligence</span>
        </div>
        <nav>
          <p className="stat-label" style={{marginBottom:'10px'}}>CONNECTED KIOSKS</p>
          {kiosks.map(k => (
            <div key={k.id} className={`nav-item ${activeKiosk===k.id?'active':''}`}
              onClick={() => post('kiosk/select', {id:k.id})}>
              <span style={{color: activeKiosk===k.id?'var(--neon)':'var(--t3)'}}>◈</span>
              <div>
                <div style={{fontSize:'0.8rem',fontWeight:700}}>{k.location}</div>
                <div style={{fontSize:'0.6rem',opacity:0.6,fontFamily:'var(--font-mono)'}}>{k.id}</div>
              </div>
            </div>
          ))}
        </nav>
        <div style={{marginTop:'auto',padding:'15px 0',borderTop:'1px solid var(--border)'}}>
          <div style={{fontFamily:'var(--font-mono)',fontSize:'0.6rem',color:'var(--t3)',textAlign:'center'}}>AURA RETAIL OS v2.0</div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        {/* Header */}
        <header className="top-header">
          <div className="kiosk-info">
            <h2>{state?.location}</h2>
            <p>ID: {state?.id} &nbsp;|&nbsp; TYPE: {state?.type}</p>
          </div>
          <div style={{display:'flex',gap:'10px',alignItems:'center'}}>
            <span className="mode-pill" style={{background: modeColors[state?.mode]+'22', color: modeColors[state?.mode], border:'1px solid '+modeColors[state?.mode]+'44', padding:'6px 14px', borderRadius:'20px', fontSize:'0.7rem', fontWeight:700, fontFamily:'var(--font-mono)', textTransform:'uppercase', letterSpacing:'1px'}}>
              {modeIcons[state?.mode]} {state?.mode?.replace('_',' ')}
            </span>
            <button className="btn" onClick={() => post('undo')}>↩ UNDO</button>
          </div>
        </header>

        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Mode</div>
            <div className="stat-value" style={{color: modeColors[state?.mode], fontSize:'1.4rem'}}>{state?.mode?.replace('_',' ')}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Pricing Strategy</div>
            <div className="stat-value" style={{color:'var(--accent)',fontSize:'1.4rem'}}>{state?.strat}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Transactions</div>
            <div className="stat-value">{state?.txns?.length || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Hardware</div>
            <div className="stat-value" style={{color: state?.status?.sensors==='OK'?'var(--success)':'var(--danger)', fontSize:'1.4rem'}}>
              {state?.status?.sensors==='OK' ? '● ONLINE' : '● FAULT'}
            </div>
          </div>
        </div>

        {/* Diagnostics Card */}
        <section className="card" style={{marginBottom:'25px'}}>
          <div className="card-header"><h3>⚙ SYSTEM DIAGNOSTICS (Facade Pattern)</h3></div>
          <div className="card-body">
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:'15px'}}>
              <div className="diag-item">
                <div className="stat-label">Sensor Status</div>
                <div style={{fontSize:'1.1rem',fontWeight:700,color:state?.status?.sensors==='OK'?'var(--success)':'var(--danger)',fontFamily:'var(--font-mono)'}}>
                  {state?.status?.sensors}
                </div>
              </div>
              <div className="diag-item">
                <div className="stat-label">Operating Mode</div>
                <div style={{fontSize:'1.1rem',fontWeight:700,color:modeColors[state?.mode],fontFamily:'var(--font-mono)'}}>
                  {state?.status?.mode}
                </div>
              </div>
              <div className="diag-item">
                <div className="stat-label">Active Pricing</div>
                <div style={{fontSize:'1.1rem',fontWeight:700,color:'var(--accent)',fontFamily:'var(--font-mono)'}}>
                  {state?.status?.pricing}
                </div>
              </div>
              <div className="diag-item">
                <div className="stat-label">Maintenance Lock</div>
                <div style={{fontSize:'1.1rem',fontWeight:700,color:isMaintenanceOrEmergency?'var(--danger)':'var(--success)',fontFamily:'var(--font-mono)'}}>
                  {isMaintenanceOrEmergency ? '🔒 LOCKED' : '🔓 OPEN'}
                </div>
              </div>
              <div className="diag-item">
                <div className="stat-label">Purchase Allowed</div>
                <div style={{fontSize:'1.1rem',fontWeight:700,color:(state?.mode==='active'||state?.mode==='emergency')?'var(--success)':'var(--danger)',fontFamily:'var(--font-mono)'}}>
                  {(state?.mode==='active'||state?.mode==='emergency') ? '✓ YES' : '✗ BLOCKED'}
                </div>
              </div>
              <div className="diag-item">
                <div className="stat-label">Kiosk Type</div>
                <div style={{fontSize:'1.1rem',fontWeight:700,fontFamily:'var(--font-mono)'}}>
                  {state?.type}
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="dashboard-grid">
          <div className="col-left">
            {/* Mode Switcher - State Pattern */}
            <section className="card">
              <div className="card-header"><h3>🔄 MODE CONTROL (State Pattern)</h3></div>
              <div className="card-body">
                <div className="mode-container">
                  {Object.entries(modeIcons).map(([m, icon]) => (
                    <div key={m} className={`mode-btn ${state?.mode===m?'active':''}`}
                      style={state?.mode===m ? {borderColor:modeColors[m],boxShadow:`0 0 15px ${modeColors[m]}33`} : {}}
                      onClick={() => post('mode', {mode:m})}>
                      <div className="mode-icon">{icon}</div>
                      <div className="mode-name" style={{color:state?.mode===m?modeColors[m]:'var(--t2)'}}>{m.replace('_',' ')}</div>
                    </div>
                  ))}
                </div>
                {isMaintenanceOrEmergency && (
                  <div style={{marginTop:'15px',padding:'12px',background:'rgba(255,0,85,0.1)',border:'1px solid rgba(255,0,85,0.3)',borderRadius:'8px',fontSize:'0.75rem',color:'var(--danger)'}}>
                    ⚠ Hardware is in <b>{state?.mode}</b> mode. {state?.mode==='maintenance' ? 'Purchases are BLOCKED until maintenance completes.' : 'Only limited essential purchases allowed.'}
                  </div>
                )}
              </div>
            </section>

            {/* Pricing Strategy */}
            <section className="card">
              <div className="card-header"><h3>💰 PRICING (Strategy Pattern)</h3></div>
              <div className="card-body">
                <div className="mode-container">
                  {[{k:'standard',n:'Standard',d:'Base price',i:'📊'},{k:'discounted',n:'Discounted',d:'-15% off',i:'🏷'},{k:'emergency',n:'Emergency',d:'+10% markup',i:'🚨'}].map(s => (
                    <div key={s.k} className={`mode-btn ${state?.strat===s.k?'active':''}`} onClick={() => post('pricing',{strategy:s.k})}>
                      <div className="mode-icon">{s.i}</div>
                      <div className="mode-name">{s.n}</div>
                      <div style={{fontSize:'0.6rem',color:'var(--t3)',marginTop:'4px'}}>{s.d}</div>
                    </div>
                  ))}
                </div>
                <div style={{marginTop:'15px',padding:'12px',background:'rgba(0,243,255,0.05)',border:'1px solid var(--border)',borderRadius:'8px'}}>
                  <div style={{fontSize:'0.7rem',color:'var(--t3)',marginBottom:'8px'}}>PRICE CALCULATOR</div>
                  <div style={{display:'flex',gap:'10px',alignItems:'center',flexWrap:'wrap'}}>
                    <input type="number" value={priceCalc.base} onChange={e=>setPriceCalc({...priceCalc,base:+e.target.value})}
                      placeholder="Base Price" style={{background:'rgba(0,0,0,0.3)',border:'1px solid var(--border)',borderRadius:'6px',padding:'8px',color:'var(--neon)',fontFamily:'var(--font-mono)',width:'100px'}} />
                    <span style={{color:'var(--t3)'}}>×</span>
                    <input type="number" value={priceCalc.qty} min="1" onChange={e=>setPriceCalc({...priceCalc,qty:+e.target.value})}
                      style={{background:'rgba(0,0,0,0.3)',border:'1px solid var(--border)',borderRadius:'6px',padding:'8px',color:'var(--neon)',fontFamily:'var(--font-mono)',width:'60px'}} />
                    <button className="btn btn-primary" style={{fontSize:'0.7rem',padding:'8px 14px'}} onClick={handleCalcPrice}>CALC</button>
                    {calcResult && <span style={{fontFamily:'var(--font-mono)',fontSize:'1.2rem',fontWeight:700,color:'var(--success)'}}>= ₹{calcResult.final}</span>}
                  </div>
                </div>
              </div>
            </section>

            {/* Inventory & Purchase */}
            <section className="card">
              <div className="card-header"><h3>📦 INVENTORY & PURCHASE (Command Pattern)</h3></div>
              <div className="card-body">
                {/* Purchase Form */}
                <form onSubmit={handlePurchase} style={{marginBottom:'20px',padding:'15px',background:'rgba(188,0,255,0.05)',border:'1px solid rgba(188,0,255,0.2)',borderRadius:'10px'}}>
                  <div style={{fontSize:'0.7rem',color:'var(--accent)',fontWeight:700,marginBottom:'12px',textTransform:'uppercase',letterSpacing:'1px'}}>🛒 New Purchase</div>
                  <div style={{display:'flex',gap:'10px',flexWrap:'wrap',alignItems:'flex-end'}}>
                    <div style={{flex:1,minWidth:'120px'}}>
                      <label style={{fontSize:'0.6rem',color:'var(--t3)',display:'block',marginBottom:'4px'}}>PRODUCT</label>
                      <select value={purchaseForm.pid} onChange={e=>setPurchaseForm({...purchaseForm,pid:e.target.value})}
                        style={{width:'100%',background:'rgba(0,0,0,0.3)',border:'1px solid var(--border)',borderRadius:'6px',padding:'8px',color:'var(--t1)',fontFamily:'var(--font-mono)',fontSize:'0.75rem'}}>
                        <option value="">-- Select --</option>
                        {inventory.map(p => <option key={p.id} value={p.id}>{p.nm} (₹{p.price}) [Stock: {p.qty}]</option>)}
                      </select>
                    </div>
                    <div style={{width:'70px'}}>
                      <label style={{fontSize:'0.6rem',color:'var(--t3)',display:'block',marginBottom:'4px'}}>QTY</label>
                      <input type="number" min="1" value={purchaseForm.qty} onChange={e=>setPurchaseForm({...purchaseForm,qty:+e.target.value})}
                        style={{width:'100%',background:'rgba(0,0,0,0.3)',border:'1px solid var(--border)',borderRadius:'6px',padding:'8px',color:'var(--neon)',fontFamily:'var(--font-mono)'}} />
                    </div>
                    <div style={{width:'100px'}}>
                      <label style={{fontSize:'0.6rem',color:'var(--t3)',display:'block',marginBottom:'4px'}}>USER ID</label>
                      <input value={purchaseForm.uid} onChange={e=>setPurchaseForm({...purchaseForm,uid:e.target.value})}
                        style={{width:'100%',background:'rgba(0,0,0,0.3)',border:'1px solid var(--border)',borderRadius:'6px',padding:'8px',color:'var(--t1)',fontFamily:'var(--font-mono)',fontSize:'0.75rem'}} />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={isMaintenanceOrEmergency && state?.mode==='maintenance'}>
                      {state?.mode==='maintenance' ? '🔒 LOCKED' : '🛒 BUY'}
                    </button>
                  </div>
                </form>

                {/* Product Grid */}
                <div className="product-grid">
                  {inventory.map(p => {
                    const stockPct = Math.round((p.qty / p.max) * 100);
                    const stockColor = stockPct > 50 ? 'var(--success)' : stockPct > 20 ? 'var(--warn)' : 'var(--danger)';
                    return (
                      <div key={p.id} className="product-item">
                        <div style={{fontSize:'0.65rem',color:'var(--t3)',fontFamily:'var(--font-mono)',marginBottom:'5px'}}>{p.id}</div>
                        <div style={{fontSize:'0.85rem',fontWeight:700,marginBottom:'5px'}}>{p.nm}</div>
                        <div className="product-price">₹{p.price}</div>
                        <div style={{fontSize:'0.6rem',color:p.cat==='essential'?'var(--danger)':p.cat==='premium'?'var(--accent)':'var(--t3)',margin:'5px 0',textTransform:'uppercase'}}>{p.cat}</div>
                        {/* Stock Bar */}
                        <div style={{width:'100%',height:'4px',background:'rgba(255,255,255,0.1)',borderRadius:'2px',marginTop:'8px'}}>
                          <div style={{width:`${stockPct}%`,height:'100%',background:stockColor,borderRadius:'2px',transition:'width 0.5s'}}></div>
                        </div>
                        <div style={{display:'flex',justifyContent:'space-between',marginTop:'4px'}}>
                          <span style={{fontSize:'0.6rem',color:stockColor}}>Stock: {p.qty}</span>
                          {p.hw && <span style={{fontSize:'0.55rem',color:'var(--danger)'}}>⚠ FAULT</span>}
                        </div>
                        <button className="btn" style={{marginTop:'8px',fontSize:'0.6rem',padding:'4px 10px',width:'100%'}}
                          onClick={() => post('restock', {pid:p.id, qty:5})}>+ RESTOCK</button>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>
          </div>

          <div className="col-right">
            {/* Event Feed - Observer Pattern */}
            <section className="card">
              <div className="card-header"><h3>📡 EVENT FEED (Observer)</h3></div>
              <div className="card-body">
                <div className="event-log">
                  {events.length === 0 && <div style={{textAlign:'center',color:'var(--t3)',padding:'20px',fontSize:'0.75rem'}}>No events yet. Make a purchase to trigger events.</div>}
                  {events.slice().reverse().map((e, i) => {
                    const isDanger = e.type.includes('Failed') || e.type.includes('Failure') || e.type.includes('Emergency');
                    const isWarn = e.type.includes('LowStock');
                    return (
                      <div key={i} className="event-entry">
                        <span className="event-time">{e.time}</span>
                        <span className={`event-type ${isDanger?'type-danger':isWarn?'type-warn':'type-success'}`}>{e.type}</span>
                        {e.data && Object.keys(e.data).length > 0 && (
                          <span style={{fontSize:'0.6rem',color:'var(--t3)',marginLeft:'auto'}}>
                            {Object.values(e.data).join(' | ')}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            {/* Transactions - Command Pattern */}
            <section className="card">
              <div className="card-header"><h3>📋 TRANSACTIONS (Command)</h3></div>
              <div className="card-body">
                <div style={{maxHeight:'350px',overflowY:'auto'}}>
                  {(!state?.txns || state.txns.length===0) && <div style={{textAlign:'center',color:'var(--t3)',padding:'20px',fontSize:'0.75rem'}}>No transactions yet.</div>}
                  {state?.txns?.slice().reverse().map(tx => (
                    <div key={tx.id} style={{padding:'10px',marginBottom:'8px',background:'rgba(255,255,255,0.02)',border:'1px solid var(--border)',borderRadius:'8px'}}>
                      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                        <span style={{fontFamily:'var(--font-mono)',fontSize:'0.7rem',fontWeight:700,color:'var(--neon)'}}>TX-{tx.id}</span>
                        <span style={{fontFamily:'var(--font-mono)',fontWeight:700,color:tx.type==='refunded'?'var(--danger)':'var(--success)'}}>₹{tx.amount}</span>
                      </div>
                      <div style={{fontSize:'0.65rem',color:'var(--t2)',margin:'4px 0'}}>{tx.desc}</div>
                      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                        <span style={{fontSize:'0.6rem',color:'var(--t3)'}}>{tx.time}</span>
                        <button className="btn" style={{fontSize:'0.55rem',padding:'3px 8px'}} disabled={tx.type==='refunded'}
                          onClick={() => post('refund', {tid:tx.id})}>
                          {tx.type==='refunded' ? '✓ REFUNDED' : '↩ REFUND'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Memento Snapshots */}
            <section className="card">
              <div className="card-header"><h3>📸 SNAPSHOTS (Memento)</h3></div>
              <div className="card-body">
                {(!state?.mems || state.mems.length===0) && <div style={{textAlign:'center',color:'var(--t3)',padding:'15px',fontSize:'0.75rem'}}>No snapshots. Make a purchase to create one.</div>}
                {state?.mems?.map(m => (
                  <div key={m.id} style={{padding:'10px',background:'rgba(188,0,255,0.05)',border:'1px solid rgba(188,0,255,0.2)',borderRadius:'8px',marginBottom:'8px'}}>
                    <div style={{fontFamily:'var(--font-mono)',fontSize:'0.7rem',color:'var(--accent)',fontWeight:700}}>SNAP-{m.id}</div>
                    <div style={{fontSize:'0.65rem',color:'var(--t2)',marginTop:'3px'}}>{m.desc}</div>
                    <div style={{fontSize:'0.6rem',color:'var(--t3)',marginTop:'3px'}}>{m.time}</div>
                  </div>
                ))}
                <button className="btn" style={{width:'100%',marginTop:'10px',fontSize:'0.7rem'}} onClick={() => post('undo')}>
                  ↩ ROLLBACK TO LAST SNAPSHOT
                </button>
              </div>
            </section>
          </div>
        </div>
      </main>

      {/* Toasts */}
      <div style={{position:'fixed',bottom:'20px',right:'20px',zIndex:9999,display:'flex',flexDirection:'column-reverse',gap:'8px'}}>
        {toasts.map(t => (
          <div key={t.id} style={{
            padding:'12px 18px',borderRadius:'10px',fontSize:'0.75rem',fontWeight:600,
            background: t.type==='error' ? 'rgba(255,0,85,0.15)' : 'rgba(0,255,149,0.15)',
            border: `1px solid ${t.type==='error'?'rgba(255,0,85,0.4)':'rgba(0,255,149,0.4)'}`,
            color: t.type==='error' ? 'var(--danger)' : 'var(--success)',
            backdropFilter:'blur(10px)', animation:'slideIn 0.3s ease'
          }}>{t.type==='error'?'✗':'✓'} {t.msg}</div>
        ))}
      </div>
      <style>{`@keyframes slideIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:translateX(0)}}`}</style>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
