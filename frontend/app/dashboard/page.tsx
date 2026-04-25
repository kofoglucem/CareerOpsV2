"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Wifi, Linkedin, Bot, Search } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [proxyStatus, setProxyStatus] = useState<any>(null);
  const [configs, setConfigs] = useState<any[]>([]);

  useEffect(() => {
    api.get("/users/me").then(({ data }) => setUser(data));
    api.get("/proxy/status").then(({ data }) => setProxyStatus(data));
    api.get("/jobs/search-configs").then(({ data }) => setConfigs(data));
  }, []);

  const cards = [
    {
      title: "Residential IP",
      icon: Wifi,
      status: proxyStatus?.has_proxy,
      statusLabel: proxyStatus?.has_proxy ? "Aktif" : "Pasif",
      color: proxyStatus?.has_proxy ? "text-green-400" : "text-red-400",
      href: "/dashboard/settings",
    },
    {
      title: "LinkedIn",
      icon: Linkedin,
      status: proxyStatus?.linkedin_logged_in,
      statusLabel: proxyStatus?.linkedin_logged_in
        ? proxyStatus.linkedin_email
        : "Bağlı Değil",
      color: proxyStatus?.linkedin_logged_in ? "text-green-400" : "text-red-400",
      href: "/dashboard/settings",
    },
    {
      title: "Aktif Aramalar",
      icon: Search,
      status: configs.filter((c) => c.is_active).length > 0,
      statusLabel: `${configs.filter((c) => c.is_active).length} aktif`,
      color: "text-blue-400",
      href: "/dashboard/jobs",
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Hoş geldin, {user?.username} 👋</h1>
          <p className="text-gray-400 mt-1">İş arama durumun aşağıda</p>
        </div>
        <div className="card !p-4 flex items-center gap-2">
          <span className="text-yellow-400 font-bold text-xl">{user?.tokens}</span>
          <span className="text-gray-400 text-sm">token</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {cards.map(({ title, icon: Icon, statusLabel, color, href }) => (
          <Link key={title} href={href} className="card hover:border-gray-700 transition-colors cursor-pointer">
            <div className="flex items-center gap-3 mb-3">
              <Icon size={20} className="text-gray-400" />
              <span className="font-medium">{title}</span>
            </div>
            <p className={`text-sm font-medium ${color}`}>{statusLabel}</p>
          </Link>
        ))}
      </div>

      {configs.length > 0 && (
        <div className="card">
          <h2 className="font-semibold mb-4">Aktif Aramalar</h2>
          <div className="space-y-3">
            {configs.filter((c) => c.is_active).map((c: any) => (
              <div key={c.id} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{c.keywords.join(", ")}</p>
                  <p className="text-xs text-gray-400">{c.interval === "4h" ? "Her 4 saatte" : "Her 2 saatte"}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-400">
                    Sonraki: {c.next_run_at ? new Date(c.next_run_at).toLocaleTimeString("tr-TR") : "-"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
