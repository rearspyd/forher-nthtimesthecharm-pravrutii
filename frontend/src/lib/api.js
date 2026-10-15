import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API, withCredentials: true });

export const SYMPTOMS = [
  "Cramps", "Headache", "Bloating", "Fatigue", "Back pain", "Breast tenderness", "Acne", "Nausea",
  "Cravings", "Trouble sleeping", "Spotting", "Discharge change", "Dizziness", "Hot flashes", "Constipation", "Diarrhoea",
];
export const MOODS = ["Calm", "Content", "Anxious", "Irritable", "Low", "Tired", "Focused", "Sensitive"];
export const FLOWS = [
  { value: "none", label: "No bleeding" },
  { value: "spotting", label: "Spotting" },
  { value: "light", label: "Light" },
  { value: "medium", label: "Medium" },
  { value: "heavy", label: "Heavy" },
];
export const CYCLE_CONTEXTS = [
  { value: "regular", label: "Fairly regular cycles" },
  { value: "irregular", label: "Irregular or unpredictable cycles" },
  { value: "unknown", label: "Not sure yet" },
  { value: "pregnancy", label: "Pregnant" },
  { value: "postpartum", label: "Postpartum / breastfeeding" },
  { value: "menopause", label: "Perimenopause / menopause" },
  { value: "not_applicable", label: "Estimates not applicable to me" },
];

export const draftKey = (date) => `forher:draft:${date}`;
export const readDraft = (date) => {
  try { return JSON.parse(localStorage.getItem(draftKey(date))); } catch { return null; }
};
export const writeDraft = (date, data) => localStorage.setItem(draftKey(date), JSON.stringify({ ...data, saved_at: Date.now() }));
export const clearDraft = (date) => localStorage.removeItem(draftKey(date));
export const pendingDrafts = () => Object.keys(localStorage).filter((k) => k.startsWith("forher:draft:")).map((k) => k.replace("forher:draft:", ""));
