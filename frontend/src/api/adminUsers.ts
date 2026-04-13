import client from "./client";

export type AdminUser = {
  id: number;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
};

export async function listUsers(): Promise<AdminUser[]> {
  const res = await client.get("/admin/users");
  return res.data;
}

export async function createUser(payload: {
  email: string;
  password: string;
  is_admin?: boolean;
}): Promise<AdminUser> {
  const res = await client.post("/admin/users", payload);
  return res.data;
}

export async function deleteUser(userId: number): Promise<void> {
  await client.delete(`/admin/users/${userId}`);
}