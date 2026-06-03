/**
 * AppNavigator.tsx — Bottom tab navigator for SentinelEdge mobile app.
 */

import React from 'react';
import { View, Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import HomeScreen from '../screens/HomeScreen';
import AlertScreen from '../screens/AlertScreen';
import AcknowledgeScreen from '../screens/AcknowledgeScreen';
import SettingsScreen from '../screens/SettingsScreen';
import { useWebSocket } from '../hooks/useWebSocket';

const Tab = createBottomTabNavigator();

const COLORS = {
  bg: '#0f1117',
  card: '#1a1d27',
  primary: '#7c3aed',
  danger: '#ef4444',
  textSecondary: '#9ca3af',
};

// Badge component for unread count
function TabBadge({ count }: { count: number }) {
  if (count === 0) return null;
  return (
    <View style={{
      position: 'absolute',
      right: -8,
      top: -4,
      backgroundColor: COLORS.danger,
      borderRadius: 9,
      minWidth: 18,
      height: 18,
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: 4,
    }}>
      <Text style={{ color: '#fff', fontSize: 10, fontWeight: '700' }}>
        {count > 99 ? '99+' : count}
      </Text>
    </View>
  );
}

function NavigatorContent() {
  const { breaches } = useWebSocket();
  const hasActiveBreach = breaches.length > 0;

  return (
    <Tab.Navigator
      screenOptions={{
        tabBarStyle: {
          backgroundColor: COLORS.card,
          borderTopColor: 'rgba(255,255,255,0.05)',
          borderTopWidth: 1,
          paddingBottom: 4,
          height: 60,
        },
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.textSecondary,
        headerStyle: { backgroundColor: COLORS.bg, borderBottomColor: 'rgba(255,255,255,0.05)' },
        headerTintColor: '#f9fafb',
        headerTitleStyle: { fontWeight: '700', fontSize: 16 },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: 'SentinelEdge',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Alerts"
        component={AlertScreen}
        options={{
          title: 'Alert Log',
          tabBarIcon: ({ color, size }) => (
            <View>
              <Ionicons name="notifications" size={size} color={color} />
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="Acknowledge"
        component={AcknowledgeScreen}
        options={{
          title: 'Acknowledge',
          tabBarIcon: ({ color, size }) => (
            <Ionicons
              name="checkmark-circle"
              size={size}
              color={hasActiveBreach ? COLORS.danger : color}
            />
          ),
          tabBarLabel: ({ color }) => (
            <Text style={{
              color: hasActiveBreach ? COLORS.danger : color,
              fontSize: 10,
              fontWeight: hasActiveBreach ? '700' : '400',
            }}>
              Acknowledge
            </Text>
          ),
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: 'Settings',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="settings" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <NavigatorContent />
    </NavigationContainer>
  );
}
