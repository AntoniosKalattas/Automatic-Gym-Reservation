import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
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
    if (!normalized) return;
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
  const [error, setError] = useState('');
  const [saveMsg, setSaveMsg] = useState(''); // success or error message for save
  const [sniperDay, setSniperDay] = useState('8');
  const [sniperTime, setSniperTime] = useState('5');
  const [sniperRunning, setSniperRunning] = useState(false);
  const [sniperLogs, setSniperLogs] = useState([]);
  const [sniperLoading, setSniperLoading] = useState(false);
  const [diagData, setDiagData] = useState(null);
  const [diagLoading, setDiagLoading] = useState(false);

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

  const fetchSniperStatus = useCallback(async () => {
    if (!ngrokUrl) return;
    try {
      const res = await fetch(`${ngrokUrl}/snipe`, { headers: NGROK_HEADERS });
      if (res.ok) {
        const json = await res.json();
        setSniperRunning(json.running);
        setSniperLogs(json.logs || []);
      }
    } catch (e) {
      console.log('Error fetching sniper status:', e);
    }
  }, [ngrokUrl]);

  useEffect(() => {
    let interval;
    if (ngrokUrl && (activeTab === 'sniper' || sniperRunning)) {
      fetchSniperStatus();
      interval = setInterval(fetchSniperStatus, 2000);
    }
    return () => clearInterval(interval);
  }, [ngrokUrl, activeTab, sniperRunning, fetchSniperStatus]);

  const handleStartSniper = async () => {
    if (!ngrokUrl) { setSaveMsg('error:Set your API URL first.'); return; }
    setSniperLoading(true);
    setError('');
    try {
      const res = await fetch(`${ngrokUrl}/snipe`, {
        method: 'POST',
        headers: NGROK_HEADERS,
        body: JSON.stringify({ day: parseInt(sniperDay), time: parseInt(sniperTime) }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to start sniper');
      setSniperRunning(true);
      setSniperLogs(['Starting sniper...']);
    } catch (e) {
      setError(`Sniper: ${e.message}`);
    } finally {
      setSniperLoading(false);
    }
  };

  const handleStopSniper = async () => {
    if (!ngrokUrl) return;
    setSniperLoading(true);
    setError('');
    try {
      const res = await fetch(`${ngrokUrl}/snipe/stop`, {
        method: 'POST',
        headers: NGROK_HEADERS,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to stop sniper');
      setSniperRunning(false);
    } catch (e) {
      setError(`Sniper: ${e.message}`);
    } finally {
      setSniperLoading(false);
    }
  };

  const fetchDiagnostics = useCallback(async () => {
    if (!ngrokUrl) return;
    setDiagLoading(true);
    try {
      const res = await fetch(`${ngrokUrl}/diagnose`, { headers: NGROK_HEADERS });
      if (res.ok) {
        const json = await res.json();
        setDiagData(json);
      } else {
        throw new Error('Failed to fetch diagnostics');
      }
    } catch (e) {
      console.log('Error fetching diagnostics:', e);
    } finally {
      setDiagLoading(false);
    }
  }, [ngrokUrl]);

  useEffect(() => {
    if (activeTab === 'diagnostics') {
      fetchDiagnostics();
    }
  }, [activeTab, fetchDiagnostics]);

  const fetchAll = useCallback(async () => {
    if (!ngrokUrl) return;
    setLoading(true);
    setError('');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const [schedRes, statRes] = await Promise.all([
        fetch(`${ngrokUrl}/schedule`, { headers: NGROK_HEADERS, signal: controller.signal }),
        fetch(`${ngrokUrl}/status`, { headers: NGROK_HEADERS, signal: controller.signal }),
      ]);
      if (!schedRes.ok || !statRes.ok) throw new Error('Bad response from server');
      const schedJson = await schedRes.json();
      const statJson = await statRes.json();
      setSchedule(schedJson.schedule || {});
      setStatusData(statJson.status || {});
      setConnected(true);
    } catch (e) {
      setConnected(false);
      setError(e.name === 'AbortError' ? 'Connection timed out. Is api.py running?' : 'Could not reach the API. Check your URL.');
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
    if (!ngrokUrl) { setSaveMsg('error:Set your API URL first.'); return; }
    setSaving(true);
    setSaveMsg('');
    try {
      const res = await fetch(`${ngrokUrl}/schedule`, {
        method: 'POST',
        headers: NGROK_HEADERS,
        body: JSON.stringify({ schedule }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || 'Unknown error');
      setSaveMsg('ok:Schedule saved!');
    } catch (e) {
      setSaveMsg(`error:${e.message}`);
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

      {/* Error banner */}
      {error ? (
        <View style={styles.errorBanner}>
          <Text style={styles.errorBannerText}>{error}</Text>
          <TouchableOpacity onPress={() => setError('')}>
            <Text style={styles.errorBannerDismiss}>✕</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {/* Tabs */}
      <View style={styles.tabs}>
        {['schedule', 'status', 'sniper', 'diagnostics'].map(tab => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab === 'schedule' ? 'Schedule' : tab === 'status' ? 'History' : tab === 'sniper' ? 'Sniper' : 'System'}
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
              <>
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
                {saveMsg ? (
                  <Text style={saveMsg.startsWith('ok:') ? styles.saveMsgOk : styles.saveMsgErr}>
                    {saveMsg.slice(3)}
                  </Text>
                ) : null}
              </>
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

        {activeTab === 'sniper' && (
          <>
            <Text style={styles.sectionTitle}>Gym Sniper</Text>
            <Text style={styles.sectionSub}>
              Continuously fires requests to claim a booking on a specific day and time.
            </Text>

            <View style={styles.sniperForm}>
              <View style={styles.formRow}>
                <Text style={styles.formLabel}>Target Day (of month)</Text>
                <TextInput
                  style={styles.urlInput}
                  value={sniperDay}
                  onChangeText={setSniperDay}
                  placeholder="e.g. 15"
                  keyboardType="number-pad"
                />
              </View>

              <View style={styles.formRow}>
                <Text style={styles.formLabel}>Target Time Slot</Text>
                <View style={styles.pickerWrapper}>
                  <Picker
                    selectedValue={Number(sniperTime)}
                    onValueChange={v => setSniperTime(String(v))}
                    style={styles.picker}
                    itemStyle={styles.pickerItem}
                    dropdownIconColor="#4CAF50"
                  >
                    {[...WEEKDAY_OPTIONS, ...SATURDAY_OPTIONS].map(opt => (
                      <Picker.Item key={opt.value} label={opt.label} value={opt.value} color="#fff" />
                    ))}
                  </Picker>
                </View>
              </View>

              {sniperRunning ? (
                <TouchableOpacity
                  style={[styles.stopBtn, sniperLoading && styles.saveScheduleBtnDisabled]}
                  onPress={handleStopSniper}
                  disabled={sniperLoading}
                >
                  {sniperLoading ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveScheduleBtnText}>Stop Sniper ⏹</Text>}
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={[styles.saveScheduleBtn, sniperLoading && styles.saveScheduleBtnDisabled]}
                  onPress={handleStartSniper}
                  disabled={sniperLoading}
                >
                  {sniperLoading ? <ActivityIndicator color="#fff" /> : <Text style={styles.saveScheduleBtnText}>Start Sniper 🎯</Text>}
                </TouchableOpacity>
              )}
            </View>

            <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Sniper Live Logs</Text>
            <View style={styles.consoleContainer}>
              {sniperLogs.length > 0 ? (
                sniperLogs.map((logLine, idx) => (
                  <Text key={idx} style={styles.consoleText}>{logLine}</Text>
                ))
              ) : (
                <Text style={styles.consolePlaceholder}>Logs will appear here once started.</Text>
              )}
            </View>
          </>
        )}

        {activeTab === 'diagnostics' && (
          <>
            <Text style={styles.sectionTitle}>System Diagnostics</Text>
            <Text style={styles.sectionSub}>Verify connection and server health metrics.</Text>

            {diagLoading ? (
              <ActivityIndicator color="#4CAF50" size="large" style={{ marginTop: 32 }} />
            ) : diagData ? (
              <View style={styles.diagCard}>
                <View style={styles.diagRowItem}>
                  <Text style={styles.diagLabelItem}>Flask API Status</Text>
                  <View style={[styles.diagBadge, styles.badgeSuccess]}>
                    <Text style={styles.diagBadgeText}>ONLINE</Text>
                  </View>
                </View>

                <View style={styles.diagRowItem}>
                  <Text style={styles.diagLabelItem}>Metro Bundler</Text>
                  <View style={[styles.diagBadge, diagData.metro === 'OK' ? styles.badgeSuccess : styles.badgeFail]}>
                    <Text style={styles.diagBadgeText}>{diagData.metro === 'OK' ? 'RUNNING' : 'OFFLINE'}</Text>
                  </View>
                </View>

                <View style={styles.diagRowItem}>
                  <Text style={styles.diagLabelItem}>Chrome Profile</Text>
                  <View style={[styles.diagBadge, diagData.chrome_profile === 'OK' ? styles.badgeSuccess : styles.badgeWarning]}>
                    <Text style={styles.diagBadgeText}>{diagData.chrome_profile === 'OK' ? 'FOUND' : 'MISSING'}</Text>
                  </View>
                </View>

                <View style={styles.pathBox}>
                  <Text style={styles.pathBoxLabel}>Chrome Profile Path</Text>
                  <Text style={styles.pathBoxText} numberOfLines={3}>{diagData.chrome_path}</Text>
                </View>

                <TouchableOpacity
                  style={styles.saveScheduleBtn}
                  onPress={fetchDiagnostics}
                >
                  <Text style={styles.saveScheduleBtnText}>Run Diagnostics Again</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>No diagnostic data. Make sure API is running.</Text>
                <TouchableOpacity
                  style={[styles.saveScheduleBtn, { marginTop: 12 }]}
                  onPress={fetchDiagnostics}
                >
                  <Text style={styles.saveScheduleBtnText}>Run Diagnostics</Text>
                </TouchableOpacity>
              </View>
            )}
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

  // error banner
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(244,67,54,0.15)',
    borderBottomWidth: 1,
    borderBottomColor: C.red,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  errorBannerText: {
    color: C.red,
    fontSize: 13,
    flex: 1,
  },
  errorBannerDismiss: {
    color: C.red,
    fontSize: 14,
    paddingLeft: 12,
  },

  // save message
  saveMsgOk: {
    color: C.green,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 8,
  },
  saveMsgErr: {
    color: C.red,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 8,
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

  // sniper styling
  sniperForm: {
    backgroundColor: C.surface,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
  },
  formRow: {
    marginBottom: 16,
  },
  formLabel: {
    color: C.textSecondary,
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 8,
  },
  stopBtn: {
    backgroundColor: C.red,
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    marginTop: 16,
  },
  consoleContainer: {
    backgroundColor: '#000',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    padding: 12,
    minHeight: 180,
  },
  consoleText: {
    color: '#00FF00',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 12,
    marginBottom: 4,
  },
  consolePlaceholder: {
    color: C.textSecondary,
    fontSize: 13,
    textAlign: 'center',
    marginTop: 70,
  },

  // Diagnostics Styling
  diagCard: {
    backgroundColor: C.surface,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
  },
  diagRowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  diagLabelItem: {
    color: C.textPrimary,
    fontSize: 15,
    fontWeight: '500',
  },
  diagBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  diagBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: C.textPrimary,
  },
  badgeWarning: {
    backgroundColor: 'rgba(255,152,0,0.2)',
    borderWidth: 1,
    borderColor: '#FF9800',
  },
  pathBox: {
    backgroundColor: '#111',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
    padding: 12,
    marginTop: 16,
    marginBottom: 8,
  },
  pathBoxLabel: {
    color: C.textSecondary,
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  pathBoxText: {
    color: C.textMuted,
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
});
