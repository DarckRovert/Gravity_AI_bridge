"""
╔══════════════════════════════════════════════════════════════════════════════╗
╔        GRAVITY SPARK — ULTRA-PREMIUM OVERLAY TEMPLATES V15.1 PRO             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

TEMPLATES = {

"chat_cyberpunk": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; overflow: hidden; font-family: 'Courier New', monospace; background: transparent; width: 100vw; height: 100vh; padding: 15px; box-sizing: border-box; }
        .chat-wrap { display: flex; flex-direction: column; justify-content: flex-end; height: 100%; gap: 15px; }
        .msg {
            position: relative; padding: 15px; background: rgba(5, 5, 10, 0.85); backdrop-filter: blur(10px);
            clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
            border-left: 3px solid #00f0ff; color: #fff; animation: slideUp 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
            box-shadow: inset 0 0 20px rgba(0, 240, 255, 0.1);
        }
        .msg::before {
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(90deg, rgba(0,240,255,0.1), transparent); pointer-events: none; z-index: -1;
        }
        @keyframes slideUp { 0% { opacity: 0; transform: translateY(30px) scale(0.95); } 100% { opacity: 1; transform: translateY(0) scale(1); } }
        .header { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
        .avatar { width: 30px; height: 30px; clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%); background: #00f0ff; display: flex; justify-content: center; align-items: center; color: #000; font-weight: bold; font-size: 14px; }
        .name { color: #00f0ff; font-weight: 900; letter-spacing: 1px; text-shadow: 0 0 8px #00f0ff; text-transform: uppercase; }
        .text { font-size: 14px; line-height: 1.4; color: #d0f8ff; text-shadow: 0 0 2px rgba(0,240,255,0.5); }
        .scanlines { position: absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.25) 50%), linear-gradient(90deg, rgba(255,0,0,0.06), rgba(0,255,0,0.02), rgba(0,0,255,0.06)); background-size: 100% 2px, 3px 100%; pointer-events: none; z-index: 999; }
    </style>
</head>
<body>
    <div class="scanlines"></div>
    <div class="chat-wrap" id="chat"></div>
    <script>
        const names = ["N3O", "TR1N1TY", "M0RPH", "CYPH3R", "GL1TCH", "Z3R0"];
        const msgs = ["SISTEMA COMPROMETIDO.", "ACCESO AUTORIZADO.", "DESCARGANDO DATOS...", "CONEXIÓN ESTABLECIDA.", "BYPASS FIREWALL EXITOSO.", "INICIANDO PROTOCOLO OMEGA."];
        const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*";
        
        function scramble(el, text, speed) {
            let i = 0;
            const iv = setInterval(() => {
                el.innerText = text.substring(0, i) + Array(text.length - i).fill(0).map(()=>chars[Math.floor(Math.random()*chars.length)]).join('');
                i += 1;
                if(i > text.length) clearInterval(iv);
            }, speed);
        }

        function spawn() {
            const wrap = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = 'msg';
            const name = names[Math.floor(Math.random()*names.length)];
            const rawMsg = msgs[Math.floor(Math.random()*msgs.length)];
            const color = `hsl(${Math.random()*60 + 180}, 100%, 50%)`;
            
            div.style.borderLeftColor = color;
            div.innerHTML = `
                <div class="header">
                    <div class="avatar" style="background:${color}">${name[0]}</div>
                    <div class="name" style="color:${color}; text-shadow: 0 0 8px ${color}">${name}</div>
                </div>
                <div class="text"></div>
            `;
            wrap.appendChild(div);
            if(wrap.children.length > 6) wrap.removeChild(wrap.firstChild);
            
            scramble(div.querySelector('.text'), rawMsg, 30);
            setTimeout(spawn, Math.random()*3000 + 2000);
        }
        spawn();
    </script>
</body>
</html>""",

"dashboard_hud": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; overflow: hidden; font-family: 'Arial', sans-serif; background: transparent; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .hud { width: 350px; background: radial-gradient(circle at 50% 0%, rgba(20,10,40,0.9), rgba(5,0,15,0.9)); border: 1px solid #aa00ff; border-radius: 16px; padding: 20px; box-shadow: 0 0 30px rgba(170,0,255,0.3), inset 0 0 20px rgba(0,255,255,0.1); position: relative; }
        .hud::before { content:''; position: absolute; top:-2px; left:-2px; right:-2px; bottom:-2px; background: linear-gradient(45deg, #00ffff, #aa00ff); z-index: -1; border-radius: 18px; opacity: 0.5; filter: blur(5px); animation: pulseGlow 3s infinite alternate; }
        @keyframes pulseGlow { 0% { opacity: 0.3; } 100% { opacity: 0.8; } }
        .title { color: #00ffff; font-size: 10px; text-transform: uppercase; letter-spacing: 4px; font-weight: 900; margin-bottom: 20px; display: flex; justify-content: space-between; }
        .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .stat { background: rgba(0,0,0,0.5); border: 1px solid rgba(0,255,255,0.3); border-radius: 8px; padding: 10px; text-align: center; }
        .stat-val { color: #fff; font-size: 24px; font-weight: bold; font-family: monospace; text-shadow: 0 0 10px rgba(255,255,255,0.5); }
        .stat-lbl { color: #aa00ff; font-size: 10px; font-weight: bold; margin-top: 5px; letter-spacing: 1px; }
        canvas { width: 100%; height: 60px; background: rgba(0,0,0,0.3); border-radius: 8px; border: 1px solid rgba(170,0,255,0.3); }
        .rings { display: flex; justify-content: space-around; margin-top: 20px; }
        svg { width: 60px; height: 60px; filter: drop-shadow(0 0 5px #00ffff); }
        .ring1 { transform-origin: center; animation: spin 4s linear infinite; stroke-dasharray: 40 10; }
        .ring2 { transform-origin: center; animation: spin 3s linear infinite reverse; stroke-dasharray: 20 20; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="hud">
        <div class="title"><span>SYS.HUD.V15</span> <span id="status" style="color:#0f0;">ONLINE</span></div>
        <div class="stat-grid">
            <div class="stat"><div class="stat-val" id="v">0%</div><div class="stat-lbl">CPU LOAD</div></div>
            <div class="stat"><div class="stat-val" id="s" style="color:#00ffff;">0%</div><div class="stat-lbl">RAM USE</div></div>
        </div>
        <canvas id="chart"></canvas>
        <div class="rings">
            <svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="#aa00ff" stroke-width="4" class="ring1"/><circle cx="50" cy="50" r="30" fill="none" stroke="#00ffff" stroke-width="2" class="ring2"/></svg>
            <svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="#ff0055" stroke-width="4" class="ring2"/><circle cx="50" cy="50" r="30" fill="none" stroke="#aa00ff" stroke-width="2" class="ring1"/></svg>
            <svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="#00ffff" stroke-width="4" class="ring1"/><circle cx="50" cy="50" r="30" fill="none" stroke="#ff0055" stroke-width="2" class="ring2"/></svg>
        </div>
    </div>
    <script>
        // Fetch Real Telemetry
        const ctx = document.getElementById('chart').getContext('2d');
        const W = 300, H = 100;
        document.getElementById('chart').width = W; document.getElementById('chart').height = H;
        let points = Array(15).fill(H); // Inicia gráfica abajo
        
        async function fetchRealData() {
            try {
                // Se conecta al motor local de Gravity!
                let res = await fetch('http://127.0.0.1:7860/v1/hardware');
                let data = await res.json();
                
                document.getElementById('v').innerText = Math.round(data.cpu_percent) + '%';
                document.getElementById('s').innerText = Math.round(data.ram_percent) + '%';
                
                // Mapear CPU (0-100) a altura Canvas (H-0)
                let y = H - (data.cpu_percent / 100 * H);
                points.push(y);
                points.shift();
                
                document.getElementById('status').innerText = 'LIVE SYNC';
                document.getElementById('status').style.color = '#0f0';
            } catch(e) {
                document.getElementById('status').innerText = 'OFFLINE';
                document.getElementById('status').style.color = '#f00';
            }
        }
        setInterval(fetchRealData, 1000);
        fetchRealData();

        function draw() {
            ctx.clearRect(0,0,W,H);
            ctx.beginPath();
            ctx.moveTo(0, points[0]);
            for(let i=0; i<points.length-1; i++) {
                const xc = (i*(W/14) + (i+1)*(W/14)) / 2;
                const yc = (points[i] + points[i+1]) / 2;
                ctx.quadraticCurveTo(i*(W/14), points[i], xc, yc);
            }
            ctx.lineTo(W, points[points.length-1]);
            ctx.lineWidth = 3; ctx.strokeStyle = '#00ffff'; ctx.stroke();
            
            ctx.lineTo(W, H); ctx.lineTo(0, H);
            const grad = ctx.createLinearGradient(0,0,0,H);
            grad.addColorStop(0, 'rgba(0,255,255,0.4)'); grad.addColorStop(1, 'rgba(0,255,255,0)');
            ctx.fillStyle = grad; ctx.fill();
            
            requestAnimationFrame(draw);
        }
        draw();
    </script>
</body>
</html>""",

"alerta_epica": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; overflow: hidden; background: transparent; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Impact', sans-serif; perspective: 800px; }
        canvas { position: absolute; top:0; left:0; width:100%; height:100%; pointer-events: none; }
        .wrap { text-align: center; z-index: 10; opacity: 0; transform: scale(0.5) translateZ(-500px); }
        .show .wrap { animation: popIn 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
        .hide .wrap { animation: popOut 0.5s ease-in forwards; }
        @keyframes popIn { 100% { opacity: 1; transform: scale(1) translateZ(0); } }
        @keyframes popOut { 100% { opacity: 0; transform: scale(1.5) translateZ(300px); filter: blur(10px); } }
        
        .title { font-size: 40px; color: #ff0055; text-transform: uppercase; letter-spacing: 8px; text-shadow: 0 0 20px rgba(255,0,85,0.8); margin-bottom: -10px; }
        .name { 
            font-size: 90px; text-transform: uppercase; background: linear-gradient(90deg, #ffd700, #ff8c00, #ffd700, #fff);
            background-size: 300% 100%; -webkit-background-clip: text; color: transparent;
            filter: drop-shadow(0 10px 10px rgba(0,0,0,0.8)) drop-shadow(0 0 30px rgba(255,215,0,0.6));
            animation: shine 3s linear infinite, float 2s ease-in-out infinite alternate;
        }
        @keyframes shine { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
        @keyframes float { 100% { transform: translateY(-15px) rotateX(10deg); } }
        @keyframes shake { 0%, 100% { transform: translate(0,0); } 10%, 30%, 50%, 70%, 90% { transform: translate(-5px,-5px); } 20%, 40%, 60%, 80% { transform: translate(5px,5px); } }
        .shake-active { animation: shake 0.4s cubic-bezier(.36,.07,.19,.97) both; }
    </style>
</head>
<body>
    <canvas id="cvs"></canvas>
    <div class="wrap" id="w">
        <div class="title">NUEVA DONACIÓN</div>
        <div class="name" id="n">GRAVITY PRO</div>
    </div>
    <script>
        const ctx = document.getElementById('cvs').getContext('2d');
        let W = window.innerWidth, H = window.innerHeight;
        document.getElementById('cvs').width = W; document.getElementById('cvs').height = H;
        let parts = [];
        
        function boom() {
            parts = [];
            for(let i=0; i<300; i++) {
                const a = Math.random() * Math.PI * 2;
                const v = Math.random() * 25 + 5;
                parts.push({ x: W/2, y: H/2, vx: Math.cos(a)*v, vy: Math.sin(a)*v - 5, life: 1, decay: Math.random()*0.02 + 0.01, size: Math.random()*10+5, c: `hsl(${Math.random()*40+30}, 100%, 50%)` });
            }
        }
        
        function draw() {
            ctx.clearRect(0,0,W,H);
            for(let i=parts.length-1; i>=0; i--) {
                let p = parts[i];
                p.x += p.vx; p.y += p.vy; p.vy += 0.4; p.vx *= 0.96; p.life -= p.decay;
                if(p.life <= 0) { parts.splice(i,1); continue; }
                ctx.globalAlpha = p.life; ctx.fillStyle = p.c;
                ctx.beginPath(); ctx.arc(p.x, p.y, p.size*p.life, 0, Math.PI*2); ctx.fill();
            }
            ctx.globalAlpha = 1;
            requestAnimationFrame(draw);
        }
        draw();

        function trig() {
            document.body.className = "show shake-active";
            setTimeout(()=> document.body.className = "show", 400);
            boom();
            setTimeout(() => document.body.className = "hide", 5000);
        }
        setInterval(trig, 9000); setTimeout(trig, 500);
    </script>
</body>
</html>""",

"brb_synthwave": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { background-color: #0c0214; margin: 0; overflow: hidden; font-family: 'Arial Black', sans-serif; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; width: 100vw; perspective: 1000px; }
        
        /* Stars Parallax */
        .stars { position: absolute; top:0; left:0; width:100%; height:100%; background: #0c0214; z-index: -2; }
        .star { position: absolute; background: #fff; border-radius: 50%; animation: twinkle 2s infinite alternate; }
        @keyframes twinkle { 0% { opacity: 0.2; } 100% { opacity: 1; box-shadow: 0 0 10px #fff; } }

        /* Grid Floor */
        .grid { position: absolute; bottom: -20%; width: 200%; left: -50%; height: 70%; background-image: linear-gradient(to right, rgba(0,255,255,0.4) 2px, transparent 2px), linear-gradient(to top, rgba(0,255,255,0.4) 2px, transparent 2px); background-size: 80px 80px; transform: rotateX(75deg); transform-origin: top center; animation: gridMove 1s linear infinite; box-shadow: inset 0 100px 100px #0c0214; z-index: -1; }
        @keyframes gridMove { 0% { background-position: 0 0; } 100% { background-position: 0 80px; } }

        /* Sun & Reflection */
        .sun { position: absolute; top: 15%; width: 400px; height: 400px; border-radius: 50%; background: linear-gradient(to bottom, #ff007f 0%, #ffaa00 100%); box-shadow: 0 0 150px rgba(255,0,127,0.8); z-index: 0; clip-path: polygon(0 0, 100% 0, 100% 50%, 0 50%, 0 55%, 100% 55%, 100% 63%, 0 63%, 0 72%, 100% 72%, 100% 83%, 0 83%, 0 96%, 100% 96%, 100% 100%, 0 100%); }

        /* VHS Canvas Overlay */
        canvas { position: absolute; top:0; left:0; width:100%; height:100%; z-index: 999; pointer-events: none; mix-blend-mode: overlay; opacity: 0.3; }

        .text-wrap { position: relative; z-index: 10; text-align: center; display: flex; flex-direction: column; align-items: center; }
        .title { font-size: 80px; color: transparent; -webkit-text-stroke: 2px #fff; text-transform: uppercase; letter-spacing: 10px; position: relative; animation: glitchText 4s infinite; }
        .title::before, .title::after { content: 'VUELVO ENSEGUIDA'; position: absolute; top:0; left:0; width:100%; height:100%; opacity: 0.8; }
        .title::before { color: #0ff; z-index: -1; transform: translate(-4px, 2px); }
        .title::after { color: #f0f; z-index: -2; transform: translate(4px, -2px); }
        @keyframes glitchText { 0%, 96%, 100% { transform: skewX(0deg); filter: hue-rotate(0deg); } 97% { transform: skewX(10deg); filter: hue-rotate(90deg); } 98% { transform: skewX(-10deg); filter: invert(1); } }

        .timer { font-size: 90px; color: #fff; text-shadow: 0 0 20px #0ff, 0 0 40px #0ff, 0 0 80px #0ff; font-family: monospace; font-weight: 900; margin-top: 20px; background: rgba(0,0,0,0.4); padding: 10px 40px; border-radius: 20px; backdrop-filter: blur(5px); }
    </style>
</head>
<body>
    <div class="stars" id="stars"></div>
    <div class="sun"></div>
    <div class="grid"></div>
    <div class="text-wrap">
        <div class="title" id="t">VUELVO ENSEGUIDA</div>
        <div class="timer" id="time">05:00</div>
    </div>
    <canvas id="vhs"></canvas>
    <script>
        // Stars
        const st = document.getElementById('stars');
        for(let i=0; i<100; i++){
            let s = document.createElement('div'); s.className = 'star';
            s.style.left = Math.random()*100+'%'; s.style.top = Math.random()*100+'%';
            s.style.width = s.style.height = (Math.random()*3+1)+'px';
            s.style.animationDelay = Math.random()*2+'s'; st.appendChild(s);
        }
        
        // VHS Noise
        const ctx = document.getElementById('vhs').getContext('2d');
        const W = window.innerWidth, H = window.innerHeight;
        document.getElementById('vhs').width = W; document.getElementById('vhs').height = H;
        function noise(){
            ctx.clearRect(0,0,W,H);
            ctx.fillStyle = 'white';
            for(let i=0; i<50; i++){
                ctx.globalAlpha = Math.random();
                ctx.fillRect(0, Math.random()*H, W, Math.random()*5);
            }
            requestAnimationFrame(noise);
        }
        noise();

        // Timer
        let sec = 300; const tmr = document.getElementById('time'), ttt = document.getElementById('t');
        const iv = setInterval(()=>{
            sec--; if(sec<=0) { clearInterval(iv); tmr.innerText="00:00"; ttt.innerText="¡ESTAMOS DE VUELTA!"; return; }
            tmr.innerText = String(Math.floor(sec/60)).padStart(2,'0') + ":" + String(sec%60).padStart(2,'0');
        }, 1000);
    </script>
</body>
</html>""",

"now_playing": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; padding: 20px; font-family: 'Segoe UI', sans-serif; background: transparent; }
        .widget { display: flex; align-items: center; gap: 20px; width: 450px; background: rgba(15,10,25,0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); border-radius: 50px; padding: 15px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); position: relative; overflow: hidden; }
        .widget::before { content:''; position: absolute; top:0; left:0; width:100%; height:100%; background: linear-gradient(120deg, transparent, rgba(255,255,255,0.05), transparent); animation: shine 3s infinite; }
        @keyframes shine { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
        
        .disk { width: 80px; height: 80px; border-radius: 50%; background: repeating-radial-gradient(#111, #111 4px, #222 5px, #222 6px); border: 3px solid #000; display: flex; align-items: center; justify-content: center; animation: spin 3s linear infinite; box-shadow: 0 0 30px rgba(0,255,255,0.5); transition: box-shadow 0.1s; position: relative; z-index: 2; }
        .disk::after { content:''; width: 25px; height: 25px; border-radius: 50%; background: conic-gradient(#f00, #ff0, #0f0, #0ff, #00f, #f0f, #f00); border: 2px solid #fff; }
        .disk-center { position: absolute; width: 6px; height: 6px; background: #000; border-radius: 50%; z-index: 3; }
        @keyframes spin { 100% { transform: rotate(360deg); } }

        .info { flex-grow: 1; z-index: 2; }
        .lbl { font-size: 11px; color: #00ffff; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px; }
        .track { font-size: 20px; color: #fff; font-weight: bold; text-shadow: 0 0 10px rgba(255,255,255,0.3); white-space: nowrap; overflow: hidden; position: relative; width: 100%; }
        .track span { display: inline-block; animation: marquee 15s linear infinite; padding-left: 100%; }
        @keyframes marquee { 100% { transform: translateX(-100%); } }
        
        canvas { position: absolute; bottom: 0; left: 120px; width: calc(100% - 140px); height: 40px; z-index: 1; opacity: 0.5; }
    </style>
</head>
<body>
    <div class="widget">
        <div class="disk" id="disk"><div class="disk-center"></div></div>
        <div class="info">
            <div class="lbl">Now Playing</div>
            <div class="track"><span id="s">Synthwave Mix - Lazerhawk / Overdrive / 1984</span></div>
        </div>
        <canvas id="eq"></canvas>
    </div>
    <script>
        // Procedural EQ + Glow sync
        const ctx = document.getElementById('eq').getContext('2d');
        const W = 300, H = 40; document.getElementById('eq').width = W; document.getElementById('eq').height = H;
        const disk = document.getElementById('disk');
        let phase = 0;
        
        function draw() {
            ctx.clearRect(0,0,W,H);
            phase += 0.2;
            let avg = 0;
            const bars = 30;
            const bw = W/bars;
            
            for(let i=0; i<bars; i++) {
                // Fake noise using multiple sines
                let val = Math.sin(phase + i*0.5)*10 + Math.sin(phase*1.5 + i*0.2)*10 + 20;
                if(val < 2) val = 2;
                avg += val;
                
                let grad = ctx.createLinearGradient(0, H, 0, 0);
                grad.addColorStop(0, '#aa00ff'); grad.addColorStop(1, '#00ffff');
                ctx.fillStyle = grad;
                ctx.fillRect(i*bw + 1, H - val, bw - 2, val);
            }
            avg = avg/bars;
            disk.style.boxShadow = `0 0 ${avg*2}px rgba(0,255,255,${avg/40})`;
            requestAnimationFrame(draw);
        }
        draw();
    </script>
</body>
</html>""",

"meta_subs": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; padding: 30px; font-family: 'Arial', sans-serif; background: transparent; display: flex; justify-content: center; }
        .bar-wrap { position: relative; width: 500px; height: 60px; background: rgba(10,5,20,0.8); border: 2px solid rgba(255,255,255,0.1); border-radius: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); overflow: hidden; backdrop-filter: blur(10px); }
        
        /* SVG Liquid Fill */
        svg { position: absolute; top:0; left:0; width:100%; height:100%; border-radius: 30px; }
        .text { position: absolute; top:0; left:0; width:100%; height:100%; display: flex; justify-content: space-between; align-items: center; padding: 0 25px; box-sizing: border-box; color: #fff; font-weight: 900; font-size: 20px; z-index: 10; text-shadow: 0 2px 10px rgba(0,0,0,0.8); letter-spacing: 2px; }
        
        .milestone { position: absolute; top: 0; width: 2px; height: 100%; background: rgba(255,255,255,0.3); z-index: 5; }
        .m25 { left: 25%; } .m50 { left: 50%; } .m75 { left: 75%; }

        /* Canvas Sparks */
        canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 999; }
    </style>
</head>
<body>
    <canvas id="cvs"></canvas>
    <div class="bar-wrap">
        <svg viewBox="0 0 500 60" preserveAspectRatio="none">
            <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stop-color="#ff0055"/>
                    <stop offset="100%" stop-color="#ffaa00"/>
                </linearGradient>
            </defs>
            <!-- Liquid Path -->
            <path id="liquid" d="M0,60 L0,30 Q25,20 50,30 T100,30 L100,60 Z" fill="url(#grad)"/>
        </svg>
        <div class="milestone m25"></div><div class="milestone m50"></div><div class="milestone m75"></div>
        <div class="text"><span>META SUBS</span><span id="txt">0 / 100</span></div>
    </div>
    <script>
        const path = document.getElementById('liquid');
        const txt = document.getElementById('txt');
        let subs = 0, target = 100, phase = 0;
        
        // Liquid Animation
        function animateWave() {
            phase -= 0.1;
            const pct = subs/target;
            const width = pct * 500;
            const baseH = 60 - (pct * 60);
            const amp = pct > 0 && pct < 1 ? 5 : 0; // Solo onda si está llenando
            
            // Construir path curvo (onda)
            let d = `M0,60 L0,${baseH} `;
            for(let x=0; x<=width; x+=10) {
                let y = baseH + Math.sin(x*0.05 + phase)*amp;
                d += `L${x},${y} `;
            }
            d += `L${width},60 Z`;
            path.setAttribute('d', d);
            requestAnimationFrame(animateWave);
        }
        animateWave();

        // Sparks Canvas
        const ctx = document.getElementById('cvs').getContext('2d');
        const W = window.innerWidth, H = window.innerHeight;
        document.getElementById('cvs').width = W; document.getElementById('cvs').height = H;
        let sparks = [];

        function fireSparks(xRatio, color) {
            const bx = (window.innerWidth - 500)/2 + (xRatio*500);
            const by = 30 + 20; // offset top + half height
            for(let i=0; i<50; i++) {
                sparks.push({ x: bx, y: by, vx: (Math.random()-0.5)*15, vy: (Math.random()-1)*15, life: 1, c: color });
            }
        }

        function drawSparks() {
            ctx.clearRect(0,0,W,H);
            for(let i=sparks.length-1; i>=0; i--) {
                let s = sparks[i];
                s.x += s.vx; s.y += s.vy; s.vy += 0.5; s.life -= 0.02;
                if(s.life <= 0) { sparks.splice(i,1); continue; }
                ctx.globalAlpha = s.life; ctx.fillStyle = s.c;
                ctx.beginPath(); ctx.arc(s.x, s.y, 3, 0, Math.PI*2); ctx.fill();
            }
            requestAnimationFrame(drawSparks);
        }
        drawSparks();

        // Logic
        setInterval(() => {
            if(subs < target) {
                subs += 1; txt.innerText = `${subs} / ${target}`;
                if(subs===25) fireSparks(0.25, '#00ffff');
                if(subs===50) fireSparks(0.50, '#ff00ff');
                if(subs===75) fireSparks(0.75, '#ffff00');
                if(subs===100) fireSparks(1.0, '#00ff00');
            } else subs = 0;
        }, 300);
    </script>
</body>
</html>""",

"reloj_scifi": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; background: transparent; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'Courier New', monospace; overflow: hidden; }
        .holo-wrap { position: relative; width: 300px; height: 300px; display: flex; justify-content: center; align-items: center; }
        
        /* Concéntricos SVG */
        svg { position: absolute; width: 100%; height: 100%; filter: drop-shadow(0 0 10px #0f0); }
        .r1 { stroke: rgba(0,255,0,0.8); stroke-width: 2; stroke-dasharray: 4 10; animation: spin 20s linear infinite; }
        .r2 { stroke: rgba(0,255,0,0.5); stroke-width: 10; stroke-dasharray: 50 20 10 20; animation: spin 15s linear infinite reverse; }
        .r3 { stroke: rgba(0,255,0,0.3); stroke-width: 40; stroke-dasharray: 2 4; animation: spin 30s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }

        /* Escaneo Radar */
        .radar { position: absolute; width: 100%; height: 100%; border-radius: 50%; background: conic-gradient(rgba(0,255,0,0.4) 0deg, transparent 60deg); animation: spin 2s linear infinite; }
        
        /* Central Content */
        .center { position: relative; z-index: 10; text-align: center; color: #0f0; text-shadow: 0 0 8px #0f0; background: rgba(0,10,0,0.8); border-radius: 50%; width: 160px; height: 160px; display: flex; flex-direction: column; justify-content: center; align-items: center; border: 2px solid #0f0; box-shadow: inset 0 0 20px #0f0; }
        .time { font-size: 26px; font-weight: bold; margin-bottom: 5px; letter-spacing: 2px; }
        .sys { font-size: 10px; opacity: 0.8; }
        
        /* Blips (Puntos detectados) */
        .blip { position: absolute; width: 6px; height: 6px; background: #fff; border-radius: 50%; box-shadow: 0 0 10px #fff; opacity: 0; }
        @keyframes fadeOut { 0% { opacity: 1; transform: scale(1.5); } 100% { opacity: 0; transform: scale(1); } }
    </style>
</head>
<body>
    <div class="holo-wrap" id="w">
        <svg viewBox="0 0 200 200">
            <circle cx="100" cy="100" r="90" fill="none" class="r1"/>
            <circle cx="100" cy="100" r="75" fill="none" class="r2"/>
            <circle cx="100" cy="100" r="50" fill="none" class="r3"/>
        </svg>
        <div class="radar"></div>
        <div class="center">
            <div class="time" id="t">00:00:00</div>
            <div class="sys" id="s">CPU: 12% | RAM: 45%</div>
        </div>
    </div>
    <script>
        // Clock & LLM Status Fetch
        async function fetchSys() {
            try {
                let res = await fetch('http://127.0.0.1:7860/v1/status');
                let data = await res.json();
                let model = data.active_model || 'NO MODEL';
                let provider = data.active_provider || 'NO PROV';
                if(model.length > 10) model = model.substring(0,10) + '..';
                document.getElementById('s').innerText = `PRV: ${provider.toUpperCase()} | MOD: ${model.toUpperCase()}`;
            } catch(e) {
                document.getElementById('s').innerText = 'GRAVITY API OFFLINE';
            }
        }

        setInterval(()=>{
            const d = new Date();
            document.getElementById('t').innerText = String(d.getHours()).padStart(2,'0')+":"+String(d.getMinutes()).padStart(2,'0')+":"+String(d.getSeconds()).padStart(2,'0');
        }, 1000);
        
        setInterval(fetchSys, 3000);
        fetchSys();

        // Radar Blips
        const w = document.getElementById('w');
        setInterval(()=>{
            if(Math.random()>0.5){
                let b = document.createElement('div'); b.className = 'blip';
                let angle = Math.random() * Math.PI * 2;
                let r = Math.random() * 40 + 60; // radius between 60 and 100
                b.style.left = (150 + Math.cos(angle)*r - 3) + 'px';
                b.style.top = (150 + Math.sin(angle)*r - 3) + 'px';
                b.style.animation = 'fadeOut 1.5s forwards';
                w.appendChild(b);
                setTimeout(()=>b.remove(), 1500);
            }
        }, 800);
    </script>
</body>
</html>""",

"gravity_core": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; overflow: hidden; background: transparent; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: 'Courier New', monospace; }
        canvas { position: absolute; top:0; left:0; width:100%; height:100%; }
        .core { position: absolute; width: 40px; height: 40px; border-radius: 50%; background: #fff; box-shadow: 0 0 50px #0ff, 0 0 100px #0ff, inset 0 0 20px #fff; animation: pulse 2s infinite alternate; }
        @keyframes pulse { 0% { transform: scale(0.8); opacity: 0.8; } 100% { transform: scale(1.2); opacity: 1; } }
        .info { position: absolute; bottom: 20px; text-align: center; color: #0ff; text-shadow: 0 0 10px #0ff; font-weight: bold; font-size: 14px; letter-spacing: 2px; }
    </style>
</head>
<body>
    <canvas id="c"></canvas>
    <div class="core" id="core"></div>
    <div class="info" id="info">CORE ESTABLE<br>LATENCIA: 0ms</div>
    <script>
        const canvas = document.getElementById('c');
        const ctx = canvas.getContext('2d');
        let W = window.innerWidth, H = window.innerHeight;
        canvas.width = W; canvas.height = H;

        // 3D Cube Math
        const nodes = [[-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1], [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1]];
        const edges = [[0,1], [1,3], [3,2], [2,0], [4,5], [5,7], [7,6], [6,4], [0,4], [1,5], [2,6], [3,7]];
        let angleX = 0, angleY = 0;
        let rotSpeed = 0.01;
        let nodeColor = '#0ff';

        function rotate(node, ax, ay) {
            let sinx = Math.sin(ax), cosx = Math.cos(ax);
            let siny = Math.sin(ay), cosy = Math.cos(ay);
            let x = node[0], y = node[1], z = node[2];
            let xy = cosx*y - sinx*z, xz = sinx*y + cosx*z;
            let yx = cosy*x + siny*xz, yz = -siny*x + cosy*xz;
            return [yx, xy, yz];
        }

        function draw() {
            ctx.clearRect(0, 0, W, H);
            angleX += rotSpeed; angleY += rotSpeed*0.7;
            
            let projected = nodes.map(n => {
                let r = rotate(n, angleX, angleY);
                let z = r[2] + 4; // perspective zoom
                let fov = 300;
                return [r[0] * fov/z + W/2, r[1] * fov/z + H/2];
            });

            ctx.strokeStyle = nodeColor;
            ctx.lineWidth = 2;
            ctx.lineJoin = 'round';

            for(let e of edges) {
                ctx.beginPath();
                ctx.moveTo(projected[e[0]][0], projected[e[0]][1]);
                ctx.lineTo(projected[e[1]][0], projected[e[1]][1]);
                ctx.stroke();
            }
            requestAnimationFrame(draw);
        }
        draw();

        async function fetchStatus() {
            try {
                let res = await fetch('http://127.0.0.1:7860/v1/status');
                let data = await res.json();
                let lat = 0;
                if(data.backends && data.backends.length > 0) lat = data.backends[0].latency_ms;
                document.getElementById('info').innerHTML = `CORE: ${data.active_provider || 'LOCAL'}<br>LATENCIA: ${lat}ms`;
                
                // Si la latencia es alta, rota más rápido y se pone inestable (naranja)
                if(lat > 2000) { rotSpeed = 0.05; nodeColor = '#ffaa00'; document.getElementById('core').style.boxShadow = '0 0 50px #ffaa00, 0 0 100px #ffaa00'; }
                else { rotSpeed = 0.01; nodeColor = '#0ff'; document.getElementById('core').style.boxShadow = '0 0 50px #0ff, 0 0 100px #0ff'; }
            } catch(e) {
                document.getElementById('info').innerHTML = `CORE OFFLINE<br>RECONECTANDO...`;
                rotSpeed = 0.001; nodeColor = '#f00';
            }
        }
        setInterval(fetchStatus, 3000); fetchStatus();
    </script>
</body>
</html>""",

"cinematic_start": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; overflow: hidden; background: transparent; }
        .bars { position: absolute; width: 100%; height: 12vh; background: #000; z-index: 100; left: 0; }
        .bar-top { top: 0; } .bar-bottom { bottom: 0; }
        canvas { position: absolute; top:0; left:0; width:100%; height:100%; filter: blur(5px) contrast(1.2); }
        .text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; z-index: 50; }
        .title { font-family: 'Arial Black', sans-serif; font-size: 50px; color: transparent; -webkit-text-stroke: 2px rgba(255,255,255,0.8); letter-spacing: 15px; animation: pulse 4s infinite alternate; }
        .timer { font-family: monospace; font-size: 30px; color: #fff; margin-top: 10px; letter-spacing: 5px; opacity: 0.8; }
        @keyframes pulse { 0% { text-shadow: 0 0 0 rgba(255,255,255,0); } 100% { text-shadow: 0 0 30px rgba(255,255,255,0.8); } }
    </style>
</head>
<body>
    <div class="bars bar-top"></div><div class="bars bar-bottom"></div>
    <canvas id="fog"></canvas>
    <div class="text">
        <div class="title" id="t">STARTING SOON</div>
        <div class="timer" id="tm">10:00</div>
    </div>
    <script>
        // Volumetric Fog using overlapping sine waves and particles
        const canvas = document.getElementById('fog');
        const ctx = canvas.getContext('2d');
        let W = window.innerWidth, H = window.innerHeight;
        canvas.width = W; canvas.height = H;
        
        let particles = [];
        for(let i=0; i<150; i++){
            particles.push({
                x: Math.random()*W, y: Math.random()*H,
                r: Math.random()*150 + 50,
                vx: (Math.random()-0.5)*1, vy: (Math.random()-0.5)*0.5,
                phase: Math.random()*Math.PI*2
            });
        }

        let isDone = false;

        function render() {
            ctx.clearRect(0,0,W,H);
            for(let p of particles) {
                p.x += p.vx; p.y += p.vy; p.phase += 0.01;
                if(p.x < -p.r) p.x = W+p.r; if(p.x > W+p.r) p.x = -p.r;
                if(p.y < -p.r) p.y = H+p.r; if(p.y > H+p.r) p.y = -p.r;
                
                let rad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
                let alpha = isDone ? 0 : (Math.sin(p.phase)*0.03 + 0.05); // Disipate when done
                rad.addColorStop(0, `rgba(150, 150, 200, ${alpha})`);
                rad.addColorStop(1, 'rgba(150, 150, 200, 0)');
                ctx.fillStyle = rad;
                ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2); ctx.fill();
            }
            requestAnimationFrame(render);
        }
        render();

        let sec = 600;
        const iv = setInterval(()=>{
            sec--;
            if(sec<=0) {
                clearInterval(iv);
                isDone = true;
                document.getElementById('t').innerText = "SYSTEM ONLINE";
                document.getElementById('tm').innerText = "READY";
                return;
            }
            document.getElementById('tm').innerText = String(Math.floor(sec/60)).padStart(2,'0')+":"+String(sec%60).padStart(2,'0');
        }, 1000);
    </script>
</body>
</html>""",

"matrix_rain": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; overflow: hidden; background: transparent; }
        canvas { display: block; }
    </style>
</head>
<body>
    <canvas id="m"></canvas>
    <script>
        const canvas = document.getElementById('m');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth; canvas.height = window.innerHeight;
        
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*';
        const fontSize = 16;
        const columns = canvas.width / fontSize;
        const drops = [];
        for(let x=0; x<columns; x++) drops[x] = 1;
        
        let injectWord = null;
        let injectCol = 0;
        let injectIdx = 0;

        function draw() {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.font = fontSize + 'px monospace';
            
            for(let i=0; i<drops.length; i++) {
                let text = chars.charAt(Math.floor(Math.random() * chars.length));
                
                // Inject real words from Security API
                if(injectWord && i === injectCol && drops[i] >= injectIdx && drops[i] < injectIdx + injectWord.length) {
                    text = injectWord[drops[i] - injectIdx];
                    ctx.fillStyle = '#fff'; // Resaltar palabra inyectada
                } else {
                    ctx.fillStyle = '#0f0';
                }
                
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                if(drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }
            requestAnimationFrame(draw);
        }
        draw();

        async function fetchSec() {
            try {
                let res = await fetch('http://127.0.0.1:7860/v1/security');
                let data = await res.json();
                if(data.status && Math.random() > 0.5) {
                    const words = ["SECURE", "FIREWALL", "SYSTEM", "GRAVITY", "MONITOR", "ACTIVE"];
                    injectWord = words[Math.floor(Math.random()*words.length)];
                    injectCol = Math.floor(Math.random() * columns);
                    injectIdx = drops[injectCol] + 2;
                }
            } catch(e) {}
        }
        setInterval(fetchSec, 4000);
    </script>
</body>
</html>"""
}

