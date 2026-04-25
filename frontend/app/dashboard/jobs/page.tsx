"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Plus, X, ExternalLink, Star, Trash2 } from "lucide-react";

export default function JobsPage() {
  const [configs, setConfigs] = useState<any[]>([]);
  const [listings, setListings] = useState<any>({ total: 0, items: [] });
  const [keywords, setKeywords] = useState<string[]>([]);
  const [kwInput, setKwInput] = useState("");
  const [interval, setInterval] = useState("4h");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get("/jobs/search-configs").then(({ data }) => setConfigs(data));
    loadListings(1);
  }, []);

  const loadListings = (p: number) => {
    api.get(`/jobs/listings?page=${p}&per_page=20`).then(({ data }) => {
      setListings(data);
      setPage(p);
    });
  };

  const addKeyword = () => {
    if (kwInput.trim() && !keywords.includes(kwInput.trim())) {
      setKeywords([...keywords, kwInput.trim()]);
      setKwInput("");
    }
  };

  const createConfig = async () => {
    if (keywords.length === 0) return;
    setLoading(true);
    setMsg("");
    try {
      await api.post("/jobs/search-config", { keywords, interval });
      setMsg("Arama başlatıldı! İlk sonuçlar 1 dakika içinde gelecek.");
      setKeywords([]);
      api.get("/jobs/search-configs").then(({ data }) => setConfigs(data));
    } catch (err: any) {
      setMsg(err.response?.data?.detail || "Hata");
    } finally {
      setLoading(false);
    }
  };

  const deleteConfig = async (id: string) => {
    await api.delete(`/jobs/search-configs/${id}`);
    setConfigs(configs.map((c) => (c.id === id ? { ...c, is_active: false } : c)));
  };

  const markRead = async (id: string) => {
    await api.patch(`/jobs/listings/${id}/read`);
    setListings({
      ...listings,
      items: listings.items.map((j: any) => (j.id === id ? { ...j, is_new: false } : j)),
    });
  };

  const evaluateJob = async (id: string) => {
    try {
      const { data } = await api.post("/ai/evaluate", { job_listing_id: id });
      setMsg(`AI Skoru: ${data.score}/100`);
      loadListings(page);
    } catch (err: any) {
      setMsg(err.response?.data?.detail || "AI değerlendirme başarısız");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">İş İlanları / Job Listings</h1>

      {/* New search config */}
      <div className="card">
        <h2 className="font-semibold mb-4">Yeni Arama / New Search</h2>
        <div className="flex gap-2 mb-3">
          <input
            className="input flex-1"
            placeholder="Keyword ekle (ör: Frontend Developer)"
            value={kwInput}
            onChange={(e) => setKwInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addKeyword()}
          />
          <button onClick={addKeyword} className="btn-secondary px-3">
            <Plus size={16} />
          </button>
        </div>
        <div className="flex flex-wrap gap-2 mb-4">
          {keywords.map((kw) => (
            <span key={kw} className="flex items-center gap-1 bg-primary-600 text-white text-sm px-3 py-1 rounded-full">
              {kw}
              <button onClick={() => setKeywords(keywords.filter((k) => k !== kw))}>
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
        <div className="flex items-center gap-4 mb-4">
          <label className="text-sm text-gray-400">Arama Aralığı:</label>
          <select className="input w-auto" value={interval} onChange={(e) => setInterval(e.target.value)}>
            <option value="4h">Her 4 Saatte (ücretsiz)</option>
            <option value="2h">Her 2 Saatte (100 token)</option>
          </select>
        </div>
        {msg && <p className={`text-sm mb-3 ${msg.includes("Hata") || msg.includes("başarısız") ? "text-red-400" : "text-green-400"}`}>{msg}</p>}
        <button onClick={createConfig} className="btn-primary" disabled={loading || keywords.length === 0}>
          {loading ? "Başlatılıyor..." : "Aramayı Başlat"}
        </button>
      </div>

      {/* Active configs */}
      {configs.filter((c) => c.is_active).length > 0 && (
        <div className="card">
          <h2 className="font-semibold mb-3">Aktif Aramalar</h2>
          <div className="space-y-2">
            {configs.filter((c) => c.is_active).map((c: any) => (
              <div key={c.id} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{c.keywords.join(", ")}</p>
                  <p className="text-xs text-gray-400">{c.interval === "4h" ? "Her 4 saatte" : "Her 2 saatte"}</p>
                </div>
                <button onClick={() => deleteConfig(c.id)} className="text-red-400 hover:text-red-300 p-1">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Job listings */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">
            Bulunan İlanlar{" "}
            <span className="text-gray-400 font-normal text-sm">({listings.total} toplam)</span>
          </h2>
          <button onClick={() => loadListings(1)} className="btn-secondary text-sm py-1 px-3">
            Yenile
          </button>
        </div>
        {listings.items.length === 0 ? (
          <div className="card text-center text-gray-400 py-12">
            <p>Henüz iş ilanı bulunamadı.</p>
            <p className="text-sm mt-1">Bir arama başlatın ve bekleyin.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {listings.items.map((job: any) => (
              <div
                key={job.id}
                className={`card transition-colors ${job.is_new ? "border-primary-600" : ""}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {job.is_new && (
                        <span className="text-xs bg-primary-600 text-white px-2 py-0.5 rounded-full">Yeni</span>
                      )}
                      {job.ai_match_score !== null && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          job.ai_match_score >= 70 ? "bg-green-900 text-green-300" :
                          job.ai_match_score >= 40 ? "bg-yellow-900 text-yellow-300" :
                          "bg-red-900 text-red-300"
                        }`}>
                          {job.ai_match_score.toFixed(0)}% uyum
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-100">{job.title}</h3>
                    <p className="text-sm text-gray-400 mt-0.5">
                      {job.company} {job.location ? `• ${job.location}` : ""}
                    </p>
                    {job.description && (
                      <p className="text-sm text-gray-500 mt-2 line-clamp-2">{job.description}</p>
                    )}
                    {job.ai_analysis && (
                      <p className="text-sm text-gray-400 mt-2 bg-gray-800 p-2 rounded-lg">{job.ai_analysis}</p>
                    )}
                  </div>
                  <div className="flex flex-col gap-2 shrink-0">
                    {job.url && (
                      <a href={job.url} target="_blank" rel="noopener noreferrer" className="btn-secondary text-xs py-1 px-2 flex items-center gap-1">
                        <ExternalLink size={12} />
                        Görüntüle
                      </a>
                    )}
                    {job.is_new && (
                      <button onClick={() => markRead(job.id)} className="btn-secondary text-xs py-1 px-2">
                        Okundu
                      </button>
                    )}
                    {job.ai_match_score === null && (
                      <button onClick={() => evaluateJob(job.id)} className="text-xs py-1 px-2 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-800 flex items-center gap-1">
                        <Star size={12} />
                        AI (50T)
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {/* Pagination */}
        {listings.total > 20 && (
          <div className="flex gap-2 mt-4">
            <button disabled={page === 1} onClick={() => loadListings(page - 1)} className="btn-secondary text-sm py-1 px-3 disabled:opacity-50">Önceki</button>
            <span className="text-gray-400 text-sm py-1 px-2">{page}</span>
            <button disabled={page * 20 >= listings.total} onClick={() => loadListings(page + 1)} className="btn-secondary text-sm py-1 px-3 disabled:opacity-50">Sonraki</button>
          </div>
        )}
      </div>
    </div>
  );
}
