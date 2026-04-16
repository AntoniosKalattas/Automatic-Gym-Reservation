import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  StatusBar,
  Platform,
  KeyboardAvoidingView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Picker } from '@react-native-picker/picker';

const STORAGE_KEY = '@gym_ngrok_url';

const DAY_NAMES = {
  '0': 'Monday',
  '1': 'Tuesday',
  '2': 'Wednesday',
  '3': 'Thursday',
  '4': 'Friday',
  '5': 'Saturday',
};

const WEEKDAY_OPTIONS = [
  { value: 1, label: '07:45' },
  { value: 2, label: '09:30' },
  { value: 3, label: '11:15' },
  { value: 4, label: '13:00' },
  { value: 5, label: '14:45' },
  { value: 6, label: '16:45' },
  { value: 7, label: '18:30' },
  { value: 8, label: '20:15' },
];

const SATURDAY_OPTIONS = [
  { value: 1, label: '08:45' },
  { value: 2, label: '10:30' },
  { value: 3, label: '12:15' },
];

const NGROK_HEADERS = {
  'ngrok-skip-browser-warning': 'true',
  'Content-Type': 'application/json',
};

// ─── helpers ────────────────────────────────────────────────────────────────

function normalizeUrl(raw) {
  let url = raw.trim().replace(/\/+$/, '');
  if (url && !url.startsWith('http')) url = 'https://' + url;
  return url;
}

function optionsForDay(dayKey) {
  return dayKey === '5' ? SATURDAY_OPTIONS : WEEKDAY_OPTIONS;
}

function labelForOption(dayKey, value) {
  const opts = optionsForDay(dayKey);
  const found = opts.find(o => o.value === Number(value));
  return found ? found.label : '—';
}

// ─── sub-components ─────────────────────────────────────────────────────────

function ConnectionBar({ url, onSave }) {
  const [input, setInput] = useState(url);
  const [editing, setEditing] = useState(!url);

  useEffect(() => { setInput(url); setEditing(!url); }, [url]);

  const handleSave = () => {
    const normalized = normalizeUrl(input);
    if (!normalized) { Alert.alert('Error', 'Enter a valid ngrok URL'); return; }
    onSave(normalized);
    setEditing(false);
  };

  return (
    <View style={styles.connectionBar}>
      <Text style={styles.connectionLabel}>ngrok URL</Text>
      {editing ? (
        <View style={styles.connectionInputRow}>
          <TextInput
            style={styles.urlInput}
            value={input}
            onChangeText={setInput}
            placeholder="https://xxxx.ngrok-free.app"
            placeholderTextColor="#555"
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            returnKeyType="done"
            onSubmitEditing={handleSave}
          />
          <TouchableOpacity style={styles.saveBtn} onPress={handleSave}>
            <Text style={styles.saveBtnText}>Save</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity onPress={() => setEditing(true)} style={styles.urlDisplay}>
          <Text style={styles.urlText} numberOfLines={1}>{url}</Text>
          <Text style={styles.editHint}>tap to edit</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

function DayRow({ dayKey, value, onValueChange }) {
  const options = optionsForDay(dayKey);
  const isSat = dayKey === '5';

  return (
    <View style={styles.dayRow}>
      <View style={styles.dayLabelCol}>
        <Text style={styles.dayName}>{DAY_NAMES[dayKey]}</Text>
        {isSat && <Text style={styles.satBadge}>Sat</Text>}
      </View>
      <View style={styles.pickerWrapper}>
        <Picker
          selectedValue={Number(value)}
          onValueChange={v => onValueChange(dayKey, v)}
          style={styles.picker}
          itemStyle={styles.pickerItem}
          dropdownIconColor="#4CAF50"
        >
          {options.map(opt => (
            <Picker.Item key={opt.value} label={opt.label} value={opt.value} color="#fff" />
          ))}
        </Picker>
      </View>
    </View>
  );
}

function StatusCard({ statusData }) {
  const entries = Object.entries(statusData).sort(([a], [b]) => b.localeCompare(a));

  if (!entries.length) {
    return (
      <View style={styles.statusEmpty}>
        <Text style={styles.statusEmptyText}>No reservation history yet.</Text>
      </View>
    );
  }

  return (
    <View>
      {entries.map(([date, status]) => (
        <View key={date} style={styles.statusRow}>
          <Text style={styles.statusDate}>{date}</Text>
          <View style={[styles.statusBadge, status === 'SUCCESS' ? styles.badgeSuccess : styles.badgeFail]}>
            <Text style={styles.statusBadgeText}>{status}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

// ─── main app ───────────────────────────────────────────────────────────────

export default function App() {
  const [ngrokUrl, setNgrokUrl] = useState('');
  const [schedule, setSchedule] = useState({});
  const [statusData, setStatusData] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [connected, setConnected] = useState(null); // null=unknown, true, false
  const [activeTab, setActiveTab] = useState('schedule'); // 'schedule' | 'status'

  // Load saved URL on mount
  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then(val => {
      if (val) setNgrokUrl(val);
    });
  }, []);

  // Fetch data whenever URL changes
  useEffect(() => {
    if (ngrokUrl) {
      fetchAll();
    }
  }, [ngrokUrl]);

  const fetchAll = useCallback(async () => {
    if (!ngrokUrl) return;
    setLoading(true);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const [schedRes, statRes] = await Promise.all([
        fetch(`${ngrokUrl}/schedule`, { headers: NGROK_HEADERS, signal: controller.signal }),
        fetch(`${ngrokUrl}/status`, { headers: NGROK_HEADERS, signal: controller.signal }),
      ]);
      if (!schedRes.ok || !statRes.ok) throw new Error('Bad response');
      const schedJson = await schedRes.json();
      const statJson = await statRes.json();
      setSchedule(schedJson.schedule || {});
      setStatusData(statJson.status || {});
      setConnected(true);
    } catch (e) {
      setConnected(false);
      const msg = e.name === 'AbortError'
        ? 'Request timed out after 10 seconds.'
        : `Could not reach ${ngrokUrl}`;
      Alert.alert('Connection failed', `${msg}\n\nMake sure api.py is running and ngrok is active.`);
    } finally {
      clearTimeout(timer);
      setLoading(false);
    }
  }, [ngrokUrl]);

  const handleSaveUrl = async (url) => {
    await AsyncStorage.setItem(STORAGE_KEY, url);
    setNgrokUrl(url);
  };

  const handleDayChange = (dayKey, value) => {
    setSchedule(prev => ({ ...prev, [dayKey]: value }));
  };

  const handleSaveSchedule = async () => {
    if (!ngrokUrl) { Alert.alert('No URL', 'Set your ngrok URL first.'); return; }
    setSaving(true);
    try {
      const res = await fetch(`${ngrokUrl}/schedule`, {
        method: 'POST',
        headers: NGROK_HEADERS,
        body: JSON.stringify({ schedule }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || 'Unknown error');
      Alert.alert('Saved', 'Schedule updated successfully!');
    } catch (e) {
      Alert.alert('Save failed', e.message);
    } finally {
      setSaving(false);
    }
  };

  const connectionDot = connected === null ? '#888' : connected ? '#4CAF50' : '#f44336';

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <StatusBar barStyle="light-content" backgroundColor="#0f0f0f" />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={[styles.dot, { backgroundColor: connectionDot }]} />
          <Text style={styles.headerTitle}>Gym Reservation</Text>
        </View>
        {ngrokUrl ? (
          <TouchableOpacity onPress={fetchAll} disabled={loading}>
            {loading
              ? <ActivityIndicator color="#4CAF50" size="small" />
              : <Text style={styles.refreshBtn}>↻ Refresh</Text>
            }
          </TouchableOpacity>
        ) : null}
      </View>

      {/* Connection bar */}
      <ConnectionBar url={ngrokUrl} onSave={handleSaveUrl} />

      {/* Tabs */}
      <View style={styles.tabs}>
        {['schedule', 'status'].map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab === 'schedule' ? 'Schedule' : 'History'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Body */}
      <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
        {activeTab === 'schedule' && (
          <>
            <Text style={styles.sectionTitle}>Weekly Time Slots</Text>
            <Text style={styles.sectionSub}>
              Times are booked 5 days in advance. Tap a time to change it.
            </Text>

            {Object.keys(DAY_NAMES).length > 0 && Object.keys(schedule).length > 0
              ? Object.keys(DAY_NAMES).map(dayKey => (
                  <DayRow
                    key={dayKey}
                    dayKey={dayKey}
                    value={schedule[dayKey] ?? 1}
                    onValueChange={handleDayChange}
                  />
                ))
              : (
                <View style={styles.emptyState}>
                  {loading
                    ? <ActivityIndicator color="#4CAF50" size="large" />
                    : <Text style={styles.emptyStateText}>
                        {ngrokUrl ? 'Failed to load schedule.' : 'Enter your ngrok URL above to get started.'}
                      </Text>
                  }
                </View>
              )
            }

            {Object.keys(schedule).length > 0 && (
              <TouchableOpacity
                style={[styles.saveScheduleBtn, saving && styles.saveScheduleBtnDisabled]}
                onPress={handleSaveSchedule}
                disabled={saving}
              >
                {saving
                  ? <ActivityIndicator color="#fff" />
                  : <Text style={styles.saveScheduleBtnText}>Save Schedule</Text>
                }
              </TouchableOpacity>
            )}
          </>
        )}

        {activeTab === 'status' && (
          <>
            <Text style={styles.sectionTitle}>Reservation History</Text>
            <Text style={styles.sectionSub}>Last 14 days of reservation attempts.</Text>
            {loading
              ? <ActivityIndicator color="#4CAF50" size="large" style={{ marginTop: 32 }} />
              : <StatusCard statusData={statusData} />
            }
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ─── styles ─────────────────────────────────────────────────────────────────

const C = {
  bg: '#0f0f0f',
  surface: '#1a1a1a',
  border: '#2a2a2a',
  green: '#4CAF50',
  red: '#f44336',
  textPrimary: '#ffffff',
  textSecondary: '#888',
  textMuted: '#555',
};

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: C.bg,
  },

  // header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Platform.OS === 'ios' ? 56 : 40,
    paddingHorizontal: 20,
    paddingBottom: 12,
    backgroundColor: C.bg,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  headerTitle: {
    color: C.textPrimary,
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  refreshBtn: {
    color: C.green,
    fontSize: 14,
    fontWeight: '600',
  },

  // connection bar
  connectionBar: {
    padding: 16,
    backgroundColor: C.surface,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  connectionLabel: {
    color: C.textSecondary,
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  connectionInputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  urlInput: {
    flex: 1,
    backgroundColor: '#111',
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 9,
    color: C.textPrimary,
    fontSize: 14,
  },
  saveBtn: {
    backgroundColor: C.green,
    borderRadius: 8,
    paddingHorizontal: 16,
    justifyContent: 'center',
  },
  saveBtnText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  urlDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  urlText: {
    color: C.green,
    fontSize: 14,
    flex: 1,
  },
  editHint: {
    color: C.textMuted,
    fontSize: 11,
    marginLeft: 8,
  },

  // tabs
  tabs: {
    flexDirection: 'row',
    backgroundColor: C.surface,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: C.green,
  },
  tabText: {
    color: C.textSecondary,
    fontSize: 14,
    fontWeight: '600',
  },
  tabTextActive: {
    color: C.textPrimary,
  },

  // body
  body: {
    padding: 16,
    paddingBottom: 48,
  },
  sectionTitle: {
    color: C.textPrimary,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  sectionSub: {
    color: C.textSecondary,
    fontSize: 13,
    marginBottom: 16,
  },

  // day rows
  dayRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.surface,
    borderRadius: 12,
    marginBottom: 8,
    paddingLeft: 16,
    borderWidth: 1,
    borderColor: C.border,
    overflow: 'hidden',
  },
  dayLabelCol: {
    width: 100,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dayName: {
    color: C.textPrimary,
    fontSize: 15,
    fontWeight: '600',
  },
  satBadge: {
    fontSize: 10,
    color: '#aaa',
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 4,
  },
  pickerWrapper: {
    flex: 1,
  },
  picker: {
    color: C.textPrimary,
    backgroundColor: 'transparent',
  },
  pickerItem: {
    color: C.textPrimary,
    fontSize: 15,
  },

  // save button
  saveScheduleBtn: {
    backgroundColor: C.green,
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    marginTop: 16,
  },
  saveScheduleBtnDisabled: {
    opacity: 0.6,
  },
  saveScheduleBtnText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 16,
    letterSpacing: 0.3,
  },

  // status
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: C.surface,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: C.border,
  },
  statusDate: {
    color: C.textPrimary,
    fontSize: 15,
    fontWeight: '500',
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeSuccess: {
    backgroundColor: 'rgba(76,175,80,0.2)',
    borderWidth: 1,
    borderColor: C.green,
  },
  badgeFail: {
    backgroundColor: 'rgba(244,67,54,0.2)',
    borderWidth: 1,
    borderColor: C.red,
  },
  statusBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: C.textPrimary,
  },
  statusEmpty: {
    paddingVertical: 48,
    alignItems: 'center',
  },
  statusEmptyText: {
    color: C.textSecondary,
    fontSize: 14,
  },

  // empty state
  emptyState: {
    paddingVertical: 48,
    alignItems: 'center',
  },
  emptyStateText: {
    color: C.textSecondary,
    fontSize: 14,
    textAlign: 'center',
  },
});
