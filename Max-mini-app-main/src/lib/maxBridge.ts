import { getMaxIdFromStorage } from "./authStorage";

interface MaxBridgeUser {
  id?: number;
}

interface MaxBridge {
  user?: MaxBridgeUser;
  init?: () => void;
}

interface MaxBridgeWindow extends Window {
  MaxBridge?: MaxBridge;
  Max?: MaxBridge;
}

function getBridgeInstance(): MaxBridge | null {
  if (typeof window === "undefined") {
    return null;
  }
  const win = window as MaxBridgeWindow;
  return win.MaxBridge || win.Max || null;
}

/**
 * In MAX it is required to call bridge initialization before using it.
 * We keep the call resilient because inside the web build bridge might be unavailable.
 */
export function initMaxBridge() {
  try {
    const bridge = getBridgeInstance();
    if (bridge?.init) {
      bridge.init();
      console.log("[maxBridge] Bridge initialised");
    }
  } catch (error) {
    console.warn("[maxBridge] Failed to initialise bridge:", error);
  }
}

/**
 * Returns MAX user id from bridge (or stored fallback) if possible.
 */
export function getMaxUserId(): number | null {
  try {
    const bridge = getBridgeInstance();
    const fromBridge = bridge?.user?.id;
    if (typeof fromBridge === "number" && Number.isFinite(fromBridge)) {
      return fromBridge;
    }
  } catch (error) {
    console.warn("[maxBridge] Unable to read user id from bridge:", error);
  }

  return getMaxIdFromStorage();
}
