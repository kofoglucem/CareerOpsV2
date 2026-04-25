"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Users, Coins, Settings } from "lucide-react";

export default function AdminPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [tokenSettings, setTokenSettings] = useState<any>(null);
  const [selectedUser, setSelectedUser] = useState("");
  const [tokenAmount, setTokenAmount] = useState("");
  const [reason, setReason] = useState("Admin tarafından yüklendi");
  const [msg, setMsg] = useState("");
  const [settingsMsg, setSettingsMsg] = useState("");

  useEffect(() => {
    api.get("/admin/users").then(({ data }) => setUsers(data));
    api.get("/admin/tokens/settings").then(({ data }) => setTokenSettings(data));
  }, []);

  const addTokens = async () => {
    if (!selectedUser || !tokenAmount) return;
    try {
      const { data } = await api.post("/admin/tokens/add", {
        user_id: selectedUser,
        amount: parseInt(tokenAmount),
        reason,
      });
      setMsg(data.message);
      api.get("/admin/users").then(({ data }) => setUsers(data));
    } catch (err: any) {
      setMsg(err.response?.data?.detail || "Hata");
    }
  };

  const updateSettings = async () => {
    try {
      await api.patch("/admin/tokens/settings", tokenSettings);
      setSettingsMsg("Ayarlar güncellendi");
    } catch {
      setSettingsMsg("Hata");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Yönetim Paneli / Admin Panel</h1>

      {/* Token add */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Coins size={20} className="text-yellow-400" />
          <h2 className="font-semibold">Kullanıcıya Token Yükle</h2>
        </div>
        <div className="space-y-3">
          <select className="input" value={selectedUser} onChange={(e) => setSelectedUser(e.target.value)}>
            <option value="">Kullanıcı seçin...</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.username} ({u.email}) — {u.tokens} token
              </option>
            ))}
          </select>
          <input
            className="input"
            type="number"
            placeholder="Token miktarı"
            value={tokenAmount}
            onChange={(e) => setTokenAmount(e.target.value)}
          />
          <input
            className="input"
            placeholder="Sebep"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <button onClick={addTokens} className="btn-primary">Token Yükle</button>
          {msg && <p className={`text-sm ${msg.includes("Hata") ? "text-red-400" : "text-green-400"}`}>{msg}</p>}
        </div>
      </div>

      {/* Token settings */}
      {tokenSettings && (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <Settings size={20} className="text-gray-400" />
            <h2 className="font-semibold">Token Maliyetleri</h2>
          </div>
          <div className="space-y-3">
            <div>
              <label className="text-sm text-gray-400 block mb-1">Residential IP Maliyeti</label>
              <input
                className="input"
                type="number"
                value={tokenSettings.cost_residential_ip}
                onChange={(e) => setTokenSettings({ ...tokenSettings, cost_residential_ip: parseInt(e.target.value) })}
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 block mb-1">2 Saatlik Arama Maliyeti</label>
              <input
                className="input"
                type="number"
                value={tokenSettings.cost_search_2h}
                onChange={(e) => setTokenSettings({ ...tokenSettings, cost_search_2h: parseInt(e.target.value) })}
              />
            </div>
            <div>
              <label className="text-sm text-gray-400 block mb-1">AI Değerlendirme Maliyeti</label>
              <input
                className="input"
                type="number"
                value={tokenSettings.cost_ai_evaluation}
                onChange={(e) => setTokenSettings({ ...tokenSettings, cost_ai_evaluation: parseInt(e.target.value) })}
              />
            </div>
            <button onClick={updateSettings} className="btn-primary">Kaydet</button>
            {settingsMsg && <p className={`text-sm ${settingsMsg.includes("Hata") ? "text-red-400" : "text-green-400"}`}>{settingsMsg}</p>}
          </div>
        </div>
      )}

      {/* Users list */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Users size={20} className="text-blue-400" />
          <h2 className="font-semibold">Kullanıcılar ({users.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-800">
                <th className="text-left pb-2">Kullanıcı</th>
                <th className="text-left pb-2">E-posta</th>
                <th className="text-left pb-2">Token</th>
                <th className="text-left pb-2">Rol</th>
                <th className="text-left pb-2">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {users.map((u) => (
                <tr key={u.id} className="py-2">
                  <td className="py-2 font-medium">{u.username}</td>
                  <td className="py-2 text-gray-400">{u.email}</td>
                  <td className="py-2 text-yellow-400">{u.tokens}</td>
                  <td className="py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${u.role === "admin" ? "bg-purple-900 text-purple-300" : "bg-gray-800 text-gray-300"}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"}`}>
                      {u.is_active ? "Aktif" : "Pasif"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
