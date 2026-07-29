const CASES_CHANGED_EVENT = "cases:changed";
const CASES_CHANGED_STORAGE_KEY = "crm:lastCaseChangeAt";

export function emitCasesChanged(): void {
  if (typeof window === "undefined") {
    return;
  }

  const timestamp = String(Date.now());
  window.localStorage.setItem(CASES_CHANGED_STORAGE_KEY, timestamp);
  window.dispatchEvent(new Event(CASES_CHANGED_EVENT));
}

export function subscribeCasesChanged(listener: () => void): () => void {
  if (typeof window === "undefined") {
    return () => undefined;
  }

  const onWindowEvent = () => listener();
  const onStorageEvent = (event: StorageEvent) => {
    if (event.key === CASES_CHANGED_STORAGE_KEY) {
      listener();
    }
  };

  window.addEventListener(CASES_CHANGED_EVENT, onWindowEvent);
  window.addEventListener("storage", onStorageEvent);

  return () => {
    window.removeEventListener(CASES_CHANGED_EVENT, onWindowEvent);
    window.removeEventListener("storage", onStorageEvent);
  };
}
