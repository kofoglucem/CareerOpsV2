"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Briefcase, Settings, Shield, LogOut, Home, Coins } from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) { router.push("/login"); return; }
    api.get("/users/me").then(({ data }) => setUser(data)).catch(() => router.push("/login"));
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const nav = [
    { href: "/dashboard", label: "Panel", icon: Home },
    { href: "/dashboard/jobs", label: "İş İlanları", icon: Briefcase },
    { href: "/dashboard/settings", label: "Ayarlar", icon: Settings },
    ...(user?.role === "admin" ? [{ href: "/dashboard/admin", label: "Yönetim", icon: Shield }] : []),
  ];

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold text-primary-500">CareerOpsV2</h1>
          {user && (
            <div className="mt-2">
              <p className="text-sm text-gray-300">{user.username}</p>
              <div className="flex items-center gap-1 mt-1">
                <Coins size={14} className="text-yellow-400" />
                <span className="text-sm text-yellow-400 font-medium">{user.tokens} token</span>
              </div>
            </div>
          )}
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                pathname === href
                  ? "bg-primary-600 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-gray-100"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-gray-100 w-full transition-colors"
          >
            <LogOut size={16} />
            Çıkış / Logout
          </button>
        </div>
      </aside>
      {/* Main */}
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  );
}
