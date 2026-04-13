import client from "./client";

export type CurrentUser = {
  id: number;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
};

export async function getCurrentUser(): Promise<CurrentUser> {
  const res = await client.get("/auth/me");
  return res.data;
}