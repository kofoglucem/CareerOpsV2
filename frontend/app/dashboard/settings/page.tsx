"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Wifi, Linkedin, Bot, FileText } from "lucide-react";

export default function SettingsPage() {
  const [proxyStatus, setProxyStatus] = useState<any>(null);
  const [liEmail, setLiEmail] = useState("");
  const [liPassword, setLiPassword] = useState("");
  const [aiProvider, setAiProvider] = useState("deepseek");
  const [aiEmail, setAiEmail] = useState("");
  const [aiPassword, setAiPassword] = useState("");
  const [cvText, setCvText] = useState("");
  const [msgs, setMsgs] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.get("/proxy/status").then(({ data }) => setProxyStatus(data));
    api.get("/users/me").then(({ data }) => {
      if (data.cv_text) setCvText(data.cv_text);
    });
  }, []);

  const setMsg = (key: string, val: string) => setMsgs((m) => ({ ...m, [key]: val }));
  const setLoad = (key: string, val: boolean) => setLoading((l) => ({ ...l, [key]: val }));

  const acquireProxy = async () => {
    setLoad("proxy", true);
    try {
      const { data } = await api.post("/proxy/acquire");
      setMsg("proxy", data.message);
      api.get("/proxy/status").then(({ data }) => setProxyStatus(data));
    } catch (err: any) {
      setMsg("proxy", err.response?.data?.detail || "Hata");
    } finally {
      setLoad("proxy", false);
    }
  };

  const linkedinLogin = async () => {
    setLoad("li", true);
    try {
      const { data } = await api.post("/proxy/linkedin/login", { email: liEmail, password: liPassword });
      setMsg("li", data.message);
      api.get("/proxy/status").then(({ data }) => setProxyStatus(data));
    } catch (err: any) {
      setMsg("li", err.response?.data?.detail || "Hata");
    } finally {
      setLoad("li", false);
    }
  };

  const aiLogin = async () => {
    setLoad("ai", true);
    try {
      const { data } = await api.post("/ai/login", { provider: aiProvider, email: aiEmail, password: aiPassword });
      setMsg("ai", data.message);
    } catch (err: any) {
      setMsg("ai", err.response?.data?.detail || "Hata");
    } finally {
      setLoad("ai", false);
    }
  };

  const saveCV = async () => {
    setLoad("cv", true);
    try {
      await api.patch("/users/me/cv", { cv_text: cvText });
      setMsg("cv", "CV kaydedildi!");
    } catch {
      setMsg("cv", "Hata");
    } finally {
      setLoad("cv", false);
    }
  };

  const StatusBadge = ({ ok }: { ok: boolean }) => (
    <span className={`text-xs px-2 py-0.5 rounded-full ${ok ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"}`}>
      {ok ? "Aktif" : "Pasif"}
    </span>
  );

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Ayarlar / Settings</h1>

      {/* Proxy */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Wifi size={20} className="text-primary-500" />
          <h2 className="font-semibold">Residential IP</h2>
          {proxyStatus && <StatusBadge ok={proxyStatus.has_proxy} />}
        </div>
        <p className="text-sm text-gray-400 mb-4">
          LinkedIn araması yapabilmek için residential IP gerekmektedir. (20 token)
        </p>
        {!proxyStatus?.has_proxy && (
          <button onClick={acquireProxy} disabled={loading.proxy} className="btn-primary">
            {loading.proxy ? "Alınıyor..." : "Residential IP Al (20 Token)"}
          </button>
        )}
        {msgs.proxy && <p className={`text-sm mt-2 ${msgs.proxy.includes("Hata") || msgs.proxy.includes("Yetersiz") ? "text-red-400" : "text-green-400"}`}>{msgs.proxy}</p>}
      </div>

      {/* LinkedIn */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Linkedin size={20} className="text-blue-500" />
          <h2 className="font-semibold">LinkedIn Girişi</h2>
          {proxyStatus && <StatusBadge ok={proxyStatus.linkedin_logged_in} />}
        </div>
        {proxyStatus?.linkedin_logged_in ? (
          <p className="text-sm text-green-400">{proxyStatus.linkedin_email} ile giriş yapılmış</p>
        ) : (
          <div className="space-y-3">
            <input className="input" type="email" placeholder="LinkedIn E-posta" value={liEmail} onChange={(e) => setLiEmail(e.target.value)} />
            <input className="input" type="password" placeholder="LinkedIn Şifre" value={liPassword} onChange={(e) => setLiPassword(e.target.value)} />
            <button onClick={linkedinLogin} disabled={loading.li || !proxyStatus?.has_proxy} className="btn-primary">
              {loading.li ? "Giriş yapılıyor..." : "LinkedIn'e Giriş Yap"}
            </button>
            {!proxyStatus?.has_proxy && <p className="text-xs text-yellow-400">Önce Residential IP almalısınız</p>}
          </div>
        )}
        {msgs.li && <p className={`text-sm mt-2 ${msgs.li.includes("Hata") || msgs.li.includes("başarısız") ? "text-red-400" : "text-green-400"}`}>{msgs.li}</p>}
      </div>

      {/* AI Service */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Bot size={20} className="text-purple-500" />
          <h2 className="font-semibold">AI Servisi (İsteğe Bağlı)</h2>
        </div>
        <p className="text-sm text-gray-400 mb-4">İş ilanlarını CV'nizle karşılaştırarak uyum skoru almak için kullanılır. (50 token/değerlendirme)</p>
        <div className="space-y-3">
          <select className="input" value={aiProvider} onChange={(e) => setAiProvider(e.target.value)}>
            <option value="deepseek">DeepSeek</option>
            <option value="chatgpt">ChatGPT</option>
          </select>
          <input className="input" type="email" placeholder="E-posta" value={aiEmail} onChange={(e) => setAiEmail(e.target.value)} />
          <input className="input" type="password" placeholder="Şifre" value={aiPassword} onChange={(e) => setAiPassword(e.target.value)} />
          <button onClick={aiLogin} disabled={loading.ai} className="btn-primary">
            {loading.ai ? "Giriş yapılıyor..." : `${aiProvider === "deepseek" ? "DeepSeek" : "ChatGPT"}'e Giriş Yap`}
          </button>
        </div>
        {msgs.ai && <p className={`text-sm mt-2 ${msgs.ai.includes("Hata") || msgs.ai.includes("başarısız") ? "text-red-400" : "text-green-400"}`}>{msgs.ai}</p>}
      </div>

      {/* CV */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <FileText size={20} className="text-green-500" />
          <h2 className="font-semibold">CV Metni</h2>
        </div>
        <p className="text-sm text-gray-400 mb-3">AI değerlendirme için CV'nizi metin olarak girin.</p>
        <textarea
          className="input h-48 resize-none"
          placeholder="CV metninizi buraya yapıştırın..."
          value={cvText}
          onChange={(e) => setCvText(e.target.value)}
        />
        <button onClick={saveCV} disabled={loading.cv} className="btn-primary mt-3">
          {loading.cv ? "Kaydediliyor..." : "CV'yi Kaydet"}
        </button>
        {msgs.cv && <p className={`text-sm mt-2 ${msgs.cv.includes("Hata") ? "text-red-400" : "text-green-400"}`}>{msgs.cv}</p>}
      </div>
    </div>
  );
}
