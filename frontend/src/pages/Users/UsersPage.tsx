import { useEffect, useState } from "react";
import DashboardLayout from "../../layouts/DashboardLayout";
import { createUser, deleteUser, listUsers, updateUser } from "../../services/userService";
import type { AuthRole, AuthUser, UserPayload } from "../../types/auth";

const blankUser = (): UserPayload => ({ full_name: "", username: "", email: "", password: "", role: "Executive", is_active: true });

export default function UsersPage() {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [form, setForm] = useState<UserPayload>(blankUser);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => { try { setUsers(await listUsers()); } catch (e) { setError(e instanceof Error ? e.message : "Unable to load users"); } };
  useEffect(() => { void load(); }, []);
  const set = <K extends keyof UserPayload>(key: K, value: UserPayload[K]) => setForm((current) => ({ ...current, [key]: value }));
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setError(null);
    try {
      if (editingId) await updateUser(editingId, { ...form, password: form.password || undefined });
      else await createUser(form);
      setForm(blankUser()); setEditingId(null); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to save user"); }
  }
  function edit(user: AuthUser) { setEditingId(user.id); setForm({ full_name: user.full_name, username: user.username, email: user.email, password: "", role: user.role, is_active: user.is_active }); }
  async function remove(user: AuthUser) { if (!window.confirm(`Delete ${user.username}?`)) return; try { await deleteUser(user.id); await load(); } catch (e) { setError(e instanceof Error ? e.message : "Unable to delete user"); } }
  return <DashboardLayout><div className="grid gap-6 xl:grid-cols-[360px_1fr]"><form onSubmit={submit} className="space-y-3 rounded-2xl bg-white p-5 shadow"><h1 className="text-2xl font-semibold">{editingId ? "Edit user" : "Add user"}</h1>{error && <p className="text-sm text-red-600">{error}</p>}{(["full_name", "username", "email", "password"] as const).map((key) => <input key={key} required={key !== "password" || !editingId} type={key === "password" ? "password" : key === "email" ? "email" : "text"} placeholder={key.replace("_", " ")} value={form[key] ?? ""} onChange={(e) => set(key, e.target.value)} className="w-full rounded-lg border p-2" />)}<select value={form.role} onChange={(e) => set("role", e.target.value as AuthRole)} className="w-full rounded-lg border p-2">{(["Admin", "Manager", "Executive"] as AuthRole[]).map((role) => <option key={role}>{role}</option>)}</select><label className="flex gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={(e) => set("is_active", e.target.checked)} />Active</label><div className="flex gap-2"><button className="rounded-lg bg-emerald-600 px-4 py-2 text-white">Save</button>{editingId && <button type="button" onClick={() => { setEditingId(null); setForm(blankUser()); }} className="rounded-lg border px-4 py-2">Cancel</button>}</div></form><section className="overflow-x-auto rounded-2xl bg-white p-5 shadow"><h2 className="mb-4 text-xl font-semibold">Users</h2><table className="min-w-full text-sm"><thead><tr className="border-b text-left"><th>Name</th><th>Username</th><th>Role</th><th>Status</th><th /></tr></thead><tbody>{users.map((user) => <tr key={user.id} className="border-b"><td className="py-3">{user.full_name}<div className="text-slate-500">{user.email}</div></td><td>{user.username}</td><td>{user.role}</td><td>{user.is_active ? "Active" : "Inactive"}</td><td className="space-x-2"><button onClick={() => edit(user)} className="text-emerald-700">Edit</button><button onClick={() => void remove(user)} className="text-red-600">Delete</button></td></tr>)}</tbody></table></section></div></DashboardLayout>;
}
