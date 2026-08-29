import React, { useState, useEffect, useRef } from "react";
import * as THREE from "three";

const LOG_LINES = [
  "SISTEMA INICIALIZADO",
  "DIAGNÓSTICO DE NÚCLEO: NOMINAL",
  "ENLACE SATELITAL: ESTABLE",
  "PROTOCOLOS DE SEGURIDAD: ACTIVOS",
  "ANÁLISIS ATMOSFÉRICO EN CURSO",
];

const RESPONSES = [
  "Todos los sistemas funcionan dentro de parámetros normales, señor.",
  "Procesando su solicitud. Un momento, por favor.",
  "He localizado la información solicitada en la base de datos.",
  "Los niveles de energía se mantienen estables al 98%.",
  "Ejecutando protocolo solicitado. Confirmación en curso.",
];

function useTypedLog(lines, speed = 45) {
  const [displayed, setDisplayed] = useState([]);
  useEffect(() => {
    let cancelled = false;
    async function run() {
      for (let i = 0; i < lines.length; i++) {
        let text = "";
        for (let c = 0; c < lines[i].length; c++) {
          if (cancelled) return;
          text += lines[i][c];
          setDisplayed((prev) => {
            const next = [...prev];
            next[i] = text;
            return next;
          });
          await new Promise((r) => setTimeout(r, speed));
        }
        await new Promise((r) => setTimeout(r, 250));
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, []);
  return displayed;
}

const BLUES = ["#7CF0FF", "#4FD8EA", "#3AA9E0", "#2E7CD6", "#1AA8C0", "#6EC8FF", "#B7EFFA", "#1E5FA8"];

function DotRing({ size, duration, reverse, dotCount = 24, dotSize = 3, opacity = 0.6 }) {
  const dots = new Array(dotCount).fill(0);
  return (
    <div
      style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        width: size,
        height: size,
        marginLeft: -size / 2,
        marginTop: -size / 2,
        animation: `spin ${duration}s linear infinite ${reverse ? "reverse" : ""}`,
      }}
    >
      {dots.map((_, i) => {
        const angle = (360 / dotCount) * i;
        const color = BLUES[i % BLUES.length];
        const sizeJitter = dotSize + ((i % 3) - 1) * 0.6;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              width: sizeJitter,
              height: sizeJitter,
              borderRadius: "50%",
              background: color,
              boxShadow: `0 0 4px ${color}`,
              opacity,
              transform: `rotate(${angle}deg) translate(${size / 2}px) rotate(-${angle}deg)`,
            }}
          />
        );
      })}
    </div>
  );
}

function Waveform({ active }) {
  const bars = new Array(28).fill(0);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 3, height: 40 }}>
      {bars.map((_, i) => (
        <div
          key={i}
          style={{
            width: 3,
            borderRadius: 2,
            background: "linear-gradient(180deg, #7CF0FF, #1AA8C0)",
            height: active ? undefined : 4,
            opacity: active ? 1 : 0.25,
            animation: active
              ? `wave 900ms ease-in-out infinite`
              : "none",
            animationDelay: `${i * 45}ms`,
          }}
        />
      ))}
    </div>
  );
}

function heartbeatScale(t) {
  // t in [0,1) — mirrors the CSS heartbeat keyframes (lub-dub)
  const points = [
    [0, 1],
    [0.14, 1.1],
    [0.28, 0.97],
    [0.42, 1.14],
    [0.7, 1],
    [1, 1],
  ];
  for (let i = 0; i < points.length - 1; i++) {
    const [t0, s0] = points[i];
    const [t1, s1] = points[i + 1];
    if (t >= t0 && t <= t1) {
      const f = (t - t0) / (t1 - t0);
      return s0 + (s1 - s0) * f;
    }
  }
  return 1;
}

// cheap layered sine "noise" — deterministic, no external noise lib needed
function pseudoNoise(x, y, z) {
  return (
    Math.sin(x * 4.1 + y * 1.7) * Math.cos(z * 3.3 + x * 0.9) * 0.5 +
    Math.sin(y * 6.2 + z * 2.1) * Math.cos(x * 5.4) * 0.3 +
    Math.sin(x * 11 + z * 9) * 0.12
  );
}

function makeTissueTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#7A0F16";
  ctx.fillRect(0, 0, 512, 512);
  // mottled blotches: darker maroon patches + brighter pink-red patches
  for (let i = 0; i < 260; i++) {
    const x = Math.random() * 512;
    const y = Math.random() * 512;
    const r = 14 + Math.random() * 46;
    const dark = Math.random() > 0.5;
    const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
    if (dark) {
      grad.addColorStop(0, "rgba(60,6,8,0.55)");
      grad.addColorStop(1, "rgba(60,6,8,0)");
    } else {
      grad.addColorStop(0, "rgba(220,90,90,0.35)");
      grad.addColorStop(1, "rgba(220,90,90,0)");
    }
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
  // fine wet specular speckles
  for (let i = 0; i < 900; i++) {
    ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.05})`;
    ctx.fillRect(Math.random() * 512, Math.random() * 512, 1.4, 1.4);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

function buildVentricleGeometry() {
  const geo = new THREE.IcosahedronGeometry(1, 5);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    const z = pos.getZ(i);
    // elongate downward into a tapered apex, widen upper chambers
    const taper = y < 0 ? 1 + y * 0.55 : 1;
    let nx = x * taper;
    let ny = y * 1.55;
    let nz = z * taper * 0.92 + 0.12; // slight forward bulge (right ventricle)

    // organic surface bumps (muscle fiber texture)
    const n = pseudoNoise(x * 2.2, y * 2.2, z * 2.2);
    const bump = 1 + n * 0.05;
    nx *= bump;
    ny *= bump;
    nz *= bump;

    // pull in a groove between left/right ventricles on the front face
    if (z > 0.2 && y < 0.3) {
      const groove = Math.exp(-Math.pow((x - 0.05) * 6, 2)) * 0.09;
      nz -= groove;
    }
    pos.setXYZ(i, nx, ny, nz);
  }
  geo.computeVertexNormals();
  return geo;
}

function Heart({ size = 90, listening }) {
  const mountRef = useRef(null);
  const listeningRef = useRef(listening);
  listeningRef.current = listening;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 20);
    camera.position.set(0.15, 0.1, 5.4);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(size, size);
    mount.appendChild(renderer.domElement);

    const heartGroup = new THREE.Group();
    scene.add(heartGroup);

    // holographic translucent red material (X-ray / medical scan look)
    const tissueMat = new THREE.MeshPhysicalMaterial({
      color: 0xff2b2b,
      transparent: true,
      opacity: 0.55,
      roughness: 0.2,
      metalness: 0,
      emissive: 0x990000,
      emissiveIntensity: 0.5,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0xff6b6b,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0xff3333,
      transparent: true,
      opacity: 0.22,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const vesselMat = tissueMat;
    const vesselInsideMat = new THREE.MeshBasicMaterial({
      color: 0xff9a9a,
      transparent: true,
      opacity: 0.5,
    });

    const addWithWireAndGlow = (geo, scale, position, rotation) => {
      const mesh = new THREE.Mesh(geo, tissueMat);
      const wire = new THREE.Mesh(geo, wireMat);
      const glow = new THREE.Mesh(geo, glowMat);
      [mesh, wire, glow].forEach((m) => {
        if (scale) m.scale.set(...scale);
        if (position) m.position.set(...position);
        if (rotation) m.rotation.set(...rotation);
      });
      glow.scale.set(
        (scale ? scale[0] : 1) * 1.12,
        (scale ? scale[1] : 1) * 1.12,
        (scale ? scale[2] : 1) * 1.12
      );
      heartGroup.add(glow, mesh, wire);
      return mesh;
    };

    // main ventricular mass
    const bodyGeo = buildVentricleGeometry();
    addWithWireAndGlow(bodyGeo, [1.05, 1.3, 1.05], [0, -0.15, 0]);

    // left & right atria (upper bumps, slightly behind)
    const atriumGeo = new THREE.SphereGeometry(0.5, 24, 20);
    addWithWireAndGlow(atriumGeo, [0.72, 0.6, 0.68], [-0.42, 1.02, -0.15]);
    addWithWireAndGlow(atriumGeo, [0.68, 0.58, 0.66], [0.5, 0.95, -0.05]);

    // aorta: curved tube arching up and over
    const aortaCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-0.1, 1.15, 0.05),
      new THREE.Vector3(-0.05, 1.65, -0.05),
      new THREE.Vector3(0.25, 1.85, -0.15),
      new THREE.Vector3(0.55, 1.6, -0.2),
      new THREE.Vector3(0.6, 1.25, -0.05),
    ]);
    const aortaGeo = new THREE.TubeGeometry(aortaCurve, 40, 0.16, 14, false);
    addWithWireAndGlow(aortaGeo);

    // pulmonary trunk
    const pulmGeo = new THREE.CylinderGeometry(0.15, 0.19, 0.7, 14);
    addWithWireAndGlow(pulmGeo, null, [0.15, 1.55, 0.28], [0.5, 0, 0.35]);

    // vena cava / pulmonary vein stumps
    const stumps = [
      { pos: [-0.55, 1.25, -0.25], rot: [0.3, 0, -0.4], r: 0.1, h: 0.4 },
      { pos: [0.75, 1.15, -0.3], rot: [-0.2, 0, 0.6], r: 0.09, h: 0.35 },
      { pos: [-0.15, 1.35, -0.4], rot: [0.6, 0.2, 0], r: 0.08, h: 0.3 },
    ];
    stumps.forEach(({ pos, rot, r, h }) => {
      const g = new THREE.CylinderGeometry(r, r * 1.15, h, 12);
      addWithWireAndGlow(g, null, pos, rot);
      const capGeo = new THREE.CircleGeometry(r, 12);
      const cap = new THREE.Mesh(capGeo, vesselInsideMat);
      cap.position.set(pos[0], pos[1] + h / 2, pos[2]);
      cap.rotation.set(rot[0] + Math.PI / 2, rot[1], rot[2]);
      heartGroup.add(cap);
    });

    // surface groove line (interventricular sulcus) for realism
    const sulcusPts = [];
    for (let i = 0; i <= 20; i++) {
      const f = i / 20;
      sulcusPts.push(
        new THREE.Vector3(0.05 - f * 0.15, 0.9 - f * 1.7, 0.95 - f * 0.3)
      );
    }
    const sulcusCurve = new THREE.CatmullRomCurve3(sulcusPts);
    const sulcusGeo = new THREE.TubeGeometry(sulcusCurve, 24, 0.03, 6, false);
    const sulcusMesh = new THREE.Mesh(
      sulcusGeo,
      new THREE.MeshBasicMaterial({
        color: 0xffb3b3,
        transparent: true,
        opacity: 0.5,
      })
    );
    heartGroup.add(sulcusMesh);

    heartGroup.rotation.set(0.1, -0.5, 0);
    heartGroup.position.y = -0.15;

    scene.add(new THREE.AmbientLight(0xff5555, 0.5));
    const key = new THREE.PointLight(0xff3333, 1.2, 12);
    key.position.set(1.5, 1.5, 3);
    scene.add(key);
    const rimLight = new THREE.PointLight(0xff8080, 0.8, 12);
    rimLight.position.set(-2, 0.5, -2);
    scene.add(rimLight);

    let frameId;
    const start = performance.now();

    const animate = () => {
      const elapsed = performance.now() - start;
      const cycle = listeningRef.current ? 620 : 1100;
      const t = (elapsed % cycle) / cycle;
      const s = heartbeatScale(t);
      heartGroup.scale.set(s, s * 0.97 + 0.03, s);
      heartGroup.rotation.y = -0.5 + Math.sin(elapsed / 2800) * 0.5;
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      heartGroup.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
      });
      renderer.dispose();
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [size]);

  return (
    <div
      ref={mountRef}
      style={{
        width: size,
        height: size,
        filter: "drop-shadow(0 6px 12px rgba(0,0,0,0.6))",
      }}
    />
  );
}

function RadarCore({ size = 190, listening }) {
  const c = 100;
  const outerTicks = new Array(28).fill(0).map((_, i) => {
    const angle = (360 / 28) * i;
    const isMain = i % (28 / 8) === 0;
    const r1 = isMain ? 80 : 90;
    const r2 = isMain ? 106 : 98;
    return { angle, r1, r2 };
  });
  const innerSpikes = new Array(18).fill(0).map((_, i) => {
    const angle = (360 / 18) * i;
    return { angle, r1: 14, r2: 34 };
  });
  const whiteSegments = new Array(8).fill(0).map((_, i) => (360 / 8) * i + 12);

  const polar = (angle, r) => {
    const rad = (angle * Math.PI) / 180;
    return [c + r * Math.cos(rad), c + r * Math.sin(rad)];
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 200"
      style={{ overflow: "visible" }}
    >
      {/* radial ticks */}
      <g style={{ animation: `spin ${listening ? 10 : 34}s linear infinite` }}>
        {outerTicks.map((t, i) => {
          const [x1, y1] = polar(t.angle, t.r1);
          const [x2, y2] = polar(t.angle, t.r2);
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#EAFBFF"
              strokeWidth={1.4}
              opacity={0.8}
            />
          );
        })}
        {/* dashed pink/magenta circle */}
        <circle
          cx={c}
          cy={c}
          r={80}
          fill="none"
          stroke="#FF4FA3"
          strokeWidth={1.4}
          strokeDasharray="6 7"
          opacity={0.85}
        />
        {/* white arc segments */}
        {whiteSegments.map((angle, i) => (
          <rect
            key={i}
            x={c - 11}
            y={c - 68}
            width={22}
            height={9}
            rx={3}
            fill="#F4FBFF"
            style={{
              transformOrigin: `${c}px ${c}px`,
              transform: `rotate(${angle}deg)`,
              filter: "drop-shadow(0 0 5px rgba(244,251,255,0.9))",
            }}
          />
        ))}
      </g>

      {/* inner group: red spikes + dashed circle, opposite rotation */}
      <g
        style={{
          animation: `spin ${listening ? 5 : 16}s linear infinite reverse`,
        }}
      >
        {innerSpikes.map((t, i) => {
          const [x1, y1] = polar(t.angle, t.r1);
          const [x2, y2] = polar(t.angle, t.r2);
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="#FF3B3B"
              strokeWidth={1.2}
              opacity={0.75}
            />
          );
        })}
        <circle
          cx={c}
          cy={c}
          r={38}
          fill="none"
          stroke="#FF3B3B"
          strokeWidth={1.3}
          strokeDasharray="4 5"
          opacity={0.85}
        />
      </g>

      {/* center */}
      <circle
        cx={c}
        cy={c}
        r={9}
        fill="none"
        stroke="#FF3B3B"
        strokeWidth={1.4}
        style={{
          animation: `heartbeat ${listening ? "0.6s" : "1.1s"} ease-in-out infinite`,
          transformOrigin: `${c}px ${c}px`,
        }}
      />
      <circle
        cx={c}
        cy={c}
        r={3.2}
        fill="#FF3B3B"
        style={{
          animation: `heartbeat ${listening ? "0.6s" : "1.1s"} ease-in-out infinite`,
          transformOrigin: `${c}px ${c}px`,
          filter: "drop-shadow(0 0 6px #FF3B3B)",
        }}
      />
    </svg>
  );
}

function StatPanel({ label, value, sub }) {
  return (
    <div
      style={{
        border: "1px solid rgba(79,216,234,0.25)",
        background: "rgba(10,25,38,0.55)",
        padding: "10px 14px",
        minWidth: 150,
      }}
    >
      <div
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          letterSpacing: 2,
          color: "#5FA9BC",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: "'Orbitron', sans-serif",
          fontSize: 20,
          color: "#EAFBFF",
          fontWeight: 600,
        }}
      >
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 10, color: "#3E7C8C", marginTop: 2 }}>{sub}</div>
      )}
    </div>
  );
}

export default function Jarvis() {
  const [listening, setListening] = useState(false);
  const [response, setResponse] = useState(
    "Buenas tardes. Todos los sistemas están operativos. ¿En qué puedo asistirle?"
  );
  const [time, setTime] = useState(new Date());
  const log = useTypedLog(LOG_LINES);
  const timeoutRef = useRef(null);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const handleActivate = () => {
    setListening(true);
    setResponse("Escuchando...");
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setListening(false);
      setResponse(RESPONSES[Math.floor(Math.random() * RESPONSES.length)]);
    }, 2200);
  };

  const hh = time.toLocaleTimeString("es-ES", { hour12: false });

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        background:
          "radial-gradient(ellipse at center, #10254A 0%, #071228 60%, #030A1A 100%)",
        color: "#EAFBFF",
        fontFamily: "'Inter', sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        padding: 20,
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity: 0.6; transform: scale(1); } 50% { opacity: 1; transform: scale(1.04); } }
        @keyframes wave { 0%,100% { height: 4px; } 50% { height: 32px; } }
        @keyframes sweep { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes heartbeat {
          0%, 100% { transform: scale(1); }
          14% { transform: scale(1.08); }
          28% { transform: scale(0.98); }
          42% { transform: scale(1.12); }
          70% { transform: scale(1); }
        }
        @keyframes glowbeat {
          0%, 100% { box-shadow: 0 0 30px 4px rgba(79,216,234,0.3); }
          14% { box-shadow: 0 0 45px 8px rgba(124,240,255,0.5); }
          28% { box-shadow: 0 0 25px 3px rgba(79,216,234,0.25); }
          42% { box-shadow: 0 0 55px 12px rgba(124,240,255,0.6); }
          70% { box-shadow: 0 0 30px 4px rgba(79,216,234,0.3); }
        }
        @keyframes tilt3d {
          0%, 100% { transform: rotateY(-14deg) rotateX(4deg); }
          50% { transform: rotateY(14deg) rotateX(-4deg); }
        }
        .core-btn:focus-visible { outline: 2px solid #7CF0FF; outline-offset: 6px; }
        @media (prefers-reduced-motion: reduce) {
          * { animation: none !important; }
        }
      `}</style>

      {/* rectángulo principal de la interfaz */}
      <div
        style={{
          position: "relative",
          overflow: "hidden",
          border: "1px solid rgba(124,240,255,0.35)",
          borderRadius: 4,
          boxShadow: "0 0 40px rgba(79,216,234,0.15)",
          background: "rgba(4,12,26,0.4)",
          maxWidth: 480,
          width: "100%",
          transform: "scale(0.85)",
          transformOrigin: "top center",
          marginBottom: -40,
        }}
      >
      {/* grid overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(79,216,234,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(79,216,234,0.04) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
          pointerEvents: "none",
        }}
      />

      {/* top bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "18px 28px",
          borderBottom: "1px solid rgba(79,216,234,0.2)",
          position: "relative",
          zIndex: 2,
        }}
      >
        <div
          style={{
            fontFamily: "'Orbitron', sans-serif",
            fontWeight: 900,
            letterSpacing: 6,
            fontSize: 18,
            color: "#7CF0FF",
            animation: "flicker 6s infinite",
          }}
        >
          J.A.R.V.I.S.
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: "#5FA9BC",
            letterSpacing: 1,
          }}
        >
          {hh} · SISTEMA EN LÍNEA
        </div>
      </div>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          gap: 40,
          padding: "40px 20px 20px",
          position: "relative",
          zIndex: 2,
        }}
      >
        {/* left stats */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <StatPanel label="ENERGÍA" value="98%" sub="NIVEL ÓPTIMO" />
          <StatPanel label="TEMP. NÚCLEO" value="36.4°C" sub="ESTABLE" />
          <StatPanel label="RED" value="ACTIVA" sub="LATENCIA 4ms" />
        </div>

        {/* core */}
        <div
          style={{
            position: "relative",
            width: 190,
            height: 190,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <button
            className="core-btn"
            onClick={handleActivate}
            aria-label={listening ? "Escuchando" : "Activar asistente"}
            style={{
              width: 190,
              height: 190,
              borderRadius: "50%",
              border: "none",
              background: "transparent",
              cursor: "pointer",
              padding: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <RadarCore size={190} listening={listening} />
          </button>
        </div>

        {/* right stats */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <StatPanel label="SEGURIDAD" value="MÁXIMA" sub="SIN AMENAZAS" />
          <StatPanel label="ALMACENAMIENTO" value="72%" sub="4.1 TB LIBRES" />
          <StatPanel label="CLIMA LOCAL" value="19°C" sub="DESPEJADO" />
        </div>
      </div>

      {/* response line */}
      <div
        style={{
          maxWidth: 640,
          margin: "10px auto 0",
          textAlign: "center",
          padding: "0 20px",
          minHeight: 50,
          position: "relative",
          zIndex: 2,
        }}
      >
        <p
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 14,
            color: "#B7EFFA",
            lineHeight: 1.5,
          }}
        >
          {response}
        </p>
      </div>

      {/* waveform */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          marginTop: 8,
          position: "relative",
          zIndex: 2,
        }}
      >
        <Waveform active={listening} />
      </div>

      {/* bottom log */}
      <div
        style={{
          borderTop: "1px solid rgba(79,216,234,0.2)",
          marginTop: 30,
          padding: "14px 28px 24px",
          position: "relative",
          zIndex: 2,
        }}
      >
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            color: "#3E7C8C",
            letterSpacing: 1,
            marginBottom: 6,
          }}
        >
          REGISTRO DEL SISTEMA
        </div>
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 12,
            color: "#5FA9BC",
            display: "flex",
            flexDirection: "column",
            gap: 3,
          }}
        >
          {LOG_LINES.map((_, i) => (
            <div key={i}>
              <span style={{ color: "#2D6474" }}>{`>`}</span> {log[i] || ""}
              {i === LOG_LINES.length - 1 && log[i] !== LOG_LINES[i] ? (
                <span style={{ opacity: 0.6 }}>▍</span>
              ) : null}
            </div>
          ))}
        </div>
      </div>
      </div>
    </div>
  );
}
