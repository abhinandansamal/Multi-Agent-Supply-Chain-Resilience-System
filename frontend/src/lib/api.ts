export interface ScanResponse {
  region: string;
  risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  summary: string;
  timestamp: string;
}

export interface PurchaseResponse {
  status: string;
  summary: string;
  timestamp: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  // Trigger a Risk Scan (Watchtower Agent)
  scanRegion: async (region: string): Promise<ScanResponse> => {
    try {
      const res = await fetch(`${API_URL}/api/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Scan API Error:", error);
      throw error;
    }
  },

  // Trigger a Purchase (Procurement Agent)
  purchaseParts: async (part: string, qty: number): Promise<PurchaseResponse> => {
    try {
      const res = await fetch(`${API_URL}/api/purchase`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          part_name: part,
          quantity: qty,
          risk_level: "CRITICAL"
        }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Purchase API Error:", error);
      throw error;
    }
  }
};