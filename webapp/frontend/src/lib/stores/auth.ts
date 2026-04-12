import { writable } from 'svelte/store';

export interface User {
  id: number;
  username: string;
  display_name: string;
  is_admin: boolean;
  exam_access: boolean;
}

export const user = writable<User | null>(null);
export const token = writable<string | null>(null);
