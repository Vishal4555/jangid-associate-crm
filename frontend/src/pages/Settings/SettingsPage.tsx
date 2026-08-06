import { useEffect, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { Alert, Card, PageHeader } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { updateCurrentUser } from "../../services/authService";

export default function SettingsPage() {
  const { currentUser } = useAuth(); const [fullName, setFullName] = useState(""); const [email, setEmail] = useState(""); const [message, setMessage] = useState<string | null>(null);
  useEffect(() => { setFullName(currentUser?.full_name ?? ""); setEmail(currentUser?.email ?? ""); }, [currentUser]);
  async function submit(event: React.FormEvent) { event.preventDefault(); setMessage(null); try { await updateCurrentUser({ full_name: fullName, email }); setMessage("Profile updated. Refreshing the session will show the new details."); } catch (e) { setMessage(e instanceof Error ? e.message : "Unable to update profile"); } }
  return <DashboardLayout><PageHeader eyebrow="Account" title="Settings" subtitle="Update your profile details." />
    <Card><form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
      {message && <Alert tone="info" className="md:col-span-2">{message}</Alert>}
      <label className="text-sm font-medium">Full name<input required value={fullName} onChange={(e) => setFullName(e.target.value)} className="mt-1 block w-full border px-3 py-2" /></label>
      <label className="text-sm font-medium">Email<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1 block w-full border px-3 py-2" /></label>
      <div className="md:col-span-2"><button className="rounded-xl bg-orange-600 px-4 py-2 text-white hover:bg-orange-700">Save settings</button></div>
    </form></Card>
  </DashboardLayout>;
}
