// User appearance store — set by layout, read by chat components
import { writable } from 'svelte/store';

export interface UserAppearance {
  initial: string;
  avatarColor: string;
  displayName: string;
}

export const userAppearance = writable<UserAppearance>({
  initial: 'U',
  avatarColor: '#3b82f6',
  displayName: '',
});
