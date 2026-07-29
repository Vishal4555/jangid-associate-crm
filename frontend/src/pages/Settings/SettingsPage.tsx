import { useEffect, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { useAuth } from "../../context/AuthContext";
import { updateCurrentUser } from "../../services/authService";

export default function SettingsPage() {
  const { currentUser } = useAuth(); const [fullName, setFullName] = useState(""); const [email, setEmail] = useState(""); const [message, setMessage] = useState<string | null>(null);
  useEffect(() => { setFullName(currentUser?.full_name ?? ""); setEmail(currentUser?.email ?? ""); }, [currentUser]);
  async function submit(event: React.FormEvent) { event.preventDefault(); setMessage(null); try { await updateCurrentUser({ full_name: fullName, email }); setMessage("Profile updated. Refreshing the session will show the new details."); } catch (e) { setMessage(e instanceof Error ? e.message : "Unable to update profile"); } }
  return <DashboardLayout><form onSubmit={submit} className="max-w-xl space-y-4 rounded-2xl bg-white p-6 shadow"><h1 className="text-2xl font-semibold">Settings</h1><p className="text-sm text-slate-500">Update your profile details.</p>{message && <p className="text-sm text-emerald-700">{message}</p>}<label className="block">Full name<input required value={fullName} onChange={(e) => setFullName(e.target.value)} className="mt-1 w-full rounded-lg border p-2" /></label><label className="block">Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 w-full rounded-lg border p-2" /></label><button className="rounded-lg bg-emerald-600 px-4 py-2 text-white">Save settings</button></form></DashboardLayout>;
}
