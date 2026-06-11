// ─────────────────────────────────────────────
//  SentinelEdge — Authentication Service
// ─────────────────────────────────────────────
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { API_BASE } from '../config/config';

const STORAGE_KEY_TOKEN = '@sentineledge_token';
const STORAGE_KEY_USERNAME = '@sentineledge_username';

/**
 * login — POST /api/admin/login
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{token: string, username: string}>}
 */
export const login = async (username, password) => {
  const response = await axios.post(
    `${API_BASE}/admin/login`,
    { username, pin: password },   // backend expects 'pin', not 'password'
    {
      timeout: 8000,
      headers: { 'Content-Type': 'application/json' },
    }
  );
  return response.data;
};

/**
 * saveSession — persist token + username to AsyncStorage
 * @param {string} token
 * @param {string} username
 */
export const saveSession = async (token, username) => {
  await AsyncStorage.multiSet([
    [STORAGE_KEY_TOKEN, token],
    [STORAGE_KEY_USERNAME, username],
  ]);
};

/**
 * getSession — read token + username from AsyncStorage
 * @returns {Promise<{token: string|null, username: string|null}>}
 */
export const getSession = async () => {
  const pairs = await AsyncStorage.multiGet([STORAGE_KEY_TOKEN, STORAGE_KEY_USERNAME]);
  const token = pairs[0][1];
  const username = pairs[1][1];
  return { token, username };
};

/**
 * clearSession — remove token + username from AsyncStorage
 */
export const clearSession = async () => {
  await AsyncStorage.multiRemove([STORAGE_KEY_TOKEN, STORAGE_KEY_USERNAME]);
};

/**
 * verifySession — returns true if a token exists in storage
 * @returns {Promise<boolean>}
 */
export const verifySession = async () => {
  const token = await AsyncStorage.getItem(STORAGE_KEY_TOKEN);
  return token !== null && token.length > 0;
};
