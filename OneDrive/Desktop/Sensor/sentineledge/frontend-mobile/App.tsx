/**
 * App.tsx — Root React Native component.
 * Initialises notifications and renders the navigator.
 */

import React, { useEffect } from 'react';
import { StatusBar } from 'react-native';
import AppNavigator from './src/navigation/AppNavigator';
import { requestNotificationPermissions } from './src/services/notifications';

export default function App() {
  useEffect(() => {
    // Request notification permissions on first launch
    requestNotificationPermissions().catch(() => {});
  }, []);

  return (
    <>
      <StatusBar barStyle="light-content" backgroundColor="#0f1117" />
      <AppNavigator />
    </>
  );
}
